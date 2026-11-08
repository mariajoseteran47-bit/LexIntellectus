"""
LexIntellectus - Automated Test Suite for Sprint 6 (API Pública + Webhooks)
Tests:
1. API Key creation, SHA-256 hashing at rest, scope validation, and revocation
2. Multi-tenant isolation across /api/v1/public/* endpoints
3. External ERP invoice sync (QuickBooks, Xero, Alegra, SAP)
4. External payment registration & automatic invoice 'pagada' transition
5. Webhook subscription management, HMAC-SHA256 signature verification, and delivery logs
"""

import json
import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.billing import Factura, LineaFactura, RegistroTiempo
from app.models.case import EstadoExpediente, Expediente
from app.models.client import PerfilCliente
from app.models.integrations import ApiKey, WebhookDeliveryLog
from app.models.tenant import Despacho
from app.models.user import Usuario
from app.services.webhook_service import webhook_service


@pytest.mark.asyncio
async def test_sprint6_public_api_and_webhooks(client: AsyncClient, db_session: AsyncSession):
    db_session.expire_on_commit = False

    # Setup Tenant A and Tenant B for isolation testing
    tenant_a_id = uuid.uuid4()
    tenant_b_id = uuid.uuid4()
    admin_a_id = uuid.uuid4()
    client_a_id = uuid.uuid4()
    client_b_id = uuid.uuid4()
    case_a_id = uuid.uuid4()
    status_a_id = uuid.uuid4()
    invoice_a_id = uuid.uuid4()
    invoice_b_id = uuid.uuid4()

    tenant_a = Despacho(id=tenant_a_id, nombre="Bufete Central A", status="activo")
    tenant_b = Despacho(id=tenant_b_id, nombre="Bufete Externo B", status="activo")
    db_session.add_all([tenant_a, tenant_b])
    await db_session.flush()

    admin_a = Usuario(
        id=admin_a_id,
        tenant_id=tenant_a_id,
        email="admin_s6@bufetea.com",
        password_hash="fake",
        nombre="Admin",
        apellido="Integraciones",
        tipo_usuario="admin_despacho",
        status="activo",
    )
    client_a = Usuario(
        id=client_a_id,
        tenant_id=tenant_a_id,
        email="cliente_s6@empresa.com.ni",
        password_hash="fake",
        nombre="Corporación",
        apellido="Nicaragua",
        tipo_usuario="cliente",
        status="activo",
    )
    client_b = Usuario(
        id=client_b_id,
        tenant_id=tenant_b_id,
        email="cliente_b@otro.com",
        password_hash="fake",
        nombre="Otro",
        apellido="Cliente",
        tipo_usuario="cliente",
        status="activo",
    )
    db_session.add_all([admin_a, client_a, client_b])
    await db_session.flush()

    profile_a = PerfilCliente(
        id=uuid.uuid4(),
        user_id=client_a_id,
        tenant_id=tenant_a_id,
        tipo_persona="juridica",
        razon_social="Corporación Nicaragua S.A.",
        ruc="J0310000999999",
        ciudad="Managua",
        es_exento_iva=False,
    )
    status_a = EstadoExpediente(
        id=status_a_id,
        tenant_id=tenant_a_id,
        codigo="activo",
        nombre="En Trámite",
    )
    db_session.add_all([profile_a, status_a])
    await db_session.flush()

    case_a = Expediente(
        id=case_a_id,
        tenant_id=tenant_a_id,
        numero_interno="EXP-2026-S6",
        numero_causa="0099-2026-MER",
        tipo_servicio="contrato",
        ramo="mercantil",
        materia_especifica="Fusión Societaria",
        estado_id=status_a_id,
        cliente_principal_id=client_a_id,
        abogado_responsable_id=admin_a_id,
        valor_estimado=Decimal("25000.00"),
    )
    db_session.add(case_a)
    await db_session.flush()

    time_entry_a = RegistroTiempo(
        id=uuid.uuid4(),
        tenant_id=tenant_a_id,
        case_id=case_a_id,
        user_id=admin_a_id,
        horas=Decimal("4.50"),
        descripcion="Revisión de cláusulas de indemnidad",
        tarifa_aplicada=Decimal("120.00"),
        es_facturable=True,
        facturado=False,
    )
    invoice_a = Factura(
        id=invoice_a_id,
        tenant_id=tenant_a_id,
        client_id=client_a_id,
        case_id=case_a_id,
        numero_factura="FAC-S6-001",
        estado="enviada",
        fecha_emision=date(2026, 8, 1),
        fecha_vencimiento=date(2026, 8, 31),
        subtotal=Decimal("1000.00"),
        iva_porcentaje=Decimal("15.00"),
        iva_monto=Decimal("150.00"),
        total_factura=Decimal("1150.00"),
        neto_a_pagar=Decimal("1150.00"),
        moneda="USD",
    )
    line_a = LineaFactura(
        id=uuid.uuid4(),
        factura_id=invoice_a_id,
        descripcion="Honorarios por Due Diligence y Contrato",
        cantidad=Decimal("1.00"),
        precio_unitario=Decimal("1000.00"),
        subtotal=Decimal("1000.00"),
        tipo_item="honorario",
        es_exento=False,
    )
    invoice_b = Factura(
        id=invoice_b_id,
        tenant_id=tenant_b_id,
        client_id=client_b_id,
        numero_factura="FAC-TENANT-B-999",
        estado="enviada",
        fecha_emision=date(2026, 8, 1),
        fecha_vencimiento=date(2026, 8, 31),
        subtotal=Decimal("500.00"),
        total_factura=Decimal("500.00"),
        neto_a_pagar=Decimal("500.00"),
    )
    db_session.add_all([time_entry_a, invoice_a, line_a, invoice_b])
    await db_session.commit()

    admin_token = create_access_token(subject=str(admin_a_id))
    admin_headers = {
        "Authorization": f"Bearer {admin_token}",
        "X-Tenant-ID": str(tenant_a_id),
    }

    # 1. Create a read-only API Key via Backoffice Admin endpoint
    create_ro_resp = await client.post(
        "/api/v1/integrations/api-keys",
        json={
            "nombre": "QuickBooks Solo Lectura",
            "plataforma": "quickbooks",
            "scopes": ["read:invoices", "read:clients", "read:matters", "read:time_entries"],
            "rate_limit_per_minute": 100,
        },
        headers=admin_headers,
    )
    assert create_ro_resp.status_code == 201
    ro_data = create_ro_resp.json()
    raw_ro_key = ro_data["raw_key"]
    ro_key_id = ro_data["id"]
    assert raw_ro_key.startswith("li_live_")

    # Verify plaintext key is NOT stored in DB
    db_key = (await db_session.execute(select(ApiKey).where(ApiKey.id == uuid.UUID(ro_key_id)))).scalar_one()
    assert db_key.key_hash != raw_ro_key
    assert len(db_key.key_hash) == 64

    # 2. Access Public API endpoints using X-API-Key
    pub_ro_headers = {"X-API-Key": raw_ro_key}

    inv_resp = await client.get("/api/v1/public/invoices", headers=pub_ro_headers)
    assert inv_resp.status_code == 200
    inv_list = inv_resp.json()["items"]
    assert len(inv_list) == 1
    assert inv_list[0]["numero_factura"] == "FAC-S6-001"
    # Ensure Tenant B's invoice is completely isolated
    assert all(i["id"] != str(invoice_b_id) for i in inv_list)

    clients_resp = await client.get("/api/v1/public/clients", headers=pub_ro_headers)
    assert clients_resp.status_code == 200
    clients_list = clients_resp.json()["items"]
    assert len(clients_list) == 1
    assert clients_list[0]["ruc"] == "J0310000999999"

    matters_resp = await client.get("/api/v1/public/matters/summary", headers=pub_ro_headers)
    assert matters_resp.status_code == 200
    assert matters_resp.json()["total"] == 1
    assert matters_resp.json()["items"][0]["numero_interno"] == "EXP-2026-S6"

    te_resp = await client.get("/api/v1/public/time-entries", headers=pub_ro_headers)
    assert te_resp.status_code == 200
    assert te_resp.json()["total"] == 1
    assert te_resp.json()["items"][0]["monto_total"] == 540.0

    # 3. Verify Scope Enforcement (read-only key cannot write payments or sync invoices)
    forbidden_sync = await client.patch(
        f"/api/v1/public/invoices/{invoice_a_id}/sync",
        json={"external_id": "QB-9001", "sync_platform": "quickbooks"},
        headers=pub_ro_headers,
    )
    assert forbidden_sync.status_code == 403

    # 4. Create Full-Access ERP API Key & Webhook Subscription
    create_rw_resp = await client.post(
        "/api/v1/integrations/api-keys",
        json={
            "nombre": "Alegra ERP Bidireccional",
            "plataforma": "alegra",
            "scopes": [
                "read:invoices",
                "write:invoices",
                "read:payments",
                "write:payments",
            ],
        },
        headers=admin_headers,
    )
    assert create_rw_resp.status_code == 201
    raw_rw_key = create_rw_resp.json()["raw_key"]
    pub_rw_headers = {"X-API-Key": raw_rw_key}

    wh_resp = await client.post(
        "/api/v1/integrations/webhooks",
        json={
            "nombre": "ERP Payment Listener",
            "url": "https://erp.ejemplo.com.ni/webhooks/lexintellectus",
            "events": ["payment.received", "invoice.paid"],
        },
        headers=admin_headers,
    )
    assert wh_resp.status_code == 201
    wh_data = wh_resp.json()
    wh_id = wh_data["id"]
    wh_secret = wh_data["secret"]
    assert wh_secret.startswith("whsec_")

    # Verify HMAC-SHA256 helper
    sample_bytes = b'{"event":"invoice.paid"}'
    sig = webhook_service.compute_signature(wh_secret, sample_bytes)
    assert sig.startswith("sha256=")
    assert webhook_service.verify_signature(wh_secret, sample_bytes, sig) is True
    assert webhook_service.verify_signature("wrong_secret", sample_bytes, sig) is False

    # 5. Sync Invoice with ERP external_id
    sync_resp = await client.patch(
        f"/api/v1/public/invoices/{invoice_a_id}/sync",
        json={"external_id": "ALEGRA-INV-778", "sync_platform": "alegra"},
        headers=pub_rw_headers,
    )
    assert sync_resp.status_code == 200
    assert sync_resp.json()["external_id"] == "ALEGRA-INV-778"
    assert sync_resp.json()["sync_status"] == "sincronizado"

    # Cross-tenant sync attempt must return 404
    cross_tenant_sync = await client.patch(
        f"/api/v1/public/invoices/{invoice_b_id}/sync",
        json={"external_id": "HACK-1", "sync_platform": "alegra"},
        headers=pub_rw_headers,
    )
    assert cross_tenant_sync.status_code == 404

    # 6. Register Payment via Public API & verify Webhook dispatch + Invoice 'pagada' transition
    with patch.object(
        webhook_service,
        "_send_http_post",
        new=AsyncMock(return_value=(200, '{"received": true}')),
    ):
        pay_resp = await client.post(
            "/api/v1/public/payments",
            json={
                "factura_id": str(invoice_a_id),
                "monto": "1150.00",
                "moneda": "USD",
                "metodo_pago": "transferencia",
                "referencia_externa": "BAC-TRX-998877",
                "plataforma_origen": "alegra",
            },
            headers=pub_rw_headers,
        )
        assert pay_resp.status_code == 201
        assert pay_resp.json()["referencia_externa"] == "BAC-TRX-998877"

    # Verify invoice is now marked as 'pagada'
    inv_after = await client.get("/api/v1/public/invoices?estado=pagada", headers=pub_rw_headers)
    assert inv_after.status_code == 200
    assert len(inv_after.json()["items"]) == 1
    assert inv_after.json()["items"][0]["id"] == str(invoice_a_id)

    # Verify webhook delivery logs were recorded for both payment.received and invoice.paid
    logs_resp = await client.get(f"/api/v1/integrations/webhooks/{wh_id}/logs", headers=admin_headers)
    assert logs_resp.status_code == 200
    logs_data = logs_resp.json()
    assert len(logs_data) >= 2
    delivered_events = {l["event_type"] for l in logs_data}
    assert "payment.received" in delivered_events
    assert "invoice.paid" in delivered_events
    assert all(l["success"] is True for l in logs_data)

    # 7. Revoke API Key and verify immediate 401 rejection
    revoke_resp = await client.delete(f"/api/v1/integrations/api-keys/{ro_key_id}", headers=admin_headers)
    assert revoke_resp.status_code == 200

    rejected_resp = await client.get("/api/v1/public/invoices", headers=pub_ro_headers)
    assert rejected_resp.status_code == 401
