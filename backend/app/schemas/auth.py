"""
LexIntellectus - Auth Schemas
Request and response models for authentication endpoints.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


# === Request Schemas ===

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    nombre: str = Field(min_length=2, max_length=100)
    apellido: str = Field(min_length=2, max_length=100)
    telefono: Optional[str] = None
    tenant_nombre: str = Field(min_length=2, max_length=255, description="Nombre del despacho")
    tenant_ruc: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# === Response Schemas ===

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserInfoResponse(BaseModel):
    id: UUID
    email: str
    nombre: str
    apellido: str
    tipo_usuario: str
    tenant_id: UUID
    tenant_nombre: Optional[str] = None
    sede_id: Optional[UUID] = None
    foto_url: Optional[str] = None
    status: str
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    token: TokenResponse
    user: UserInfoResponse
