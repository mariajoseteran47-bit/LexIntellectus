"""
LexIntellectus — API: Discussion Threads + Document Approvals
Sprint 3: Full CRUD for collaboration features.
"""

import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_db
from app.core.rbac import require_permission
from app.models.user import Usuario
from app.models.collaboration import HiloDiscusion, MensajeHilo, AprobacionDocumento
from app.schemas.collaboration import (
    ThreadCreate, ThreadUpdate, ThreadResponse, ThreadListResponse,
    MessageCreate, MessageUpdate, MessageResponse,
    ApprovalRequest, ApprovalAction, ApprovalResponse, ApprovalListResponse
)

router = APIRouter(tags=["Collaboration"])


# ═══════════════════════════════════════════════════════════════
#  HILOS DE DISCUSIÓN
# ═══════════════════════════════════════════════════════════════

@router.get("/cases/{case_id}/threads", response_model=ThreadListResponse)
async def list_threads(
    case_id: UUID,
    tipo_canal: Optional[str] = None,
    cerrado: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("cases.read"))
):
    """Listar hilos de discusión de un expediente."""
    tenant_id = current_user.tenant_id
    query = select(HiloDiscusion).where(
        HiloDiscusion.expediente_id == case_id,
        HiloDiscusion.tenant_id == tenant_id
    )
    if tipo_canal:
        query = query.where(HiloDiscusion.tipo_canal == tipo_canal)
    if cerrado is not None:
        query = query.where(HiloDiscusion.cerrado == cerrado)

    query = query.order_by(HiloDiscusion.fijado.desc(), HiloDiscusion.ultimo_mensaje_at.desc().nullslast())

    result = await db.execute(query)
    threads = result.scalars().all()

    # Enrich with author names
    items = []
    for t in threads:
        resp = ThreadResponse.model_validate(t)
        if t.creado_por:
            resp.creado_por_nombre = t.creado_por.nombre_completo or t.creado_por.email
        items.append(resp)

    return ThreadListResponse(items=items, total=len(items))


@router.post("/cases/{case_id}/threads", response_model=ThreadResponse, status_code=201)
async def create_thread(
    case_id: UUID,
    data: ThreadCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("cases.read"))
):
    """Crear un nuevo hilo de discusión."""
    thread = HiloDiscusion(
        id=uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        expediente_id=case_id,
        titulo=data.titulo,
        tipo_canal=data.tipo_canal,
        creado_por_id=current_user.id,
    )
    db.add(thread)
    await db.flush()

    resp = ThreadResponse.model_validate(thread)
    resp.creado_por_nombre = current_user.nombre_completo or current_user.email
    return resp


@router.patch("/threads/{thread_id}", response_model=ThreadResponse)
async def update_thread(
    thread_id: UUID,
    data: ThreadUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("cases.read"))
):
    """Actualizar un hilo (cerrar, fijar, renombrar)."""
    result = await db.execute(
        select(HiloDiscusion).where(
            HiloDiscusion.id == thread_id,
            HiloDiscusion.tenant_id == current_user.tenant_id
        )
    )
    thread = result.scalar_one_or_none()
    if not thread:
        raise HTTPException(status_code=404, detail="Hilo no encontrado")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(thread, field, value)

    await db.flush()
    return ThreadResponse.model_validate(thread)


# ═══════════════════════════════════════════════════════════════
#  MENSAJES DE HILO
# ═══════════════════════════════════════════════════════════════

@router.get("/threads/{thread_id}/messages", response_model=List[MessageResponse])
async def list_messages(
    thread_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("cases.read"))
):
    """Listar mensajes de un hilo."""
    # Verify thread exists and belongs to tenant
    thread_check = await db.execute(
        select(HiloDiscusion).where(
            HiloDiscusion.id == thread_id,
            HiloDiscusion.tenant_id == current_user.tenant_id
        )
    )
    if not thread_check.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Hilo no encontrado")

    result = await db.execute(
        select(MensajeHilo).where(MensajeHilo.hilo_id == thread_id)
        .order_by(MensajeHilo.created_at.asc())
    )
    messages = result.scalars().all()

    items = []
    for m in messages:
        resp = MessageResponse.model_validate(m)
        if m.autor:
            resp.autor_nombre = m.autor.nombre_completo or m.autor.email
        items.append(resp)

    return items


@router.post("/threads/{thread_id}/messages", response_model=MessageResponse, status_code=201)
async def create_message(
    thread_id: UUID,
    data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("cases.read"))
):
    """Enviar un mensaje a un hilo."""
    # Verify thread
    result = await db.execute(
        select(HiloDiscusion).where(
            HiloDiscusion.id == thread_id,
            HiloDiscusion.tenant_id == current_user.tenant_id
        )
    )
    thread = result.scalar_one_or_none()
    if not thread:
        raise HTTPException(status_code=404, detail="Hilo no encontrado")
    if thread.cerrado:
        raise HTTPException(status_code=400, detail="Este hilo está cerrado")

    message = MensajeHilo(
        id=uuid.uuid4(),
        hilo_id=thread_id,
        autor_id=current_user.id,
        contenido=data.contenido,
        adjuntos=data.adjuntos or [],
        menciones=data.menciones or [],
        es_resolucion=data.es_resolucion,
    )
    db.add(message)

    # Update thread counters
    thread.total_mensajes = (thread.total_mensajes or 0) + 1
    thread.ultimo_mensaje_at = datetime.utcnow()

    # If resolution, close thread
    if data.es_resolucion:
        thread.cerrado = True

    await db.flush()

    resp = MessageResponse.model_validate(message)
    resp.autor_nombre = current_user.nombre_completo or current_user.email
    return resp


