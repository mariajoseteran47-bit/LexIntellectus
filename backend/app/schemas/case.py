"""
LexIntellectus - Case Schemas
Pydantic models for Expedientes and Partes.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal


# === Parte Procesal ===

class ParteBase(BaseModel):
    nombre_completo: str = Field(min_length=2, max_length=255)
    tipo_persona: str = "natural" # enum
    documento_identidad: Optional[str] = None
    tipo_documento: Optional[str] = "cedula"
    rol_procesal: str # enum
    representante_legal: Optional[str] = None
    abogado_patrocinador: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    notas: Optional[str] = None


class ParteCreate(ParteBase):
    pass


class ParteUpdate(BaseModel):
    nombre_completo: Optional[str] = None
    tipo_persona: Optional[str] = None
    documento_identidad: Optional[str] = None
    tipo_documento: Optional[str] = None
    rol_procesal: Optional[str] = None
    representante_legal: Optional[str] = None
    abogado_patrocinador: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    notas: Optional[str] = None


class ParteResponse(ParteBase):
    id: UUID
    expediente_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# === Estado Expediente ===

class EstadoBase(BaseModel):
    codigo: str
    nombre: str
    color_hex: Optional[str] = None
    es_final: bool = False
    orden: int = 0


class EstadoCreate(EstadoBase):
    pass


class EstadoResponse(EstadoBase):
    id: UUID
    tenant_id: UUID

    class Config:
        from_attributes = True


# === Expediente ===

class ExpedienteBase(BaseModel):
    sede_id: Optional[UUID] = None
    numero_causa: Optional[str] = None
    ramo: str # enum
    tipo_proceso: Optional[str] = None  # ordinario, ejecutivo, etc.
    materia_especifica: Optional[str] = None
    juzgado: Optional[str] = None
    juez: Optional[str] = None
    secretario: Optional[str] = None
    estado_id: Optional[UUID] = None
    resumen: Optional[str] = None
    fecha_apertura: Optional[date] = None
    fecha_cierre: Optional[date] = None
    abogado_responsable_id: Optional[UUID] = None
    cliente_principal_id: Optional[UUID] = None
    co_abogados: Optional[list] = []
    abogado_contraparte: Optional[str] = None
    prioridad: str = "normal"
    valor_estimado: Optional[Decimal] = None
    moneda: Optional[str] = "NIO"
    observaciones_ia: Optional[str] = None
    # Resolution
    tipo_resolucion: Optional[str] = None
    numero_sentencia: Optional[str] = None
    fecha_sentencia: Optional[date] = None
    resultado_detalle: Optional[str] = None
    monto_adjudicado: Optional[Decimal] = None
    recurso_pendiente: Optional[bool] = False
    # Materia-specific data (flexible JSON)
    datos_materia: Optional[dict] = {}


class ExpedienteCreate(ExpedienteBase):
    partes: List[ParteCreate] = []


class ExpedienteUpdate(BaseModel):
    sede_id: Optional[UUID] = None
    numero_causa: Optional[str] = None
    ramo: Optional[str] = None
    tipo_proceso: Optional[str] = None
    materia_especifica: Optional[str] = None
    juzgado: Optional[str] = None
    juez: Optional[str] = None
    secretario: Optional[str] = None
    estado_id: Optional[UUID] = None
    resumen: Optional[str] = None
    fecha_apertura: Optional[date] = None
    fecha_cierre: Optional[date] = None
    abogado_responsable_id: Optional[UUID] = None
    cliente_principal_id: Optional[UUID] = None
    co_abogados: Optional[list] = None
    abogado_contraparte: Optional[str] = None
    prioridad: Optional[str] = None
    valor_estimado: Optional[Decimal] = None
    moneda: Optional[str] = None
    observaciones_ia: Optional[str] = None
    tipo_resolucion: Optional[str] = None
    numero_sentencia: Optional[str] = None
    fecha_sentencia: Optional[date] = None
    resultado_detalle: Optional[str] = None
    monto_adjudicado: Optional[Decimal] = None
    recurso_pendiente: Optional[bool] = None
    datos_materia: Optional[dict] = None


class ExpedienteResponse(ExpedienteBase):
    id: UUID
    tenant_id: UUID
    numero_interno: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    partes: List[ParteResponse] = []
    # estado relationship could be nested if needed

    class Config:
        from_attributes = True


class ExpedienteListResponse(BaseModel):
    items: List[ExpedienteResponse]
    total: int
    page: int
    size: int
