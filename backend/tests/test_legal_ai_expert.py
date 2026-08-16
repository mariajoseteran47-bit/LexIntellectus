import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.tenant import Despacho
from app.models.user import Usuario
from app.models.ai import LegalSource, LegalChunk, LAASession
from app.services.poder_judicial_scraper import PoderJudicialScraperService
from app.services.rag_engine import RAGEngine
from app.core.config import settings
from app.core.security import create_access_token

@pytest.mark.asyncio
async def test_legal_ai_anonymizer():
    """Unit test for the PII scrubber / anonymization regex parser."""
    text_with_pii = (
        "La compareciente doña Josefa Blandón, con cédula de identidad 001-120584-0002A "
        "y número RUC J0310000012345, con número telefónico +505 8888-8888 y correo electrónico "
        "josefa.blandon@gmail.com, se presenta ante don Sergio Palacios."
    )
    
    anonymized = PoderJudicialScraperService.anonymize_text(text_with_pii)
    
    # Assertions
    assert "001-120584-0002A" not in anonymized
    assert "[CEDULA_ANONIMIZADA]" in anonymized
    
    assert "J0310000012345" not in anonymized
    assert "[RUC_ANONIMIZADO]" in anonymized
    
    assert "+505 8888-8888" not in anonymized
    assert "[TELEFONO_ANONIMIZADO]" in anonymized
    
    assert "josefa.blandon@gmail.com" not in anonymized
    assert "[CORREO_ANONIMIZADO]" in anonymized
    
    # Compareciente patterns
    assert "Josefa Blandón" not in anonymized
    assert "Sergio Palacios" not in anonymized

@pytest.mark.asyncio
async def test_scraper_ingestion_and_endpoint(client: AsyncClient, db_session: AsyncSession):
    """Integration test for scraping consultascausas, pgvector ingestion, and endpoint routing."""
    db_session.expire_on_commit = False

    # Setup Tenant and User
    tenant_id = uuid.uuid4()
    lawyer_id = uuid.uuid4()
    
    tenant = Despacho(
        id=tenant_id,
        nombre="Despacho Experto IA",
        status="activo"
    )
    db_session.add(tenant)
    await db_session.flush()

    lawyer = Usuario(
        id=lawyer_id,
        tenant_id=tenant_id,
        email="lawyer_expert@test.com",
        password_hash="fake_hash",
        nombre="Abogado",
        apellido="Experto",
        telefono="+505 7777-7777",
        tipo_usuario="abogado",
        status="activo"
    )
    db_session.add(lawyer)
    await db_session.flush()

    # 1. Test Service directly
    scraper = PoderJudicialScraperService(db_session)
    res = await scraper.ingest_scraped_case_to_rag(asunto_id="002-2026-CIV")
    assert res["status"] == "success"
    assert res["asunto_id"] == "002-2026-CIV"
    assert res["actuaciones_anonimizadas_count"] > 0
    await scraper.close()

    # Verify database insertion
    source_query = select(LegalSource).where(LegalSource.titulo.like("%Causa Judicial 002-2026-CIV%"))
    source_res = await db_session.execute(source_query)
    source = source_res.scalar_one_or_none()
    assert source is not None
    assert source.tipo_fuente == "jurisprudencia"

    chunk_query = select(LegalChunk).where(LegalChunk.source_id == source.id)
    chunk_res = await db_session.execute(chunk_query)
    chunk = chunk_res.scalar_one_or_none()
    assert chunk is not None
    assert chunk.vector_embedding is not None
    assert len(chunk.vector_embedding) == 3072  # Expect 3072 dimension Gemini representation

    # 2. Test Endpoint /ai/scraper/cause
    token = create_access_token(subject=str(lawyer_id))
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": str(tenant_id)
    }

    response = await client.post(
        "/api/v1/ai/scraper/cause",
        json={"asunto_id": "003-2026-CIV"},
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["asunto_id"] == "003-2026-CIV"

@pytest.mark.asyncio
async def test_ai_strategy_routing(db_session: AsyncSession):
    """Test strategy routing inside RAGEngine based on settings.AI_STRATEGY toggle."""
    db_session.expire_on_commit = False

    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    session_id = uuid.uuid4()

    # Pre-configure session
    session = LAASession(
        id=session_id,
        tenant_id=tenant_id,
        usuario_id=user_id,
        modo="consultor",
        titulo="Consulta de Estrategia"
    )
    
    engine = RAGEngine(db_session)

    # Strategy A: cloud_general (Should bypass vector DB context lookup)
    settings.AI_STRATEGY = "cloud_general"
    
    # We mock search_context to verify it is NOT called
    called = False
    async def mock_search_context(*args, **kwargs):
        nonlocal called
        called = True
        return []
        
    engine.search_context = mock_search_context
    
    # Force mock API responses or bypass actual Google network calls
    try:
        await engine.generate_response(session, "Hola, ¿cuál es el plazo civil?")
    except Exception:
        # We don't care if the final LLM call fails without keys in tests;
        # we are strictly asserting if the vector search was bypassed.
        pass
        
    assert not called, "Vector search was called under cloud_general strategy!"

    # Strategy B: local_expert (Should execute vector DB context lookup)
    settings.AI_STRATEGY = "local_expert"
    called = False
    
    try:
        await engine.generate_response(session, "Hola, ¿cuál es el plazo civil?")
    except Exception:
        pass
        
    assert called, "Vector search was bypassed under local_expert strategy!"
