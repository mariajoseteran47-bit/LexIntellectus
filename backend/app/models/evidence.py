"""
LexIntellectus - Evidence Management Models
Gestión probatoria: pruebas, clasificación, valoración y multimedia.
Plan Estratégico v3.0, Fase 2A.
"""

import uuid
from datetime import datetime, date
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Date, DateTime,
    ForeignKey, Enum, Numeric
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


class Prueba(Base):
    """
    Prueba procesal vinculada a un expediente.
    Cada prueba puede tener múltiples archivos adjuntos (fotos, videos, PDFs, audios).
    """
    __tablename__ = "evidences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    expediente_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # === CLASIFICACIÓN ===
    tipo_prueba = Column(
        Enum(
            'documental',       # Documentos, contratos, fotos
            'testifical',       # Testigos
            'pericial',         # Dictamen de perito
            'inspeccion',       # Inspección judicial / reconocimiento
            'confesional',      # Confesión de parte
            'presuncional',     # Presunciones legales o humanas
            'digital',          # Evidencia electrónica (correos, whatsapp, metadata)
            name="evidence_type"
        ),
        nullable=False
    )

    titulo = Column(String(300), nullable=False)
    descripcion = Column(Text)

    # === VALORACIÓN ESTRATÉGICA ===
    valoracion = Column(
        Enum('critica', 'alta', 'media', 'baja', name="evidence_weight"),
        default='media'
    )
    pertinencia = Column(Text)                    # Por qué es pertinente

    # === VINCULACIÓN A LA TEORÍA DEL CASO ===
    hecho_que_prueba = Column(Text)               # Qué hecho pretende demostrar
    teoria_caso_id = Column(UUID(as_uuid=True), ForeignKey("case_theories.id"), nullable=True)

    # === ESTADO PROCESAL ===
    estado_procesal = Column(
        Enum(
            'propuesta',        # Ofrecida pero no presentada formalmente
            'presentada',       # Fue presentada al juzgado
            'admitida',         # Admitida por el juez
            'rechazada',        # Rechazada por el juez
            'evacuada',         # Practicada / evacuada
            'desistida',        # La parte desistió de ella
            'impugnada',        # Impugnada por la contraparte
            name="evidence_status"
        ),
        default='propuesta'
    )

    fecha_proposicion = Column(Date)
    fecha_admision = Column(Date)
    fecha_evacuacion = Column(Date)

    # === DATOS ESPECÍFICOS POR TIPO ===
    # Testifical: {nombre_testigo, cedula, direccion, relacion_con_hechos}
    # Pericial: {nombre_perito, especialidad, numero_colegiatura}
    # Digital: {hash_sha256, metadata_exif, url_origen}
    datos_especificos = Column(JSONB, default={})

    # === CADENA DE CUSTODIA ===
    # [{fecha, accion, responsable, observaciones}]
    cadena_custodia = Column(JSONB, default=[])

    # === ESTRATEGIA ===
    notas_estrategia = Column(Text)               # Notas internas del abogado
    contraargumento_previsto = Column(Text)        # Cómo podría atacarla la contraparte
    base_legal = Column(String(200))              # Artículo que fundamenta su admisibilidad

    # === RESPONSABILIDAD ===
    registrado_por_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    expediente = relationship("Expediente", backref="pruebas")
    teoria_caso = relationship("TeoriaCaso")
    registrado_por = relationship("Usuario")
    adjuntos = relationship(
        "PruebaDocumento",
        back_populates="prueba",
        cascade="all, delete-orphan"
    )


class PruebaDocumento(Base):
    """
    Relación M:N entre Pruebas y Documentos (archivos en MinIO).
    Permite asociar múltiples archivos multimedia a una prueba.
    """
    __tablename__ = "evidence_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prueba_id = Column(UUID(as_uuid=True), ForeignKey("evidences.id"), nullable=False)
    documento_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)

    tipo_medio = Column(
        Enum(
            'pdf', 'foto', 'video', 'audio', 'documento_office',
            'presentacion', 'hoja_calculo', 'otro',
            name="media_type"
        ),
        default='pdf'
    )
    es_original = Column(Boolean, default=False)
    descripcion = Column(String(500))
    orden = Column(Integer, default=0)            # Orden de presentación

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    prueba = relationship("Prueba", back_populates="adjuntos")
    documento = relationship("Documento")
