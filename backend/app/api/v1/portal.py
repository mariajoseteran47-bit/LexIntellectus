from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import Usuario
from app.models.case import Expediente
from app.models.document import Documento
from app.models.billing import Factura
from app.schemas.case import ExpedienteResponse, ExpedienteListResponse
from app.schemas.document import DocumentResponse, DocumentListResponse
from app.schemas.billing import FacturaResponse
from app.services.storage import storage_service
from app.core.rate_limit import default_rate_limiter

router = APIRouter(prefix="/portal", tags=["Client Portal"], dependencies=[Depends(default_rate_limiter)])

def require_client_role(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    """Ensure the logged-in user is a client."""
    if current_user.tipo_usuario != "cliente":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso exclusivo para clientes",
        )
    return current_user

@router.get("/cases", response_model=ExpedienteListResponse)
async def list_client_cases(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_client_role)
):
    """List all legal cases where the logged-in user is the primary client."""
    tenant_id = current_user.tenant_id
    skip = (page - 1) * size

    # Filter strictly by the current user's client profile and tenant
    query = select(Expediente).where(
        Expediente.tenant_id == tenant_id,
        Expediente.cliente_principal_id == current_user.id
    )

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    if total == 0:
        return {"items": [], "total": 0, "page": page, "size": size}

    # Fetch items with eager-loaded parties (partes)
    query = query.options(selectinload(Expediente.partes)).order_by(desc(Expediente.created_at)).offset(skip).limit(size)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size
    }

@router.get("/cases/{id}", response_model=ExpedienteResponse)
async def get_client_case(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_client_role)
):
    """Retrieve details of a specific case, verifying client ownership."""
    tenant_id = current_user.tenant_id

    query = select(Expediente).options(selectinload(Expediente.partes)).where(
        Expediente.id == id,
        Expediente.tenant_id == tenant_id,
        Expediente.cliente_principal_id == current_user.id
    )
    result = await db.execute(query)
    case = result.scalar_one_or_none()

    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expediente no encontrado o sin autorización"
        )
    return case

@router.get("/documents", response_model=DocumentListResponse)
async def list_client_documents(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_client_role)
):
    """List all non-confidential documents shared in the client's cases."""
    tenant_id = current_user.tenant_id

    # Select all documents from cases owned by this client
    query = (
        select(Documento)
        .join(Expediente)
        .where(
            Documento.tenant_id == tenant_id,
            Expediente.cliente_principal_id == current_user.id,
            Documento.es_confidencial == False
        )
        .order_by(desc(Documento.created_at))
    )

    result = await db.execute(query)
    docs = result.scalars().all()

    # Cast SQLAlchemy models to Pydantic responses
    response_items = []
    for doc in docs:
        response_items.append(
            DocumentResponse(
                id=doc.id,
                expediente_id=doc.expediente_id,
                nombre_archivo=doc.nombre_archivo,
                tipo_archivo=doc.tipo_archivo,
                tamano_bytes=doc.tamano_bytes,
                created_at=doc.created_at,
                subido_por_id=doc.subido_por_id,
                descripcion=doc.descripcion,
                categoria=doc.categoria,
                tags=doc.tags
            )
        )

    return {
        "items": response_items,
        "total": len(response_items)
    }

@router.get("/documents/{id}/download")
async def download_client_document(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_client_role)
):
    """Generate a secure, short-lived presigned URL to download a shared document."""
    tenant_id = current_user.tenant_id

    query = (
        select(Documento)
        .join(Expediente)
        .where(
            Documento.id == id,
            Documento.tenant_id == tenant_id,
            Expediente.cliente_principal_id == current_user.id,
            Documento.es_confidencial == False
        )
    )

    result = await db.execute(query)
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado o sin autorización"
        )

    try:
        url = storage_service.get_presigned_url(doc.storage_path)
        return {"url": url}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar enlace de descarga: {str(e)}"
        )

@router.get("/invoices", response_model=List[FacturaResponse])
async def list_client_invoices(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_client_role)
):
    """List all published (non-draft) invoices for this client."""
    tenant_id = current_user.tenant_id

    # Fetch invoices where client_id == current_user.id and status != 'borrador'
    query = (
        select(Factura)
        .options(selectinload(Factura.lineas))
        .where(
            Factura.tenant_id == tenant_id,
            Factura.client_id == current_user.id,
            Factura.estado != "borrador"
        )
        .order_by(desc(Factura.fecha_emision))
    )

    result = await db.execute(query)
    invoices = result.scalars().all()
    return invoices

from fastapi import Response
from app.models.case import PlazoFatal
from app.services.calendar_service import CalendarService

@router.get("/calendar/ical.ics")
async def get_portal_ical(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_client_role)
):
    """Export all deadlines for the client's cases in RFC 5545 iCalendar format."""
    # Select all pending deadlines for cases owned by this client
    deadlines_query = (
        select(PlazoFatal)
        .join(Expediente)
        .where(
            Expediente.tenant_id == current_user.tenant_id,
            Expediente.cliente_principal_id == current_user.id,
            PlazoFatal.status == "pendiente"
        )
    )
    result = await db.execute(deadlines_query)
    deadlines = result.scalars().all()

    # Generate iCal content
    ical_content = CalendarService.generate_ical(
        deadlines,
        calendar_name="LexIntellectus - Mis Plazos Procesales"
    )

    return Response(
        content=ical_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": "attachment; filename=lexintellectus_calendar.ics"
        }
    )


import hashlib
from datetime import datetime
from pydantic import BaseModel
from fastapi import Request
from app.models.document import DocumentoFirma

class DocumentSignRequest(BaseModel):
    signature_svg: str

@router.post("/documents/{id}/sign")
async def sign_client_document(
    id: UUID,
    req: DocumentSignRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_client_role)
):
    """Electronically sign a document in the client portal, generating a security audit trail."""
    tenant_id = current_user.tenant_id

    # Fetch document and verify client ownership
    query = (
        select(Documento)
        .join(Expediente)
        .where(
            Documento.id == id,
            Documento.tenant_id == tenant_id,
            Expediente.cliente_principal_id == current_user.id,
            Documento.es_confidencial == False
        )
    )
    result = await db.execute(query)
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado o sin autorización"
        )

    # Capture metadata
    ip = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent", "Unknown")
    timestamp = datetime.utcnow()

    # Calculate cryptographic SHA-256 signature hash
    raw_payload = f"{doc.storage_path}|{current_user.id}|{ip}|{user_agent}|{req.signature_svg}|{timestamp.isoformat()}"
    signature_hash = hashlib.sha256(raw_payload.encode()).hexdigest()

    # Create audit record
    import uuid
    sig_id = uuid.uuid4()
    sig = DocumentoFirma(
        id=sig_id,
        tenant_id=tenant_id,
        documento_id=id,
        usuario_id=current_user.id,
        firma_hash=signature_hash,
        ip_address=ip,
        user_agent=user_agent,
        signature_svg=req.signature_svg,
        signed_at=timestamp
    )
    db.add(sig)

    # Mark document as signed by adding 'firmado' to its tags if not already there
    current_tags = list(doc.tags) if doc.tags else []
    if "firmado" not in current_tags:
        current_tags.append("firmado")
        doc.tags = current_tags

    await db.commit()

    return {
        "status": "success",
        "message": "Documento firmado electrónicamente con éxito",
        "signature_id": sig_id,
        "hash": signature_hash,
        "signed_at": timestamp
    }


