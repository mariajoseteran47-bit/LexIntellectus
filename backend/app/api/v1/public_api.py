"""
LexIntellectus ERP - Public Integration API & Webhook Management Router
Plan Estratégico Maestro v4.1 / Sprint 6 — API Pública + Webhooks

Provides:
1. /api/v1/public/*       — External ERP/Accounting endpoints authenticated via X-API-Key
                            (QuickBooks Online, Xero, SAP Business One, Alegra)
2. /api/v1/integrations/* — Backoffice administration of API Keys & Webhook Subscriptions
"""

import hashlib
import secrets
import time
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.billing import Factura, LineaFactura, RegistroTiempo
from app.models.case import Expediente
from app.models.client import PerfilCliente
from app.models.integrations import (
    SUPPORTED_API_SCOPES,
    SUPPORTED_WEBHOOK_EVENTS,
    ApiKey,
    PagoFactura,
    WebhookDeliveryLog,
    WebhookSubscription,
)
from app.models.user import Usuario
from app.schemas.integrations import (
    ApiKeyCreate,
    ApiKeyCreatedResponse,
    ApiKeyResponse,
    InvoiceErpSyncRequest,
    PublicPaymentCreate,
    PublicPaymentResponse,
    WebhookDeliveryLogResponse,
    WebhookSubscriptionCreate,
    WebhookSubscriptionResponse,
    WebhookSubscriptionUpdate,
)
from app.services.webhook_service import webhook_service

public_router = APIRouter(prefix="/public", tags=["Public Integration API (API Key)"])
integrations_router = APIRouter(prefix="/integrations", tags=["Integrations & Webhooks Admin"])

# Sliding-window rate limiter per API key hash (in-memory for deterministic behavior across environments)
_api_key_window: Dict[str, List[float]] = defaultdict(list)


def hash_api_key(raw_key: str) -> str:
    """Compute SHA-256 hex digest of a raw API key."""
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def generate_raw_api_key() -> tuple[str, str, str]:
    """
    Generate a new API key.
    Returns (raw_key, key_prefix, key_hash).
    """
    token = secrets.token_hex(24)
    raw_key = f"li_live_{token}"
    key_prefix = raw_key[:16]
    key_hash = hash_api_key(raw_key)
    return raw_key, key_prefix, key_hash


async def get_current_api_key(
    request: Request,
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
) -> ApiKey:
    """
    Authenticate external integration requests using X-API-Key header
    (or Authorization: ApiKey <key>).
    """
    raw_key = x_api_key
    if not raw_key:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.lower().startswith("apikey "):
            raw_key = auth_header.split(" ", 1)[1].strip()

    if not raw_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Header X-API-Key requerido para acceder a la API Pública",
        )

    digest = hash_api_key(raw_key)
    result = await db.execute(select(ApiKey).where(ApiKey.key_hash == digest))
    api_key = result.scalar_one_or_none()

    if not api_key or not api_key.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key inválida o revocada",
        )

    if api_key.expires_at and api_key.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key expirada",
        )

    # Per-key sliding-window rate limit (60s window)
    now = time.time()
    window = _api_key_window[digest]
    _api_key_window[digest] = [ts for ts in window if now - ts < 60.0]
    if len(_api_key_window[digest]) >= (api_key.rate_limit_per_minute or 60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Límite de peticiones por minuto excedido para esta API Key",
        )
    _api_key_window[digest].append(now)

    # Update audit timestamp & inject tenant context
    api_key.last_used_at = datetime.utcnow()
    request.state.tenant_id = api_key.tenant_id
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return api_key


def require_api_scope(required_scope: str) -> Callable:
    """Dependency factory verifying the authenticated ApiKey has the required scope."""
    async def _check_scope(api_key: ApiKey = Depends(get_current_api_key)) -> ApiKey:
        scopes = api_key.scopes or []
        if "*" not in scopes and required_scope not in scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"API Key no posee el permiso requerido: '{required_scope}'",
            )
        return api_key

    return _check_scope


# =========================================================================
# 1. PUBLIC ENDPOINTS (/api/v1/public/*) — Requires X-API-Key
# =========================================================================

