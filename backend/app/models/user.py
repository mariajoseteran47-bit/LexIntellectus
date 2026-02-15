"""
LexIntellectus - User & RBAC Models
Users, Roles, Permissions, Sessions.
Based on data_model.md v2.0, Section 1.4
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, DateTime,
    ForeignKey, Enum, PrimaryKeyConstraint, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Usuario(Base):
    """System user — lawyers, notaries, admins, clients, etc."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    sede_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    telefono = Column(String(20))
    foto_url = Column(String(500))
    tipo_usuario = Column(
        Enum(
            "admin_sistema", "admin_despacho", "abogado", "notario",
            "secretaria", "contador", "gestor", "cliente",
            name="user_type",
        ),
        nullable=False,
    )
    tipo_vinculo = Column(
        Enum(
            "socio", "asociado", "empleado", "externo", "cliente",
            name="user_link_type",
        ),
        nullable=True,
    )
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(100))
    last_login = Column(DateTime)
    status = Column(
        Enum("activo", "inactivo", "bloqueado", name="user_status"),
        default="activo",
        nullable=False,
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    despacho = relationship("Despacho", back_populates="usuarios")
    sede = relationship("Sede", back_populates="usuarios")
    roles_asignados = relationship("UsuarioRol", back_populates="usuario", cascade="all, delete-orphan")
    sesiones = relationship("SesionUsuario", back_populates="usuario", cascade="all, delete-orphan")


class Rol(Base):
    """Role definition — system or tenant-specific."""
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    es_sistema = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    permisos_asignados = relationship("RolPermiso", back_populates="rol", cascade="all, delete-orphan")
    usuarios_asignados = relationship("UsuarioRol", back_populates="rol")


class Permiso(Base):
    """Granular permission definition."""
    __tablename__ = "permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo = Column(String(100), unique=True, nullable=False)
    modulo = Column(String(50), nullable=False)
    descripcion = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    roles_asignados = relationship("RolPermiso", back_populates="permiso")


class RolPermiso(Base):
    """Many-to-many: Role ↔ Permission."""
    __tablename__ = "role_permissions"

    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id"), primary_key=True)

    rol = relationship("Rol", back_populates="permisos_asignados")
    permiso = relationship("Permiso", back_populates="roles_asignados")


class UsuarioRol(Base):
    """Many-to-many: User ↔ Role, scoped by branch."""
    __tablename__ = "user_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    sede_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "role_id", "sede_id", name="uq_user_role_sede"),
    )

    usuario = relationship("Usuario", back_populates="roles_asignados")
    rol = relationship("Rol", back_populates="usuarios_asignados")


class SesionUsuario(Base):
    """Active user session tracking."""
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    token_hash = Column(String(255), nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    usuario = relationship("Usuario", back_populates="sesiones")
