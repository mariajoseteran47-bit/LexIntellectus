"""
LexIntellectus - Tenants API
CRUD endpoints for tenant (despacho) and sede management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_active_admin
from app.models.user import Usuario
from app.models.tenant import Despacho, Sede
from app.schemas.tenant import (
    TenantUpdate,
    TenantResponse,
    SedeCreate,
    SedeResponse,
)

router = APIRouter(prefix="/tenants", tags=["Tenants"])


@router.get("/current", response_model=TenantResponse)
async def get_current_tenant(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's tenant (despacho) information."""
    result = await db.execute(
        select(Despacho).where(Despacho.id == current_user.tenant_id)
    )
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Despacho no encontrado",
        )

    return TenantResponse.model_validate(tenant)


@router.patch("/current", response_model=TenantResponse)
async def update_current_tenant(
    request: TenantUpdate,
    current_user: Usuario = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update the current tenant's information (admin only)."""
    result = await db.execute(
        select(Despacho).where(Despacho.id == current_user.tenant_id)
    )
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Despacho no encontrado",
        )

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tenant, field, value)

    await db.flush()
    return TenantResponse.model_validate(tenant)


# === Sedes (Branches) ===

@router.get("/current/sedes", response_model=List[SedeResponse])
async def list_sedes(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all branches of the current tenant."""
    result = await db.execute(
        select(Sede)
        .where(Sede.tenant_id == current_user.tenant_id)
        .order_by(Sede.es_casa_matriz.desc(), Sede.nombre)
    )
    sedes = result.scalars().all()
    return [SedeResponse.model_validate(s) for s in sedes]


@router.post(
    "/current/sedes",
    response_model=SedeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_sede(
    request: SedeCreate,
    current_user: Usuario = Depends(get_current_active_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new branch for the current tenant (admin only)."""
    # If this is marked as HQ, unset any existing HQ
    if request.es_casa_matriz:
        existing_hq = await db.execute(
            select(Sede).where(
                Sede.tenant_id == current_user.tenant_id,
                Sede.es_casa_matriz == True,
            )
        )
        hq = existing_hq.scalar_one_or_none()
        if hq:
            hq.es_casa_matriz = False

    sede = Sede(
        tenant_id=current_user.tenant_id,
        nombre=request.nombre,
        direccion=request.direccion,
        ciudad=request.ciudad,
        departamento=request.departamento,
        telefono=request.telefono,
        email=request.email,
        es_casa_matriz=request.es_casa_matriz,
    )
    db.add(sede)
    await db.flush()

    return SedeResponse.model_validate(sede)
