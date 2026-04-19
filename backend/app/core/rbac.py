"""
LexIntellectus ERP - RBAC (Role-Based Access Control) System
Permission checking dependencies for FastAPI routes.

Usage:
    @router.get("/cases")
    async def list_cases(
        current_user: Usuario = Depends(require_permission("cases.read")),
        ...
    ):

Permission format: "module.action"
    - cases.read, cases.create, cases.update, cases.delete
    - deadlines.read, deadlines.create, deadlines.update, deadlines.delete
    - documents.read, documents.create, documents.delete
    - users.read, users.create, users.update, users.delete
    - clients.read, clients.create, clients.update
    - tenants.read, tenants.update
    - ai.use
    - settings.read, settings.update
    - reports.read
"""

from typing import List, Optional
from functools import lru_cache
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import Usuario, Rol, Permiso, UsuarioRol, RolPermiso


# === Default permission mapping by user type ===
# This provides fallback permissions when no explicit roles are assigned.
# In production, roles/permissions in DB take priority.
DEFAULT_PERMISSIONS = {
    "admin_sistema": ["*"],  # Full access
    "admin_despacho": [
        "cases.*", "deadlines.*", "documents.*", "users.*",
        "clients.*", "tenants.*", "ai.use", "settings.*",
        "reports.*", "notifications.*", "knowledge.*",
    ],
    "abogado": [
        "cases.read", "cases.create", "cases.update",
        "deadlines.read", "deadlines.create", "deadlines.update",
        "documents.read", "documents.create",
        "clients.read", "clients.create", "clients.update",
        "ai.use", "reports.read",
    ],
    "notario": [
        "cases.read", "cases.create", "cases.update",
        "deadlines.read", "deadlines.create", "deadlines.update",
        "documents.read", "documents.create",
        "clients.read", "clients.create",
        "ai.use",
    ],
    "secretaria": [
        "cases.read", "cases.create",
        "deadlines.read", "deadlines.create", "deadlines.update",
        "documents.read", "documents.create",
        "clients.read", "clients.create",
    ],
    "contador": [
        "cases.read",
        "reports.read",
        "clients.read",
    ],
    "gestor": [
        "cases.read",
        "deadlines.read",
        "documents.read", "documents.create",
        "clients.read",
    ],
    "cliente": [
        "cases.read",  # Only their own cases (enforced at query level)
        "documents.read",
    ],
}


def _match_permission(required: str, granted: str) -> bool:
    """
    Check if a granted permission matches a required one.
    Supports wildcard patterns:
        - "*" matches everything
        - "cases.*" matches "cases.read", "cases.create", etc.
    """
    if granted == "*":
        return True
    if granted == required:
        return True
    # Wildcard: "module.*" matches "module.action"
    if granted.endswith(".*"):
        module = granted[:-2]
        if required.startswith(module + "."):
            return True
    return False


def has_permission(user_type: str, permission: str, db_permissions: Optional[List[str]] = None) -> bool:
    """
    Check if a user type or explicit DB permissions grant the required permission.
    DB permissions take priority if provided and non-empty.
    """
    # If DB-level permissions are loaded, use them
    if db_permissions:
        return any(_match_permission(permission, p) for p in db_permissions)

    # Fall back to default type-based permissions
    type_perms = DEFAULT_PERMISSIONS.get(user_type, [])
    return any(_match_permission(permission, p) for p in type_perms)


async def _load_user_permissions(user: Usuario, db: AsyncSession) -> List[str]:
    """
    Load explicit permissions from DB for a user through their assigned roles.
    Returns a list of permission codes, or empty list if none assigned.
    """
    try:
        # Query: User -> UserRoles -> Roles -> RolePermissions -> Permissions
        query = (
            select(Permiso.codigo)
            .join(RolPermiso, RolPermiso.permission_id == Permiso.id)
            .join(Rol, Rol.id == RolPermiso.role_id)
            .join(UsuarioRol, UsuarioRol.role_id == Rol.id)
            .where(UsuarioRol.user_id == user.id)
        )
        result = await db.execute(query)
        permissions = [row[0] for row in result.all()]
        return permissions
    except Exception:
        # If tables don't exist yet or query fails, return empty
        return []


def require_permission(*permissions: str):
    """
    FastAPI dependency factory that checks if the current user has ALL required permissions.

    Usage:
        @router.get("/cases")
        async def list_cases(
            current_user: Usuario = Depends(require_permission("cases.read")),
        ):

        # Multiple permissions (AND logic):
        @router.delete("/cases/{id}")
        async def delete_case(
            current_user: Usuario = Depends(require_permission("cases.delete")),
        ):
    """
    async def _check_permissions(
        current_user: Usuario = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> Usuario:
        user_type = str(current_user.tipo_usuario)

        # Admin sistema always has full access
        if user_type == "admin_sistema":
            return current_user

        # Try to load DB-level permissions
        db_permissions = await _load_user_permissions(current_user, db)

        # Check each required permission
        for perm in permissions:
            if not has_permission(user_type, perm, db_permissions or None):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permiso insuficiente: se requiere '{perm}'. "
                           f"Su rol ({user_type}) no tiene acceso a esta función.",
                )

        return current_user

    return _check_permissions


def require_any_permission(*permissions: str):
    """
    Similar to require_permission but uses OR logic —
    the user needs at least ONE of the listed permissions.
    """
    async def _check_any_permission(
        current_user: Usuario = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> Usuario:
        user_type = str(current_user.tipo_usuario)

        if user_type == "admin_sistema":
            return current_user

        db_permissions = await _load_user_permissions(current_user, db)

        for perm in permissions:
            if has_permission(user_type, perm, db_permissions or None):
                return current_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permiso insuficiente: se requiere al menos uno de {permissions}. "
                   f"Su rol ({user_type}) no tiene acceso.",
        )

    return _check_any_permission
