from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID

from app.core.database import get_db
from app.models.user import Usuario
from app.core.dependencies import get_current_user
from app.core.rbac import require_permission
from app.models.ai import LAASession, LegalChunk, LAAMessage
from app.services.rag_engine import RAGEngine
from app.services.ingestion import IngestionPipeline
from app.services.poder_judicial_scraper import PoderJudicialScraperService
from app.core.config import settings
import os
from sqlalchemy import func, select
from app.models.case import Expediente, ParteProcesal
from app.models.case_extended import EtapaProcesal
from app.models.workflow_engine import ChecklistDocumento
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/ai", tags=["AI"])

@router.get("/stats")
async def get_ai_stats(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("ai.use"))
):
    api_key_configured = bool(settings.GOOGLE_API_KEY or os.getenv("GOOGLE_API_KEY", ""))
    
    leyes_count = await db.scalar(select(func.count(LegalChunk.id)).where(LegalChunk.source_type == 'ley')) or 0
    jur_count = await db.scalar(select(func.count(LegalChunk.id)).where(LegalChunk.source_type == 'jurisprudencia')) or 0
    total_chunks = await db.scalar(select(func.count(LegalChunk.id))) or 0
    
    return {
        "api_key_configured": api_key_configured,
        "leyes_count": leyes_count,
        "jurisprudencia_count": jur_count,
        "total_chunks": total_chunks,
    }

@router.get("/suggestions/{expediente_id}")
async def get_document_suggestions(
    expediente_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("ai.use"))
):
    # Fetch case and current stage
    case = await db.get(Expediente, expediente_id)
    if not case or case.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
        
    etapa = None
    if case.etapa_actual_id:
        etapa = await db.get(EtapaProcesal, case.etapa_actual_id)
        
    sugerencias = []
    
    # 1. Sugerencias basadas en Checklist de Documentos pendientes
    docs_result = await db.execute(
        select(ChecklistDocumento).where(
            ChecklistDocumento.expediente_id == expediente_id,
            ChecklistDocumento.recibido == False
        )
    )
    docs_pendientes = docs_result.scalars().all()
    for doc in docs_pendientes:
        sugerencias.append({
            "titulo": f"Redactar {doc.nombre_documento}",
            "descripcion": f"Documento requerido para la etapa actual ({etapa.nombre if etapa else 'Inicial'})",
            "tipo": doc.nombre_documento,
            "mode": "redactor" if case.tipo_servicio != "escritura" else "cartulario"
        })
        
    # 2. Sugerencias Generales por Servicio y Etapa si no hay checklist
    if not sugerencias:
        stage_name = etapa.nombre.lower() if etapa else ""
        if "audiencia" in stage_name or "juicio" in stage_name:
            sugerencias.append({"titulo": "Redactar Alegato de Apertura", "descripcion": "Estructurar discurso inicial para la audiencia.", "tipo": "Alegato", "mode": "redactor"})
            sugerencias.append({"titulo": "Guion de Interrogatorio", "descripcion": "Preguntas estratégicas basadas en la Teoría del Caso.", "tipo": "Interrogatorio", "mode": "estratega"})
            sugerencias.append({"titulo": "Redactar Alegato de Clausura", "descripcion": "Estructurar discurso final persuasivo.", "tipo": "Alegato", "mode": "redactor"})
        elif case.tipo_servicio == "litigio":
            sugerencias.append({"titulo": "Redactar Demanda / Escrito Inicial", "descripcion": "Generar borrador de la acción legal.", "tipo": "Demanda", "mode": "redactor"})
        elif case.tipo_servicio == "escritura":
            sugerencias.append({"titulo": "Redactar Escritura Pública", "descripcion": "Generar matriz para protocolo.", "tipo": "Escritura", "mode": "cartulario"})
        else:
            sugerencias.append({"titulo": "Redactar Documento Principal", "descripcion": "Generar documento basado en los datos del caso.", "tipo": "Documento", "mode": "redactor"})

    return {"sugerencias": sugerencias}

