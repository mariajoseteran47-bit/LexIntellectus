"""
LexIntellectus - Audit Log Model
Complete audit trail for all sensitive actions.
Based on data_model.md v2.0, Section 1.4
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base


class LogAuditoria(Base):
    """Audit log entry for tracking all sensitive actions."""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    accion = Column(String(100), nullable=False)
    entidad = Column(String(100), nullable=False)
    entidad_id = Column(UUID(as_uuid=True))
    datos_antes = Column(JSONB)
    datos_despues = Column(JSONB)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