@router.patch("/messages/{message_id}", response_model=MessageResponse)
async def edit_message(
    message_id: UUID,
    data: MessageUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("cases.read"))
):
    """Editar un mensaje propio."""
    result = await db.execute(
        select(MensajeHilo).where(MensajeHilo.id == message_id)
    )
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")
    if str(message.autor_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Solo puede editar sus propios mensajes")

    if data.contenido is not None:
        message.contenido = data.contenido
        message.editado = True

    await db.flush()
    return MessageResponse.model_validate(message)


@router.delete("/messages/{message_id}", status_code=204)
async def delete_message(
    message_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("cases.read"))
):
    """Eliminar un mensaje propio."""
    result = await db.execute(
        select(MensajeHilo).where(MensajeHilo.id == message_id)
    )
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")
    if str(message.autor_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Solo puede eliminar sus propios mensajes")

    # Update thread counter
    thread_result = await db.execute(
        select(HiloDiscusion).where(HiloDiscusion.id == message.hilo_id)
    )
    thread = thread_result.scalar_one_or_none()
    if thread:
        thread.total_mensajes = max(0, (thread.total_mensajes or 1) - 1)

    await db.delete(message)
    await db.flush()


# ═══════════════════════════════════════════════════════════════
#  APROBACIONES DE DOCUMENTOS
# ═══════════════════════════════════════════════════════════════

@router.get("/approvals", response_model=ApprovalListResponse)
async def list_approvals(
    estado: Optional[str] = None,
    rol: str = Query("todos", description="todos | solicitante | aprobador"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("documents.read"))
):
    """Listar aprobaciones pendientes o históricas.
    
    - rol=aprobador: muestra aprobaciones donde el usuario es aprobador
    - rol=solicitante: muestra las que el usuario solicitó
    - rol=todos: muestra ambas
    """
    tenant_id = current_user.tenant_id
    query = select(AprobacionDocumento).where(
        AprobacionDocumento.tenant_id == tenant_id
    )

    if estado:
        query = query.where(AprobacionDocumento.estado == estado)

    if rol == "aprobador":
        query = query.where(AprobacionDocumento.aprobador_id == current_user.id)
    elif rol == "solicitante":
        query = query.where(AprobacionDocumento.solicitante_id == current_user.id)

    query = query.order_by(AprobacionDocumento.fecha_solicitud.desc())
    result = await db.execute(query)
    approvals = result.scalars().all()

    items = []
    for a in approvals:
        resp = ApprovalResponse.model_validate(a)
        if a.solicitante:
            resp.solicitante_nombre = a.solicitante.nombre_completo or a.solicitante.email
        if a.aprobador:
            resp.aprobador_nombre = a.aprobador.nombre_completo or a.aprobador.email
        items.append(resp)

    return ApprovalListResponse(items=items, total=len(items))


@router.post("/approvals", response_model=ApprovalResponse, status_code=201)
async def request_approval(
    data: ApprovalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("documents.read"))
):
    """Solicitar aprobación para un documento."""
    # Can't approve your own documents
    if str(data.aprobador_id) == str(current_user.id):
        raise HTTPException(status_code=400, detail="No puede solicitar aprobación a sí mismo")

    approval = AprobacionDocumento(
        id=uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        documento_id=data.documento_id,
        expediente_id=data.expediente_id,
        solicitante_id=current_user.id,
        aprobador_id=data.aprobador_id,
        motivo_solicitud=data.motivo_solicitud,
        fecha_limite=data.fecha_limite,
    )
    db.add(approval)
    await db.flush()

    resp = ApprovalResponse.model_validate(approval)
    resp.solicitante_nombre = current_user.nombre_completo or current_user.email
    return resp


@router.patch("/approvals/{approval_id}", response_model=ApprovalResponse)
async def act_on_approval(
    approval_id: UUID,
    data: ApprovalAction,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("documents.read"))
):
    """Aprobar, rechazar o solicitar revisión de un documento."""
    result = await db.execute(
        select(AprobacionDocumento).where(
            AprobacionDocumento.id == approval_id,
            AprobacionDocumento.tenant_id == current_user.tenant_id
        )
    )
    approval = result.scalar_one_or_none()
    if not approval:
        raise HTTPException(status_code=404, detail="Solicitud de aprobación no encontrada")

    # Only the designated approver can act
    if str(approval.aprobador_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Solo el aprobador designado puede gestionar esta solicitud")

    if data.estado not in ('aprobado', 'rechazado', 'revision'):
        raise HTTPException(status_code=400, detail="Estado debe ser: aprobado, rechazado, o revision")

    approval.estado = data.estado
    approval.comentarios_aprobador = data.comentarios_aprobador
    approval.fecha_respuesta = datetime.utcnow()

    await db.flush()

    resp = ApprovalResponse.model_validate(approval)
    if approval.solicitante:
        resp.solicitante_nombre = approval.solicitante.nombre_completo or approval.solicitante.email
    resp.aprobador_nombre = current_user.nombre_completo or current_user.email
    return resp


# ═══════════════════════════════════════════════════════════════
#  DASHBOARD: PENDING APPROVALS COUNT
# ═══════════════════════════════════════════════════════════════

@router.get("/approvals/pending-count")
async def pending_approval_count(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("documents.read"))
):
    """Cantidad de aprobaciones pendientes para el usuario actual."""
    result = await db.execute(
        select(func.count()).select_from(AprobacionDocumento).where(
            AprobacionDocumento.aprobador_id == current_user.id,
            AprobacionDocumento.estado == 'pendiente',
            AprobacionDocumento.tenant_id == current_user.tenant_id
        )
    )
    return {"pending": result.scalar()}
