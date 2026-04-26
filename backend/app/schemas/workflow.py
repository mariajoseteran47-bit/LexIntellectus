"""
LexIntellectus — Schemas: Workflow Stages
CRUD schemas for configurable workflow stages per service type.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime


class WorkflowStageBase(BaseModel):
    """Base schema — fields common to create and update."""
    tipo_servicio: Optional[str] = None        # litigio, escritura, contrato, etc.
    ramo: Optional[str] = None                 # civil, penal, etc. (only for litigation)
    tipo_proceso: Optional[str] = None         # ordinario, ejecutivo, etc.
    codigo: str = Field(min_length=1, max_length=50)
    nombre: str = Field(min_length=1, max_length=200)
    descripcion: Optional[str] = None
    orden: int = Field(ge=0, default=0)
    dias_plazo_legal: Optional[int] = Field(None, ge=0)
    tipo_dias: Optional[str] = "habiles"       # habiles | calendario
    base_legal: Optional[str] = None
    es_final: bool = False
    acciones_requeridas: Optional[List[Any]] = None   # JSON: tasks required at this stage
    plantillas_sugeridas: Optional[List[Any]] = None  # JSON: document templates suggested


class WorkflowStageCreate(WorkflowStageBase):
    """Schema for creating a new workflow stage."""
    pass


class WorkflowStageUpdate(BaseModel):
    """Schema for partial update — all fields optional."""
    tipo_servicio: Optional[str] = None
    ramo: Optional[str] = None
    tipo_proceso: Optional[str] = None
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    orden: Optional[int] = None
    dias_plazo_legal: Optional[int] = None
    tipo_dias: Optional[str] = None
    base_legal: Optional[str] = None
    es_final: Optional[bool] = None
    acciones_requeridas: Optional[List[Any]] = None
    plantillas_sugeridas: Optional[List[Any]] = None


class WorkflowStageReorder(BaseModel):
    """Schema for bulk reorder — list of stage IDs in new order."""
    stage_ids: List[UUID]


class WorkflowStageResponse(WorkflowStageBase):
    """Full response schema with ID and tenant."""
    id: UUID
    tenant_id: UUID
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WorkflowStageListResponse(BaseModel):
    """Paginated list of workflow stages."""
    items: List[WorkflowStageResponse]
    total: int
