"""
LexIntellectus - Billing, Time Entries, and Service Contract Models
Plan Estratégico Maestro v4.1 / Sprint 5 — Time Tracking + Facturación
Incorporating Nicaragua local tax rules (DGI, ALMA retentions, simplified regimes)
and variable credit terms with late fees/moratory interests.
"""

import uuid
from datetime import datetime, date
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Date, DateTime,
    ForeignKey, Enum, Numeric
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, backref
from app.core.database import Base


class ContratoServicio(Base):
    """
    Contract configuration defining billing scheme for a Case.
    Supports AFAs (Alternative Fee Arrangements).
    """
    __tablename__ = "service_contracts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), unique=True, nullable=False)
    client_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    esquema_cobro = Column(
        Enum('hourly', 'flat', 'milestone', 'retainer', 'contingency', name="billing_scheme"),
        nullable=False,
        default='hourly'
    )
    
    monto_tarifa = Column(Numeric(14, 2), default=0.00)  # Flat amount, retainer monthly fee, or success amount
    tarifa_hora_personalizada = Column(Numeric(10, 2), nullable=True)  # Override default user hour rate if present
    porcentaje_exito = Column(Numeric(5, 2), nullable=True)  # For contingency cuota litis (e.g. 20.00%)
    moneda = Column(String(3), default="NIO")  # NIO, USD

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    case = relationship("Expediente", backref=backref("contrato_servicio", uselist=False))

    client = relationship("Usuario", foreign_keys=[client_id])


class RegistroTiempo(Base):
    """
    Time tracked by lawyers/paralegals for a specific case.
    """
    __tablename__ = "time_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    factura_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=True)

    horas = Column(Numeric(6, 2), nullable=False, default=0.00)
    descripcion = Column(Text, nullable=False)
    fecha_registro = Column(Date, default=date.today)
    
    tarifa_aplicada = Column(Numeric(10, 2), nullable=False, default=0.00)  # Multiplied by hours
    es_facturable = Column(Boolean, default=True, nullable=False)
    facturado = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    case = relationship("Expediente")
    user = relationship("Usuario")
    factura = relationship("Factura", back_populates="registros_tiempo")


class Factura(Base):
    """
    Invoice generated for legal services.
    Handles credit terms, local Nicaragua taxes (15% VAT, 2%/10% IR DGI withholding, 1.5% ALMA municipal withholding),
    and late-payment interest fees.
    """
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    client_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=True)  # Optional link to case

    numero_factura = Column(String(50), nullable=False)  # Seq per tenant, e.g. FAC-00001
    estado = Column(
        Enum('borrador', 'enviada', 'pagada', 'vencida', 'anulada', name="invoice_status"),
        nullable=False,
        default='borrador'
    )
    
    fecha_emision = Column(Date, default=date.today, nullable=False)
    fecha_vencimiento = Column(Date, nullable=False)
    
    # Credit Terms
    es_credito = Column(Boolean, default=False, nullable=False)
    dias_credito = Column(Integer, default=0, nullable=False)  # 0 = Contado
    
    # Financial breakdown
    subtotal = Column(Numeric(14, 2), nullable=False, default=0.00)
    
    # Tax rules
    iva_porcentaje = Column(Numeric(5, 2), nullable=False, default=15.00)  # 15% (or 0% if exempt or natural person despacho)
    iva_monto = Column(Numeric(14, 2), nullable=False, default=0.00)
    
    # Withholdings (Nicaragua DGI and ALMA)
    retencion_ir_porcentaje = Column(Numeric(5, 2), nullable=False, default=0.00)  # 2.00% or 10.00%
    retencion_ir_monto = Column(Numeric(14, 2), nullable=False, default=0.00)
    retencion_alma_porcentaje = Column(Numeric(5, 2), nullable=False, default=0.00)  # 1.00% or 1.50%
    retencion_alma_monto = Column(Numeric(14, 2), nullable=False, default=0.00)
    
    # Late payment moratory interests
    tasa_interes_moratorio = Column(Numeric(5, 2), nullable=False, default=0.00)  # e.g. 2.00% monthly
    monto_interes_moratorio = Column(Numeric(14, 2), nullable=False, default=0.00)
    
    # Totals
    total_factura = Column(Numeric(14, 2), nullable=False, default=0.00)  # subtotal + iva_monto
    neto_a_pagar = Column(Numeric(14, 2), nullable=False, default=0.00)  # total_factura + moratorio - retenciones
    moneda = Column(String(3), default="NIO")

    # Integration Sync fields
    sync_platform = Column(String(50), nullable=True)  # quickbooks, alegra, xero, sap
    sync_status = Column(Enum('pendiente', 'sincronizado', 'error', name="sync_status_type"), default='pendiente')
    synced_at = Column(DateTime, nullable=True)
    external_id = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    client = relationship("Usuario", foreign_keys=[client_id])
    case = relationship("Expediente")
    lineas = relationship("LineaFactura", back_populates="factura", cascade="all, delete-orphan")
    registros_tiempo = relationship("RegistroTiempo", back_populates="factura")


class LineaFactura(Base):
    """
    Individual items inside an Invoice.
    Differentiates between professional services/honorarios (subject to VAT 15% and IR professional withholding 10%)
    and reimbursable expenses like municipal or court aranceles (exempt of VAT and DGI withholding).
    """
    __tablename__ = "invoice_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    factura_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False)

    descripcion = Column(String(255), nullable=False)
    cantidad = Column(Numeric(8, 2), nullable=False, default=1.00)
    precio_unitario = Column(Numeric(14, 2), nullable=False, default=0.00)
    subtotal = Column(Numeric(14, 2), nullable=False, default=0.00)

    # Expense categorization
    tipo_item = Column(
        Enum('honorario', 'gasto_judicial', 'gasto_registral', 'gasto_administrativo', name="invoice_item_type"),
        nullable=False,
        default='honorario'
    )
    es_exento = Column(Boolean, default=False, nullable=False)  # If true, 0% VAT applies to this line

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    factura = relationship("Factura", back_populates="lineas")
