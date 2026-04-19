from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date, timedelta

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.rbac import require_permission
from app.models.user import Usuario
from app.models.case import Expediente, PlazoFatal

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    tenant_id = current_user.tenant_id
    today = date.today()
    in_7_days = today + timedelta(days=7)

    # 1. Active Cases
    q_cases = select(func.count()).where(
        Expediente.tenant_id == tenant_id,
        Expediente.fecha_cierre == None
    )
    active_cases = await db.scalar(q_cases)

    # 2. Urgent Deadlines (Due in next 7 days or overdue, status pending)
    q_deadlines = select(func.count()).join(Expediente).where(
        Expediente.tenant_id == tenant_id,
        PlazoFatal.status == "pendiente",
        PlazoFatal.fecha_vencimiento <= in_7_days
    )
    urgent_deadlines = await db.scalar(q_deadlines)

    # 3. Total pending deadlines
    q_total = select(func.count()).join(Expediente).where(
        Expediente.tenant_id == tenant_id,
        PlazoFatal.status == "pendiente"
    )
    total_deadlines = await db.scalar(q_total)
    
    return {
        "active_cases": active_cases,
        "urgent_deadlines": urgent_deadlines,
        "total_deadlines": total_deadlines,
        "system_status": "operational"
    }

@router.get("/upcoming-deadlines")
async def get_upcoming_deadlines(
    limit: int = Query(10, le=30),
    include_overdue: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Returns upcoming deadlines ordered by urgency (overdue first, then soonest).
    Includes overdue deadlines by default for visibility.
    """
    tenant_id = current_user.tenant_id
    today = date.today()
    
    query = select(PlazoFatal).join(Expediente).where(
        Expediente.tenant_id == tenant_id,
        PlazoFatal.status == "pendiente",
    )
    
    if not include_overdue:
        query = query.where(PlazoFatal.fecha_vencimiento >= today)
    
    query = query.order_by(PlazoFatal.fecha_vencimiento.asc()).limit(limit)
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    return items

