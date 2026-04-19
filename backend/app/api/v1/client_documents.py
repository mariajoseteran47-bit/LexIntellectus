"""
LexIntellectus - Client Documents API
Upload, download y gestión de documentos asociados a clientes y representantes.
Integra con MinIO para almacenamiento S3.
"""

import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from pydantic import BaseModel
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.rbac import require_permission
from app.models.user import Usuario
from app.models.client import PerfilCliente
from app.models.client_document import DocumentoCliente
from app.services.storage import storage_service

router = APIRouter(prefix="/client-documents", tags=["Client Documents"])


# === Schemas ===

class ClientDocumentResponse(BaseModel):
    id: UUID
    client_profile_id: UUID
    representative_id: Optional[UUID] = None
    tipo_documento: Optional[str] = None
    nombre_archivo: str
    tipo_archivo: Optional[str] = None
    tamano_bytes: Optional[int] = None
    descripcion: Optional[str] = None
    numero_documento: Optional[str] = None
    fecha_emision: Optional[datetime] = None
    fecha_vencimiento: Optional[datetime] = None
    vigente: bool = True
    download_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ClientDocumentListResponse(BaseModel):
    items: List[ClientDocumentResponse]
    total: int


# === Endpoints ===

@router.get("/{profile_id}", response_model=ClientDocumentListResponse)
async def list_client_documents(
    profile_id: str,
    tipo: Optional[str] = Query(None),
    representative_id: Optional[str] = Query(None),
    current_user: Usuario = Depends(require_permission("clients.read")),
    db: AsyncSession = Depends(get_db),
):
    """List all documents for a client profile, optionally filtered by type or representative."""
    # Verify profile belongs to tenant
    profile_check = await db.execute(
        select(PerfilCliente).where(
            PerfilCliente.id == profile_id,
            PerfilCliente.tenant_id == current_user.tenant_id,
        )
    )
    if not profile_check.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Perfil de cliente no encontrado")

    query = select(DocumentoCliente).where(
        DocumentoCliente.client_profile_id == profile_id,
        DocumentoCliente.tenant_id == current_user.tenant_id,
    )

    if tipo:
        query = query.where(DocumentoCliente.tipo_documento == tipo)
    if representative_id:
        query = query.where(DocumentoCliente.representative_id == representative_id)

    count_q = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_q) or 0

    result = await db.execute(query.order_by(DocumentoCliente.created_at.desc()))
    docs = result.scalars().all()

    items = []
    for doc in docs:
        item = ClientDocumentResponse.model_validate(doc)
        try:
            item.download_url = storage_service.get_presigned_url(doc.storage_path, expiration_minutes=30)
        except Exception:
            item.download_url = None
        items.append(item)

    return ClientDocumentListResponse(items=items, total=total)


@router.post("/{profile_id}/upload", response_model=ClientDocumentResponse, status_code=201)
async def upload_client_document(
    profile_id: str,
    file: UploadFile = File(...),
    tipo_documento: str = Form("otro"),
    descripcion: Optional[str] = Form(None),
    numero_documento: Optional[str] = Form(None),
    representative_id: Optional[str] = Form(None),
    current_user: Usuario = Depends(require_permission("clients.update")),
    db: AsyncSession = Depends(get_db),
):
    """Upload a document and associate it with a client or representative."""
    # Verify profile belongs to tenant
    profile_check = await db.execute(
        select(PerfilCliente).where(
            PerfilCliente.id == profile_id,
            PerfilCliente.tenant_id == current_user.tenant_id,
        )
    )
    if not profile_check.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Perfil de cliente no encontrado")

    # Read file
    file_data = await file.read()
    if len(file_data) > 20 * 1024 * 1024:  # 20MB limit
        raise HTTPException(status_code=413, detail="Archivo demasiado grande (máx 20MB)")

    # Build MinIO path: clients/{profile_id}/{tipo}/{uuid}_{filename}
    file_ext = file.filename.split(".")[-1] if "." in file.filename else "bin"
    object_name = f"clients/{profile_id}/{tipo_documento}/{uuid.uuid4().hex[:8]}_{file.filename}"

    # Upload to MinIO
    try:
        storage_service.upload_file(file_data, object_name, file.content_type or "application/octet-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir archivo: {str(e)}")

    # Save record
    doc = DocumentoCliente(
        tenant_id=current_user.tenant_id,
        client_profile_id=profile_id,
        representative_id=representative_id if representative_id else None,
        tipo_documento=tipo_documento,
        nombre_archivo=file.filename,
        tipo_archivo=file.content_type,
        tamano_bytes=len(file_data),
        storage_path=object_name,
        descripcion=descripcion,
        numero_documento=numero_documento,
        subido_por_id=current_user.id,
    )
    db.add(doc)
    await db.flush()

    response = ClientDocumentResponse.model_validate(doc)
    try:
        response.download_url = storage_service.get_presigned_url(object_name, expiration_minutes=30)
    except Exception:
        pass

    return response


@router.delete("/{profile_id}/{document_id}", status_code=204)
async def delete_client_document(
    profile_id: str,
    document_id: str,
    current_user: Usuario = Depends(require_permission("clients.update")),
    db: AsyncSession = Depends(get_db),
):
    """Delete a client document from the database and MinIO."""
    result = await db.execute(
        select(DocumentoCliente).where(
            DocumentoCliente.id == document_id,
            DocumentoCliente.client_profile_id == profile_id,
            DocumentoCliente.tenant_id == current_user.tenant_id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    # Delete from MinIO
    try:
        storage_service.delete_file(doc.storage_path)
    except Exception:
        pass  # If MinIO fails, still remove DB record

    await db.delete(doc)
    await db.flush()
