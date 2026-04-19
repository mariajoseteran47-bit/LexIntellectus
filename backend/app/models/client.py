"""
LexIntellectus - Client Profile & Legal Representatives Models
CRM Legal: Personas Naturales/Jurídicas, Apoderados, Representantes Legales.
Plan Estratégico v3.0, Fase 1B.
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


class PerfilCliente(Base):
    """
    Perfil extendido de cliente (CRM Legal).
    Vinculado 1:1 a Usuario donde tipo_usuario = 'cliente'.
    Soporta tanto personas naturales como jurídicas.
    """
    __tablename__ = "client_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # === TIPO DE PERSONA ===
    tipo_persona = Column(
        Enum('natural', 'juridica', name="client_person_type"),
        nullable=False,
        default='natural'
    )

    # === IDENTIFICACIÓN (ambos tipos) ===
    cedula_identidad = Column(String(50))       # Cédula para naturales
    ruc = Column(String(30))                     # RUC (aplica a ambos)
    nacionalidad = Column(String(100), default="Nicaragüense")

    # === DATOS PERSONA JURÍDICA ===
    razon_social = Column(String(300))           # Nombre legal registrado
    nombre_comercial = Column(String(300))       # Nombre de fantasía / DBA
    tipo_sociedad = Column(
        Enum(
            'sociedad_anonima', 'sociedad_colectiva',
            'sociedad_responsabilidad_limitada', 'cooperativa',
            'fundacion', 'asociacion', 'empresa_individual',
            'sucursal_extranjera', 'otro',
            name="company_type"
        ),
        nullable=True
    )
    fecha_constitucion = Column(Date)
    numero_escritura_constitucion = Column(String(100))
    registro_mercantil = Column(String(100))      # Número de inscripción
    actividad_economica = Column(String(200))

    # === CONTACTO Y DOMICILIO ===
    direccion_domicilio = Column(Text)            # Dirección legal / domicilio
    ciudad = Column(String(100))
    departamento = Column(String(100))
    pais = Column(String(100), default="Nicaragua")

    # === RELACIÓN COMERCIAL ===
    fecha_primera_consulta = Column(Date)
    referido_por = Column(String(200))            # Cómo llegó al despacho
    calificacion_riesgo = Column(
        Enum('bajo', 'medio', 'alto', name="client_risk_level"),
        default='bajo'
    )
    segmento = Column(
        Enum('individual', 'pyme', 'corporativo', 'gobierno', 'ong',
             name="client_segment"),
        default='individual'
    )

    # === NOTAS INTERNAS ===
    notas_internas = Column(Text)                 # Observaciones confidenciales de la firma

    # === KYC / COMPLIANCE ===
    kyc_verificado = Column(Boolean, default=False)
    kyc_fecha_verificacion = Column(Date)
    pep = Column(Boolean, default=False)          # Persona Expuesta Políticamente
    pep_detalle = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    usuario = relationship("Usuario", backref="perfil_cliente")
    representantes = relationship(
        "RepresentanteLegal",
        back_populates="perfil_cliente",
        cascade="all, delete-orphan"
    )


class RepresentanteLegal(Base):
    """
    Apoderados y representantes legales de clientes jurídicos.
    Un cliente jurídico puede tener múltiples representantes con distintos tipos de poder.
    """
    __tablename__ = "legal_representatives"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("client_profiles.id"),
        nullable=False
    )
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # === DATOS DEL REPRESENTANTE ===
    nombre_completo = Column(String(300), nullable=False)
    cedula_identidad = Column(String(50))
    telefono = Column(String(20))
    email = Column(String(255))
    cargo = Column(String(200))                   # "Gerente General", "Presidente de Junta"

    # === DATOS DEL PODER ===
    tipo_poder = Column(
        Enum(
            'generalisimo',                        # Puede hacer todo
            'general_administracion',              # Administración ordinaria
            'especial',                            # Actos específicos
            'judicial',                            # Solo para litigios
            name="power_of_attorney_type"
        ),
        nullable=False
    )
    numero_escritura = Column(String(100))         # Número de la escritura del poder
    fecha_otorgamiento = Column(Date, nullable=False)
    fecha_vencimiento = Column(Date)               # NULL si es indefinido
    notario_autorizante = Column(String(200))      # Nombre del notario
    libro_protocolo = Column(String(50))           # Libro del protocolo notarial
    folio_protocolo = Column(String(50))
    tomo_protocolo = Column(String(50))

    # === ALCANCE ===
    alcance_facultades = Column(Text)              # Descripción de las facultades otorgadas
    restricciones = Column(Text)                   # Limitaciones expresas del poder

    # === VIGENCIA ===
    vigente = Column(Boolean, default=True)
    motivo_revocacion = Column(String(300))        # Si fue revocado, por qué

    # === DOCUMENTACIÓN ===
    documento_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=True
    )                                              # Escaneo del poder en MinIO

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    perfil_cliente = relationship("PerfilCliente", back_populates="representantes")
    documento = relationship("Documento")
