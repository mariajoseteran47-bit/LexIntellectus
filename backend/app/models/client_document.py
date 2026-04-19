"""
LexIntellectus - Client Documents Model
Documentos asociados a clientes y representantes legales: RUC, poderes, 
declaración de beneficiario final, matrícula de alcaldía, etc.
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, DateTime,
    ForeignKey, Enum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class DocumentoCliente(Base):
    """
    Documentos asociados al perfil de un cliente (no a un expediente).
    Almacenados en MinIO. Pueden vincularse al cliente o a un representante legal.
    """
    __tablename__ = "client_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    client_profile_id = Column(UUID(as_uuid=True), ForeignKey("client_profiles.id"), nullable=False)
    representative_id = Column(UUID(as_uuid=True), ForeignKey("legal_representatives.id"), nullable=True)

    # === CLASIFICACIÓN ===
    tipo_documento = Column(
        Enum(
            'ruc',                          # Constancia de RUC (DGI)
            'cedula_identidad',             # Cédula de identidad
            'pasaporte',                    # Pasaporte
            'poder_general',                # Escritura de poder
            'poder_especial',               # Poder especial
            'escritura_constitucion',       # Escritura de constitución de sociedad
            'reforma_estatutaria',          # Reformas a los estatutos
            'declaracion_beneficiario',     # Declaración de beneficiario final (Ley 977)
            'matricula_alcaldia',           # Matrícula de la Alcaldía
            'registro_mercantil',           # Inscripción en Registro Público Mercantil
            'solvencia_fiscal',             # Solvencia fiscal DGI
            'solvencia_municipal',          # Solvencia municipal
            'estados_financieros',          # Balance general, estado de resultados
            'contrato',                     # Contratos con terceros
            'acta_junta_directiva',         # Actas de junta directiva
            'certificacion_acciones',       # Certificación de acciones / participaciones
            'otro',                         # Cualquier otro
            name="client_document_type"
        ),
        nullable=False,
        default='otro'
    )

    # === ARCHIVO ===
    nombre_archivo = Column(String(300), nullable=False)
    tipo_archivo = Column(String(100))          # MIME type: application/pdf, image/jpeg
    tamano_bytes = Column(Integer)
    storage_path = Column(String(500), nullable=False)  # MinIO object path

    # === METADATA ===
    descripcion = Column(Text)                  # Nota del usuario
    numero_documento = Column(String(100))      # Ej: "J0310000098765" para RUC
    fecha_emision = Column(DateTime)            # Cuándo fue emitido
    fecha_vencimiento = Column(DateTime)        # Cuándo vence (si aplica)
    vigente = Column(Boolean, default=True)

    # === TRAZABILIDAD ===
    subido_por_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    perfil_cliente = relationship("PerfilCliente", backref="documentos")
    representante = relationship("RepresentanteLegal", backref="documentos")
    subido_por = relationship("Usuario")
