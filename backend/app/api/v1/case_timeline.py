"""
LexIntellectus — API de Actuaciones Procesales y Notas del Caso
El timeline vivo del expediente: cada escrito, providencia, audiencia, recurso.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.rbac import require_permission
from app.models.user import Usuario
from app.models.case import Expediente
from app.models.case_extended import ActuacionProcesal, NotaCaso, TeoriaCaso

router = APIRouter(prefix="/cases", tags=["Case Timeline"])


# === SCHEMAS ===

class ActuacionCreate(BaseModel):
    tipo: str
    titulo: str = Field(min_length=3, max_length=300)
    descripcion: Optional[str] = None
    fecha_evento: datetime
    etapa_procesal_id: Optional[UUID] = None
    resultado: Optional[str] = None
    base_legal: Optional[str] = None
    documento_ids: Optional[list] = []
    asignado_a_id: Optional[UUID] = None
    estado: str = "completado"

class ActuacionResponse(BaseModel):
    id: UUID
    expediente_id: UUID
    tipo: str
    titulo: str
    descripcion: Optional[str]
    fecha_evento: datetime
    resultado: Optional[str]
    base_legal: Optional[str]
    documento_ids: Optional[list]
    estado: str
    registrado_por_id: Optional[UUID]
    asignado_a_id: Optional[UUID]
    analisis_ia: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

class NotaCreate(BaseModel):
    tipo: str = "observacion"
    contenido: str = Field(min_length=1)
    es_privada: bool = False
    prioridad: str = "normal"

class NotaResponse(BaseModel):
    id: UUID
    expediente_id: UUID
    tipo: str
    contenido: str
    es_privada: bool
    prioridad: str
    autor_id: UUID
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class TeoriaCreate(BaseModel):
    hechos_relevantes: Optional[list] = []
    pretensiones: Optional[list] = []
    normas_aplicables: Optional[list] = []
    excepciones_previstas: Optional[list] = []
    pruebas_plan: Optional[list] = []
    fortalezas: Optional[str] = None
    debilidades: Optional[str] = None
    riesgos: Optional[str] = None
    estrategia_general: Optional[str] = None
    contraargumentos: Optional[list] = []

class TeoriaResponse(BaseModel):
    id: UUID
    expediente_id: UUID
    hechos_relevantes: Optional[list]
    pretensiones: Optional[list]
    normas_aplicables: Optional[list]
    excepciones_previstas: Optional[list]
    pruebas_plan: Optional[list]
    fortalezas: Optional[str]
    debilidades: Optional[str]
    riesgos: Optional[str]
    estrategia_general: Optional[str]
    contraargumentos: Optional[list]
    generada_por_ia: bool
    analisis_ia: Optional[str]
    version: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True


# === ACTUACIONES (TIMELINE) ===

@router.get("/{case_id}/actuaciones")
async def list_actuaciones(
    case_id: UUID,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    tipo: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("cases.read")),
):
    """Listar todas las actuaciones de un expediente (timeline)."""
    tenant_id = current_user.tenant_id
    
    # Verificar acceso al caso
    case = await db.scalar(
        select(Expediente).where(Expediente.id == case_id, Expediente.tenant_id == tenant_id)
    )
    if not case:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    
    query = select(ActuacionProcesal).where(ActuacionProcesal.expediente_id == case_id)
    if tipo:
        query = query.where(ActuacionProcesal.tipo == tipo)
    
    # Count
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    
    # Fetch (más recientes primero)
    skip = (page - 1) * size
    query = query.order_by(desc(ActuacionProcesal.fecha_evento)).offset(skip).limit(size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return {
        "items": [
            {
                "id": str(a.id),
                "tipo": a.tipo,
                "titulo": a.titulo,
                "descripcion": a.descripcion,
                "fecha_evento": a.fecha_evento.isoformat() if a.fecha_evento else None,
                "resultado": a.resultado,
                "base_legal": a.base_legal,
                "documento_ids": a.documento_ids or [],
                "estado": a.estado,
                "registrado_por_id": str(a.registrado_por_id) if a.registrado_por_id else None,
                "asignado_a_id": str(a.asignado_a_id) if a.asignado_a_id else None,
                "analisis_ia": a.analisis_ia,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in items
        ],
        "total": total,
        "page": page,
        "size": size,
    }


@router.post("/{case_id}/actuaciones", status_code=201)
async def create_actuacion(
    case_id: UUID,
    data: ActuacionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("cases.update")),
):
    """Registrar una nueva actuación procesal en el timeline."""
    tenant_id = current_user.tenant_id
    
    case = await db.scalar(
        select(Expediente).where(Expediente.id == case_id, Expediente.tenant_id == tenant_id)
    )
    if not case:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    
    actuacion = ActuacionProcesal(
        expediente_id=case_id,
        tipo=data.tipo,
        titulo=data.titulo,
        descripcion=data.descripcion,
        fecha_evento=data.fecha_evento,
        etapa_procesal_id=data.etapa_procesal_id,
        resultado=data.resultado,
        base_legal=data.base_legal,
        documento_ids=data.documento_ids or [],
        asignado_a_id=data.asignado_a_id,
        estado=data.estado,
        registrado_por_id=current_user.id,
    )
    
    db.add(actuacion)
    await db.commit()
    await db.refresh(actuacion)
    
    return {
        "id": str(actuacion.id),
        "tipo": actuacion.tipo,
        "titulo": actuacion.titulo,
        "fecha_evento": actuacion.fecha_evento.isoformat(),
        "message": f"Actuación '{actuacion.titulo}' registrada exitosamente",
    }


# === NOTAS INTERNAS ===

@router.get("/{case_id}/notas")
async def list_notas(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("cases.read")),
):
    """Listar notas internas del caso."""
    tenant_id = current_user.tenant_id
    
    case = await db.scalar(
        select(Expediente).where(Expediente.id == case_id, Expediente.tenant_id == tenant_id)
    )
    if not case:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    
    query = select(NotaCaso).where(NotaCaso.expediente_id == case_id)
    # Filtrar notas privadas (solo el autor puede verlas)
    # OR logic: not private, OR is the author
    from sqlalchemy import or_
    query = query.where(
        or_(NotaCaso.es_privada == False, NotaCaso.autor_id == current_user.id)
    )
    query = query.order_by(desc(NotaCaso.created_at))
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    return [
        {
            "id": str(n.id),
            "tipo": n.tipo,
            "contenido": n.contenido,
            "es_privada": n.es_privada,
            "prioridad": n.prioridad,
            "autor_id": str(n.autor_id),
            "created_at": n.created_at.isoformat() if n.created_at else None,
            "updated_at": n.updated_at.isoformat() if n.updated_at else None,
        }
        for n in items
    ]


@router.post("/{case_id}/notas", status_code=201)
async def create_nota(
    case_id: UUID,
    data: NotaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("cases.update")),
):
    """Crear una nota interna en el caso."""
    tenant_id = current_user.tenant_id
    
    case = await db.scalar(
        select(Expediente).where(Expediente.id == case_id, Expediente.tenant_id == tenant_id)
    )
    if not case:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    
    nota = NotaCaso(
        expediente_id=case_id,
        tipo=data.tipo,
        contenido=data.contenido,
        es_privada=data.es_privada,
        prioridad=data.prioridad,
        autor_id=current_user.id,
    )
    
    db.add(nota)
    await db.commit()
    await db.refresh(nota)
    
    return {
        "id": str(nota.id),
        "tipo": nota.tipo,
        "message": "Nota creada exitosamente",
    }


# === TEORÍA DEL CASO ===

@router.get("/{case_id}/teoria")
async def get_teoria(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("cases.read")),
):
    """Obtener la teoría del caso más reciente."""
    tenant_id = current_user.tenant_id
    
    case = await db.scalar(
        select(Expediente).where(Expediente.id == case_id, Expediente.tenant_id == tenant_id)
    )
    if not case:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    
    teoria = await db.scalar(
        select(TeoriaCaso)
        .where(TeoriaCaso.expediente_id == case_id)
        .order_by(desc(TeoriaCaso.version))
    )
    
    if not teoria:
        return None
    
    return {
        "id": str(teoria.id),
        "hechos_relevantes": teoria.hechos_relevantes or [],
        "pretensiones": teoria.pretensiones or [],
        "normas_aplicables": teoria.normas_aplicables or [],
        "excepciones_previstas": teoria.excepciones_previstas or [],
        "pruebas_plan": teoria.pruebas_plan or [],
        "fortalezas": teoria.fortalezas,
        "debilidades": teoria.debilidades,
        "riesgos": teoria.riesgos,
        "estrategia_general": teoria.estrategia_general,
        "contraargumentos": teoria.contraargumentos or [],
        "generada_por_ia": teoria.generada_por_ia,
        "analisis_ia": teoria.analisis_ia,
        "version": teoria.version,
        "created_at": teoria.created_at.isoformat() if teoria.created_at else None,
        "updated_at": teoria.updated_at.isoformat() if teoria.updated_at else None,
    }


@router.post("/{case_id}/teoria", status_code=201)
async def save_teoria(
    case_id: UUID,
    data: TeoriaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("cases.update")),
):
    """Guardar o actualizar la teoría del caso (crea nueva versión)."""
    tenant_id = current_user.tenant_id
    
    case = await db.scalar(
        select(Expediente).where(Expediente.id == case_id, Expediente.tenant_id == tenant_id)
    )
    if not case:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    
    # Obtener versión actual
    latest = await db.scalar(
        select(TeoriaCaso.version)
        .where(TeoriaCaso.expediente_id == case_id)
        .order_by(desc(TeoriaCaso.version))
    )
    next_version = (latest or 0) + 1
    
    teoria = TeoriaCaso(
        expediente_id=case_id,
        hechos_relevantes=data.hechos_relevantes,
        pretensiones=data.pretensiones,
        normas_aplicables=data.normas_aplicables,
        excepciones_previstas=data.excepciones_previstas,
        pruebas_plan=data.pruebas_plan,
        fortalezas=data.fortalezas,
        debilidades=data.debilidades,
        riesgos=data.riesgos,
        estrategia_general=data.estrategia_general,
        contraargumentos=data.contraargumentos,
        version=next_version,
        autor_id=current_user.id,
    )
    
    db.add(teoria)
    await db.commit()
    await db.refresh(teoria)
    
    return {
        "id": str(teoria.id),
        "version": teoria.version,
        "message": f"Teoría del caso v{teoria.version} guardada exitosamente",
    }
