"""
LexIntellectus - Tenant Schemas
Request and response models for tenant (despacho) management.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime, date


class TenantBase(BaseModel):
    nombre: str = Field(min_length=2, max_length=255)
    nombre_comercial: Optional[str] = None
    ruc: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None


class TenantCreate(TenantBase):
    pass


class TenantUpdate(BaseModel):
    nombre: Optional[str] = None
    nombre_comercial: Optional[str] = None
    ruc: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    logo_url: Optional[str] = None
    config_json: Optional[dict[str, Any]] = None


class TenantResponse(BaseModel):
    id: UUID
    nombre: str
    nombre_comercial: Optional[str] = None
    ruc: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    logo_url: Optional[str] = None
    plan_id: Optional[UUID] = None
    status: str
    fecha_registro: Optional[datetime] = None
    fecha_vencimiento_plan: Optional[date] = None
    config_json: Optional[dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


# === Sede (Branch) ===

class SedeBase(BaseModel):
    nombre: str = Field(min_length=2, max_length=255)
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    departamento: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    es_casa_matriz: bool = False


class SedeCreate(SedeBase):
    pass


class SedeResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    nombre: str
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    departamento: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    es_casa_matriz: bool
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
