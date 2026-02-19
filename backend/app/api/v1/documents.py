from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import Optional
from uuid import UUID
import uuid

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import Usuario
from app.models.case import Expediente
from app.models.document import Documento
from app.schemas.document import DocumentResponse, DocumentListResponse
from app.services.storage import storage_service

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    expediente_id: UUID = Form(...),
    descripcion: Optional[str] = Form(None),
    categoria: str = Form("general"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    tenant_id = request.state.tenant_id
    
    # Verify expediente ownership
    expediente = await db.execute(select(Expediente).where(
        Expediente.id == expediente_id,
        Expediente.tenant_id == tenant_id
    ))
    if not expediente.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Expediente not found")

    # Read file content
    content = await file.read()
    
    # Generate storage path: tenant_id/case_id/uuid_filename
    file_ext = file.filename.split('.')[-1] if '.' in file.filename else 'bin'
    object_name = f"{tenant_id}/{expediente_id}/{uuid.uuid4()}.{file_ext}"
    
    # Upload to MinIO
    try:
        storage_service.upload_file(content, object_name, file.content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    # Save metadata to DB
    doc = Documento(
        tenant_id=tenant_id,
        expediente_id=expediente_id,
        nombre_archivo=file.filename,
        tipo_archivo=file.content_type,
        tamano_bytes=len(content),
        storage_path=object_name,
        subido_por_id=current_user.id,
        descripcion=descripcion,
        categoria=categoria
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    
    return doc

@router.get("", response_model=DocumentListResponse)
async def list_documents(
    request: Request,
    expediente_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    tenant_id = request.state.tenant_id
    
    query = select(Documento).where(Documento.tenant_id == tenant_id)
    
    if expediente_id:
        query = query.where(Documento.expediente_id == expediente_id)
        
    query = query.order_by(desc(Documento.created_at))
    
    result = await db.execute(query)
    docs = result.scalars().all()
    
    # Generate presigned URLs for each (or client can request individually)
    # For list, maybe we don't generate URLs to save calls, strictly only on download?
    # Or generate short lived ones. Let's return without URL for list to be fast.
    
    return {
        "items": docs,
        "total": len(docs)
    }

@router.get("/{id}/download")
async def download_document(
    request: Request,
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    tenant_id = request.state.tenant_id
    
    query = select(Documento).where(
        Documento.id == id,
        Documento.tenant_id == tenant_id
    )
    result = await db.execute(query)
    doc = result.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    url = storage_service.get_presigned_url(doc.storage_path)
    return {"url": url}

@router.delete("/{id}", status_code=204)
async def delete_document(
    request: Request,
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    tenant_id = request.state.tenant_id
    
    query = select(Documento).where(
        Documento.id == id,
        Documento.tenant_id == tenant_id
    )
    result = await db.execute(query)
    doc = result.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    # Delete from MinIO
    storage_service.delete_file(doc.storage_path)
    
    # Delete from DB
    await db.delete(doc)
    await db.commit()
