from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.rbac import require_permission
from app.models.user import Usuario
from app.models.case import Expediente, ParteProcesal, EstadoExpediente
from app.models.case_extended import NotaInterna, HistorialEstado, ActuacionProcesal, EtapaProcesal
from app.schemas.case import (
    ExpedienteCreate, ExpedienteUpdate, ExpedienteResponse, ExpedienteListResponse,
    ParteCreate, ParteResponse, NotaInternaCreate, NotaInternaResponse, EstadoResponse
)

router = APIRouter(prefix="/cases", tags=["Cases"])

@router.get("", response_model=ExpedienteListResponse)
async def list_cases(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    ramo: Optional[str] = None,
    tipo_servicio: Optional[str] = None,
    estado_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("cases.read"))
):
    tenant_id = current_user.tenant_id
    skip = (page - 1) * size
    
    query = select(Expediente).where(Expediente.tenant_id == tenant_id)
    
    if search:
        search_filter = or_(
            Expediente.numero_causa.ilike(f"%{search}%"),
            Expediente.numero_interno.ilike(f"%{search}%"),
            Expediente.juzgado.ilike(f"%{search}%"),
            Expediente.resumen.ilike(f"%{search}%"),
        )
        query = query.where(search_filter)
    
    if ramo:
        query = query.where(Expediente.ramo == ramo)
    
    if tipo_servicio:
        query = query.where(Expediente.tipo_servicio == tipo_servicio)
    
    if estado_id:
        query = query.where(Expediente.estado_id == estado_id)
        
    # Total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Validation for page
    if total == 0:
        return {"items": [], "total": 0, "page": page, "size": size}
        
    # Fetch items with eager-loaded parties
    query = query.options(selectinload(Expediente.partes)).order_by(desc(Expediente.created_at)).offset(skip).limit(size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size
    }

@router.post("", response_model=ExpedienteResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    case_in: ExpedienteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("cases.create"))
):
    tenant_id = current_user.tenant_id
    
    # Generate simple internal number (placeholder logic)
    # in prod, use a sequence or counter table
    import datetime
    timestamp_code = datetime.datetime.now().strftime("%Y%m%d%H%M")
    numero_interno = f"EXP-{timestamp_code}"
    
    new_case = Expediente(
        **case_in.model_dump(exclude={"partes"}),
        tenant_id=tenant_id,
        numero_interno=numero_interno
    )
    
    if not new_case.abogado_responsable_id:
        new_case.abogado_responsable_id = current_user.id
        
    db.add(new_case)
    await db.flush() # get ID
    
    # Add parties
    for parte_in in case_in.partes:
        new_parte = ParteProcesal(
            **parte_in.model_dump(),
            expediente_id=new_case.id
        )
        db.add(new_parte)
        
    await db.commit()
    await db.refresh(new_case, attribute_names=["partes"])
    return new_case

@router.get("/{case_id}", response_model=ExpedienteResponse)
async def get_case(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("cases.read"))
):
    tenant_id = current_user.tenant_id
    query = select(Expediente).where(
        Expediente.id == case_id,
        Expediente.tenant_id == tenant_id
    )
    result = await db.execute(query)
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    # Ensure parties are loaded (lazy loading might require explicit option or refresh)
    # But lazy='select' (default) on async requires await, or selectinload
    # However, create_case did refresh. For get, we might need options.
    # Let's use explicit eager load if needed, but Pydantic from_attributes usually triggers it?
    # No, asyncpg doesn't trigger lazy loads. We must use selectinload.
    
    # Re-query with eager load
    from sqlalchemy.orm import selectinload
    query = select(Expediente).options(selectinload(Expediente.partes)).where(
        Expediente.id == case_id,
        Expediente.tenant_id == tenant_id
    )
    result = await db.execute(query)
    case = result.scalar_one_or_none()
    
    return case

@router.patch("/{case_id}", response_model=ExpedienteResponse)
async def update_case(
    case_id: UUID,
    case_in: ExpedienteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("cases.update"))
):
    tenant_id = current_user.tenant_id
    
    # Fetch
    query = select(Expediente).where(
        Expediente.id == case_id,
        Expediente.tenant_id == tenant_id
    )
    result = await db.execute(query)
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    # Update
    update_data = case_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(case, field, value)
        
    await db.commit()
    
    # Return with relations
    from sqlalchemy.orm import selectinload
    query = select(Expediente).options(selectinload(Expediente.partes)).where(Expediente.id == case_id)
    result = await db.execute(query)
    case = result.scalar_one_or_none()
    
    return case

