from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from typing import List, Optional
from uuid import UUID
from datetime import date, timedelta

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import Usuario
from app.models.case import PlazoFatal, Expediente
from app.schemas.deadline import DeadlineCreate, DeadlineUpdate, DeadlineResponse, DeadlineListResponse

router = APIRouter(prefix="/deadlines", tags=["Deadlines"])

@router.get("", response_model=DeadlineListResponse)
async def list_deadlines(
    request: Request,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    expediente_id: Optional[UUID] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    tenant_id = request.state.tenant_id
    skip = (page - 1) * size
    
    # We need to join with Expediente to ensure tenant ownership implicitly?
    # Or PlazoFatal should have tenant_id?
    # PlazoFatal doesn't have tenant_id in the model I defined earlier.
    # It links to Expediente which has tenant_id.
    
    query = select(PlazoFatal).join(Expediente).where(Expediente.tenant_id == tenant_id)
    
    if expediente_id:
        query = query.where(PlazoFatal.expediente_id == expediente_id)
        
    if status_filter:
        query = query.where(PlazoFatal.status == status_filter)
        
    if start_date:
        query = query.where(PlazoFatal.fecha_vencimiento >= start_date)
    if end_date:
        query = query.where(PlazoFatal.fecha_vencimiento <= end_date)
        
    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    if total == 0:
        return {"items": [], "total": 0, "page": page, "size": size}
        
    # Order by due date asc (soonest first)
    query = query.order_by(PlazoFatal.fecha_vencimiento.asc()).offset(skip).limit(size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size
    }

@router.post("", response_model=DeadlineResponse, status_code=status.HTTP_201_CREATED)
async def create_deadline(
    request: Request,
    deadline_in: DeadlineCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    tenant_id = request.state.tenant_id
    
    # Verify expediente belongs to tenant
    expediente = await db.execute(
        select(Expediente).where(
            Expediente.id == deadline_in.expediente_id,
            Expediente.tenant_id == tenant_id
        )
    )
    if not expediente.scalar_one_or_none():
         raise HTTPException(status_code=404, detail="Expediente not found")
         
    new_deadline = PlazoFatal(**deadline_in.model_dump())
    db.add(new_deadline)
    await db.commit()
    await db.refresh(new_deadline)
    return new_deadline

@router.get("/{id}", response_model=DeadlineResponse)
async def get_deadline(
    request: Request,
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    tenant_id = request.state.tenant_id
    
    query = select(PlazoFatal).join(Expediente).where(
        PlazoFatal.id == id,
        Expediente.tenant_id == tenant_id
    )
    result = await db.execute(query)
    deadline = result.scalar_one_or_none()
    
    if not deadline:
        raise HTTPException(status_code=404, detail="Deadline not found")
        
    return deadline

@router.patch("/{id}", response_model=DeadlineResponse)
async def update_deadline(
    request: Request,
    id: UUID,
    deadline_in: DeadlineUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    tenant_id = request.state.tenant_id
    
    query = select(PlazoFatal).join(Expediente).where(
        PlazoFatal.id == id,
        Expediente.tenant_id == tenant_id
    )
    result = await db.execute(query)
    deadline = result.scalar_one_or_none()
    
    if not deadline:
        raise HTTPException(status_code=404, detail="Deadline not found")
        
    update_data = deadline_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(deadline, field, value)
        
    await db.commit()
    await db.refresh(deadline)
    return deadline

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deadline(
    request: Request,
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    tenant_id = request.state.tenant_id
    
    query = select(PlazoFatal).join(Expediente).where(
        PlazoFatal.id == id,
        Expediente.tenant_id == tenant_id
    )
    result = await db.execute(query)
    deadline = result.scalar_one_or_none()
    
    if not deadline:
        raise HTTPException(status_code=404, detail="Deadline not found")
        
    await db.delete(deadline)
    await db.commit()
