from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.core.database import Base

class Documento(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    expediente_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    
    nombre_archivo = Column(String(255), nullable=False)
    tipo_archivo = Column(String(100)) # mime type
    tamano_bytes = Column(Integer)
    
    storage_path = Column(String(500), nullable=False) # MinIO object name
    
    subido_por_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    descripcion = Column(String(500))
    categoria = Column(String(50), default="general") # evidencia, escrito, notificacion, etc.
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    expediente = relationship("Expediente") # Backref could be added in Expediente if needed
    subido_por = relationship("Usuario")