@router.post("/{case_id}/partes", response_model=ParteResponse)
async def add_party(
    case_id: UUID,
    parte_in: ParteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("cases.create"))
):
    tenant_id = current_user.tenant_id
    
    # Verify case ownership
    query = select(Expediente).where(
        Expediente.id == case_id,
        Expediente.tenant_id == tenant_id
    )
    result = await db.execute(query)
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    new_parte = ParteProcesal(
        **parte_in.model_dump(),
        expediente_id=case_id
    )
    db.add(new_parte)
    await db.commit()
    await db.refresh(new_parte)
    return new_parte


@router.patch("/{case_id}/status")
async def change_case_status(
    case_id: UUID,
    status_update: dict,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("cases.update"))
):
    """Change the status of a case (workflow transition)."""
    tenant_id = current_user.tenant_id
    
    query = select(Expediente).where(
        Expediente.id == case_id,
        Expediente.tenant_id == tenant_id
    )
    result = await db.execute(query)
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    new_status_id = status_update.get("estado_id")
    if not new_status_id:
        raise HTTPException(status_code=400, detail="estado_id is required")
    
    # Verify the new status exists and belongs to tenant
    status_query = select(EstadoExpediente).where(
        EstadoExpediente.id == new_status_id,
        EstadoExpediente.tenant_id == tenant_id
    )
    status_result = await db.execute(status_query)
    new_status = status_result.scalar_one_or_none()
    
    if not new_status:
        raise HTTPException(status_code=404, detail="Status not found")
    
    old_status_id = case.estado_id
    case.estado_id = new_status.id
    
    # Create history record
    history = HistorialEstado(
        expediente_id=case_id,
        estado_anterior_id=old_status_id,
        estado_nuevo_id=new_status.id,
        registrado_por_id=current_user.id,
        motivo=f"Cambio de estado administrativo a {new_status.nombre}"
    )
    db.add(history)

    # If marking as final status, set close date
    if new_status.es_final and not case.fecha_cierre:
        from datetime import date
        case.fecha_cierre = date.today()
    
    await db.commit()
    await db.refresh(case)
    
    return {
        "id": str(case.id),
        "estado_id": str(case.estado_id),
        "estado_nombre": new_status.nombre,
        "fecha_cierre": str(case.fecha_cierre) if case.fecha_cierre else None,
        "message": f"Estado cambiado a '{new_status.nombre}'"
    }


@router.get("/statuses/list")
async def list_case_statuses(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("cases.read"))
):
    """List all available case statuses for the tenant."""
    tenant_id = current_user.tenant_id
    query = select(EstadoExpediente).where(
        EstadoExpediente.tenant_id == tenant_id
    ).order_by(EstadoExpediente.orden)
    
    result = await db.execute(query)
    statuses = result.scalars().all()
    
    return [
        {
            "id": str(s.id),
            "codigo": s.codigo,
            "nombre": s.nombre,
            "color_hex": s.color_hex,
            "es_final": s.es_final,
            "orden": s.orden,
        }
        for s in statuses
    ]


# === Bóveda de Discusión / Notas Internas ===

@router.get("/{case_id}/notes", response_model=List[NotaInternaResponse])
async def list_case_notes(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("cases.read"))
):
    """Obtener todas las notas e hilos de discusión del expediente."""
    tenant_id = current_user.tenant_id

    # Verify case ownership
    query = select(Expediente).where(
        Expediente.id == case_id,
        Expediente.tenant_id == tenant_id
    )
    result = await db.execute(query)
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")

    # Fetch notes with author data
    notes_query = select(NotaInterna).options(
        selectinload(NotaInterna.autor)
    ).where(
        NotaInterna.expediente_id == case_id
    ).order_by(NotaInterna.created_at.desc())
    
    notes_result = await db.execute(notes_query)
    notes = notes_result.scalars().all()

    # Manual mapping for autor_nombre and autor_foto
    response_notes = []
    for note in notes:
        note_dict = note.__dict__.copy()
        if note.autor:
            note_dict["autor_nombre"] = f"{note.autor.nombre} {note.autor.apellido}"
            note_dict["autor_foto"] = getattr(note.autor, "foto_url", None)
        response_notes.append(note_dict)

    return response_notes


