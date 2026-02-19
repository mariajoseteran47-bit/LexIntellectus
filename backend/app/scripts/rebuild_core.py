import asyncio
from datetime import datetime, timezone
import uuid
from sqlalchemy import text
from app.core.database import AsyncSessionLocal, Base, engine
import app.models  # Registers all models in Base.metadata
from app.models.user import Usuario
from app.models.tenant import Despacho, Sede
from app.core.security import hash_password

async def rebuild_core_tables():
    print("🧹 Realizando limpieza total de tablas core...")
    async with engine.begin() as conn:
        # Esto dropeará todas las tablas definidas en Base
        await conn.run_sync(Base.metadata.drop_all)
    
    print("🏗️ Recreando tablas core...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("🌱 Re-sembrando administrador...")
    async with AsyncSessionLocal() as db:
        tenant = Despacho(
            id=uuid.uuid4(),
            nombre="LexIntellectus Demo",
            ruc="001-000000-0000X",
            email="contacto@lexintellectus.com",
            status="activo"
        )
        db.add(tenant)
        await db.flush()

        sede = Sede(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            nombre="Casa Matriz",
            es_casa_matriz=True,
            status="activa"
        )
        db.add(sede)
        await db.flush()

        admin = Usuario(
            tenant_id=tenant.id,
            sede_id=sede.id,
            email="admin@lexintellectus.com",
            password_hash=hash_password("admin123"),
            nombre="Admin",
            apellido="LexIntellectus",
            tipo_usuario="admin_despacho",
            status="activo",
            last_login=datetime.now()
        )
        db.add(admin)
        await db.commit()
    
    print("✅ Reconstrucción exitosa!")

if __name__ == "__main__":
    asyncio.run(rebuild_core_tables())
