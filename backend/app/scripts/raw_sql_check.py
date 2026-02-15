import asyncio
from sqlalchemy import text
from app.core.database import engine

async def raw_sql_check():
    print("🔍 Ejecutando RAW SQL check...")
    async with engine.connect() as conn:
        # Check columns of workers
        result = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'users';"))
        columns = [row[0] for row in result]
        print(f"Columnas en 'users' (vía SQLAlchemy engine): {columns}")
        
        # Check if table even exists
        result = await conn.execute(text("SELECT to_regclass('public.users');"))
        regclass = result.scalar()
        print(f"Regclass for public.users: {regclass}")

if __name__ == "__main__":
    asyncio.run(raw_sql_check())
