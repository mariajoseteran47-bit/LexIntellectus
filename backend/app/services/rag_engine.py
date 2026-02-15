import os
import json
import asyncio
from typing import List, Dict, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from pgvector.sqlalchemy import Vector
import google.generativeai as genai

from app.core.config import settings
from app.models.ai import LegalChunk, LAASession, LAAMessage, LAACaseTheory, LAAValidation
from app.services.prompts import PromptLibrary

class RAGEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.api_key = settings.GOOGLE_API_KEY if hasattr(settings, 'GOOGLE_API_KEY') else os.getenv("GOOGLE_API_KEY")
        genai.configure(api_key=self.api_key)
        self.embedding_model = "models/gemini-embedding-001"
        self.chat_model = "models/gemini-1.5-flash"

    async def get_embedding(self, text: str) -> List[float]:
        try:
            # Gemini Embedding call (Synchronous in SDK, but we run in thread or just await if it supports it)
            # For now using simple call
            result = genai.embed_content(
                model=self.embedding_model,
                content=text,
                task_type="retrieval_document"
            )
            # The result is 768 dim for text-embedding-004 by default usually
            # But the DB expects 1536 dim if we configured it so.
            # Let's check the vector dim in model definition
            print(f"DEBUG: Embedding dim = {len(result['embedding'])}")
            return result['embedding']
        except Exception as e:
            print(f"Embedding error: {e}")
            raise e

    async def search_context(self, query_text: str, limit: int = 5) -> List[LegalChunk]:
        query_embedding = await self.get_embedding(query_text)
        
        # PGVector search
        stmt = select(LegalChunk).order_by(
            LegalChunk.vector_embedding.l2_distance(query_embedding)
        ).limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def generate_response(
        self, 
        session: LAASession, 
        user_message: str,
        case_context: Optional[str] = None
    ) -> str:
        # 1. Retrieve Context
        chunks = []
        context_str = ""
        
        if session.modo == 'consultor':
            chunks = await self.search_context(user_message)
            context_str = "\n\n".join([f"Fuente: {c.source_type} - {c.hash_contenido[:8]}:\n{c.contenido_texto}" for c in chunks])
        
        # 2. Build System Prompt
        system_prompt = PromptLibrary.get_prompt(session.modo, context_str, case_context)
        
        # 3. Call Gemini
        model = genai.GenerativeModel(self.chat_model)
        full_prompt = f"{system_prompt}\n\nMensaje del Usuario: {user_message}"
        
        # Using synchronous call in a way that works (or just the right async method)
        # Actually generate_content_async is correct for newer SDKs. 
        # But if it failed, let's use the standard one.
        response = model.generate_content(full_prompt)
        response_text = response.text
        
        # 4. Save Message
        msg = LAAMessage(
            session_id=session.id,
            rol='assistant',
            contenido=response_text,
            chunks_utilizados_ids=[c.id for c in chunks],
            modelo_usado=self.chat_model
        )
        self.db.add(msg)
        await self.db.commit()
        
        return response_text

    async def analyze_strategy(self, session: LAASession, case_data: Dict) -> LAACaseTheory:
        # Mode Strategist
        system_prompt = PromptLibrary.get_prompt('estratega', case_data=json.dumps(case_data))
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Generar Teoría del Caso ahora."}
        ]
        
        completion = await self.client.chat.completions.create(
            model=self.chat_model,
            messages=messages,
            response_format={"type": "json_object"}
        )
        
        analysis_json = json.loads(completion.choices[0].message.content)
        
        theory = LAACaseTheory(
            session_id=session.id,
            expediente_id=session.expediente_id,
            resumen_ejecutivo=analysis_json.get('teoria_caso', {}).get('resumen_ejecutivo'),
            hechos_facticos_json=analysis_json.get('teoria_caso', {}).get('hechos_facticos'),
            # ... map other fields
            estrategia_recomendada=analysis_json.get('teoria_caso', {}).get('estrategia')
        )
        self.db.add(theory)
        await self.db.commit()
        return theory
