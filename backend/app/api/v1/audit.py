"""
LexIntellectus ERP - Audit Log API
Provides read-only access to audit logs for administrators.
"""

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import Optional
from uuid import UUID
from datetime import date

from app.core.database import get_db
from app.core.rbac import require_permission
from app.models.user import Usuario
from app.models.audit import LogAuditoria

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/logs")
async def get_audit_logs(
    request: Request,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    accion: Optional[str] = None,
    entidad: Optional[str] = None,
    user_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("settings.read")),
):
    """
    List audit logs with filtering. Only accessible to users with settings.read permission.
    """
    tenant_id = current_user.tenant_id
    skip = (page - 1) * size
    
    query = select(LogAuditoria).where(LogAuditoria.tenant_id == tenant_id)
    
    if accion:
        query = query.where(LogAuditoria.accion == accion)
    if entidad:
        query = query.where(LogAuditoria.entidad == entidad)
    if user_id:
        query = query.where(LogAuditoria.user_id == user_id)
    if start_date:
        query = query.where(LogAuditoria.created_at >= start_date)
    if end_date:
        from datetime import datetime, timedelta
        end_dt = datetime.combine(end_date, datetime.max.time())
        query = query.where(LogAuditoria.created_at <= end_dt)
    
    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Fetch
    query = query.order_by(desc(LogAuditoria.created_at)).offset(skip).limit(size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return {
        "items": [
            {
                "id": str(log.id),
                "user_id": str(log.user_id) if log.user_id else None,
                "accion": log.accion,
                "entidad": log.entidad,
                "entidad_id": str(log.entidad_id) if log.entidad_id else None,
                "datos_antes": log.datos_antes,
                "datos_despues": log.datos_despues,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in items
        ],
        "total": total,
        "page": page,
        "size": size,
    }


@router.get("/logs/actions")
async def get_audit_action_types(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("settings.read")),
):
    """Returns distinct action types for filter dropdowns."""
    result = await db.execute(
        select(LogAuditoria.accion).distinct()
        .where(LogAuditoria.tenant_id == current_user.tenant_id)
    )
    return [row[0] for row in result.all()]


@router.get("/logs/entities")
async def get_audit_entity_types(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("settings.read")),
):
    """Returns distinct entity types for filter dropdowns."""
    result = await db.execute(
        select(LogAuditoria.entidad).distinct()
        .where(LogAuditoria.tenant_id == current_user.tenant_id)
    )
    return [row[0] for row in result.all()]
