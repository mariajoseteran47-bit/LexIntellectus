"""
LexIntellectus — Models: Discussion Threads + Document Approvals
Sprint 3: Collaboration and formal approval workflows.
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, DateTime, ForeignKey, Enum
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


class HiloDiscusion(Base):
    """
    Discussion thread linked to a case.
    Supports internal (legal team) and client-facing channels.
    """
    __tablename__ = "case_threads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    expediente_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)

    titulo = Column(String(300), nullable=False)
    tipo_canal = Column(
        Enum('interno', 'cliente', name="thread_channel_type"),
        nullable=False,
        default='interno'
    )
    # Thread status
    cerrado = Column(Boolean, default=False)
    fijado = Column(Boolean, default=False)  # Pinned thread

    # Creator
    creado_por_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Counters (denormalized for performance)
    total_mensajes = Column(Integer, default=0)
    ultimo_mensaje_at = Column(DateTime, nullable=True)

    # Relationships
    expediente = relationship("Expediente", backref="hilos_discusion")
    creado_por = relationship("Usuario", foreign_keys=[creado_por_id])
    mensajes = relationship("MensajeHilo", back_populates="hilo", order_by="MensajeHilo.created_at")


class MensajeHilo(Base):
    """
    Individual message within a discussion thread.
    Supports mentions, attachments, and resolution marking.
    """
    __tablename__ = "thread_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hilo_id = Column(UUID(as_uuid=True), ForeignKey("case_threads.id", ondelete="CASCADE"), nullable=False)
    autor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    contenido = Column(Text, nullable=False)
    # Attachments: list of document IDs or file references
    adjuntos = Column(JSONB, default=[])
    # Mentions: list of user IDs mentioned with @
    menciones = Column(JSONB, default=[])

    # Special flags
    es_resolucion = Column(Boolean, default=False)  # Marks thread as resolved
    editado = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    hilo = relationship("HiloDiscusion", back_populates="mensajes")
    autor = relationship("Usuario", foreign_keys=[autor_id])


class AprobacionDocumento(Base):
    """
    Document approval workflow.
    Supports request → approve/reject cycle with comments.
    """
    __tablename__ = "document_approvals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    documento_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    expediente_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=True)  # Optional link

    # Workflow participants
    solicitante_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    aprobador_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Status
    estado = Column(
        Enum('pendiente', 'aprobado', 'rechazado', 'revision', name="approval_status"),
        nullable=False,
        default='pendiente'
    )

    # Context
    motivo_solicitud = Column(Text)  # Why approval is requested
    comentarios_aprobador = Column(Text)  # Approver's feedback
    version_documento = Column(Integer, default=1)  # Which version was approved

    # Timestamps
    fecha_solicitud = Column(DateTime, default=datetime.utcnow)
    fecha_respuesta = Column(DateTime, nullable=True)
    fecha_limite = Column(DateTime, nullable=True)  # Deadline for approval

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    documento = relationship("Documento", backref="aprobaciones")
    expediente = relationship("Expediente", backref="aprobaciones")
    solicitante = relationship("Usuario", foreign_keys=[solicitante_id])
    aprobador = relationship("Usuario", foreign_keys=[aprobador_id])
