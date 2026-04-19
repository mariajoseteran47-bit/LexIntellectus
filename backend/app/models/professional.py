"""
LexIntellectus - Professional Profile Models
Perfiles profesionales del equipo legal: seniority, especialidad, tarifa.
Plan Estratégico v3.0, Fase 1A.
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


class PerfilProfesional(Base):
    """
    Perfil profesional extendido para miembros del equipo legal.
    Vinculado 1:1 a Usuario donde tipo_usuario IN (abogado, notario, secretaria, gestor, contador).
    """
    __tablename__ = "professional_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # === JERARQUÍA ===
    nivel_jerarquico = Column(
        Enum(
            'socio', 'asociado_senior', 'asociado_junior',
            'paralegal', 'pasante', 'soporte',
            name="seniority_level"
        ),
        nullable=False,
        default='asociado_junior'
    )

    # === ESPECIALIDADES ===
    # ["penal", "civil", "corporativo", "tributario", "laboral", "familia", "mercantil", "notarial"]
    especialidades = Column(JSONB, default=[])
    especialidad_principal = Column(String(100))  # La principal para asignación automática

    # === COLEGIATURA / HABILITACIÓN ===
    numero_colegiatura = Column(String(50))       # Carnet CSJ
    fecha_colegiatura = Column(Date)
    numero_notario = Column(String(50))            # Solo notarios: sello/número
    universidad = Column(String(200))
    grado_academico = Column(String(100))          # Licenciatura, Maestría, Doctorado
    anios_experiencia = Column(Integer, default=0)

    # === TARIFAS FACTURABLES ===
    tarifa_hora_usd = Column(Numeric(10, 2), default=0)
    tarifa_hora_nio = Column(Numeric(10, 2), default=0)
    tarifa_hora_efectiva = Column(Numeric(10, 2), default=0)  # La que se usa en facturación

    # === CAPACIDAD Y CARGA ===
    horas_meta_semanal = Column(Integer, default=40)       # Horas facturables objetivo
    casos_max_simultaneos = Column(Integer, default=20)    # Límite de casos activos

    # === METADATA ===
    idiomas = Column(JSONB, default=["es"])        # ["es", "en", "fr"]
    bio_profesional = Column(Text)
    activo_litigio = Column(Boolean, default=True)  # ¿Participa en juicios?

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    usuario = relationship("Usuario", backref="perfil_profesional")
