"""
LexIntellectus ERP - Audit Service
Lightweight audit logging service for tracking actions across the system.
"""

from uuid import UUID
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request

from app.models.audit import LogAuditoria


class AuditService:
    """Service for creating and querying audit log entries."""
    
    @staticmethod
    async def log(
        db: AsyncSession,
        tenant_id: UUID,
        user_id: UUID,
        accion: str,
        entidad: str,
        entidad_id: Optional[UUID] = None,
        datos_antes: Optional[Dict[str, Any]] = None,
        datos_despues: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
    ):
        """
        Create an audit log entry.
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            user_id: User who performed the action
            accion: Action type (e.g., 'crear', 'actualizar', 'eliminar', 'login', 'logout')
            entidad: Entity type (e.g., 'expediente', 'plazo', 'documento', 'usuario')
            entidad_id: Optional ID of the entity acted on
            datos_antes: Optional snapshot of data before the action
            datos_despues: Optional snapshot of data after the action
            request: Optional FastAPI request for IP/User-Agent
        """
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent", "")[:500]
        
        entry = LogAuditoria(
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
        
        db.add(entry)
        # Note: We don't commit here — the caller should commit
        # This way audit entries are part of the same transaction
        return entry


audit_service = AuditService()