@public_router.get("/invoices")
async def public_list_invoices(
    estado: Optional[str] = Query(default=None),
    sync_status: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    api_key: ApiKey = Depends(require_api_scope("read:invoices")),
    db: AsyncSession = Depends(get_db),
):
    """
    List invoices for external accounting systems (QuickBooks, Xero, SAP, Alegra).
    Includes line items and Nicaraguan fiscal breakdowns (IVA 15%, IR, ALMA).
    """
    query = (
        select(Factura)
        .options(selectinload(Factura.lineas), selectinload(Factura.client))
        .where(Factura.tenant_id == api_key.tenant_id)
        .order_by(desc(Factura.fecha_emision))
    )
    if estado:
        query = query.where(Factura.estado == estado)
    if sync_status:
        query = query.where(Factura.sync_status == sync_status)

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    invoices = result.scalars().all()

    items = []
    for inv in invoices:
        items.append({
            "id": str(inv.id),
            "numero_factura": inv.numero_factura,
            "estado": inv.estado,
            "client_id": str(inv.client_id),
            "client_name": f"{inv.client.nombre} {inv.client.apellido}".strip() if inv.client else None,
            "client_email": inv.client.email if inv.client else None,
            "case_id": str(inv.case_id) if inv.case_id else None,
            "fecha_emision": inv.fecha_emision.isoformat() if inv.fecha_emision else None,
            "fecha_vencimiento": inv.fecha_vencimiento.isoformat() if inv.fecha_vencimiento else None,
            "moneda": inv.moneda,
            "subtotal": float(inv.subtotal or 0),
            "iva_porcentaje": float(inv.iva_porcentaje or 0),
            "iva_monto": float(inv.iva_monto or 0),
            "retencion_ir_monto": float(inv.retencion_ir_monto or 0),
            "retencion_alma_monto": float(inv.retencion_alma_monto or 0),
            "monto_interes_moratorio": float(inv.monto_interes_moratorio or 0),
            "total_factura": float(inv.total_factura or 0),
            "neto_a_pagar": float(inv.neto_a_pagar or 0),
            "sync_platform": inv.sync_platform,
            "sync_status": inv.sync_status,
            "synced_at": inv.synced_at.isoformat() if inv.synced_at else None,
            "external_id": inv.external_id,
            "lineas": [
                {
                    "id": str(line.id),
                    "descripcion": line.descripcion,
                    "cantidad": float(line.cantidad or 1),
                    "precio_unitario": float(line.precio_unitario or 0),
                    "subtotal": float(line.subtotal or 0),
                    "tipo_item": line.tipo_item,
                    "es_exento": bool(line.es_exento),
                }
                for line in (inv.lineas or [])
            ],
        })

    return {"total": len(items), "items": items}


@public_router.patch("/invoices/{invoice_id}/sync")
async def public_sync_invoice(
    invoice_id: UUID,
    body: InvoiceErpSyncRequest,
    api_key: ApiKey = Depends(require_api_scope("write:invoices")),
    db: AsyncSession = Depends(get_db),
):
    """
    Acknowledge that an invoice was imported/synced into an external ERP
    (QuickBooks, Xero, SAP Business One, Alegra).
    """
    result = await db.execute(
        select(Factura).where(
            Factura.id == invoice_id,
            Factura.tenant_id == api_key.tenant_id,
        )
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    invoice.external_id = body.external_id
    invoice.sync_platform = body.sync_platform.lower()
    invoice.sync_status = body.sync_status if body.sync_status in ("pendiente", "sincronizado", "error") else "sincronizado"
    invoice.synced_at = datetime.utcnow()

    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)

    return {
        "id": str(invoice.id),
        "numero_factura": invoice.numero_factura,
        "external_id": invoice.external_id,
        "sync_platform": invoice.sync_platform,
        "sync_status": invoice.sync_status,
        "synced_at": invoice.synced_at.isoformat(),
    }


