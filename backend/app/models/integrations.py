"""
LexIntellectus - External Integrations, Public API Keys & Webhooks Models
Plan Estratégico Maestro v4.1 / Sprint 6 — API Pública + Webhooks
Supports external accounting & ERP systems (QuickBooks, Xero, SAP Business One, Alegra).
"""

import uuid
from datetime import datetime, date
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Date, DateTime,
    ForeignKey, Numeric
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


SUPPORTED_WEBHOOK_EVENTS = [
    "matter.created",
    "matter.status_changed",
    "matter.stage_changed",
    "matter.closed",
    "invoice.created",
    "invoice.paid",
    "invoice.overdue",
    "document.uploaded",
    "document.approved",
    "deadline.approaching",
    "deadline.expired",
    "client.created",
    "payment.received",
    "conflict.detected",
]

SUPPORTED_API_SCOPES = [
    "read:invoices",
    "write:invoices",
    "read:payments",
    "write:payments",
    "read:clients",
    "read:matters",
    "read:time_entries",
]


class ApiKey(Base):
    """
    API Key for external systems (QuickBooks, Xero, SAP, Alegra) to authenticate
    against /api/v1/public/* endpoints.
    Only the SHA-256 hash of the key is stored at rest.
    """
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    nombre = Column(String(120), nullable=False)
    plataforma = Column(String(50), default="custom", nullable=False)  # quickbooks, xero, alegra, sap, custom
    key_prefix = Column(String(24), nullable=False, index=True)
    key_hash = Column(String(64), nullable=False, unique=True, index=True)
    scopes = Column(JSONB, nullable=False, default=list)
    rate_limit_per_minute = Column(Integer, default=60, nullable=False)

    activo = Column(Boolean, default=True, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WebhookSubscription(Base):
    """
    Webhook subscription endpoint configured per tenant to receive real-time events
    signed with HMAC-SHA256.
    """
    __tablename__ = "webhook_subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    nombre = Column(String(120), nullable=False)
    url = Column(String(500), nullable=False)
    events = Column(JSONB, nullable=False, default=list)
    secret = Column(String(128), nullable=False)

    activo = Column(Boolean, default=True, nullable=False)
    failure_count = Column(Integer, default=0, nullable=False)
    last_triggered_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    deliveries = relationship(
        "WebhookDeliveryLog",
        back_populates="subscription",
        cascade="all, delete-orphan",
    )


class WebhookDeliveryLog(Base):
    """
    Audit log of outbound webhook deliveries and HTTP responses.
    """
    __tablename__ = "webhook_delivery_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    subscription_id = Column(
        UUID(as_uuid=True),
        ForeignKey("webhook_subscriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    event_type = Column(String(80), nullable=False)
    payload = Column(JSONB, nullable=False)
    signature = Column(String(128), nullable=True)
    response_status = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    attempt_count = Column(Integer, default=1, nullable=False)
    success = Column(Boolean, default=False, nullable=False)
    delivered_at = Column(DateTime, default=datetime.utcnow)

    subscription = relationship("WebhookSubscription", back_populates="deliveries")


class PagoFactura(Base):
    """
    Payment transaction record linked to an Invoice (Factura), supporting external
    bank reconciliation, ERP sync (QuickBooks/Xero/Alegra/SAP), and online gateways.
    """
    __tablename__ = "invoice_payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    factura_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False, index=True)

    monto = Column(Numeric(14, 2), nullable=False)
    moneda = Column(String(3), default="NIO", nullable=False)
    metodo_pago = Column(String(50), default="transferencia", nullable=False)  # transferencia, tarjeta, cheque, efectivo, ach
    referencia_externa = Column(String(120), nullable=True)
    plataforma_origen = Column(String(50), default="manual", nullable=False)  # quickbooks, xero, alegra, sap, stripe, paypal, manual
    notas = Column(Text, nullable=True)
    fecha_pago = Column(Date, default=date.today, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    factura = relationship("Factura", backref="pagos")
