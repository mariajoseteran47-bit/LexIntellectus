import asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.user import Usuario
from app.models.tenant import Despacho
from app.core.security import hash_password
from sqlalchemy import select

async def create_admin():
    print("🚀 Creando usuario administrador...")
    async with AsyncSessionLocal() as db:
        # Get Tenant
        res = await db.execute(select(Despacho).limit(1))
        tenant = res.scalar_one_or_none()
        
        if not tenant:
            tenant = Despacho(
                id=uuid.uuid4(),
                nombre="LexIntellectus Demo",
                ruc="001-000000-0000X",
                email="contacto@lexintellectus.com"
            )
            db.add(tenant)
            await db.flush()

        # Check if admin exists
        res = await db.execute(select(Usuario).where(Usuario.email == "admin@lexintellectus.com"))
        admin = res.scalar_one_or_none()
        
        if not admin:
            p = "admin123"
            print(f"DEBUG: Hashing password '{p}'")
            h = hash_password(p)
            print(f"DEBUG: Hash generated: {h[:10]}...")
            admin = Usuario(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                email="admin@lexintellectus.com",
                password_hash=h,
                nombre="Admin",
                apellido="LexIntellectus",
                tipo_usuario="admin_despacho",
                status="activo"
            )
            db.add(admin)
            await db.commit()
            print("✅ Usuario Administrador creado!")
            print("📧 Email: admin@lexintellectus.com")
            print("🔑 Password: admin123")
        else:
            print("ℹ️ El usuario administrador ya existe.")

if __name__ == "__main__":
    asyncio.run(create_admin())
