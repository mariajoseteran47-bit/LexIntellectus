"""
LexIntellectus - Professional Profile Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal


class ProfessionalProfileBase(BaseModel):
    nivel_jerarquico: str = "asociado_junior"
    especialidades: List[str] = []
    especialidad_principal: Optional[str] = None
    numero_colegiatura: Optional[str] = None
    fecha_colegiatura: Optional[date] = None
    numero_notario: Optional[str] = None
    universidad: Optional[str] = None
    grado_academico: Optional[str] = None
    anios_experiencia: int = 0
    tarifa_hora_usd: Decimal = Decimal("0")
    tarifa_hora_nio: Decimal = Decimal("0")
    horas_meta_semanal: int = 40
    casos_max_simultaneos: int = 20
    idiomas: List[str] = ["es"]
    bio_profesional: Optional[str] = None
    activo_litigio: bool = True


class ProfessionalProfileCreate(ProfessionalProfileBase):
    user_id: UUID


class ProfessionalProfileUpdate(BaseModel):
    nivel_jerarquico: Optional[str] = None
    especialidades: Optional[List[str]] = None
    especialidad_principal: Optional[str] = None
    numero_colegiatura: Optional[str] = None
    fecha_colegiatura: Optional[date] = None
    numero_notario: Optional[str] = None
    universidad: Optional[str] = None
    grado_academico: Optional[str] = None
    anios_experiencia: Optional[int] = None
    tarifa_hora_usd: Optional[Decimal] = None
    tarifa_hora_nio: Optional[Decimal] = None
    horas_meta_semanal: Optional[int] = None
    casos_max_simultaneos: Optional[int] = None
    idiomas: Optional[List[str]] = None
    bio_profesional: Optional[str] = None
    activo_litigio: Optional[bool] = None


class ProfessionalProfileResponse(ProfessionalProfileBase):
    id: UUID
    user_id: UUID
    tenant_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
