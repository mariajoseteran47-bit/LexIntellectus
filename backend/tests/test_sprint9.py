import pytest
import uuid
import hashlib
from datetime import date, datetime
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.models.tenant import Despacho
from app.models.user import Usuario
from app.models.case import Expediente, EstadoExpediente, PlazoFatal
from app.models.document import Documento, DocumentoFirma
from app.core.security import create_access_token
from app.services.calendar_service import CalendarService
from app.services.encryption_service import encryption_service

@pytest.mark.asyncio
async def test_sprint9_features(client: AsyncClient, db_session: AsyncSession):
    # Disable attribute expiration on commit to completely prevent MissingGreenlet exceptions in async tests
    db_session.expire_on_commit = False

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

    # Pre-generate IDs to avoid lazy-loading issues
    tenant_id = uuid.uuid4()
    lawyer_id = uuid.uuid4()
    client_user_id = uuid.uuid4()
    case_id = uuid.uuid4()
    status_id = uuid.uuid4()
    doc_id = uuid.uuid4()

    # 1. Setup Tenant and Users
    tenant = Despacho(
        id=tenant_id,
        nombre="Despacho Sprint 9",
        status="activo"
    )
    db_session.add(tenant)
    await db_session.flush()

    # Test at-rest encryption on telephone number
    # We write a phone number and it should be encrypted in DB but decrypted in python
    lawyer = Usuario(
        id=lawyer_id,
        tenant_id=tenant_id,
        email="lawyer9@test.com",
        password_hash="fake_hash",
        nombre="Abogado",
        apellido="Sprint9",
        telefono="+505 8888-8888",  # Should be encrypted
        tipo_usuario="abogado",
        status="activo"
    )
    
    client_user = Usuario(
        id=client_user_id,
        tenant_id=tenant_id,
        email="client9@test.com",
        password_hash="fake_hash",
        nombre="Cliente",
        apellido="Sprint9",
        tipo_usuario="cliente",
        status="activo"
    )
    db_session.add_all([lawyer, client_user])
    await db_session.flush()

    # Check at-rest encryption on Usuario.telefono
    assert lawyer.telefono == "+505 8888-8888"

    # Query DB directly using raw SQL to verify it is stored as encrypted cyphertext (not plaintext)
    raw_result = await db_session.execute(
        text("SELECT telefono FROM users WHERE id = :id"),
        {"id": lawyer_id}
    )
    db_telefono = raw_result.scalar()
    assert db_telefono != "+505 8888-8888"
    assert len(db_telefono) > 30  # Fernet cyphertext is always longer due to base64 & iv
    
    # 2. Setup Case, Deadline, and Document
    status_exp = EstadoExpediente(
        id=status_id,
        tenant_id=tenant_id,
        codigo="activo",
        nombre="Activo"
    )
    db_session.add(status_exp)
    await db_session.flush()

    case = Expediente(
        id=case_id,
        tenant_id=tenant_id,
        numero_causa="001-2026-CIV",
        tipo_servicio="litigio",
        cliente_principal_id=client_user_id,
        estado_id=status_id,
        resumen="Caso de prueba para Sprint 9"
    )
    db_session.add(case)
    await db_session.flush()

    # Add PlazoFatal
    deadline = PlazoFatal(
        id=uuid.uuid4(),
        expediente_id=case_id,
        descripcion="Contestar Excepciones",
        tipo_plazo="procesal",
        fecha_vencimiento=date(2026, 6, 15),
        hora_vencimiento="13:00:00",
        prioridad="alta",
        status="pendiente"
    )
    db_session.add(deadline)
    await db_session.flush()

    # Add Document
    doc = Documento(
        id=doc_id,
        tenant_id=tenant_id,
        expediente_id=case_id,
        nombre_archivo="contrato_arrendamiento.pdf",
        tipo_archivo="application/pdf",
        tamano_bytes=1024,
        storage_path="vault/contrato.pdf",
        subido_por_id=lawyer_id,
        descripcion="Contrato para firmar",
        es_confidencial=False,
        tags=[]
    )
    db_session.add(doc)
    await db_session.flush()

    # Verify iCal generation service works
    ical_res = CalendarService.generate_ical([deadline], calendar_name="Test Calendar")
    assert "BEGIN:VCALENDAR" in ical_res
    assert "Plazo Fatal: Contestar Excepciones" in ical_res
    assert "DTSTART:20260615T130000" in ical_res
    assert "END:VCALENDAR" in ical_res

    # Prepare Auth Token for Client
    client_token = create_access_token(subject=str(client_user_id))
    headers = {
        "Authorization": f"Bearer {client_token}",
        "X-Tenant-ID": str(tenant_id)
    }

    # 3. Test iCal Endpoint
    response = await client.get("/api/v1/portal/calendar/ical.ics", headers=headers)
    assert response.status_code == 200
    assert "text/calendar" in response.headers["content-type"]
    assert "BEGIN:VCALENDAR" in response.text
    assert "Contestar Excepciones" in response.text

    # 4. Test Signature Endpoint
    sig_svg = "<svg><path d='M 10 10 L 100 100'></path></svg>"
    sig_response = await client.post(
        f"/api/v1/portal/documents/{doc_id}/sign",
        json={"signature_svg": sig_svg},
        headers=headers
    )
    assert sig_response.status_code == 200
    data = sig_response.json()
    assert data["status"] == "success"
    assert "signature_id" in data
    assert "hash" in data

    # Verify audit record is created in database
    sig_record_query = select(DocumentoFirma).where(DocumentoFirma.documento_id == doc_id)
    sig_record_res = await db_session.execute(sig_record_query)
    sig_record = sig_record_res.scalar_one()
    assert sig_record.usuario_id == client_user_id
    assert sig_record.signature_svg == sig_svg
    assert len(sig_record.firma_hash) == 64  # SHA-256 hex length is 64 characters

    # 5. Test AI Draft Endpoint
    ai_token = create_access_token(subject=str(lawyer_id))
    ai_headers = {
        "Authorization": f"Bearer {ai_token}",
        "X-Tenant-ID": str(tenant_id)
    }
    
    draft_response = await client.post(
        "/api/v1/ai/draft",
        json={
            "expediente_id": str(case_id),
            "draft_type": "demanda",
            "instructions": "Presentar demanda por incumplimiento contractual"
        },
        headers=ai_headers
    )
    assert draft_response.status_code == 200
    assert "draft" in draft_response.json()
    assert "DEMANDA INICIAL DE JUICIO" in draft_response.json()["draft"]

    # 6. Test AI Predict Endpoint
    predict_response = await client.post(
        "/api/v1/ai/predict",
        json={"expediente_id": str(case_id)},
        headers=ai_headers
    )
    assert predict_response.status_code == 200
    pred_data = predict_response.json()
    assert "probabilidad_exito" in pred_data
    assert "fortalezas" in pred_data
    assert "debilidades" in pred_data

    # 7. Test AI Classify Endpoint
    files = {"file": ("contrato.pdf", b"%PDF-1.4...", "application/pdf")}
    classify_response = await client.post(
        "/api/v1/ai/classify",
        files=files,
        headers=ai_headers
    )
    assert classify_response.status_code == 200
    class_data = classify_response.json()
    assert "tipo_documento" in class_data
    assert "resumen" in class_data

    # 8. Test AI Summarize Endpoint
    summarize_response = await client.post(
        "/api/v1/ai/summarize-actuacion",
        json={"actuacion_data": {"tipo": "Notificación", "detalle": "Sentencia de primer grado dictada por el juez", "fecha": "2026-05-31"}},
        headers=ai_headers
    )
    assert summarize_response.status_code == 200
    assert "summary" in summarize_response.json()
