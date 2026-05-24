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
    mode: str = Body(..., regex="^(consultor|estratega|redactor|cartulario)$"),
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
    source_type: str = Form("ley"), # ley, jurisprudencia
    metadata: str = Form("{}"), # JSON string
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("ai.use"))
):
    # Verify Admin role?
    # if current_user.role.name != 'admin': ...
    
    content = await file.read()
    engine = RAGEngine(db)
    
    # Ingest
    chunks_count = await IngestionPipeline.process_document_async(
        db, content, {"source_type": source_type}, engine
    )
    
    return {"status": "success", "chunks_created": chunks_count}

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
