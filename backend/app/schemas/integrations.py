"""
LexIntellectus - Schemas for Public API Keys, Webhooks & External ERP Integrations
Plan Estratégico Maestro v4.1 / Sprint 6 — API Pública + Webhooks
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ApiKeyCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=120)
    plataforma: str = Field(default="custom", max_length=50)
    scopes: List[str] = Field(default_factory=lambda: ["read:invoices", "read:clients", "read:matters"])
    rate_limit_per_minute: int = Field(default=60, ge=1, le=5000)
    expires_at: Optional[datetime] = None


class ApiKeyResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    nombre: str
    plataforma: str
    key_prefix: str
    scopes: List[str]
    rate_limit_per_minute: int
    activo: bool
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ApiKeyCreatedResponse(ApiKeyResponse):
    """Returned only once upon creation so the admin can copy the raw key."""
    raw_key: str


class WebhookSubscriptionCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=120)
    url: str = Field(..., min_length=8, max_length=500)
    events: List[str] = Field(..., min_length=1)
    secret: Optional[str] = None
    activo: bool = True


class WebhookSubscriptionUpdate(BaseModel):
    nombre: Optional[str] = None
    url: Optional[str] = None
    events: Optional[List[str]] = None
    activo: Optional[bool] = None


class WebhookSubscriptionResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    nombre: str
    url: str
    events: List[str]
    secret: str
    activo: bool
    failure_count: int
    last_triggered_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WebhookDeliveryLogResponse(BaseModel):
    id: UUID
    subscription_id: UUID
    event_type: str
    payload: Dict[str, Any]
    signature: Optional[str] = None
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    attempt_count: int
    success: bool
    delivered_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class InvoiceErpSyncRequest(BaseModel):
    external_id: str = Field(..., min_length=1, max_length=255)
    sync_platform: str = Field(..., min_length=2, max_length=50)
    sync_status: str = Field(default="sincronizado")


class PublicPaymentCreate(BaseModel):
    factura_id: UUID
    monto: Decimal = Field(..., gt=0)
    moneda: str = Field(default="NIO", max_length=3)
    metodo_pago: str = Field(default="transferencia", max_length=50)
    referencia_externa: Optional[str] = None
    plataforma_origen: str = Field(default="quickbooks", max_length=50)
    notas: Optional[str] = None
    fecha_pago: Optional[date] = None


class PublicPaymentResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    factura_id: UUID
    monto: Decimal
    moneda: str
    metodo_pago: str
    referencia_externa: Optional[str] = None
    plataforma_origen: str
    notas: Optional[str] = None
    fecha_pago: date
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
