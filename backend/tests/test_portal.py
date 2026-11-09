import pytest
import uuid
from decimal import Decimal
from datetime import date
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.tenant import Despacho
from app.models.user import Usuario
from app.models.case import Expediente, EstadoExpediente
from app.models.document import Documento
from app.models.billing import Factura
from app.core.security import create_access_token

@pytest.mark.asyncio
async def test_client_portal_and_payments(client: AsyncClient, db_session: AsyncSession):
    # Mock FastAPILimiter redis to prevent startup exception in pytest environment
    from fastapi_limiter import FastAPILimiter
    from unittest.mock import AsyncMock
    FastAPILimiter.redis = AsyncMock()
    FastAPILimiter.redis.eval = AsyncMock(return_value=0)
    FastAPILimiter.redis.evalsha = AsyncMock(return_value=0)
    async def mock_identifier(*args, **kwargs):
        return "mock_ip"
    FastAPILimiter.identifier = mock_identifier
    async def mock_callback(*args, **kwargs):
        pass
    FastAPILimiter.http_callback = mock_callback



    # Pre-generate all UUIDs to prevent lazy-load expired attributes issues in SQLAlchemy async
    tenant_id = uuid.uuid4()

    lawyer_id = uuid.uuid4()
    client_user_id = uuid.uuid4()
    other_client_id = uuid.uuid4()
    status_exp_id = uuid.uuid4()
    case_owned_id = uuid.uuid4()
    case_other_id = uuid.uuid4()
    doc_shared_id = uuid.uuid4()
    doc_confidential_id = uuid.uuid4()
    doc_other_id = uuid.uuid4()
    invoice_published_id = uuid.uuid4()
    invoice_draft_id = uuid.uuid4()
    invoice_other_id = uuid.uuid4()

    # 1. Create a Tenant
    tenant = Despacho(
        id=tenant_id,
        nombre="Despacho Test",
        status="activo"
    )
    db_session.add(tenant)
    await db_session.commit()

    # 2. Create Lawyer & Client Users
    lawyer = Usuario(
        id=lawyer_id,
        tenant_id=tenant_id,
        email="lawyer@test.com",
        password_hash="fake_hash",
        nombre="Abogado",
        apellido="Test",
        tipo_usuario="abogado",
        status="activo"
    )
    
    client_user = Usuario(
        id=client_user_id,
        tenant_id=tenant_id,
        email="client@test.com",
        password_hash="fake_hash",
        nombre="Cliente",
        apellido="Test",
        tipo_usuario="cliente",
        status="activo"
    )

    other_client = Usuario(
        id=other_client_id,
        tenant_id=tenant_id,
        email="other@test.com",
        password_hash="fake_hash",
        nombre="Otro",
        apellido="Cliente",
        tipo_usuario="cliente",
        status="activo"
    )

    db_session.add_all([lawyer, client_user, other_client])
    await db_session.commit()

    # 3. Create Case Status and Cases
    status_exp = EstadoExpediente(
        id=status_exp_id,
        tenant_id=tenant_id,
        codigo="activo",
        nombre="Activo"
    )
    db_session.add(status_exp)
    await db_session.commit()

    # Case owned by client_user
    case_owned = Expediente(
        id=case_owned_id,
        tenant_id=tenant_id,
        numero_causa="CAUSA-OWNED-123",
        numero_interno="INT-OWNED-123",
        tipo_servicio="litigio",
        estado_id=status_exp_id,
        abogado_responsable_id=lawyer_id,
        cliente_principal_id=client_user_id
    )

    # Case owned by other_client
    case_other = Expediente(
        id=case_other_id,
        tenant_id=tenant_id,
        numero_causa="CAUSA-OTHER-456",
        numero_interno="INT-OTHER-456",
        tipo_servicio="litigio",
        estado_id=status_exp_id,
        abogado_responsable_id=lawyer_id,
        cliente_principal_id=other_client_id
    )

    db_session.add_all([case_owned, case_other])
    await db_session.commit()

    # 4. Create Documents (shared & confidential)
    doc_shared = Documento(
        id=doc_shared_id,
        tenant_id=tenant_id,
        expediente_id=case_owned_id,
        nombre_archivo="contrato_shared.pdf",
        tipo_archivo="application/pdf",
        tamano_bytes=1024,
        storage_path="path/to/shared.pdf",
        es_confidencial=False,
        subido_por_id=lawyer_id
    )

    doc_confidential = Documento(
        id=doc_confidential_id,
        tenant_id=tenant_id,
        expediente_id=case_owned_id,
        nombre_archivo="memo_confidential.pdf",
        tipo_archivo="application/pdf",
        tamano_bytes=2048,
        storage_path="path/to/confidential.pdf",
        es_confidencial=True,
        subido_por_id=lawyer_id
    )

    doc_other = Documento(
        id=doc_other_id,
        tenant_id=tenant_id,
        expediente_id=case_other_id,
        nombre_archivo="other_shared.pdf",
        tipo_archivo="application/pdf",
        tamano_bytes=1024,
        storage_path="path/to/other.pdf",
        es_confidencial=False,
        subido_por_id=lawyer_id
    )

    db_session.add_all([doc_shared, doc_confidential, doc_other])
    await db_session.commit()

    # 5. Create Invoices (published & draft)
    invoice_published = Factura(
        id=invoice_published_id,
        tenant_id=tenant_id,
        client_id=client_user_id,
        case_id=case_owned_id,
        numero_factura="FAC-001",
        estado="enviada",
        fecha_emision=date.today(),
        fecha_vencimiento=date.today(),
        subtotal=Decimal("100.00"),
        total_factura=Decimal("115.00"),
        neto_a_pagar=Decimal("115.00"),
        moneda="USD"
    )

    invoice_draft = Factura(
        id=invoice_draft_id,
        tenant_id=tenant_id,
        client_id=client_user_id,
        case_id=case_owned_id,
        numero_factura="FAC-002",
        estado="borrador",
        fecha_emision=date.today(),
        fecha_vencimiento=date.today(),
        subtotal=Decimal("200.00"),
        total_factura=Decimal("230.00"),
        neto_a_pagar=Decimal("230.00"),
        moneda="USD"
    )

    invoice_other = Factura(
        id=invoice_other_id,
        tenant_id=tenant_id,
        client_id=other_client_id,
        case_id=case_other_id,
        numero_factura="FAC-003",
        estado="enviada",
        fecha_emision=date.today(),
        fecha_vencimiento=date.today(),
        subtotal=Decimal("300.00"),
        total_factura=Decimal("345.00"),
        neto_a_pagar=Decimal("345.00"),
        moneda="USD"
    )

    db_session.add_all([invoice_published, invoice_draft, invoice_other])
    await db_session.commit()

    # 6. Auth Tokens
    client_token = create_access_token(subject=str(client_user_id))
    lawyer_token = create_access_token(subject=str(lawyer_id))


    headers_client = {"Authorization": f"Bearer {client_token}", "X-Tenant-ID": str(tenant_id)}
    headers_lawyer = {"Authorization": f"Bearer {lawyer_token}", "X-Tenant-ID": str(tenant_id)}

    # =========================================================================
    # TEST 1: Access Restriction (Only clients can access client portal)
    # =========================================================================
    resp = await client.get("/api/v1/portal/cases", headers=headers_lawyer)
    assert resp.status_code == 403, "Lawyer should be forbidden from accessing client portal endpoints"

    # =========================================================================
    # TEST 2: Cases Endpoint (Client can only see their own cases)
    # =========================================================================
    resp = await client.get("/api/v1/portal/cases", headers=headers_client)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["numero_causa"] == "CAUSA-OWNED-123"

    # Test single case retrieval
    resp = await client.get(f"/api/v1/portal/cases/{case_owned_id}", headers=headers_client)
    assert resp.status_code == 200
    assert resp.json()["numero_causa"] == "CAUSA-OWNED-123"

    # Test unauthorized case retrieval
    resp = await client.get(f"/api/v1/portal/cases/{case_other_id}", headers=headers_client)
    assert resp.status_code == 404, "Client should not be able to retrieve another client's case"

    # =========================================================================
    # TEST 3: Documents Endpoint (Shared documents only)
    # =========================================================================
    resp = await client.get("/api/v1/portal/documents", headers=headers_client)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["nombre_archivo"] == "contrato_shared.pdf"

    # Test download shared document
    resp = await client.get(f"/api/v1/portal/documents/{doc_shared_id}/download", headers=headers_client)
    assert resp.status_code == 200
    assert "url" in resp.json()

    # Test download confidential document
    resp = await client.get(f"/api/v1/portal/documents/{doc_confidential_id}/download", headers=headers_client)
    assert resp.status_code == 404, "Client should not be able to download confidential case documents"

    # =========================================================================
    # TEST 4: Invoices Endpoint (Published invoices only)
    # =========================================================================
    resp = await client.get("/api/v1/portal/invoices", headers=headers_client)
    assert resp.status_code == 200
    invoices = resp.json()
    assert len(invoices) == 1
    assert invoices[0]["numero_factura"] == "FAC-001"

    # =========================================================================
    # TEST 5: Payments Session Creation (Stripe & PayPal)
    # =========================================================================
    # Create Stripe Checkout Session
    resp = await client.post(
        "/api/v1/payments/create-session",
        json={"invoice_id": str(invoice_published_id), "provider": "stripe"},
        headers=headers_client
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "stripe"
    assert "url" in data
    assert "session_id" in data
    assert data["is_mock"] is True  # We have default placeholder keys in testing

    # Create PayPal Sandbox Session
    resp = await client.post(
        "/api/v1/payments/create-session",
        json={"invoice_id": str(invoice_published_id), "provider": "paypal"},
        headers=headers_client
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] == "paypal"
    assert "url" in data
    assert "order_id" in data
    assert data["is_mock"] is True

    # Test unauthorized payment creation (cannot pay other client's invoice)
    resp = await client.post(
        "/api/v1/payments/create-session",
        json={"invoice_id": str(invoice_other_id), "provider": "stripe"},
        headers=headers_client
    )
    assert resp.status_code == 403, "Client should not be able to create payment session for other client's invoice"

    # =========================================================================
    # TEST 6: Capture & Confirm Payments
    # =========================================================================
    # Capture PayPal payment (Mock)
    resp = await client.post(
        "/api/v1/payments/paypal-capture",
        json={"order_id": "PAY-MOCK-123456", "invoice_id": str(invoice_published_id)},
        headers=headers_client
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"

    # Check that the invoice status has transitioned to 'pagada'
    result = await db_session.execute(select(Factura).where(Factura.id == invoice_published_id))
    inv = result.scalar_one()
    assert inv.estado == "pagada"

    # =========================================================================
    # TEST 7: Portal Dashboard, Threads, Approvals, Profile & Bank Transfer
    # =========================================================================
    # 7.1 Dashboard summary
    dash_resp = await client.get("/api/v1/portal/dashboard", headers=headers_client)
    assert dash_resp.status_code == 200
    assert dash_resp.json()["active_cases"] == 1

    # 7.2 Create & message in client thread
    thread_resp = await client.post(
        "/api/v1/portal/threads",
        json={
            "expediente_id": str(case_owned_id),
            "titulo": "Consulta sobre audiencia",
            "mensaje_inicial": "Estimado abogado, ¿a qué hora es la audiencia?"
        },
        headers=headers_client,
    )
    assert thread_resp.status_code == 201
    thread_id = thread_resp.json()["id"]

    msg_resp = await client.post(
        f"/api/v1/portal/threads/{thread_id}/messages",
        json={"contenido": "Adjunto comprobante adicional."},
        headers=headers_client,
    )
    assert msg_resp.status_code == 201

    list_msgs = await client.get(f"/api/v1/portal/threads/{thread_id}/messages", headers=headers_client)
    assert list_msgs.status_code == 200
    assert len(list_msgs.json()["messages"]) == 2

    # 7.3 Approvals decision from portal
    from app.models.collaboration import AprobacionDocumento
    approval_id = uuid.uuid4()
    ap = AprobacionDocumento(
        id=approval_id,
        tenant_id=tenant_id,
        documento_id=doc_shared_id,
        expediente_id=case_owned_id,
        solicitante_id=lawyer_id,
        aprobador_id=client_user_id,
        estado="pendiente",
        motivo_solicitud="Aprobar borrador de contrato",
    )
    db_session.add(ap)
    await db_session.commit()

    app_list = await client.get("/api/v1/portal/approvals", headers=headers_client)
    assert app_list.status_code == 200
    assert app_list.json()["total"] == 1

    app_dec = await client.post(
        f"/api/v1/portal/approvals/{approval_id}/decision",
        json={"estado": "aprobado", "comentarios": "Conforme con el borrador"},
        headers=headers_client,
    )
    assert app_dec.status_code == 200
    assert app_dec.json()["estado"] == "aprobado"

    # 7.4 Client Profile GET & PATCH
    prof_get = await client.get("/api/v1/portal/profile", headers=headers_client)
    assert prof_get.status_code == 200

    prof_patch = await client.patch(
        "/api/v1/portal/profile",
        json={"telefono": "+505 8888-9999", "ciudad": "León"},
        headers=headers_client,
    )
    assert prof_patch.status_code == 200
    assert prof_patch.json()["ciudad"] == "León"

    # 7.5 iCal with ?token= query param (without Authorization header)
    ical_q = await client.get(f"/api/v1/portal/calendar/ical.ics?token={client_token}")
    assert ical_q.status_code == 200
    assert "BEGIN:VCALENDAR" in ical_q.text

    # 7.6 Bank Transfer Payment Reporting
    inv_transfer_id = uuid.uuid4()
    inv_transfer = Factura(
        id=inv_transfer_id,
        tenant_id=tenant_id,
        client_id=client_user_id,
        case_id=case_owned_id,
        numero_factura="FAC-TRANSFER-01",
        estado="enviada",
        fecha_emision=date.today(),
        fecha_vencimiento=date.today(),
        subtotal=Decimal("500.00"),
        total_factura=Decimal("575.00"),
        neto_a_pagar=Decimal("575.00"),
        moneda="NIO",
    )
    db_session.add(inv_transfer)
    await db_session.commit()

    bt_resp = await client.post(
        "/api/v1/payments/bank-transfer",
        json={
            "invoice_id": str(inv_transfer_id),
            "banco_origen": "BAC Credomatic",
            "numero_referencia": "TF-2026-998877",
            "monto": 575.00,
        },
        headers=headers_client,
    )
    assert bt_resp.status_code == 200
    assert bt_resp.json()["invoice_status"] == "pagada"

    # =========================================================================
    # TEST 8: Nicaragua Procedural Calculator (CPCN Art. 129-135)
    # =========================================================================
    calc_resp = await client.post(
        "/api/v1/deadlines/calculate",
        json={
            "fecha_inicio": "2026-07-30",
            "cantidad_dias": 5,
            "dias_tipo": "habiles",
            "municipio": "managua",
            "incluir_vacaciones_judiciales": True,
        },
        headers=headers_lawyer,
    )
    assert calc_resp.status_code == 200
    calc_data = calc_resp.json()
    assert calc_data["cantidad_dias"] == 5
    # Should skip Aug 1 (Santo Domingo + Saturday) and weekend
    assert any("Santo Domingo" in ex["motivo"] or "Sábado" in ex["motivo"] for ex in calc_data["dias_excluidos"])

    hol_resp = await client.get("/api/v1/deadlines/holidays?year=2026&municipio=managua", headers=headers_lawyer)
    assert hol_resp.status_code == 200
    assert hol_resp.json()["total"] > 10

    # =========================================================================
    # TEST 9: Cryptographic QR Certification & Public Verification
    # =========================================================================
    qr_rep = await client.get("/api/v1/qr/report?period=month", headers=headers_lawyer)
    assert qr_rep.status_code == 200
    rep_data = qr_rep.json()
    assert rep_data["verification_code"].startswith("LEX-")
    assert rep_data["qr_svg_data_uri"].startswith("data:image/svg+xml;base64,")

    # Public verification of the report QR token (no auth required)
    ver_rep = await client.get(f"/api/v1/qr/verify?token={rep_data['token']}")
    assert ver_rep.status_code == 200
    assert ver_rep.json()["valid"] is True
    assert ver_rep.json()["entity_type"] == "report"

    # Invoice QR & Public verification
    qr_inv = await client.get(f"/api/v1/qr/invoice/{inv_transfer_id}", headers=headers_client)
    assert qr_inv.status_code == 200
    inv_qr_data = qr_inv.json()
    ver_inv = await client.get(f"/api/v1/qr/verify?token={inv_qr_data['token']}")
    assert ver_inv.status_code == 200
    assert ver_inv.json()["live_status"]["estado_actual"] == "pagada"

    # Tampered token must be rejected
    bad_ver = await client.get(f"/api/v1/qr/verify?token={inv_qr_data['token']}tampered")
    assert bad_ver.status_code == 400
