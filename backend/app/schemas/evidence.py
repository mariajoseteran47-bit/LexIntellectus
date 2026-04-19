"""
LexIntellectus - Evidence Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime, date


class EvidenceDocumentBase(BaseModel):
    documento_id: UUID
    tipo_medio: str = "pdf"
    es_original: bool = False
    descripcion: Optional[str] = None
    orden: int = 0


class EvidenceDocumentCreate(EvidenceDocumentBase):
    pass


class EvidenceDocumentResponse(EvidenceDocumentBase):
    id: UUID
    prueba_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class EvidenceBase(BaseModel):
    tipo_prueba: str
    titulo: str
    descripcion: Optional[str] = None
    valoracion: str = "media"
    pertinencia: Optional[str] = None
    hecho_que_prueba: Optional[str] = None
    teoria_caso_id: Optional[UUID] = None
    estado_procesal: str = "propuesta"
    fecha_proposicion: Optional[date] = None
    fecha_admision: Optional[date] = None
    fecha_evacuacion: Optional[date] = None
    datos_especificos: Optional[Any] = None
    notas_estrategia: Optional[str] = None
    contraargumento_previsto: Optional[str] = None
    base_legal: Optional[str] = None


class EvidenceCreate(EvidenceBase):
    expediente_id: UUID


class EvidenceUpdate(BaseModel):
    tipo_prueba: Optional[str] = None
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    valoracion: Optional[str] = None
    pertinencia: Optional[str] = None
    hecho_que_prueba: Optional[str] = None
    teoria_caso_id: Optional[UUID] = None
    estado_procesal: Optional[str] = None
    fecha_proposicion: Optional[date] = None
    fecha_admision: Optional[date] = None
    fecha_evacuacion: Optional[date] = None
    datos_especificos: Optional[Any] = None
    notas_estrategia: Optional[str] = None
    contraargumento_previsto: Optional[str] = None
    base_legal: Optional[str] = None
    cadena_custodia: Optional[List[Any]] = None


class EvidenceResponse(EvidenceBase):
    id: UUID
    expediente_id: UUID
    tenant_id: UUID
    cadena_custodia: Optional[List[Any]] = []
    registrado_por_id: Optional[UUID] = None
    adjuntos: List[EvidenceDocumentResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EvidenceListResponse(BaseModel):
    items: List[EvidenceResponse]
    total: int
