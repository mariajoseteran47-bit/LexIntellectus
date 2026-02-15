import asyncio
from app.services.rag_engine import RAGEngine
from app.core.database import AsyncSessionLocal
from app.models.ai import LAASession
from sqlalchemy import select

async def verify_logic():
    print("🧠 Iniciando verificación lógica del LAA Engine...")
    
    # Pregunta de prueba
    pregunta = "¿Qué dice el Código Civil sobre el cumplimiento de los contratos?"
    
    # Usar un tenant dummy (el que sembramos tiene ID predecible si lo buscamos)
    async with AsyncSessionLocal() as db:
        engine = RAGEngine(db=db)
        
        # Recuperar la sesión que sembramos
        res = await db.execute(select(LAASession).limit(1))
        session_obj = res.scalar_one_or_none()
        
        if not session_obj:
            print("❌ No se encontró la sesión de prueba. ¿Corriste el seeding?")
            return

        # 1. Probar Búsqueda de Contexto (RAG Retrieval)
        print(f"🔍 Buscando contexto legal para: {pregunta}")
        chunks = await engine.search_context(pregunta)
        if chunks:
            print(f"✅ Se encontraron {len(chunks)} fragmentos relevantes:")
            for c in chunks:
                print(f"   - [{c.source_type}] {c.contenido_texto[:60]}...")
        else:
            print("❌ No se encontraron fragmentos. ¿Corriste el seeding?")
            return

        # 2. Probar Generación (LLM)
        print(f"\n🤖 Procesando generación con Gemini para sesión {session_obj.id}...")
        try:
            response = await engine.generate_response(
                session=session_obj,
                user_message=pregunta
            )
            print(f"\nLAA: {response}")
            print("\n✅ Verificación lógica COMPLETA (End-to-End).")
        except Exception as e:
            print(f"\n⚠️ Error en generación LLM: {e}")
            print("💡 La arquitectura RAG ha sido validada en su fase de RECUPERACIÓN (DB -> Vector -> Contexto).")

if __name__ == "__main__":
    asyncio.run(verify_logic())
