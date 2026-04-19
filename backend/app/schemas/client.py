"""
LexIntellectus - Client Profile & Representative Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime, date


# === RepresentanteLegal ===

class RepresentativeBase(BaseModel):
    nombre_completo: str
    cedula_identidad: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    cargo: Optional[str] = None
    tipo_poder: str  # generalisimo, general_administracion, especial, judicial
    numero_escritura: Optional[str] = None
    fecha_otorgamiento: date
    fecha_vencimiento: Optional[date] = None
    notario_autorizante: Optional[str] = None
    libro_protocolo: Optional[str] = None
    folio_protocolo: Optional[str] = None
    tomo_protocolo: Optional[str] = None
    alcance_facultades: Optional[str] = None
    restricciones: Optional[str] = None
    vigente: bool = True


class RepresentativeCreate(RepresentativeBase):
    pass


class RepresentativeUpdate(BaseModel):
    nombre_completo: Optional[str] = None
    cedula_identidad: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    cargo: Optional[str] = None
    tipo_poder: Optional[str] = None
    fecha_vencimiento: Optional[date] = None
    vigente: Optional[bool] = None
    motivo_revocacion: Optional[str] = None


class RepresentativeResponse(RepresentativeBase):
    id: UUID
    client_profile_id: UUID
    motivo_revocacion: Optional[str] = None
    documento_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


# === PerfilCliente ===

class ClientProfileBase(BaseModel):
    tipo_persona: Optional[str] = "natural"
    cedula_identidad: Optional[str] = None
    ruc: Optional[str] = None
    nacionalidad: Optional[str] = "Nicaragüense"
    razon_social: Optional[str] = None
    nombre_comercial: Optional[str] = None
    tipo_sociedad: Optional[str] = None
    fecha_constitucion: Optional[date] = None
    numero_escritura_constitucion: Optional[str] = None
    registro_mercantil: Optional[str] = None
    actividad_economica: Optional[str] = None
    direccion_domicilio: Optional[str] = None
    ciudad: Optional[str] = None
    departamento: Optional[str] = None
    pais: Optional[str] = "Nicaragua"
    fecha_primera_consulta: Optional[date] = None
    referido_por: Optional[str] = None
    calificacion_riesgo: Optional[str] = "bajo"
    segmento: Optional[str] = "individual"
    notas_internas: Optional[str] = None


class ClientProfileCreate(ClientProfileBase):
    user_id: UUID


class ClientProfileUpdate(BaseModel):
    tipo_persona: Optional[str] = None
    cedula_identidad: Optional[str] = None
    ruc: Optional[str] = None
    razon_social: Optional[str] = None
    nombre_comercial: Optional[str] = None
    tipo_sociedad: Optional[str] = None
    fecha_constitucion: Optional[date] = None
    numero_escritura_constitucion: Optional[str] = None
    registro_mercantil: Optional[str] = None
    actividad_economica: Optional[str] = None
    direccion_domicilio: Optional[str] = None
    ciudad: Optional[str] = None
    departamento: Optional[str] = None
    fecha_primera_consulta: Optional[date] = None
    referido_por: Optional[str] = None
    calificacion_riesgo: Optional[str] = None
    segmento: Optional[str] = None
    notas_internas: Optional[str] = None
    kyc_verificado: Optional[bool] = None


# === MiembroJuntaDirectiva ===

class BoardMemberBase(BaseModel):
    nombre_completo: str
    cedula_identidad: Optional[str] = None
    cargo: str  # presidente, vicepresidente, secretario, etc.
    cargo_personalizado: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    fecha_nombramiento: Optional[date] = None
    fecha_vencimiento: Optional[date] = None
    numero_acta_nombramiento: Optional[str] = None
    inscrita_registro_mercantil: bool = False
    activo: bool = True


class BoardMemberCreate(BoardMemberBase):
    pass


class BoardMemberResponse(BoardMemberBase):
    id: UUID
    client_profile_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# === Accionista ===

class ShareholderBase(BaseModel):
    tipo_accionista: Optional[str] = "natural"
    nombre_completo: str
    cedula_ruc: Optional[str] = None
    nacionalidad: Optional[str] = "Nicaragüense"
    numero_acciones: Optional[int] = None
    porcentaje_participacion: Optional[float] = None
    tipo_acciones: Optional[str] = None
    valor_nominal: Optional[float] = None
    es_beneficiario_final: bool = False
    pep: bool = False
    fecha_adquisicion: Optional[date] = None
    activo: bool = True


class ShareholderCreate(ShareholderBase):
    pass


class ShareholderResponse(ShareholderBase):
    id: UUID
    client_profile_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class ClientProfileResponse(ClientProfileBase):
    id: UUID
    user_id: UUID
    tenant_id: UUID
    kyc_verificado: bool = False
    pep: bool = False
    representantes: List[RepresentativeResponse] = []
    junta_directiva: List[BoardMemberResponse] = []
    accionistas: List[ShareholderResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True


class ClientProfileListResponse(BaseModel):
    items: List[ClientProfileResponse]
    total: int
    page: int
    size: int