@router.post("/chat")
async def chat_interaction(
    message: str = Body(...),
    mode: str = Body(..., pattern="^(consultor|estratega|redactor|cartulario)$"),
    session_id: Optional[UUID] = Body(None),
    expediente_id: Optional[UUID] = Body(None),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("ai.use"))
):
    # 1. Get or Create Session
    if session_id:
        session = await db.get(LAASession, session_id)
        if not session or session.usuario_id != current_user.id:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        session = LAASession(
            tenant_id=current_user.tenant_id,
            usuario_id=current_user.id,
            expediente_id=expediente_id,
            modo=mode,
            titulo=message[:50]
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

    # 2. Save User Message
    user_msg = LAAMessage(
        session_id=session.id,
        rol='user',
        contenido=message
    )
    db.add(user_msg)
    await db.commit()

    # 3. Fetch Case Context
    case_context_str = ""
    if expediente_id:
        case = await db.get(Expediente, expediente_id)
        if case:
            # Fetch parties
            parties_result = await db.execute(select(ParteProcesal).where(ParteProcesal.expediente_id == expediente_id))
            parties = parties_result.scalars().all()
            parties_info = ", ".join([f"{p.rol_procesal}: {p.nombre_completo}" for p in parties])
            
            case_context_str = f"Servicio: {case.tipo_servicio}\nResumen: {case.resumen}\nPartes: {parties_info}\nDatos Materia: {case.datos_materia}"

    # 4. Process with RAG Engine
    engine = RAGEngine(db)
    
    if mode == 'estratega':
        # Strategy context
        case_data = {"resumen": case_context_str}
        await engine.analyze_strategy(session, case_data)
        response_text = "He generado la Teoría del Caso. Puedes verla en el panel lateral."
    else:
        # Consultant, Redactor, or Cartulario
        # Pasa el contexto completo al RAG
        response_text = await engine.generate_response(session, message, case_context=case_context_str)
    
    return {
        "session_id": session.id,
        "response": response_text
    }

@router.post("/ingest")
async def ingest_document(
    file: UploadFile = File(...),
    source_type: str = Form("ley"), # ley, jurisprudencia, doctrina, reglamento
    titulo: str = Form(""),  # Título del documento (ej. "Código Civil de Nicaragua")
    metadata: str = Form("{}"), # JSON string adicional
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("ai.use"))
):
    """
    Ingest a legal document (PDF) into the RAG knowledge base.
    
    For legal documents (laws, codes), the pipeline automatically:
    1. Detects article boundaries (Art. X.-)
    2. Segments by individual articles instead of generic chunking
    3. Creates a LegalSource record
    4. Deduplicates by content hash
    
    For non-legal documents, uses standard sliding-window chunking.
    """
    import json as _json
    content = await file.read()
    engine = RAGEngine(db)
    
    # Build complete metadata
    doc_titulo = titulo or file.filename or "Documento Sin Título"
    try:
        extra_meta = _json.loads(metadata) if metadata else {}
    except _json.JSONDecodeError:
        extra_meta = {}
    
    ingest_metadata = {
        "source_type": source_type,
        "titulo": doc_titulo,
        **extra_meta
    }
    
    # Ingest with intelligent segmentation
    chunks_count = await IngestionPipeline.process_document_async(
        db, content, ingest_metadata, engine
    )
    
    return {
        "status": "success",
        "titulo": doc_titulo,
        "source_type": source_type,
        "chunks_created": chunks_count,
        "message": f"Documento '{doc_titulo}' procesado exitosamente. {chunks_count} fragmentos vectorizados."
    }

@router.get("/history/{session_id}")
async def get_history(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("ai.use"))
):
    session = await db.get(LAASession, session_id)
    if not session:
        raise HTTPException(404, "Session not found")
        
    # Return messages (joined load ideally)
    # Lazy load will fail in async without specific loader options or explicit query.
    # For now just confirming endpoints exist.
    return {"session": session}


from pydantic import BaseModel

class AIDraftRequest(BaseModel):
    expediente_id: Optional[UUID] = None
    draft_type: str  # 'demanda', 'recurso', 'contrato', 'escritura'
    instructions: str

class AIPredictRequest(BaseModel):
    expediente_id: UUID

class AISummarizeRequest(BaseModel):
    actuacion_data: dict

