import asyncio
import uuid
from datetime import datetime, timezone
from sqlalchemy import text
from app.core.database import engine, Base
import app.models  # Ensure all models are registered
from app.core.security import hash_password

async def final_rebuild():
    print("🚀 Iniciando RECONSTRUCCIÓN FINAL (con extensiones)...")
    
    # 1. Purga total y extensiones
    async with engine.begin() as conn:
        print("🧹 Limpiando esquema...")
        await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE;"))
        await conn.execute(text("CREATE SCHEMA public;"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO lexintellectus;"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))
        
        print("🔧 Instalando extensiones (pgvector)...")
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
    
    # 2. Creación de tablas
    async with engine.begin() as conn:
        print("🏗️ Creando todas las tablas desde los modelos...")
        await conn.run_sync(Base.metadata.create_all)
    
    # 3. Sembrado de Admin
    print("🌱 Sembrando datos básicos...")
    async with engine.begin() as conn:
        tenant_id = uuid.uuid4()
        sede_id = uuid.uuid4()
        user_id = uuid.uuid4()
        
        # Insert Tenant
        await conn.execute(text("""
            INSERT INTO tenants (id, nombre, ruc, email, status, created_at, updated_at)
            VALUES (:id, 'LexIntellectus Demo', '001-000000-0000X', 'contacto@lexintellectus.com', 'activo', NOW(), NOW())
        """), {"id": tenant_id})
        
        # Insert Branch
        await conn.execute(text("""
            INSERT INTO branches (id, tenant_id, nombre, es_casa_matriz, status, created_at, updated_at)
            VALUES (:id, :tenant_id, 'Casa Matriz', true, 'activa', NOW(), NOW())
        """), {"id": sede_id, "tenant_id": tenant_id})
        
        # Insert Admin
        pass_hash = hash_password("admin123")
        await conn.execute(text("""
            INSERT INTO users (id, tenant_id, sede_id, email, password_hash, nombre, apellido, tipo_usuario, status, last_login, created_at, updated_at)
            VALUES (:id, :tenant_id, :sede_id, 'admin@lexintellectus.com', :pass_hash, 'Admin', 'LexIntellectus', 'admin_despacho', 'activo', NOW(), NOW(), NOW())
        """), {"id": user_id, "tenant_id": tenant_id, "sede_id": sede_id, "pass_hash": pass_hash})
        
    print("✅ RECONSTRUCCIÓN FINAL EXITOSA!")

if __name__ == "__main__":
    asyncio.run(final_rebuild())