@router.post("/{case_id}/notes", response_model=NotaInternaResponse)
async def create_case_note(
    case_id: UUID,
    note_in: NotaInternaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("cases.update"))
):
    """Crear una nueva nota interna o actualización en la bóveda de discusión."""
    tenant_id = current_user.tenant_id

    # Verify case ownership
    query = select(Expediente).where(
        Expediente.id == case_id,
        Expediente.tenant_id == tenant_id
    )
    result = await db.execute(query)
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")

    # Save note
    new_note = NotaInterna(
        expediente_id=case_id,
        autor_id=current_user.id,
        tipo=note_in.tipo,
        contenido=note_in.contenido,
        es_privada=note_in.es_privada,
        prioridad=note_in.prioridad
    )
    db.add(new_note)
    await db.commit()
    await db.refresh(new_note)

    # Attach author explicitly for the response
    new_note.autor = current_user
    note_dict = new_note.__dict__.copy()
    note_dict["autor_nombre"] = f"{current_user.nombre} {current_user.apellido}"
    note_dict["autor_foto"] = getattr(current_user, "foto_url", None)

    return note_dict


@router.get("/config/statuses", response_model=List[EstadoResponse])
async def get_case_statuses(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("cases.read"))
):
    """Obtener la lista de estados configurados para el despacho."""
    query = select(EstadoExpediente).where(
        EstadoExpediente.tenant_id == current_user.tenant_id
    ).order_by(EstadoExpediente.orden)
    
    result = await db.execute(query)
    return result.scalars().all()


# === WORKFLOW / ETAPAS PROCESALES ===

@router.get("/workflow/stages")
async def list_workflow_stages(
    ramo: Optional[str] = None,
    tipo_servicio: Optional[str] = None,
    tipo_proceso: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("cases.read"))
):
    """Listar etapas procesales específicas para un ramo, tipo de servicio, y/o tipo de proceso."""
    from app.models.case_extended import EtapaProcesal
    
    query = select(EtapaProcesal)
    
    # For litigation: filter by ramo (and optionally tipo_proceso)
    if ramo:
        query = query.where(EtapaProcesal.ramo == ramo)
    
    # For non-litigation services: filter by tipo_servicio
    if tipo_servicio:
        query = query.where(EtapaProcesal.tipo_servicio == tipo_servicio)
    
    if tipo_proceso:
        query = query.where(EtapaProcesal.tipo_proceso == tipo_proceso)
    
    query = query.order_by(EtapaProcesal.orden)
    result = await db.execute(query)
    stages = result.scalars().all()
    
    return [
        {
            "id": str(s.id),
            "ramo": s.ramo,
            "tipo_proceso": s.tipo_proceso,
            "nombre": s.nombre,
            "orden": s.orden,
            "dias_plazo_legal": s.dias_plazo_legal,
            "es_final": s.es_final
        }
        for s in stages
    ]


@router.patch("/{case_id}/stage")
async def change_case_stage(
    case_id: UUID,
    stage_update: dict,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("cases.update"))
):
    """Actualizar la etapa procesal actual del expediente."""
    tenant_id = current_user.tenant_id
    
    query = select(Expediente).where(
        Expediente.id == case_id,
        Expediente.tenant_id == tenant_id
    )
    result = await db.execute(query)
    case = result.scalar_one_or_none()
    
    if not case:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    
    new_stage_id = stage_update.get("etapa_id")
    if not new_stage_id:
        raise HTTPException(status_code=400, detail="etapa_id es requerido")
    
    from app.models.case_extended import EtapaProcesal
    stage_query = select(EtapaProcesal).where(EtapaProcesal.id == new_stage_id)
    stage_result = await db.execute(stage_query)
    stage = stage_result.scalar_one_or_none()
    
    if not stage:
        raise HTTPException(status_code=404, detail="Etapa procesal no encontrada")
        
    case.etapa_actual_id = stage.id
    
    # Log to Timeline as a system event
    event = ActuacionProcesal(
        expediente_id=case_id,
        tipo='otro',
        titulo=f"Cambio de Etapa: {stage.nombre}",
        descripcion=f"El expediente ha pasado a la fase de {stage.nombre}.",
        fecha_evento=datetime.utcnow(),
        etapa_procesal_id=stage.id,
        registrado_por_id=current_user.id
    )
    db.add(event)
    
    await db.commit()
    await db.refresh(case)
    
    return {
        "id": str(case.id),
        "etapa_actual_id": str(case.etapa_actual_id),
        "etapa_nombre": stage.nombre,
        "message": f"Etapa procesal cambiada a '{stage.nombre}'"
    }
