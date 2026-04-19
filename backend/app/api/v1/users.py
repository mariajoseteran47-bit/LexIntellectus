"""
LexIntellectus - Users API
CRUD endpoints for user management within a tenant.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.core.database import get_db
from app.core.security import hash_password
from app.core.dependencies import get_current_user, get_current_active_admin
from app.models.user import Usuario
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    role_filter: Optional[str] = Query(None, alias="role"),
    search: Optional[str] = None,
    current_user: Usuario = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all users in the current tenant (admin only)."""
    query = select(Usuario).where(Usuario.tenant_id == current_user.tenant_id)

    if status_filter:
        query = query.where(Usuario.status == status_filter)

    if role_filter:
        query = query.where(Usuario.tipo_usuario == role_filter)

    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Usuario.nombre.ilike(search_term))
            | (Usuario.apellido.ilike(search_term))
            | (Usuario.email.ilike(search_term))
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Paginate
    query = query.offset((page - 1) * size).limit(size).order_by(Usuario.nombre)
    result = await db.execute(query)
    users = result.scalars().all()

    return UserListResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        size=size,
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: UserCreate,
    current_user: Usuario = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new user within the current tenant (admin only)."""
    # Check duplicate email
    existing = await db.execute(
        select(Usuario).where(Usuario.email == request.email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya está registrado",
        )

    user = Usuario(
        tenant_id=current_user.tenant_id,
        sede_id=request.sede_id,
        email=request.email,
        password_hash=hash_password(request.password),
        nombre=request.nombre,
        apellido=request.apellido,
        telefono=request.telefono,
        tipo_usuario=request.tipo_usuario,
        tipo_vinculo=request.tipo_vinculo,
    )
    db.add(user)
    await db.flush()

    return UserResponse.model_validate(user)


@router.get("/{user_id}/", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific user by ID (must be in same tenant)."""
    result = await db.execute(
        select(Usuario).where(
            Usuario.id == user_id,
            Usuario.tenant_id == current_user.tenant_id,
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    request: UserUpdate,
    current_user: Usuario = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update a user's information (admin only)."""
    result = await db.execute(
        select(Usuario).where(
            Usuario.id == user_id,
            Usuario.tenant_id == current_user.tenant_id,
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado",
        )

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    await db.flush()
    return UserResponse.model_validate(user)
