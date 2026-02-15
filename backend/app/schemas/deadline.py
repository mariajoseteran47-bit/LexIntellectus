from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import date, datetime

class DeadlineBase(BaseModel):
    expediente_id: UUID
    descripcion: str = Field(min_length=3, max_length=255)
    tipo_plazo: str = "procesal" # enum
    fecha_inicio: Optional[date] = None
    fecha_vencimiento: date
    hora_vencimiento: Optional[str] = "23:59:59"
    dias_tipo: str = "habiles"
    base_legal: Optional[str] = None
    usuario_responsable_id: Optional[UUID] = None
    status: str = "pendiente"
    prioridad: str = "normal"
    # Alerts setup
    alerta_72h_enviada: bool = False
    alerta_24h_enviada: bool = False
    alerta_1h_enviada: bool = False
    acciones_sugeridas_ia: Optional[str] = None

class DeadlineCreate(DeadlineBase):
    pass

class DeadlineUpdate(BaseModel):
    descripcion: Optional[str] = None
    tipo_plazo: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_vencimiento: Optional[date] = None
    hora_vencimiento: Optional[str] = None
    dias_tipo: Optional[str] = None
    base_legal: Optional[str] = None
    usuario_responsable_id: Optional[UUID] = None
    status: Optional[str] = None
    prioridad: Optional[str] = None
    acciones_sugeridas_ia: Optional[str] = None

class DeadlineResponse(DeadlineBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    # We might want to include expediente summary or responsible user name
    # related fields can be added if needed via DB join
    
    class Config:
        from_attributes = True

class DeadlineListResponse(BaseModel):
    items: list[DeadlineResponse]
    total: int
    page: int
    size: int
