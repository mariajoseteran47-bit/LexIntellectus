"""
LexIntellectus - Tenant Models
Multi-tenant core: Despachos, Sedes, Planes, Suscripciones.
Based on data_model.md v2.0, Sections 1.1–1.3, 1.5
"""

import uuid
from datetime import datetime, date
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Date, DateTime,
    ForeignKey, Enum, Numeric, UniqueConstraint, JSON
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


class Despacho(Base):
    """Tenant / Law Firm."""
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(255), nullable=False)
    nombre_comercial = Column(String(255))
    ruc = Column(String(20), unique=True)
    direccion = Column(Text)
    telefono = Column(String(20))
    email = Column(String(255))
    logo_url = Column(String(500))
    plan_id = Column(UUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=True)
    status = Column(
        Enum("activo", "suspendido", "cancelado", name="tenant_status"),
        default="activo",
        nullable=False,
    )
    fecha_registro = Column(DateTime, default=datetime.utcnow)
    fecha_vencimiento_plan = Column(Date)
    config_json = Column(JSONB, default={
        "moneda_principal": "NIO",
        "tema_ui": "light",
        "timezone": "America/Managua",
        "modulos_habilitados": [],
    })
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sedes = relationship("Sede", back_populates="despacho", cascade="all, delete-orphan")
    usuarios = relationship("Usuario", back_populates="despacho")
    plan = relationship("PlanSuscripcion", back_populates="despachos")


class Sede(Base):
    """Branch / Office location."""
    __tablename__ = "branches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    nombre = Column(String(255), nullable=False)
    direccion = Column(Text)
    ciudad = Column(String(100))
    departamento = Column(String(100))
    telefono = Column(String(20))
    email = Column(String(255))
    es_casa_matriz = Column(Boolean, default=False)
    status = Column(
        Enum("activa", "inactiva", name="branch_status"),
        default="activa",
        nullable=False,
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    despacho = relationship("Despacho", back_populates="sedes")
    usuarios = relationship("Usuario", back_populates="sede")


class PlanSuscripcion(Base):
    """Subscription plan definition."""
    __tablename__ = "subscription_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo = Column(String(50), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    precio_mensual = Column(Numeric(10, 2), default=0)
    precio_anual = Column(Numeric(10, 2), default=0)
    moneda = Column(Enum("USD", "NIO", name="currency_type"), default="USD")
    es_publico = Column(Boolean, default=True)
    orden_display = Column(Integer, default=0)
    status = Column(
        Enum("activo", "inactivo", name="plan_status"),
        default="activo",
        nullable=False,
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    despachos = relationship("Despacho", back_populates="plan")
    funcionalidades = relationship("PlanFuncionalidad", back_populates="plan", cascade="all, delete-orphan")
    limites = relationship("PlanLimite", back_populates="plan", cascade="all, delete-orphan")


class PlanFuncionalidad(Base):
    """Feature toggle per plan."""
    __tablename__ = "plan_features"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=False)
    codigo_funcionalidad = Column(String(100), nullable=False)
    esta_habilitado = Column(Boolean, default=False)
    metadata_json = Column(JSONB, default={})

    plan = relationship("PlanSuscripcion", back_populates="funcionalidades")


class PlanLimite(Base):
    """Numeric limit per plan (e.g. max_usuarios, max_expedientes)."""
    __tablename__ = "plan_limits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=False)
    codigo_limite = Column(String(100), nullable=False)
    valor_limite = Column(Integer, default=-1)  # -1 = unlimited
    metadata_json = Column(JSONB, default={})

    plan = relationship("PlanSuscripcion", back_populates="limites")


class HistorialSuscripcion(Base):
    """Subscription history per tenant."""
    __tablename__ = "subscription_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=False)
    fecha_inicio = Column(DateTime, nullable=False)
    fecha_fin = Column(DateTime)
    metodo_pago = Column(
        Enum("stripe", "paypal", "transferencia", "efectivo", name="payment_method"),
        nullable=True,
    )
    referencia_pago = Column(String(255))
    monto_pagado = Column(Numeric(10, 2))
    moneda = Column(String(3))
    status = Column(
        Enum("activa", "vencida", "cancelada", name="subscription_status"),
        default="activa",
        nullable=False,
    )
    created_at = Column(DateTime, default=datetime.utcnow)


class ConfiguracionPago(Base):
    """Payment configuration per tenant."""
    __tablename__ = "payment_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), unique=True, nullable=False)
    stripe_customer_id = Column(String(255))
    stripe_subscription_id = Column(String(255))
    paypal_payer_id = Column(String(255))
    metodo_preferido = Column(
        Enum("stripe", "paypal", "manual", name="preferred_payment"),
        default="manual",
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TransaccionPago(Base):
    """Payment transaction record."""
    __tablename__ = "payment_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    historial_suscripcion_id = Column(
        UUID(as_uuid=True), ForeignKey("subscription_history.id"), nullable=True
    )
    pasarela = Column(Enum("stripe", "paypal", "manual", name="gateway_type"))
    referencia_externa = Column(String(255))
    monto = Column(Numeric(10, 2), nullable=False)
    moneda = Column(String(3), nullable=False)
    status = Column(
        Enum("pendiente", "completado", "fallido", "reembolsado", name="transaction_status"),
        default="pendiente",
        nullable=False,
    )
    metadata_json = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
