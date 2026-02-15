"""
LexIntellectus - Auth API
Login, registration, and token refresh endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import uuid

from app.core.database import get_db
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.config import settings
from app.core.dependencies import get_current_user
from app.models.user import Usuario
from app.models.tenant import Despacho, Sede
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserInfoResponse,
    AuthResponse,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Authenticate user with email and password.
    Returns JWT access and refresh tokens.
    """
    # Find user by email
    result = await db.execute(
        select(Usuario).where(Usuario.email == request.email)
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if str(user.status) != "activo":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta inactiva o bloqueada. Contacte al administrador.",
        )

    # Update last login
    user.last_login = datetime.utcnow()

    # Get tenant name
    tenant_result = await db.execute(
        select(Despacho.nombre).where(Despacho.id == user.tenant_id)
    )
    tenant_nombre = tenant_result.scalar_one_or_none()

    # Create tokens
    extra_claims = {
        "tenant_id": str(user.tenant_id),
        "tipo_usuario": str(user.tipo_usuario),
    }
    access_token = create_access_token(str(user.id), extra_claims=extra_claims)
    refresh_token = create_refresh_token(str(user.id))

    return AuthResponse(
        token=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        ),
        user=UserInfoResponse(
            id=user.id,
            email=user.email,
            nombre=user.nombre,
            apellido=user.apellido,
            tipo_usuario=str(user.tipo_usuario),
            tenant_id=user.tenant_id,
            tenant_nombre=tenant_nombre,
            sede_id=user.sede_id,
            foto_url=user.foto_url,
            status=str(user.status),
            last_login=user.last_login,
        ),
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Register a new tenant (despacho) with an admin user.
    Creates the law firm, a default HQ branch, and the first admin user.
    """
    # Check if email already exists
    existing = await db.execute(
        select(Usuario).where(Usuario.email == request.email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya está registrado",
        )

    # Create tenant (despacho)
    tenant = Despacho(
        nombre=request.tenant_nombre,
        ruc=request.tenant_ruc,
        email=request.email,
    )
    db.add(tenant)
    await db.flush()  # Get tenant.id

    # Create default casa matriz
    sede = Sede(
        tenant_id=tenant.id,
        nombre="Casa Matriz",
        es_casa_matriz=True,
    )
    db.add(sede)
    await db.flush()

    # Create admin user
    user = Usuario(
        tenant_id=tenant.id,
        sede_id=sede.id,
        email=request.email,
        password_hash=hash_password(request.password),
        nombre=request.nombre,
        apellido=request.apellido,
        telefono=request.telefono,
        tipo_usuario="admin_despacho",
        tipo_vinculo="socio",
        last_login=datetime.utcnow(),
    )
    db.add(user)
    await db.flush()

    # Create tokens
    extra_claims = {
        "tenant_id": str(tenant.id),
        "tipo_usuario": str(user.tipo_usuario),
    }
    access_token = create_access_token(str(user.id), extra_claims=extra_claims)
    refresh_token = create_refresh_token(str(user.id))

    return AuthResponse(
        token=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        ),
        user=UserInfoResponse(
            id=user.id,
            email=user.email,
            nombre=user.nombre,
            apellido=user.apellido,
            tipo_usuario=str(user.tipo_usuario),
            tenant_id=tenant.id,
            tenant_nombre=tenant.nombre,
            sede_id=sede.id,
            foto_url=None,
            status=str(user.status),
            last_login=user.last_login,
        ),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest, db: AsyncSession = Depends(get_db)
):
    """Refresh an expired access token using a valid refresh token."""
    payload = decode_token(request.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresco inválido o expirado",
        )

    user_id = payload.get("sub")
    result = await db.execute(select(Usuario).where(Usuario.id == user_id))
    user = result.scalar_one_or_none()

    if not user or str(user.status) != "activo":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado o inactivo",
        )

    extra_claims = {
        "tenant_id": str(user.tenant_id),
        "tipo_usuario": str(user.tipo_usuario),
    }
    new_access = create_access_token(str(user.id), extra_claims=extra_claims)
    new_refresh = create_refresh_token(str(user.id))

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserInfoResponse)
async def get_me(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current authenticated user's profile."""
    tenant_result = await db.execute(
        select(Despacho.nombre).where(Despacho.id == current_user.tenant_id)
    )
    tenant_nombre = tenant_result.scalar_one_or_none()

    return UserInfoResponse(
        id=current_user.id,
        email=current_user.email,
        nombre=current_user.nombre,
        apellido=current_user.apellido,
        tipo_usuario=str(current_user.tipo_usuario),
        tenant_id=current_user.tenant_id,
        tenant_nombre=tenant_nombre,
        sede_id=current_user.sede_id,
        foto_url=current_user.foto_url,
        status=str(current_user.status),
        last_login=current_user.last_login,
    )