@public_router.get("/payments", response_model=List[PublicPaymentResponse])
async def public_list_payments(
    factura_id: Optional[UUID] = Query(default=None),
    api_key: ApiKey = Depends(require_api_scope("read:payments")),
    db: AsyncSession = Depends(get_db),
):
    """List recorded invoice payments for bank reconciliation and ERP sync."""
    query = (
        select(PagoFactura)
        .where(PagoFactura.tenant_id == api_key.tenant_id)
        .order_by(desc(PagoFactura.fecha_pago))
    )
    if factura_id:
        query = query.where(PagoFactura.factura_id == factura_id)

    result = await db.execute(query)
    return result.scalars().all()


@public_router.post("/payments", response_model=PublicPaymentResponse, status_code=status.HTTP_201_CREATED)
async def public_create_payment(
    body: PublicPaymentCreate,
    api_key: ApiKey = Depends(require_api_scope("write:payments")),
    db: AsyncSession = Depends(get_db),
):
    """
    Register an external payment (from ERP or bank reconciliation).
    Automatically updates the invoice status to 'pagada' if the payment covers net payable,
    and dispatches 'payment.received' and 'invoice.paid' webhooks.
    """
    tenant_id = api_key.tenant_id
    inv_res = await db.execute(
        select(Factura).where(
            Factura.id == body.factura_id,
            Factura.tenant_id == tenant_id,
        )
    )
    invoice = inv_res.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada en este despacho")

    invoice_id = invoice.id
    numero_factura = invoice.numero_factura
    neto_a_pagar = float(invoice.neto_a_pagar or invoice.total_factura or 0)
    invoice_moneda = invoice.moneda

    payment_id = UUID(bytes=secrets.token_bytes(16))
    payment = PagoFactura(
        id=payment_id,
        tenant_id=tenant_id,
        factura_id=invoice_id,
        monto=body.monto,
        moneda=body.moneda,
        metodo_pago=body.metodo_pago,
        referencia_externa=body.referencia_externa,
        plataforma_origen=body.plataforma_origen,
        notas=body.notas,
        fecha_pago=body.fecha_pago or date.today(),
    )
    db.add(payment)

    # Check total payments on this invoice
    sum_res = await db.execute(
        select(func.coalesce(func.sum(PagoFactura.monto), 0)).where(
            PagoFactura.factura_id == invoice_id
        )
    )
    existing_paid = Decimal(str(sum_res.scalar() or 0))
    total_paid = existing_paid + Decimal(str(body.monto))

    invoice_marked_paid = False
    if total_paid >= Decimal(str(neto_a_pagar)):
        invoice.estado = "pagada"
        db.add(invoice)
        invoice_marked_paid = True

    await db.flush()

    # Dispatch real-time webhooks
    await webhook_service.dispatch_event(
        db=db,
        tenant_id=tenant_id,
        event_type="payment.received",
        data={
            "payment_id": str(payment_id),
            "factura_id": str(invoice_id),
            "numero_factura": numero_factura,
            "monto": float(body.monto),
            "moneda": body.moneda,
            "referencia_externa": body.referencia_externa,
            "plataforma_origen": body.plataforma_origen,
        },
    )
    if invoice_marked_paid:
        await webhook_service.dispatch_event(
            db=db,
            tenant_id=tenant_id,
            event_type="invoice.paid",
            data={
                "factura_id": str(invoice_id),
                "numero_factura": numero_factura,
                "estado": "pagada",
                "neto_a_pagar": neto_a_pagar,
                "moneda": invoice_moneda,
            },
        )

    await db.commit()
    await db.refresh(payment)
    return payment


