"""
LexIntellectus — Schemas: Discussion Threads + Document Approvals
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime


# ═══════════════════════════════════════════════════════════════
# HILOS DE DISCUSIÓN
# ═══════════════════════════════════════════════════════════════

class ThreadCreate(BaseModel):
    expediente_id: UUID
    titulo: str = Field(min_length=1, max_length=300)
    tipo_canal: str = "interno"  # interno | cliente


class ThreadUpdate(BaseModel):
    titulo: Optional[str] = None
    cerrado: Optional[bool] = None
    fijado: Optional[bool] = None


class ThreadResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    expediente_id: UUID
    titulo: str
    tipo_canal: str
    cerrado: bool
    fijado: bool
    creado_por_id: UUID
    creado_por_nombre: Optional[str] = None
    total_mensajes: int
    ultimo_mensaje_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ThreadListResponse(BaseModel):
    items: List[ThreadResponse]
    total: int


# ═══════════════════════════════════════════════════════════════
# MENSAJES
# ═══════════════════════════════════════════════════════════════

class MessageCreate(BaseModel):
    contenido: str = Field(min_length=1)
    adjuntos: Optional[List[str]] = []
    menciones: Optional[List[str]] = []
    es_resolucion: bool = False


class MessageUpdate(BaseModel):
    contenido: Optional[str] = None


class MessageResponse(BaseModel):
    id: UUID
    hilo_id: UUID
    autor_id: UUID
    autor_nombre: Optional[str] = None
    autor_foto: Optional[str] = None
    contenido: str
    adjuntos: Optional[List[Any]] = []
    menciones: Optional[List[Any]] = []
    es_resolucion: bool
    editado: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════
# APROBACIONES DE DOCUMENTOS
# ═══════════════════════════════════════════════════════════════

class ApprovalRequest(BaseModel):
    documento_id: UUID
    aprobador_id: UUID
    expediente_id: Optional[UUID] = None
    motivo_solicitud: Optional[str] = None
    fecha_limite: Optional[datetime] = None


class ApprovalAction(BaseModel):
    estado: str  # aprobado | rechazado | revision
    comentarios_aprobador: Optional[str] = None


class ApprovalResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    documento_id: UUID
    expediente_id: Optional[UUID] = None
    solicitante_id: UUID
    solicitante_nombre: Optional[str] = None
    aprobador_id: UUID
    aprobador_nombre: Optional[str] = None
    estado: str
    motivo_solicitud: Optional[str] = None
    comentarios_aprobador: Optional[str] = None
    version_documento: int
    fecha_solicitud: datetime
    fecha_respuesta: Optional[datetime] = None
    fecha_limite: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ApprovalListResponse(BaseModel):
    items: List[ApprovalResponse]
    total: int
