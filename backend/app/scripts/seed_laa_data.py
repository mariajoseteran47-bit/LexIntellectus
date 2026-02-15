import asyncio
import uuid
from datetime import datetime, date
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.models.tenant import Despacho, Sede
from app.models.user import Usuario
from app.models.case import Expediente, EstadoExpediente
from app.models.ai import LegalChunk, LAASession, LAAMessage
from app.core.config import settings

# Database connection URL
SQLALCHEMY_DATABASE_URL = "postgresql+asyncpg://lexintellectus:lexintellectus_dev_2026@postgres:5432/lexintellectus"

async def seed_data():
    engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 1. Get or Create Tenant
        res = await session.execute(select(Despacho).limit(1))
        tenant = res.scalar_one_or_none()
        if not tenant:
            tenant = Despacho(
                id=uuid.uuid4(),
                nombre="Bufete de Prueba",
                ruc="J031000000001",
                email="admin@prueba.com"
            )
            session.add(tenant)
            await session.flush()

        # 2. Get or Create User
        res = await session.execute(select(Usuario).limit(1))
        user = res.scalar_one_or_none()
        if not user:
            user = Usuario(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                email="abogado@prueba.com",
                password_hash="hash", # Not used for logic here
                nombre="Juan",
                apellido="Pérez",
                tipo_usuario="abogado"
            )
            session.add(user)
            await session.flush()

        # 3. Create a Case (Expediente)
        case = Expediente(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            numero_interno="EXP-2026-001",
            numero_causa="00123-4567-CV",
            ramo="civil",
            materia_especifica="Incumplimiento de Contrato",
            juzgado="Juzgado Primero de Distrito Civil de Managua",
            resumen="Caso de prueba sobre incumplimiento de contrato de servicios profesionales.",
            abogado_responsable_id=user.id,
            fecha_apertura=date.today()
        )
        session.add(case)
        await session.flush()

        # 4. Seed Legal Chunks (Simulating Nicaraguan Civil Code)
        chunks = [
            LegalChunk(
                source_type="ley",
                contenido_texto="Art. 1836.- El contrato es ley entre las partes y debe cumplirse de buena fe.",
                hash_contenido="hash_art_1836",
                tokens_count=20,
                chunk_index=0
            ),
            LegalChunk(
                source_type="ley",
                contenido_texto="Art. 2010.- La mora del deudor da derecho al acreedor a solicitar la resolución del contrato o su cumplimiento con indemnización de daños.",
                hash_contenido="hash_art_2010",
                tokens_count=30,
                chunk_index=1
            )
        ]
        for c in chunks:
            # Check if exists by hash to avoid dupes
            exists = await session.execute(select(LegalChunk).where(LegalChunk.hash_contenido == c.hash_contenido))
            if not exists.scalar_one_or_none():
                session.add(c)
        
        await session.flush()

        # 5. Create an AI Session
        ai_session = LAASession(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            usuario_id=user.id,
            expediente_id=case.id,
            modo="consultor",
            titulo="Consulta sobre Mora"
        )
        session.add(ai_session)
        await session.flush()

        # 6. Add a Message
        msg = LAAMessage(
            session_id=ai_session.id,
            rol="user",
            contenido="¿Qué dice el Código Civil sobre el incumplimiento de contrato?"
        )
        session.add(msg)
        
        await session.commit()
        print(f"✅ Seeding completado con éxito.")
        print(f"Expediente ID: {case.id}")
        print(f"Usuario ID: {user.id}")

if __name__ == "__main__":
    asyncio.run(seed_data())
