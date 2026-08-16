import asyncio
from sqlalchemy import select, update
from app.core.database import AsyncSessionLocal
from app.models.user import Usuario
from app.core.security import hash_password, verify_password

async def reset():
    print("Resetting all passwords to admin123...")
    new_hash = hash_password("admin123")
    print(f"Generated hash: {new_hash}")
    
    async with AsyncSessionLocal() as db:
        await db.execute(update(Usuario).values(password_hash=new_hash))
        await db.commit()
        
        # Verify admin user
        res = await db.execute(select(Usuario).where(Usuario.email == "admin@lexintellectus.com"))
        admin = res.scalar_one_or_none()
        if admin:
            ok = verify_password("admin123", admin.password_hash)
            print(f"Admin verify result: {ok}")
            print(f"Admin email: {admin.email}")
            print(f"Admin status: {admin.status}")
        else:
            print("Admin user not found!")

if __name__ == "__main__":
    asyncio.run(reset())
