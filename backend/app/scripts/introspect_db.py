import asyncio
from sqlalchemy import inspect, text
from app.core.database import engine

async def introspect_schema():
    print("🔍 Introspeccionando esquema de base de datos...")
    async with engine.connect() as conn:
        def get_table_info(sync_conn):
            inspector = inspect(sync_conn)
            tables = inspector.get_table_names()
            print(f"Tablas encontradas: {tables}")
            
            if 'users' in tables:
                print("\n📋 Columnas en 'users':")
                for col in inspector.get_columns('users'):
                    print(f"  - {col['name']}: {col['type']}")
                
                print("\n📋 PK en 'users':")
                print(f"  - {inspector.get_pk_constraint('users')}")
            else:
                print("\n❌ Tabla 'users' no encontrada!")

        await conn.run_sync(get_table_info)

if __name__ == "__main__":
    asyncio.run(introspect_schema())
