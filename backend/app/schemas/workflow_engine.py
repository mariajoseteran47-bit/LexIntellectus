"""
LexIntellectus — Schemas: Tasks, Templates, and Conflict Check
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime


# ═══════════════════════════════════════════════════════════════
# TAREAS
# ═══════════════════════════════════════════════════════════════

class TaskCreate(BaseModel):
    titulo: str = Field(min_length=1, max_length=300)
    descripcion: Optional[str] = None
    categoria: str = "administrativa"
    obligatoria: bool = False
    asignado_a_id: Optional[UUID] = None
    fecha_limite: Optional[datetime] = None
    etapa_codigo: Optional[str] = None
    orden: int = 0


class TaskUpdate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    estado: Optional[str] = None
    asignado_a_id: Optional[UUID] = None
    fecha_limite: Optional[datetime] = None


class TaskResponse(BaseModel):
    id: UUID
    expediente_id: UUID
    titulo: str
    descripcion: Optional[str] = None
    estado: str
    categoria: str
    obligatoria: bool
    asignado_a_id: Optional[UUID] = None
    asignado_nombre: Optional[str] = None
    fecha_limite: Optional[datetime] = None
    fecha_completada: Optional[datetime] = None
    etapa_codigo: Optional[str] = None
    orden: int
    created_at: datetime

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    items: List[TaskResponse]
    total: int
    completadas: int
    pendientes: int


# ═══════════════════════════════════════════════════════════════
# CHECKLIST DOCUMENTOS
# ═══════════════════════════════════════════════════════════════

class ChecklistItemResponse(BaseModel):
    id: UUID
    nombre_documento: str
    descripcion: Optional[str] = None
    obligatorio: bool
    etapa_codigo: Optional[str] = None
    recibido: bool
    documento_id: Optional[UUID] = None
    fecha_recibido: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChecklistMarkReceived(BaseModel):
    documento_id: Optional[UUID] = None


# ═══════════════════════════════════════════════════════════════
# PLANTILLAS WORKFLOW
# ═══════════════════════════════════════════════════════════════

class TemplateResponse(BaseModel):
    id: UUID
    tipo_servicio: str
    ramo: Optional[str] = None
    nombre: str
    tareas: List[Any]
    docs_requeridos: List[Any]
    reglas_transicion: List[Any]
    activo: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════
# CONFLICT CHECK
# ═══════════════════════════════════════════════════════════════

class ConflictCheckRequest(BaseModel):
    nombre: str = Field(min_length=2)
    documento: Optional[str] = None
    expediente_id: Optional[UUID] = None


class ConflictMatch(BaseModel):
    tabla: str
    id: str
    nombre: str
    caso_id: Optional[str] = None
    caso_titulo: Optional[str] = None
    similitud: float


class ConflictCheckResponse(BaseModel):
    id: Optional[UUID] = None
    tiene_conflicto: bool
    nombre_buscado: str
    coincidencias: List[ConflictMatch]
    total_coincidencias: int


class TransitionCheckResponse(BaseModel):
    puede_avanzar: bool
    etapa_actual: Optional[str] = None
    etapa_destino: Optional[str] = None
    tareas_pendientes: List[str]
    docs_faltantes: List[str]
    motivo_bloqueo: Optional[str] = None
