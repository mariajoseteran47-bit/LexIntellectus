from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import Usuario
from app.models.case import Expediente, ParteProcesal, EstadoExpediente
from app.schemas.case import (
    ExpedienteCreate, ExpedienteUpdate, ExpedienteResponse, ExpedienteListResponse,
    ParteCreate, ParteResponse
)

router = APIRouter()

@router.get("/", response_model=ExpedienteListResponse)
async def list_cases(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    ramo: Optional[str] = None,
    estado_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    tenant_id = current_user.tenant_id
    skip = (page - 1) * size
    
    query = select(Expediente).where(Expediente.tenant_id == tenant_id)
    
    if search:
        search_filter = or_(
            Expediente.numero_causa.ilike(f"%{search}%"),
            Expediente.numero_interno.ilike(f"%{search}%"),
            Expediente.juzgado.ilike(f"%{search}%")
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

@router.post("/", response_model=ExpedienteResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    case_in: ExpedienteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
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
    current_user: Usuario = Depends(get_current_user)
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
    current_user: Usuario = Depends(get_current_user)
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
    current_user: Usuario = Depends(get_current_user)
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
