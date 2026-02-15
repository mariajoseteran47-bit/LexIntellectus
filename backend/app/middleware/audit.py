"""
LexIntellectus - Audit Middleware
Logs sensitive actions to the audit_logs table.
"""

from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import LogAuditoria


async def log_audit(
    db: AsyncSession,
    tenant_id: str,
    user_id: str,
    accion: str,
    entidad: str,
    entidad_id: str = None,
    datos_antes: dict = None,
    datos_despues: dict = None,
    ip_address: str = None,
    user_agent: str = None,
):
    """
    Create an audit log entry for a sensitive action.
    Call this from within API route handlers.
    """
    log = LogAuditoria(
        tenant_id=tenant_id,
        user_id=user_id,
        accion=accion,
        entidad=entidad,
        entidad_id=entidad_id,
        datos_antes=datos_antes,
        datos_despues=datos_despues,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(log)
    await db.flush()
    return log
