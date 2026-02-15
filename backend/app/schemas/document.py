from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class DocumentBase(BaseModel):
    expediente_id: UUID
    descripcion: Optional[str] = None
    categoria: str = "general"

class DocumentCreate(DocumentBase):
    # File is uploaded via Form data, so this model is for metadata validation if needed manually
    pass

class DocumentResponse(DocumentBase):
    id: UUID
    nombre_archivo: str
    tipo_archivo: Optional[str]
    tamano_bytes: Optional[int]
    created_at: datetime
    subido_por_id: Optional[UUID]
    download_url: Optional[str] = None # Generated dynamically

    class Config:
        from_attributes = True

class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
