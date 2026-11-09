from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict
from uuid import UUID
from datetime import date, datetime


class DeadlineBase(BaseModel):
    expediente_id: UUID
    descripcion: str = Field(min_length=3, max_length=255)
    tipo_plazo: Optional[str] = "procesal"
    fecha_inicio: Optional[date] = None
    fecha_vencimiento: date
    hora_vencimiento: Optional[str] = "23:59:59"
    dias_tipo: Optional[str] = "habiles"
    base_legal: Optional[str] = None
    usuario_responsable_id: Optional[UUID] = None
    status: Optional[str] = "pendiente"
    prioridad: Optional[str] = "normal"
    # Alerts setup
    alerta_72h_enviada: Optional[bool] = False
    alerta_24h_enviada: Optional[bool] = False
    alerta_1h_enviada: Optional[bool] = False
    acciones_sugeridas_ia: Optional[str] = None


class DeadlineCreate(BaseModel):
    expediente_id: UUID
    descripcion: str = Field(min_length=3, max_length=255)
    tipo_plazo: Optional[str] = "procesal"
    fecha_inicio: Optional[date] = None
    fecha_vencimiento: Optional[date] = None
    cantidad_dias: Optional[int] = Field(None, ge=1, le=3650)
    municipio: Optional[str] = "managua"
    incluir_vacaciones_judiciales: Optional[bool] = True
    hora_vencimiento: Optional[str] = "23:59:59"
    dias_tipo: Optional[str] = "habiles"
    base_legal: Optional[str] = None
    usuario_responsable_id: Optional[UUID] = None
    status: Optional[str] = "pendiente"
    prioridad: Optional[str] = "normal"
    alerta_72h_enviada: Optional[bool] = False
    alerta_24h_enviada: Optional[bool] = False
    alerta_1h_enviada: Optional[bool] = False
    acciones_sugeridas_ia: Optional[str] = None


class DeadlineCalculateRequest(BaseModel):
    fecha_inicio: date
    cantidad_dias: int = Field(..., ge=1, le=3650)
    dias_tipo: str = "habiles"
    municipio: str = "managua"
    incluir_vacaciones_judiciales: bool = True


class DeadlineCalculateResponse(BaseModel):
    fecha_inicio: str
    fecha_vencimiento: str
    cantidad_dias: int
    dias_tipo: str
    municipio: str
    incluir_vacaciones_judiciales: bool
    dias_computados: List[str]
    dias_excluidos: List[Dict[str, str]]
    total_dias_calendario_transcurridos: int
    base_legal_aplicada: str


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

    model_config = ConfigDict(from_attributes=True)


class DeadlineListResponse(BaseModel):
    items: list[DeadlineResponse]
    total: int
    page: int
    size: int