@public_router.get("/clients")
async def public_list_clients(
    api_key: ApiKey = Depends(require_api_scope("read:clients")),
    db: AsyncSession = Depends(get_db),
):
    """
    List client directory with tax identification (RUC / Cédula) for external accounting sync.
    """
    query = (
        select(Usuario, PerfilCliente)
        .outerjoin(PerfilCliente, PerfilCliente.user_id == Usuario.id)
        .where(
            Usuario.tenant_id == api_key.tenant_id,
            Usuario.tipo_usuario == "cliente",
        )
    )
    result = await db.execute(query)
    rows = result.all()

    clients = []
    for user_obj, profile in rows:
        clients.append({
            "id": str(user_obj.id),
            "profile_id": str(profile.id) if profile else None,
            "nombre": f"{user_obj.nombre} {user_obj.apellido}".strip(),
            "razon_social": profile.razon_social if profile else None,
            "nombre_comercial": profile.nombre_comercial if profile else None,
            "tipo_persona": profile.tipo_persona if profile else "natural",
            "ruc": profile.ruc if profile else None,
            "cedula_identidad": profile.cedula_identidad if profile else None,
            "email": user_obj.email,
            "telefono": user_obj.telefono,
            "ciudad": profile.ciudad if profile else None,
            "departamento": profile.departamento if profile else None,
            "pais": profile.pais if profile else "Nicaragua",
            "es_exento_iva": bool(profile.es_exento_iva) if profile else False,
            "activo": user_obj.status == "activo",
        })

    return {"total": len(clients), "items": clients}


@public_router.get("/matters/summary")
async def public_matters_summary(
    tipo_servicio: Optional[str] = Query(default=None),
    api_key: ApiKey = Depends(require_api_scope("read:matters")),
    db: AsyncSession = Depends(get_db),
):
    """
    Return operational & financial summary of legal matters (Expedientes) for ERP cost-center tracking.
    """
    query = (
        select(Expediente)
        .options(selectinload(Expediente.estado))
        .where(Expediente.tenant_id == api_key.tenant_id)
        .order_by(desc(Expediente.created_at))
    )
    if tipo_servicio:
        query = query.where(Expediente.tipo_servicio == tipo_servicio)

    result = await db.execute(query)
    cases = result.scalars().all()

    summaries = []
    for c in cases:
        summaries.append({
            "id": str(c.id),
            "numero_interno": c.numero_interno,
            "numero_causa": c.numero_causa,
            "tipo_servicio": c.tipo_servicio,
            "ramo": c.ramo,
            "materia_especifica": c.materia_especifica,
            "estado": c.estado.nombre if c.estado else None,
            "cliente_principal_id": str(c.cliente_principal_id) if c.cliente_principal_id else None,
            "abogado_responsable_id": str(c.abogado_responsable_id) if c.abogado_responsable_id else None,
            "valor_estimado": float(c.valor_estimado or 0),
            "moneda": c.moneda,
            "fecha_apertura": c.fecha_apertura.isoformat() if c.fecha_apertura else None,
            "fecha_cierre": c.fecha_cierre.isoformat() if c.fecha_cierre else None,
        })

    return {"total": len(summaries), "items": summaries}


@public_router.get("/time-entries")
async def public_list_time_entries(
    case_id: Optional[UUID] = Query(default=None),
    facturado: Optional[bool] = Query(default=None),
    api_key: ApiKey = Depends(require_api_scope("read:time_entries")),
    db: AsyncSession = Depends(get_db),
):
    """List billable and non-billable time entries for external payroll/accounting systems."""
    query = (
        select(RegistroTiempo)
        .where(RegistroTiempo.tenant_id == api_key.tenant_id)
        .order_by(desc(RegistroTiempo.fecha_registro))
    )
    if case_id:
        query = query.where(RegistroTiempo.case_id == case_id)
    if facturado is not None:
        query = query.where(RegistroTiempo.facturado == facturado)

    result = await db.execute(query)
    entries = result.scalars().all()

    items = [
        {
            "id": str(entry.id),
            "case_id": str(entry.case_id),
            "user_id": str(entry.user_id),
            "factura_id": str(entry.factura_id) if entry.factura_id else None,
            "horas": float(entry.horas or 0),
            "tarifa_aplicada": float(entry.tarifa_aplicada or 0),
            "monto_total": round(float(entry.horas or 0) * float(entry.tarifa_aplicada or 0), 2),
            "descripcion": entry.descripcion,
            "fecha_registro": entry.fecha_registro.isoformat() if entry.fecha_registro else None,
            "es_facturable": bool(entry.es_facturable),
            "facturado": bool(entry.facturado),
        }
        for entry in entries
    ]
    return {"total": len(items), "items": items}


