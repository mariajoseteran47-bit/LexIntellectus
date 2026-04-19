"""
LexIntellectus - User Schemas
Request and response models for user management.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    nombre: str = Field(min_length=2, max_length=100)
    apellido: str = Field(min_length=2, max_length=100)
    telefono: Optional[str] = None
    tipo_usuario: str
    tipo_vinculo: Optional[str] = None
    sede_id: Optional[UUID] = None


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    telefono: Optional[str] = None
    foto_url: Optional[str] = None
    tipo_usuario: Optional[str] = None
    tipo_vinculo: Optional[str] = None
    sede_id: Optional[UUID] = None
    status: Optional[str] = None


class UserResponse(BaseModel):
    id: UUID
    email: str
    nombre: str
    apellido: str
    telefono: Optional[str] = None
    foto_url: Optional[str] = None
    tipo_usuario: str
    tipo_vinculo: Optional[str] = None
    tenant_id: UUID
    sede_id: Optional[UUID] = None
    status: str
    mfa_enabled: Optional[bool] = False
    last_login: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    items: List[UserResponse]
    total: int
    page: int
    size: int
