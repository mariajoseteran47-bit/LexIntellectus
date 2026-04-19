from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.rbac import require_permission
from app.models.user import Usuario
from app.models.case import Expediente, ParteProcesal, EstadoExpediente
from app.schemas.case import (
    ExpedienteCreate, ExpedienteUpdate, ExpedienteResponse, ExpedienteListResponse,
    ParteCreate, ParteResponse
)

router = APIRouter(prefix="/cases", tags=["Cases"])

@router.get("", response_model=ExpedienteListResponse)
async def list_cases(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    ramo: Optional[str] = None,
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
    
    old_status_id = str(case.estado_id) if case.estado_id else None
    case.estado_id = new_status.id
    
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

