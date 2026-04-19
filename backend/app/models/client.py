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
    junta_directiva = relationship(
        "MiembroJuntaDirectiva",
        back_populates="perfil_cliente",
        cascade="all, delete-orphan"
    )
    accionistas = relationship(
        "Accionista",
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


class MiembroJuntaDirectiva(Base):
    """
    Miembros de la Junta Directiva de una persona jurídica.
    Presidente, Vicepresidente, Secretario, Tesorero, Vocales, Fiscal, etc.
    """
    __tablename__ = "board_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_profile_id = Column(UUID(as_uuid=True), ForeignKey("client_profiles.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    nombre_completo = Column(String(300), nullable=False)
    cedula_identidad = Column(String(50))
    cargo = Column(
        Enum(
            'presidente', 'vicepresidente', 'secretario', 'tesorero',
            'vocal', 'fiscal', 'director', 'director_suplente',
            'comisario', 'otro',
            name="board_position"
        ),
        nullable=False
    )
    cargo_personalizado = Column(String(200))      # Si es "otro"
    telefono = Column(String(20))
    email = Column(String(255))

    # Período de la junta
    fecha_nombramiento = Column(Date)
    fecha_vencimiento = Column(Date)               # Fin del período
    numero_acta_nombramiento = Column(String(100)) # Acta o escritura de elección
    inscrita_registro_mercantil = Column(Boolean, default=False)

    activo = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    perfil_cliente = relationship("PerfilCliente", back_populates="junta_directiva")


class Accionista(Base):
    """
    Composición accionaria / participaciones de una persona jurídica.
    Esencial para KYC, Ley 977 (Beneficiario Final) y conflictos de interés.
    """
    __tablename__ = "shareholders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_profile_id = Column(UUID(as_uuid=True), ForeignKey("client_profiles.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # Puede ser persona natural o jurídica
    tipo_accionista = Column(
        Enum('natural', 'juridica', name="shareholder_type"),
        default='natural'
    )
    nombre_completo = Column(String(300), nullable=False)  # Nombre o razón social
    cedula_ruc = Column(String(50))                # Cédula o RUC
    nacionalidad = Column(String(100), default="Nicaragüense")

    # Participación
    numero_acciones = Column(Integer)
    porcentaje_participacion = Column(Numeric(5, 2))  # Ej: 51.00%
    tipo_acciones = Column(String(100))               # Comunes, preferentes, etc.
    valor_nominal = Column(Numeric(14, 2))            # Valor de cada acción

    # Beneficiario final (Ley 977)
    es_beneficiario_final = Column(Boolean, default=False)
    pep = Column(Boolean, default=False)               # Persona Expuesta Políticamente

    fecha_adquisicion = Column(Date)
    activo = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    perfil_cliente = relationship("PerfilCliente", back_populates="accionistas")

