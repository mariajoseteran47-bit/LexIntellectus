"""
LexIntellectus - Billing, Time Entries, and Service Contract Schemas
Sprint 5 — Time Tracking + Facturación
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID


# ==========================================
# CONTRATO SERVICIO SCHEMAS
# ==========================================
class ContratoServicioBase(BaseModel):
    esquema_cobro: str = Field(..., description="hourly, flat, milestone, retainer, contingency")
    monto_tarifa: Decimal = Field(default=Decimal("0.00"))
    tarifa_hora_personalizada: Optional[Decimal] = None
    porcentaje_exito: Optional[Decimal] = None
    moneda: str = Field(default="NIO")

class ContratoServicioCreate(ContratoServicioBase):
    case_id: UUID
    client_id: UUID

class ContratoServicioUpdate(BaseModel):
    esquema_cobro: Optional[str] = None
    monto_tarifa: Optional[Decimal] = None
    tarifa_hora_personalizada: Optional[Decimal] = None
    porcentaje_exito: Optional[Decimal] = None
    moneda: Optional[str] = None

class ContratoServicioResponse(ContratoServicioBase):
    id: UUID
    tenant_id: UUID
    case_id: UUID
    client_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# REGISTRO TIEMPO SCHEMAS
# ==========================================
class RegistroTiempoBase(BaseModel):
    horas: Decimal
    descripcion: str
    fecha_registro: date = Field(default_factory=date.today)
    es_facturable: bool = True

class RegistroTiempoCreate(RegistroTiempoBase):
    case_id: UUID

class RegistroTiempoUpdate(BaseModel):
    horas: Optional[Decimal] = None
    descripcion: Optional[str] = None
    fecha_registro: Optional[date] = None
    es_facturable: Optional[bool] = None

class RegistroTiempoResponse(RegistroTiempoBase):
    id: UUID
    tenant_id: UUID
    case_id: UUID
    user_id: UUID
    factura_id: Optional[UUID] = None
    tarifa_aplicada: Decimal
    facturado: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# LINEA FACTURA SCHEMAS
# ==========================================
class LineaFacturaBase(BaseModel):
    descripcion: str
    cantidad: Decimal = Field(default=Decimal("1.00"))
    precio_unitario: Decimal
    tipo_item: str = Field(default="honorario", description="honorario, gasto_judicial, gasto_registral, gasto_administrativo")
    es_exento: bool = False

class LineaFacturaCreate(LineaFacturaBase):
    pass

class LineaFacturaResponse(LineaFacturaBase):
    id: UUID
    factura_id: UUID
    subtotal: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# FACTURA SCHEMAS
# ==========================================
class FacturaCreate(BaseModel):
    client_id: UUID
    case_id: Optional[UUID] = None
    es_credito: bool = False
    dias_credito: int = 0
    tasa_interes_moratorio: Decimal = Field(default=Decimal("0.00"))
    lineas: List[LineaFacturaCreate]
    moneda: str = "NIO"

class FacturaUpdateStatus(BaseModel):
    estado: str = Field(..., description="borrador, enviada, pagada, vencida, anulada")

class FacturaResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    client_id: UUID
    case_id: Optional[UUID] = None
    numero_factura: str
    estado: str
    fecha_emision: date
    fecha_vencimiento: date
    es_credito: bool
    dias_credito: int
    subtotal: Decimal
    iva_porcentaje: Decimal
    iva_monto: Decimal
    retencion_ir_porcentaje: Decimal
    retencion_ir_monto: Decimal
    retencion_alma_porcentaje: Decimal
    retencion_alma_monto: Decimal
    tasa_interes_moratorio: Decimal
    monto_interes_moratorio: Decimal
    total_factura: Decimal
    neto_a_pagar: Decimal
    moneda: str
    sync_platform: Optional[str] = None
    sync_status: Optional[str] = None
    synced_at: Optional[datetime] = None
    external_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    lineas: List[LineaFacturaResponse] = []

    class Config:
        from_attributes = True