@router.post("/draft")
async def generate_draft_endpoint(
    req: AIDraftRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("ai.use"))
):
    """Generate a structured legal draft linked to a case."""
    case_context_data = {}
    if req.expediente_id:
        case = await db.get(Expediente, req.expediente_id)
        if not case or case.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=404, detail="Expediente no encontrado")
            
        parties_result = await db.execute(
            select(ParteProcesal).where(ParteProcesal.expediente_id == req.expediente_id)
        )
        parties = parties_result.scalars().all()
        parties_info = ", ".join([f"{p.rol_procesal}: {p.nombre_completo}" for p in parties])
        
        case_context_data = {
            "tipo_servicio": case.tipo_servicio,
            "resumen": case.resumen,
            "partes": parties_info,
            "datos_materia": case.datos_materia
        }

    engine = RAGEngine(db)
    draft_content = await engine.generate_legal_draft(
        case_data=case_context_data,
        draft_type=req.draft_type,
        instructions=req.instructions
    )
    return {"draft": draft_content}

@router.post("/predict")
async def predict_success_endpoint(
    req: AIPredictRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("ai.use"))
):
    """Perform predictive success analysis on a case."""
    case = await db.get(Expediente, req.expediente_id)
    if not case or case.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
        
    parties_result = await db.execute(
        select(ParteProcesal).where(ParteProcesal.expediente_id == req.expediente_id)
    )
    parties = parties_result.scalars().all()
    parties_info = ", ".join([f"{p.rol_procesal}: {p.nombre_completo}" for p in parties])
    
    case_context_data = {
        "tipo_servicio": case.tipo_servicio,
        "resumen": case.resumen,
        "partes": parties_info,
        "datos_materia": case.datos_materia
    }

    engine = RAGEngine(db)
    prediction = await engine.predict_case_success(case_context_data)
    return prediction

@router.post("/classify")
async def classify_document_endpoint(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("ai.use"))
):
    """Auto-classify uploaded document contents and extract details."""
    file_content = await file.read()
    engine = RAGEngine(db)
    classification = await engine.classify_uploaded_document(file_content, file.filename)
    return classification

@router.post("/summarize-actuacion")
async def summarize_actuacion_endpoint(
    req: AISummarizeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("ai.use"))
):
    """Generate an automatic executive summary of a judicial action."""
    engine = RAGEngine(db)
    summary = await engine.generate_executive_summary(req.actuacion_data)
    return {"summary": summary}

class AIScraperRequest(BaseModel):
    asunto_id: str

@router.post("/scraper/cause")
async def scrape_cause_endpoint(
    req: AIScraperRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("ai.use"))
):
    """Scrapes cause details, runs PII scrub, embeds, and saves to pgvector."""
    scraper = PoderJudicialScraperService(db)
    try:
        res = await scraper.ingest_scraped_case_to_rag(req.asunto_id)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fallo en la ingesta del raspador: {str(e)}")
    finally:
        await scraper.close()


class AIIngestURLRequest(BaseModel):
    url: str           # URL del documento (HTML o PDF)
    titulo: str        # Título de la ley/código
    source_type: str = "ley"  # ley, jurisprudencia, doctrina, reglamento

