from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Boolean, Enum, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
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

    # === CAMPOS FASE 2 — Clasificación ampliada ===
    tipo_documento = Column(
        Enum(
            'escrito', 'notificacion', 'evidencia', 'poder', 'contrato',
            'sentencia', 'recurso', 'dictamen', 'acta', 'escritura',
            'factura', 'correspondencia', 'general',
            name="document_type"
        ),
        default='general'
    )
    es_confidencial = Column(Boolean, default=False)
    version = Column(Integer, default=1)
    tags = Column(JSONB, default=[])  # Etiquetas libres: ["contrato", "firmado"]
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    expediente = relationship("Expediente")
    subido_por = relationship("Usuario")
    firmas = relationship("DocumentoFirma", back_populates="documento", cascade="all, delete-orphan")


class DocumentoFirma(Base):
    """Audit record for digital/electronic signatures (Simple e-Signature)."""
    __tablename__ = "document_signatures"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    documento_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Audit trail details
    firma_hash = Column(String(64), nullable=False)  # SHA-256 hash of document and metadata
    ip_address = Column(String(50), nullable=False)
    user_agent = Column(String(500), nullable=False)
    signature_svg = Column(Text, nullable=False)     # Captured digitized SVG path/rubric
    
    signed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    documento = relationship("Documento", back_populates="firmas")
    usuario = relationship("Usuario")