@public_router.get("/webhooks", response_model=List[WebhookSubscriptionResponse])
async def public_list_webhooks(
    api_key: ApiKey = Depends(get_current_api_key),
    db: AsyncSession = Depends(get_db),
):
    """List active webhook subscriptions for this tenant via API Key."""
    result = await db.execute(
        select(WebhookSubscription)
        .where(WebhookSubscription.tenant_id == api_key.tenant_id)
        .order_by(desc(WebhookSubscription.created_at))
    )
    return result.scalars().all()


# =========================================================================
# 2. BACKOFFICE ADMIN ENDPOINTS (/api/v1/integrations/*) — Requires JWT
# =========================================================================

def _ensure_backoffice_user(user: Usuario):
    if user.tipo_usuario == "cliente":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Los clientes no tienen acceso a la configuración de integraciones",
        )


@integrations_router.get("/catalog")
async def get_integrations_catalog(
    current_user: Usuario = Depends(get_current_user),
):
    """Return supported scopes, webhook events, and ERP platforms."""
    _ensure_backoffice_user(current_user)
    return {
        "scopes": SUPPORTED_API_SCOPES,
        "webhook_events": SUPPORTED_WEBHOOK_EVENTS,
        "platforms": [
            {"id": "quickbooks", "name": "QuickBooks Online", "category": "Contabilidad"},
            {"id": "xero", "name": "Xero", "category": "Contabilidad"},
            {"id": "alegra", "name": "Alegra LATAM", "category": "Facturación & Contabilidad"},
            {"id": "sap", "name": "SAP Business One", "category": "ERP"},
            {"id": "custom", "name": "Integración Personalizada", "category": "API / Webhook"},
        ],
    }


