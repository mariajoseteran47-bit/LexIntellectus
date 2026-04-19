"""
LexIntellectus - Client Profiles API
CRM Legal: Gestión de perfiles de clientes (Natural/Jurídica),
representantes legales, junta directiva y composición accionaria.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.rbac import require_permission
from app.models.user import Usuario
from app.models.client import PerfilCliente, RepresentanteLegal, MiembroJuntaDirectiva, Accionista
from app.schemas.client import (
    ClientProfileCreate, ClientProfileUpdate, ClientProfileResponse,
    ClientProfileListResponse,
    RepresentativeCreate, RepresentativeUpdate, RepresentativeResponse,
    BoardMemberCreate, BoardMemberResponse,
    ShareholderCreate, ShareholderResponse,
)

router = APIRouter(prefix="/clients", tags=["Client Profiles"])


def _profile_options():
    """Common eager-load options for all profile queries."""
    return [
        selectinload(PerfilCliente.representantes),
        selectinload(PerfilCliente.junta_directiva),
        selectinload(PerfilCliente.accionistas),
    ]


@router.get("/profiles", response_model=ClientProfileListResponse)
async def list_client_profiles(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    tipo_persona: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: Usuario = Depends(require_permission("clients.read")),
    db: AsyncSession = Depends(get_db),
):
    """List all client profiles in the current tenant."""
    query = (
        select(PerfilCliente)
        .options(*_profile_options())
        .where(PerfilCliente.tenant_id == current_user.tenant_id)
    )

    if tipo_persona:
        query = query.where(PerfilCliente.tipo_persona == tipo_persona)
    if search:
        term = f"%{search}%"
        query = query.where(
            (PerfilCliente.razon_social.ilike(term))
            | (PerfilCliente.nombre_comercial.ilike(term))
            | (PerfilCliente.cedula_identidad.ilike(term))
            | (PerfilCliente.ruc.ilike(term))
        )

    count_q = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_q)

    query = query.offset((page - 1) * size).limit(size).order_by(PerfilCliente.created_at.desc())
    result = await db.execute(query)
    profiles = result.scalars().unique().all()

    return ClientProfileListResponse(
        items=[ClientProfileResponse.model_validate(p) for p in profiles],
        total=total or 0, page=page, size=size,
    )


@router.get("/profiles/{profile_id}", response_model=ClientProfileResponse)
async def get_client_profile(
    profile_id: str,
    current_user: Usuario = Depends(require_permission("clients.read")),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific client profile with all relationships."""
    result = await db.execute(
        select(PerfilCliente).options(*_profile_options()).where(
            PerfilCliente.id == profile_id,
            PerfilCliente.tenant_id == current_user.tenant_id,
        )
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil de cliente no encontrado")
    return ClientProfileResponse.model_validate(profile)


@router.post("/profiles", response_model=ClientProfileResponse, status_code=201)
async def create_client_profile(
    data: ClientProfileCreate,
    current_user: Usuario = Depends(require_permission("clients.create")),
    db: AsyncSession = Depends(get_db),
):
    """Create a client profile for an existing user."""
    user_result = await db.execute(
        select(Usuario).where(
            Usuario.id == data.user_id,
            Usuario.tenant_id == current_user.tenant_id,
            Usuario.tipo_usuario == "cliente",
        )
    )
    if not user_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Usuario cliente no encontrado en este despacho")

    existing = await db.execute(select(PerfilCliente).where(PerfilCliente.user_id == data.user_id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Este cliente ya tiene un perfil extendido")

    profile = PerfilCliente(tenant_id=current_user.tenant_id, **data.model_dump())
    db.add(profile)
    await db.flush()

    result = await db.execute(
        select(PerfilCliente).options(*_profile_options()).where(PerfilCliente.id == profile.id)
    )
    return ClientProfileResponse.model_validate(result.scalar_one())


@router.patch("/profiles/{profile_id}", response_model=ClientProfileResponse)
async def update_client_profile(
    profile_id: str,
    data: ClientProfileUpdate,
    current_user: Usuario = Depends(require_permission("clients.update")),
    db: AsyncSession = Depends(get_db),
):
    """Update a client profile."""
    result = await db.execute(
        select(PerfilCliente).options(*_profile_options()).where(
            PerfilCliente.id == profile_id,
            PerfilCliente.tenant_id == current_user.tenant_id,
        )
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil de cliente no encontrado")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    await db.flush()
    return ClientProfileResponse.model_validate(profile)


# === REPRESENTANTES LEGALES ===

@router.post("/profiles/{profile_id}/representatives", response_model=RepresentativeResponse, status_code=201)
async def add_representative(
    profile_id: str,
    data: RepresentativeCreate,
    current_user: Usuario = Depends(require_permission("clients.update")),
    db: AsyncSession = Depends(get_db),
):
    """Add a legal representative (apoderado) to a client profile."""
    result = await db.execute(
        select(PerfilCliente).where(
            PerfilCliente.id == profile_id,
            PerfilCliente.tenant_id == current_user.tenant_id,
        )
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil de cliente no encontrado")
    if profile.tipo_persona != "juridica":
        raise HTTPException(status_code=400, detail="Solo personas jurídicas pueden tener representantes legales")

    rep = RepresentanteLegal(client_profile_id=profile.id, tenant_id=current_user.tenant_id, **data.model_dump())
    db.add(rep)
    await db.flush()
    return RepresentativeResponse.model_validate(rep)


@router.patch("/representatives/{rep_id}", response_model=RepresentativeResponse)
async def update_representative(
    rep_id: str,
    data: RepresentativeUpdate,
    current_user: Usuario = Depends(require_permission("clients.update")),
    db: AsyncSession = Depends(get_db),
):
    """Update a legal representative."""
    result = await db.execute(
        select(RepresentanteLegal).where(
            RepresentanteLegal.id == rep_id,
            RepresentanteLegal.tenant_id == current_user.tenant_id,
        )
    )
    rep = result.scalar_one_or_none()
    if not rep:
        raise HTTPException(status_code=404, detail="Representante legal no encontrado")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(rep, field, value)
    await db.flush()
    return RepresentativeResponse.model_validate(rep)


@router.delete("/representatives/{rep_id}", status_code=204)
async def delete_representative(
    rep_id: str,
    current_user: Usuario = Depends(require_permission("clients.update")),
    db: AsyncSession = Depends(get_db),
):
    """Remove a legal representative."""
    result = await db.execute(
        select(RepresentanteLegal).where(
            RepresentanteLegal.id == rep_id, RepresentanteLegal.tenant_id == current_user.tenant_id,
        )
    )
    rep = result.scalar_one_or_none()
    if not rep:
        raise HTTPException(status_code=404, detail="Representante legal no encontrado")
    await db.delete(rep)
    await db.flush()


# === JUNTA DIRECTIVA ===

@router.post("/profiles/{profile_id}/board-members", response_model=BoardMemberResponse, status_code=201)
async def add_board_member(
    profile_id: str,
    data: BoardMemberCreate,
    current_user: Usuario = Depends(require_permission("clients.update")),
    db: AsyncSession = Depends(get_db),
):
    """Add a board member to a corporate client profile."""
    result = await db.execute(
        select(PerfilCliente).where(
            PerfilCliente.id == profile_id,
            PerfilCliente.tenant_id == current_user.tenant_id,
            PerfilCliente.tipo_persona == "juridica",
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Perfil jurídico no encontrado")

    member = MiembroJuntaDirectiva(
        client_profile_id=profile_id, tenant_id=current_user.tenant_id, **data.model_dump()
    )
    db.add(member)
    await db.flush()
    return BoardMemberResponse.model_validate(member)


@router.delete("/board-members/{member_id}", status_code=204)
async def delete_board_member(
    member_id: str,
    current_user: Usuario = Depends(require_permission("clients.update")),
    db: AsyncSession = Depends(get_db),
):
    """Remove a board member."""
    result = await db.execute(
        select(MiembroJuntaDirectiva).where(
            MiembroJuntaDirectiva.id == member_id,
            MiembroJuntaDirectiva.tenant_id == current_user.tenant_id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Miembro de junta no encontrado")
    await db.delete(member)
    await db.flush()


# === ACCIONISTAS / COMPOSICIÓN ACCIONARIA ===

@router.post("/profiles/{profile_id}/shareholders", response_model=ShareholderResponse, status_code=201)
async def add_shareholder(
    profile_id: str,
    data: ShareholderCreate,
    current_user: Usuario = Depends(require_permission("clients.update")),
    db: AsyncSession = Depends(get_db),
):
    """Add a shareholder to a corporate client profile."""
    result = await db.execute(
        select(PerfilCliente).where(
            PerfilCliente.id == profile_id,
            PerfilCliente.tenant_id == current_user.tenant_id,
            PerfilCliente.tipo_persona == "juridica",
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Perfil jurídico no encontrado")

    shareholder = Accionista(
        client_profile_id=profile_id, tenant_id=current_user.tenant_id, **data.model_dump()
    )
    db.add(shareholder)
    await db.flush()
    return ShareholderResponse.model_validate(shareholder)


@router.delete("/shareholders/{shareholder_id}", status_code=204)
async def delete_shareholder(
    shareholder_id: str,
    current_user: Usuario = Depends(require_permission("clients.update")),
    db: AsyncSession = Depends(get_db),
):
    """Remove a shareholder."""
    result = await db.execute(
        select(Accionista).where(
            Accionista.id == shareholder_id,
            Accionista.tenant_id == current_user.tenant_id,
        )
    )
    shareholder = result.scalar_one_or_none()
    if not shareholder:
        raise HTTPException(status_code=404, detail="Accionista no encontrado")
    await db.delete(shareholder)
    await db.flush()
