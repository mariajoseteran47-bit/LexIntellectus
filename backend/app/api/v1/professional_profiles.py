"""
LexIntellectus - Professional Profiles API
Gestión del talento legal: seniority, especialidades, tarifas.
Plan Estratégico v3.0, Fase 1A.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.rbac import require_permission
from app.models.user import Usuario
from app.models.professional import PerfilProfesional
from app.schemas.professional import (
    ProfessionalProfileCreate, ProfessionalProfileUpdate,
    ProfessionalProfileResponse,
)

router = APIRouter(prefix="/professionals", tags=["Professional Profiles"])


@router.get("", response_model=List[ProfessionalProfileResponse])
async def list_professional_profiles(
    nivel: Optional[str] = Query(None),
    especialidad: Optional[str] = Query(None),
    current_user: Usuario = Depends(require_permission("users.read")),
    db: AsyncSession = Depends(get_db),
):
    """List professional profiles in the tenant, filterable by seniority and specialty."""
    query = select(PerfilProfesional).where(
        PerfilProfesional.tenant_id == current_user.tenant_id
    )

    if nivel:
        query = query.where(PerfilProfesional.nivel_jerarquico == nivel)

    if especialidad:
        # JSONB contains check for specialties array
        query = query.where(
            PerfilProfesional.especialidades.contains([especialidad])
        )

    result = await db.execute(query.order_by(PerfilProfesional.nivel_jerarquico))
    profiles = result.scalars().all()
    return [ProfessionalProfileResponse.model_validate(p) for p in profiles]


@router.get("/{profile_id}", response_model=ProfessionalProfileResponse)
async def get_professional_profile(
    profile_id: str,
    current_user: Usuario = Depends(require_permission("users.read")),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific professional profile."""
    result = await db.execute(
        select(PerfilProfesional).where(
            PerfilProfesional.id == profile_id,
            PerfilProfesional.tenant_id == current_user.tenant_id,
        )
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil profesional no encontrado")
    return ProfessionalProfileResponse.model_validate(profile)


@router.get("/by-user/{user_id}", response_model=ProfessionalProfileResponse)
async def get_profile_by_user(
    user_id: str,
    current_user: Usuario = Depends(require_permission("users.read")),
    db: AsyncSession = Depends(get_db),
):
    """Get a professional profile by user ID."""
    result = await db.execute(
        select(PerfilProfesional).where(
            PerfilProfesional.user_id == user_id,
            PerfilProfesional.tenant_id == current_user.tenant_id,
        )
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Este usuario no tiene perfil profesional")
    return ProfessionalProfileResponse.model_validate(profile)


@router.post("", response_model=ProfessionalProfileResponse, status_code=201)
async def create_professional_profile(
    data: ProfessionalProfileCreate,
    current_user: Usuario = Depends(require_permission("users.create")),
    db: AsyncSession = Depends(get_db),
):
    """Create a professional profile for a team member."""
    # Verify user exists and is a professional type
    user_result = await db.execute(
        select(Usuario).where(
            Usuario.id == data.user_id,
            Usuario.tenant_id == current_user.tenant_id,
        )
    )
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if user.tipo_usuario in ("cliente",):
        raise HTTPException(
            status_code=400,
            detail="Los clientes no pueden tener perfil profesional. Use el perfil de cliente."
        )

    # Check existing
    existing = await db.execute(
        select(PerfilProfesional).where(PerfilProfesional.user_id == data.user_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Este usuario ya tiene un perfil profesional")

    profile = PerfilProfesional(
        tenant_id=current_user.tenant_id,
        **data.model_dump()
    )
    db.add(profile)
    await db.flush()
    return ProfessionalProfileResponse.model_validate(profile)


@router.patch("/{profile_id}", response_model=ProfessionalProfileResponse)
async def update_professional_profile(
    profile_id: str,
    data: ProfessionalProfileUpdate,
    current_user: Usuario = Depends(require_permission("users.update")),
    db: AsyncSession = Depends(get_db),
):
    """Update a professional profile (seniority, specialties, rates)."""
    result = await db.execute(
        select(PerfilProfesional).where(
            PerfilProfesional.id == profile_id,
            PerfilProfesional.tenant_id == current_user.tenant_id,
        )
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil profesional no encontrado")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    await db.flush()
    return ProfessionalProfileResponse.model_validate(profile)