@integrations_router.get("/api-keys", response_model=List[ApiKeyResponse])
async def list_api_keys(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all API keys belonging to the current tenant."""
    _ensure_backoffice_user(current_user)
    result = await db.execute(
        select(ApiKey)
        .where(ApiKey.tenant_id == current_user.tenant_id)
        .order_by(desc(ApiKey.created_at))
    )
    return result.scalars().all()


@integrations_router.post("/api-keys", response_model=ApiKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    body: ApiKeyCreate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new API Key for external integrations.
    The plaintext `raw_key` is returned ONLY in this creation response.
    """
    _ensure_backoffice_user(current_user)

    invalid_scopes = [s for s in body.scopes if s not in SUPPORTED_API_SCOPES and s != "*"]
    if invalid_scopes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Scopes inválidos: {invalid_scopes}. Soportados: {SUPPORTED_API_SCOPES}",
        )

    raw_key, key_prefix, key_hash = generate_raw_api_key()
    api_key = ApiKey(
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
        nombre=body.nombre,
        plataforma=body.plataforma.lower(),
        key_prefix=key_prefix,
        key_hash=key_hash,
        scopes=body.scopes,
        rate_limit_per_minute=body.rate_limit_per_minute,
        activo=True,
        expires_at=body.expires_at,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    return ApiKeyCreatedResponse(
        id=api_key.id,
        tenant_id=api_key.tenant_id,
        nombre=api_key.nombre,
        plataforma=api_key.plataforma,
        key_prefix=api_key.key_prefix,
        scopes=api_key.scopes,
        rate_limit_per_minute=api_key.rate_limit_per_minute,
        activo=api_key.activo,
        last_used_at=api_key.last_used_at,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
        raw_key=raw_key,
    )


@integrations_router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: UUID,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke (deactivate) an API key."""
    _ensure_backoffice_user(current_user)
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.id == key_id,
            ApiKey.tenant_id == current_user.tenant_id,
        )
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=404, detail="API Key no encontrada")

    api_key.activo = False
    db.add(api_key)
    await db.commit()
    return {"status": "revoked", "id": str(key_id)}


@integrations_router.get("/webhooks", response_model=List[WebhookSubscriptionResponse])
async def list_webhook_subscriptions(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List webhook subscriptions for the current tenant."""
    _ensure_backoffice_user(current_user)
    result = await db.execute(
        select(WebhookSubscription)
        .where(WebhookSubscription.tenant_id == current_user.tenant_id)
        .order_by(desc(WebhookSubscription.created_at))
    )
    return result.scalars().all()


@integrations_router.post("/webhooks", response_model=WebhookSubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook_subscription(
    body: WebhookSubscriptionCreate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new webhook subscription with an HMAC-SHA256 signing secret."""
    _ensure_backoffice_user(current_user)

    invalid_events = [e for e in body.events if e not in SUPPORTED_WEBHOOK_EVENTS and e != "*"]
    if invalid_events:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Eventos no soportados: {invalid_events}. Soportados: {SUPPORTED_WEBHOOK_EVENTS}",
        )

    signing_secret = body.secret or f"whsec_{secrets.token_hex(24)}"
    subscription = WebhookSubscription(
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
        nombre=body.nombre,
        url=body.url,
        events=body.events,
        secret=signing_secret,
        activo=body.activo,
    )
    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)
    return subscription


@integrations_router.patch("/webhooks/{webhook_id}", response_model=WebhookSubscriptionResponse)
async def update_webhook_subscription(
    webhook_id: UUID,
    body: WebhookSubscriptionUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a webhook subscription (URL, events, or active state)."""
    _ensure_backoffice_user(current_user)
    result = await db.execute(
        select(WebhookSubscription).where(
            WebhookSubscription.id == webhook_id,
            WebhookSubscription.tenant_id == current_user.tenant_id,
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Suscripción de webhook no encontrada")

    if body.events is not None:
        invalid_events = [e for e in body.events if e not in SUPPORTED_WEBHOOK_EVENTS and e != "*"]
        if invalid_events:
            raise HTTPException(status_code=400, detail=f"Eventos no soportados: {invalid_events}")
        sub.events = body.events
    if body.nombre is not None:
        sub.nombre = body.nombre
    if body.url is not None:
        sub.url = body.url
    if body.activo is not None:
        sub.activo = body.activo

    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return sub


@integrations_router.delete("/webhooks/{webhook_id}")
async def delete_webhook_subscription(
    webhook_id: UUID,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a webhook subscription."""
    _ensure_backoffice_user(current_user)
    result = await db.execute(
        select(WebhookSubscription).where(
            WebhookSubscription.id == webhook_id,
            WebhookSubscription.tenant_id == current_user.tenant_id,
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Suscripción de webhook no encontrada")

    await db.delete(sub)
    await db.commit()
    return {"status": "deleted", "id": str(webhook_id)}


@integrations_router.post("/webhooks/{webhook_id}/test", response_model=WebhookDeliveryLogResponse)
async def test_webhook_subscription(
    webhook_id: UUID,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a signed test ping event to a webhook subscription and return the delivery log."""
    _ensure_backoffice_user(current_user)
    result = await db.execute(
        select(WebhookSubscription).where(
            WebhookSubscription.id == webhook_id,
            WebhookSubscription.tenant_id == current_user.tenant_id,
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Suscripción de webhook no encontrada")

    sample_event = (sub.events[0] if sub.events else "matter.created")
    log_entry = await webhook_service.deliver_single(
        db=db,
        subscription=sub,
        event_type=sample_event,
        data={
            "test": True,
            "message": "Evento de prueba enviado desde LexIntellectus",
            "subscription_name": sub.nombre,
        },
        max_attempts=1,
    )
    await db.commit()
    await db.refresh(log_entry)
    return log_entry


@integrations_router.get("/webhooks/{webhook_id}/logs", response_model=List[WebhookDeliveryLogResponse])
async def list_webhook_delivery_logs(
    webhook_id: UUID,
    limit: int = Query(default=25, ge=1, le=100),
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List recent delivery logs for a specific webhook subscription."""
    _ensure_backoffice_user(current_user)
    result = await db.execute(
        select(WebhookDeliveryLog)
        .where(
            WebhookDeliveryLog.subscription_id == webhook_id,
            WebhookDeliveryLog.tenant_id == current_user.tenant_id,
        )
        .order_by(desc(WebhookDeliveryLog.delivered_at))
        .limit(limit)
    )
    return result.scalars().all()
