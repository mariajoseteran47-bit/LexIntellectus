"""
LexIntellectus - Evidence Management API
Gestión de pruebas procesales: CRUD, adjuntos multimedia, cadena de custodia.
Plan Estratégico v3.0, Fase 2A.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.rbac import require_permission
from app.models.user import Usuario
from app.models.case import Expediente
from app.models.evidence import Prueba, PruebaDocumento
from app.schemas.evidence import (
    EvidenceCreate, EvidenceUpdate, EvidenceResponse,
    EvidenceListResponse, EvidenceDocumentCreate, EvidenceDocumentResponse,
)

router = APIRouter(prefix="/evidences", tags=["Evidence Management"])


@router.get("", response_model=EvidenceListResponse)
async def list_evidences(
    expediente_id: Optional[str] = Query(None),
    tipo_prueba: Optional[str] = Query(None),
    valoracion: Optional[str] = Query(None),
    estado_procesal: Optional[str] = Query(None),
    current_user: Usuario = Depends(require_permission("cases.read")),
    db: AsyncSession = Depends(get_db),
):
    """List evidences, optionally filtered by case, type, weight, or status."""
    query = (
        select(Prueba)
        .options(selectinload(Prueba.adjuntos))
        .where(Prueba.tenant_id == current_user.tenant_id)
    )

    if expediente_id:
        query = query.where(Prueba.expediente_id == expediente_id)
    if tipo_prueba:
        query = query.where(Prueba.tipo_prueba == tipo_prueba)
    if valoracion:
        query = query.where(Prueba.valoracion == valoracion)
    if estado_procesal:
        query = query.where(Prueba.estado_procesal == estado_procesal)

    count_q = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_q) or 0

    result = await db.execute(query.order_by(Prueba.created_at.desc()))
    evidences = result.scalars().unique().all()

    return EvidenceListResponse(
        items=[EvidenceResponse.model_validate(e) for e in evidences],
        total=total,
    )


@router.get("/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(
    evidence_id: str,
    current_user: Usuario = Depends(require_permission("cases.read")),
    db: AsyncSession = Depends(get_db),
):
    """Get evidence detail with all attachments."""
    result = await db.execute(
        select(Prueba)
        .options(selectinload(Prueba.adjuntos))
        .where(
            Prueba.id == evidence_id,
            Prueba.tenant_id == current_user.tenant_id,
        )
    )
    evidence = result.scalar_one_or_none()
    if not evidence:
        raise HTTPException(status_code=404, detail="Prueba no encontrada")
    return EvidenceResponse.model_validate(evidence)


@router.post("", response_model=EvidenceResponse, status_code=201)
async def create_evidence(
    data: EvidenceCreate,
    current_user: Usuario = Depends(require_permission("cases.create")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new evidence record linked to a case."""
    # Verify case belongs to tenant
    result = await db.execute(
        select(Expediente).where(
            Expediente.id == data.expediente_id,
            Expediente.tenant_id == current_user.tenant_id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Expediente no encontrado en este despacho")

    evidence = Prueba(
        tenant_id=current_user.tenant_id,
        registrado_por_id=current_user.id,
        cadena_custodia=[{
            "fecha": str(data.fecha_proposicion or ""),
            "accion": "Registro inicial en el sistema",
            "responsable": f"{current_user.nombre} {current_user.apellido}",
            "observaciones": "Creación automática al registrar la prueba"
        }],
        **data.model_dump()
    )
    db.add(evidence)
    await db.flush()

    # Reload with relationships
    result = await db.execute(
        select(Prueba)
        .options(selectinload(Prueba.adjuntos))
        .where(Prueba.id == evidence.id)
    )
    return EvidenceResponse.model_validate(result.scalar_one())


@router.patch("/{evidence_id}", response_model=EvidenceResponse)
async def update_evidence(
    evidence_id: str,
    data: EvidenceUpdate,
    current_user: Usuario = Depends(require_permission("cases.update")),
    db: AsyncSession = Depends(get_db),
):
    """Update evidence metadata, status, or strategic notes."""
    result = await db.execute(
        select(Prueba)
        .options(selectinload(Prueba.adjuntos))
        .where(
            Prueba.id == evidence_id,
            Prueba.tenant_id == current_user.tenant_id,
        )
    )
    evidence = result.scalar_one_or_none()
    if not evidence:
        raise HTTPException(status_code=404, detail="Prueba no encontrada")

    update_data = data.model_dump(exclude_unset=True)

    # If status changed, add to chain of custody
    if 'estado_procesal' in update_data and update_data['estado_procesal'] != evidence.estado_procesal:
        custodia = list(evidence.cadena_custodia or [])
        custodia.append({
            "fecha": str(data.fecha_admision or data.fecha_evacuacion or ""),
            "accion": f"Cambio de estado: {evidence.estado_procesal} → {update_data['estado_procesal']}",
            "responsable": f"{current_user.nombre} {current_user.apellido}",
            "observaciones": ""
        })
        update_data['cadena_custodia'] = custodia

    for field, value in update_data.items():
        setattr(evidence, field, value)

    await db.flush()
    return EvidenceResponse.model_validate(evidence)


@router.delete("/{evidence_id}", status_code=204)
async def delete_evidence(
    evidence_id: str,
    current_user: Usuario = Depends(require_permission("cases.delete")),
    db: AsyncSession = Depends(get_db),
):
    """Delete an evidence record and its attachments."""
    result = await db.execute(
        select(Prueba).where(
            Prueba.id == evidence_id,
            Prueba.tenant_id == current_user.tenant_id,
        )
    )
    evidence = result.scalar_one_or_none()
    if not evidence:
        raise HTTPException(status_code=404, detail="Prueba no encontrada")

    await db.delete(evidence)
    await db.flush()


# === ADJUNTOS MULTIMEDIA ===

@router.post("/{evidence_id}/attachments", response_model=EvidenceDocumentResponse, status_code=201)
async def attach_document(
    evidence_id: str,
    data: EvidenceDocumentCreate,
    current_user: Usuario = Depends(require_permission("cases.update")),
    db: AsyncSession = Depends(get_db),
):
    """Attach an existing document (from MinIO) to an evidence record."""
    result = await db.execute(
        select(Prueba).where(
            Prueba.id == evidence_id,
            Prueba.tenant_id == current_user.tenant_id,
        )
    )
    evidence = result.scalar_one_or_none()
    if not evidence:
        raise HTTPException(status_code=404, detail="Prueba no encontrada")

    attachment = PruebaDocumento(
        prueba_id=evidence.id,
        **data.model_dump()
    )
    db.add(attachment)

    # Update chain of custody
    custodia = list(evidence.cadena_custodia or [])
    custodia.append({
        "fecha": str(datetime.utcnow().date()),
        "accion": f"Documento adjuntado: {data.descripcion or 'Archivo'}",
        "responsable": f"{current_user.nombre} {current_user.apellido}",
        "observaciones": f"tipo_medio: {data.tipo_medio}, es_original: {data.es_original}"
    })
    evidence.cadena_custodia = custodia

    await db.flush()
    return EvidenceDocumentResponse.model_validate(attachment)


@router.delete("/{evidence_id}/attachments/{attachment_id}", status_code=204)
async def remove_attachment(
    evidence_id: str,
    attachment_id: str,
    current_user: Usuario = Depends(require_permission("cases.update")),
    db: AsyncSession = Depends(get_db),
):
    """Remove a document attachment from an evidence record."""
    result = await db.execute(
        select(PruebaDocumento)
        .join(Prueba)
        .where(
            PruebaDocumento.id == attachment_id,
            PruebaDocumento.prueba_id == evidence_id,
            Prueba.tenant_id == current_user.tenant_id,
        )
    )
    attachment = result.scalar_one_or_none()
    if not attachment:
        raise HTTPException(status_code=404, detail="Adjunto no encontrado")

    await db.delete(attachment)
    await db.flush()


# Import at top for chain of custody timestamp
from datetime import datetime