@router.post("/ingest/url")
async def ingest_from_url(
    req: AIIngestURLRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("ai.use"))
):
    """
    Ingest a law directly from a URL.
    Downloads the content, extracts text, segments by articles, and indexes in pgvector.
    Supports both HTML pages and PDF files.
    """
    import httpx
    import re
    import hashlib
    import uuid

    engine = RAGEngine(db)

    try:
        async with httpx.AsyncClient(
            timeout=60.0, follow_redirects=True, verify=False,
            headers={"User-Agent": "Mozilla/5.0 LexIntellectus/1.0"}
        ) as client:
            response = await client.get(req.url)
            if response.status_code != 200:
                raise HTTPException(400, f"No se pudo descargar: HTTP {response.status_code}")
    except httpx.TimeoutException:
        raise HTTPException(504, "El servidor de origen no respondió (timeout). Intente más tarde o suba el PDF directamente.")
    except Exception as e:
        raise HTTPException(500, f"Error de conexión: {str(e)}")

    content_type = response.headers.get("content-type", "")
    raw_content = response.content

    # PDF handling
    if "pdf" in content_type or req.url.lower().endswith(".pdf"):
        ingest_metadata = {"source_type": req.source_type, "titulo": req.titulo}
        chunks_count = await IngestionPipeline.process_document_async(
            db, raw_content, ingest_metadata, engine
        )
        return {
            "status": "success",
            "titulo": req.titulo,
            "chunks_created": chunks_count,
            "mode": "pdf_article_segmentation"
        }

    # HTML handling
    text = response.text
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<br\s*/?>|</p>|</div>|</li>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&nbsp;', ' ').replace('&quot;', '"')
    text = re.sub(r'\n{3,}', '\n\n', text).strip()

    if len(text) < 200:
        raise HTTPException(400, f"El contenido descargado es demasiado corto ({len(text)} chars)")

    # Split into articles
    articles = IngestionPipeline.split_into_articles(text)

    if not articles:
        # Fallback to generic chunking
        chunks = IngestionPipeline.chunk_text(text)
        articles = [(str(i), chunk) for i, chunk in enumerate(chunks)]

    # Create source
    from sqlalchemy import text as sa_text
    result = await db.execute(
        sa_text("SELECT id FROM legal_sources WHERE titulo = :titulo"),
        {"titulo": req.titulo}
    )
    row = result.fetchone()
    source_id = row[0] if row else uuid.uuid4()

    if not row:
        await db.execute(
            sa_text("""
                INSERT INTO legal_sources (id, titulo, tipo_fuente, estado, created_at, updated_at)
                VALUES (:id, :titulo, :tipo, 'vigente', NOW(), NOW())
            """),
            {"id": source_id, "titulo": req.titulo, "tipo": req.source_type}
        )

    # Ingest articles
    inserted = 0
    for i, (art_num, art_text) in enumerate(articles):
        chunk_hash = hashlib.sha256(art_text.encode()).hexdigest()

        exists = await db.execute(
            sa_text("SELECT id FROM legal_chunks WHERE hash_contenido = :h"),
            {"h": chunk_hash}
        )
        if exists.fetchone():
            continue

        embedding = await engine.get_embedding(art_text)

        def _emb_to_pg(emb):
            return "[" + ",".join(str(v) for v in emb) + "]"

        chunk_id = uuid.uuid4()
        await db.execute(
            sa_text("""
                INSERT INTO legal_chunks
                    (id, source_type, source_id, chunk_index, contenido_texto,
                     vector_embedding, hash_contenido, estado_vigencia, created_at, updated_at)
                VALUES
                    (:id, :stype, :sid, :idx, :contenido,
                     CAST(:emb AS vector), :hash, 'vigente', NOW(), NOW())
            """),
            {
                "id": chunk_id, "stype": req.source_type, "sid": source_id,
                "idx": i, "contenido": art_text,
                "emb": _emb_to_pg(embedding), "hash": chunk_hash,
            }
        )
        inserted += 1

    await db.commit()

    return {
        "status": "success",
        "titulo": req.titulo,
        "articles_detected": len(articles),
        "chunks_created": inserted,
        "text_length": len(text),
        "mode": "html_article_segmentation"
    }


@router.get("/corpus/stats")
async def corpus_stats(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("ai.use"))
):
    """Returns statistics of the legal corpus in the vector database."""
    from sqlalchemy import text as sa_text

    sources = await db.execute(sa_text("""
        SELECT ls.titulo, ls.tipo_fuente, ls.estado,
               COUNT(lc.id) as num_chunks,
               ls.created_at
        FROM legal_sources ls
        LEFT JOIN legal_chunks lc ON lc.source_id = ls.id
        GROUP BY ls.id, ls.titulo, ls.tipo_fuente, ls.estado, ls.created_at
        ORDER BY ls.created_at DESC
    """))

    total_chunks = await db.execute(sa_text("SELECT COUNT(*) FROM legal_chunks"))
    total_sources = await db.execute(sa_text("SELECT COUNT(*) FROM legal_sources"))

    return {
        "total_sources": total_sources.scalar(),
        "total_chunks": total_chunks.scalar(),
        "sources": [
            {
                "titulo": row[0],
                "tipo": row[1],
                "estado": row[2],
                "articles": row[3],
                "created_at": str(row[4]) if row[4] else None
            }
            for row in sources.fetchall()
        ]
    }
