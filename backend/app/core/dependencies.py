"""
LexIntellectus ERP - Core Dependencies
Shared dependency injection functions for API routes.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import oauth2_scheme, decode_token
from app.models.user import Usuario


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    """Extract and validate the current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    user_id: Optional[str] = payload.get("sub")
    token_type: Optional[str] = payload.get("type")

    if user_id is None or token_type != "access":
        raise credentials_exception

    result = await db.execute(select(Usuario).where(Usuario.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    if user.status != "activo":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo o bloqueado",
        )

    return user


async def get_current_active_admin(
    current_user: Usuario = Depends(get_current_user),
) -> Usuario:
    """Ensure the current user is an admin."""
    if current_user.tipo_usuario not in ("admin_sistema", "admin_despacho"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permisos insuficientes. Se requiere rol de administrador.",
        )
    return current_user
