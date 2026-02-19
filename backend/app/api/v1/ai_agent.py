from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID

from app.core.database import get_db
from app.models.user import Usuario
from app.core.dependencies import get_current_user
from app.models.ai import LAASession, LegalChunk, LAAMessage
from app.services.rag_engine import RAGEngine
from app.services.ingestion import IngestionPipeline

router = APIRouter(prefix="/ai", tags=["AI"])

@router.post("/chat")
async def chat_interaction(
    message: str = Body(...),
    mode: str = Body(..., regex="^(consultor|estratega|redactor|cartulario)$"),
    session_id: Optional[UUID] = Body(None),
    expediente_id: Optional[UUID] = Body(None),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
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

    # 3. Process with RAG Engine
    engine = RAGEngine(db)
    
    if mode == 'estratega':
        # Fetch case data if expediente_id provided (mocked for now)
        case_data = {"resumen": "Caso de ejemplo...", "monto": 50000}
        await engine.analyze_strategy(session, case_data)
        response_text = "He generado la Teoría del Caso. Puedes verla en el panel lateral."
    elif mode == 'cartulario':
         response_text = "Por favor sube el documento para validar en modo Cartulario."
    else:
        # Consultant / Redactor
        response_text = await engine.generate_response(session, message)
    
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
    current_user: Usuario = Depends(get_current_user)
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
    current_user: Usuario = Depends(get_current_user)
):
    session = await db.get(LAASession, session_id)
    if not session:
        raise HTTPException(404, "Session not found")
        
    # Return messages (joined load ideally)
    # Lazy load will fail in async without specific loader options or explicit query.
    # For now just confirming endpoints exist.
    return {"session": session}
