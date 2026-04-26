"""
LexIntellectus — Models: Workflow Templates, Tasks, and Conflict Check
Sprint 4: Intelligent workflow automation and conflict of interest detection.
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, DateTime, ForeignKey, Enum
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


class PlantillaWorkflow(Base):
    """
    Workflow template per service type.
    Defines which tasks, documents, and deadlines auto-create when a case starts.
    """
    __tablename__ = "workflow_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    tipo_servicio = Column(String(50), nullable=False)  # litigio, escritura, etc.
    ramo = Column(String(50), nullable=True)             # Optional: civil, penal, etc.
    nombre = Column(String(200), nullable=False)

    # Template data (JSONB arrays)
    tareas = Column(JSONB, default=[])          # [{titulo, descripcion, dias_plazo, etapa_codigo, obligatoria}]
    docs_requeridos = Column(JSONB, default=[]) # [{nombre, descripcion, etapa_codigo, obligatorio}]
    reglas_transicion = Column(JSONB, default=[]) # [{desde_etapa, hacia_etapa, requisitos: [...]}]

    activo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TareaExpediente(Base):
    """
    Task linked to a case — auto-created from template or manually added.
    Tracks completion, assignment, and deadlines.
    """
    __tablename__ = "case_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    expediente_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)

    titulo = Column(String(300), nullable=False)
    descripcion = Column(Text, nullable=True)

    # Status
    estado = Column(
        Enum('pendiente', 'en_progreso', 'completada', 'cancelada', name="task_status"),
        nullable=False, default='pendiente'
    )

    # Classification
    categoria = Column(
        Enum('procesal', 'documental', 'administrativa', 'cliente', 'interna', name="task_category"),
        nullable=False, default='administrativa'
    )
    obligatoria = Column(Boolean, default=False)  # Required for stage transition

    # Assignment
    asignado_a_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Timing
    fecha_limite = Column(DateTime, nullable=True)
    fecha_completada = Column(DateTime, nullable=True)
    orden = Column(Integer, default=0)

    # Link to workflow stage
    etapa_codigo = Column(String(50), nullable=True)  # Links to EtapaProcesal.codigo

    # Origin
    plantilla_id = Column(UUID(as_uuid=True), ForeignKey("workflow_templates.id"), nullable=True)
    creado_por_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    expediente = relationship("Expediente", backref="tareas")
    asignado_a = relationship("Usuario", foreign_keys=[asignado_a_id])
    creado_por = relationship("Usuario", foreign_keys=[creado_por_id])


class ChecklistDocumento(Base):
    """
    Document checklist item per case — tracks which required documents have been uploaded.
    """
    __tablename__ = "case_doc_checklist"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    expediente_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)

    nombre_documento = Column(String(300), nullable=False)
    descripcion = Column(Text, nullable=True)
    obligatorio = Column(Boolean, default=True)
    etapa_codigo = Column(String(50), nullable=True)

    # Status
    recibido = Column(Boolean, default=False)
    documento_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)
    fecha_recibido = Column(DateTime, nullable=True)
    verificado_por_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    expediente = relationship("Expediente", backref="checklist_docs")
    documento = relationship("Documento")


class ConflictCheckResult(Base):
    """
    Stores conflict-of-interest check results for audit trail.
    """
    __tablename__ = "conflict_check_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    expediente_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=True)

    # Who/what was checked
    nombre_buscado = Column(String(300), nullable=False)
    documento_buscado = Column(String(50), nullable=True)

    # Results
    tiene_conflicto = Column(Boolean, default=False)
    coincidencias = Column(JSONB, default=[])  # [{tabla, id, nombre, caso_id, caso_titulo, similitud}]
    verificado_por_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    resolucion = Column(Text, nullable=True)  # How the conflict was resolved
    aprobado = Column(Boolean, nullable=True)  # null=pending, true=cleared, false=blocked

    created_at = Column(DateTime, default=datetime.utcnow)
