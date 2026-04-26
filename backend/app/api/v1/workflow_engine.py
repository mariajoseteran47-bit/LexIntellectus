"""
LexIntellectus — API: Workflow Engine (Tasks, Conflict Check, Transition Rules)
Sprint 4: Intelligent automation and conflict detection.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, text, or_
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_db
from app.core.rbac import require_permission
from app.models.user import Usuario
from app.models.workflow_engine import (
    PlantillaWorkflow, TareaExpediente, ChecklistDocumento, ConflictCheckResult
)
from app.models.case import Expediente, ParteProcesal
from app.models.case_extended import EtapaProcesal
from app.schemas.workflow_engine import (
    TaskCreate, TaskUpdate, TaskResponse, TaskListResponse,
    ChecklistItemResponse, ChecklistMarkReceived,
    TemplateResponse,
    ConflictCheckRequest, ConflictCheckResponse, ConflictMatch,
    TransitionCheckResponse
)

router = APIRouter(tags=["Workflow Engine"])


# ═══════════════════════════════════════════════════════════════
#  TAREAS POR EXPEDIENTE
# ═══════════════════════════════════════════════════════════════

@router.get("/cases/{case_id}/tasks", response_model=TaskListResponse)
async def list_tasks(
    case_id: UUID,
    estado: Optional[str] = None,
    etapa_codigo: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("cases.read"))
):
    """Listar tareas de un expediente."""
    query = select(TareaExpediente).where(
        TareaExpediente.expediente_id == case_id,
        TareaExpediente.tenant_id == current_user.tenant_id
    )
    if estado:
        query = query.where(TareaExpediente.estado == estado)
    if etapa_codigo:
        query = query.where(TareaExpediente.etapa_codigo == etapa_codigo)
    query = query.order_by(TareaExpediente.orden, TareaExpediente.created_at)

    result = await db.execute(query)
    tasks = result.scalars().all()

    items = []
    for t in tasks:
        resp = TaskResponse.model_validate(t)
        if t.asignado_a:
            resp.asignado_nombre = t.asignado_a.nombre_completo or t.asignado_a.email
        items.append(resp)

    completadas = sum(1 for t in tasks if t.estado == 'completada')
    return TaskListResponse(
        items=items, total=len(items),
        completadas=completadas, pendientes=len(items) - completadas
    )


@router.post("/cases/{case_id}/tasks", response_model=TaskResponse, status_code=201)
async def create_task(
    case_id: UUID,
    data: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("cases.read"))
):
    """Crear tarea manual para un expediente."""
    task = TareaExpediente(
        id=uuid.uuid4(),
        tenant_id=current_user.tenant_id,
        expediente_id=case_id,
        titulo=data.titulo,
        descripcion=data.descripcion,
        categoria=data.categoria,
        obligatoria=data.obligatoria,
        asignado_a_id=data.asignado_a_id,
        fecha_limite=data.fecha_limite,
        etapa_codigo=data.etapa_codigo,
        orden=data.orden,
        creado_por_id=current_user.id,
    )
    db.add(task)
    await db.flush()
    return TaskResponse.model_validate(task)


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("cases.read"))
):
    """Actualizar tarea (marcar completada, reasignar, etc.)."""
    result = await db.execute(
        select(TareaExpediente).where(
            TareaExpediente.id == task_id,
            TareaExpediente.tenant_id == current_user.tenant_id
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    # Auto-set completion date
    if data.estado == 'completada' and not task.fecha_completada:
        task.fecha_completada = datetime.utcnow()
    elif data.estado and data.estado != 'completada':
        task.fecha_completada = None

    await db.flush()
    resp = TaskResponse.model_validate(task)
    if task.asignado_a:
        resp.asignado_nombre = task.asignado_a.nombre_completo or task.asignado_a.email
    return resp


@router.delete("/tasks/{task_id}", status_code=204)
async def delete_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("cases.read"))
):
    """Eliminar tarea."""
    result = await db.execute(
        select(TareaExpediente).where(
            TareaExpediente.id == task_id,
            TareaExpediente.tenant_id == current_user.tenant_id
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    await db.delete(task)
    await db.flush()


# ═══════════════════════════════════════════════════════════════
#  CHECKLIST DE DOCUMENTOS
# ═══════════════════════════════════════════════════════════════

@router.get("/cases/{case_id}/checklist", response_model=list[ChecklistItemResponse])
async def get_checklist(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("cases.read"))
):
    """Obtener checklist de documentos requeridos para un expediente."""
    result = await db.execute(
        select(ChecklistDocumento).where(
            ChecklistDocumento.expediente_id == case_id,
            ChecklistDocumento.tenant_id == current_user.tenant_id
        ).order_by(ChecklistDocumento.created_at)
    )
    return [ChecklistItemResponse.model_validate(c) for c in result.scalars().all()]


@router.patch("/checklist/{item_id}/mark", response_model=ChecklistItemResponse)
async def mark_checklist_item(
    item_id: UUID,
    data: ChecklistMarkReceived,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("cases.read"))
):
    """Marcar un documento del checklist como recibido."""
    result = await db.execute(
        select(ChecklistDocumento).where(
            ChecklistDocumento.id == item_id,
            ChecklistDocumento.tenant_id == current_user.tenant_id
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item no encontrado")

    item.recibido = True
    item.documento_id = data.documento_id
    item.fecha_recibido = datetime.utcnow()
    item.verificado_por_id = current_user.id

    await db.flush()
    return ChecklistItemResponse.model_validate(item)


# ═══════════════════════════════════════════════════════════════
#  AUTO-CREACIÓN DE TAREAS DESDE PLANTILLA
# ═══════════════════════════════════════════════════════════════

@router.post("/cases/{case_id}/apply-template")
async def apply_template(
    case_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("cases.read"))
):
    """
    Busca la plantilla correspondiente al tipo de servicio del expediente
    y auto-crea tareas y checklist de documentos.
    """
    # Get the case
    case_result = await db.execute(
        select(Expediente).where(Expediente.id == case_id)
    )
    case = case_result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")

    # Find matching template
    query = select(PlantillaWorkflow).where(
        PlantillaWorkflow.tenant_id == current_user.tenant_id,
        PlantillaWorkflow.tipo_servicio == (case.tipo_servicio or 'litigio'),
        PlantillaWorkflow.activo == True
    )
    if case.ramo:
        query = query.where(
            or_(PlantillaWorkflow.ramo == case.ramo, PlantillaWorkflow.ramo == None)
        )
    query = query.order_by(PlantillaWorkflow.ramo.desc().nullslast())  # Prefer specific

    result = await db.execute(query)
    template = result.scalars().first()

    if not template:
        return {"message": "No hay plantilla configurada para este tipo de servicio", "tasks_created": 0, "docs_created": 0}

    # Create tasks from template
    tasks_created = 0
    for idx, tarea_def in enumerate(template.tareas or []):
        task = TareaExpediente(
            id=uuid.uuid4(),
            tenant_id=current_user.tenant_id,
            expediente_id=case_id,
            titulo=tarea_def.get('titulo', f'Tarea {idx + 1}'),
            descripcion=tarea_def.get('descripcion'),
            categoria=tarea_def.get('categoria', 'administrativa'),
            obligatoria=tarea_def.get('obligatoria', False),
            etapa_codigo=tarea_def.get('etapa_codigo'),
            orden=idx,
            plantilla_id=template.id,
            creado_por_id=current_user.id,
        )
        # Calculate deadline from days
        if tarea_def.get('dias_plazo'):
            task.fecha_limite = datetime.utcnow() + timedelta(days=tarea_def['dias_plazo'])
        db.add(task)
        tasks_created += 1

    # Create checklist items from template
    docs_created = 0
    for doc_def in template.docs_requeridos or []:
        check = ChecklistDocumento(
            id=uuid.uuid4(),
            tenant_id=current_user.tenant_id,
            expediente_id=case_id,
            nombre_documento=doc_def.get('nombre', 'Documento'),
            descripcion=doc_def.get('descripcion'),
            obligatorio=doc_def.get('obligatorio', True),
            etapa_codigo=doc_def.get('etapa_codigo'),
        )
        db.add(check)
        docs_created += 1

    await db.flush()
    return {
        "message": f"Plantilla '{template.nombre}' aplicada exitosamente",
        "template_id": str(template.id),
        "tasks_created": tasks_created,
        "docs_created": docs_created,
    }


# ═══════════════════════════════════════════════════════════════
#  VALIDACIÓN DE TRANSICIÓN DE ETAPA
# ═══════════════════════════════════════════════════════════════

@router.get("/cases/{case_id}/can-advance", response_model=TransitionCheckResponse)
async def check_stage_transition(
    case_id: UUID,
    destino_etapa_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("cases.read"))
):
    """
    Check if a case can advance to the next/specified stage.
    Validates: mandatory tasks completed, required documents received.
    """
    case_result = await db.execute(select(Expediente).where(Expediente.id == case_id))
    case = case_result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")

    # Get current stage info
    current_stage_name = None
    current_etapa_codigo = None
    if case.etapa_actual_id:
        stage_result = await db.execute(
            select(EtapaProcesal).where(EtapaProcesal.id == case.etapa_actual_id)
        )
        stage = stage_result.scalar_one_or_none()
        if stage:
            current_stage_name = stage.nombre
            current_etapa_codigo = stage.codigo

    # Check mandatory tasks for current stage
    tasks_result = await db.execute(
        select(TareaExpediente).where(
            TareaExpediente.expediente_id == case_id,
            TareaExpediente.obligatoria == True,
            TareaExpediente.estado != 'completada',
            TareaExpediente.estado != 'cancelada',
        )
    )
    pending_tasks = tasks_result.scalars().all()
    # Filter to current stage if applicable
    if current_etapa_codigo:
        pending_tasks = [t for t in pending_tasks if t.etapa_codigo == current_etapa_codigo or t.etapa_codigo is None]

    tareas_pendientes = [t.titulo for t in pending_tasks]

    # Check required documents
    docs_result = await db.execute(
        select(ChecklistDocumento).where(
            ChecklistDocumento.expediente_id == case_id,
            ChecklistDocumento.obligatorio == True,
            ChecklistDocumento.recibido == False,
        )
    )
    missing_docs_all = docs_result.scalars().all()
    if current_etapa_codigo:
        missing_docs_all = [d for d in missing_docs_all if d.etapa_codigo == current_etapa_codigo or d.etapa_codigo is None]

    docs_faltantes = [d.nombre_documento for d in missing_docs_all]

    puede_avanzar = len(tareas_pendientes) == 0 and len(docs_faltantes) == 0

    motivo = None
    if not puede_avanzar:
        parts = []
        if tareas_pendientes:
            parts.append(f"{len(tareas_pendientes)} tarea(s) obligatoria(s) pendiente(s)")
        if docs_faltantes:
            parts.append(f"{len(docs_faltantes)} documento(s) requerido(s) faltante(s)")
        motivo = " y ".join(parts)

    return TransitionCheckResponse(
        puede_avanzar=puede_avanzar,
        etapa_actual=current_stage_name,
        tareas_pendientes=tareas_pendientes,
        docs_faltantes=docs_faltantes,
        motivo_bloqueo=motivo,
    )


# ═══════════════════════════════════════════════════════════════
#  CONFLICT CHECK ENGINE
# ═══════════════════════════════════════════════════════════════

@router.post("/conflict-check", response_model=ConflictCheckResponse)
async def check_conflict(
    data: ConflictCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("cases.read"))
):
    """
    Check for conflicts of interest by searching the name against:
    - case_parties (all cases)
    - client_profiles
    Uses pg_trgm similarity for fuzzy matching.
    """
    tenant_id = current_user.tenant_id
    nombre = data.nombre.strip()
    threshold = 0.3  # Similarity threshold

    matches: list[ConflictMatch] = []

    # --- Search in case_parties ---
    try:
        parties_query = text("""
            SELECT
                cp.id, cp.nombre_completo, cp.rol_procesal, cp.documento_identidad,
                c.id as caso_id, c.resumen as caso_titulo,
                similarity(cp.nombre_completo, :nombre) as sim
            FROM case_parties cp
            JOIN cases c ON c.id = cp.expediente_id
            WHERE cp.tenant_id = :tenant_id
              AND similarity(cp.nombre_completo, :nombre) > :threshold
            ORDER BY sim DESC
            LIMIT 20
        """)
        result = await db.execute(parties_query, {
            "nombre": nombre, "tenant_id": str(tenant_id), "threshold": threshold
        })
        for row in result.mappings():
            matches.append(ConflictMatch(
                tabla="case_parties",
                id=str(row["id"]),
                nombre=row["nombre_completo"],
                caso_id=str(row["caso_id"]) if row.get("caso_id") else None,
                caso_titulo=row.get("caso_titulo"),
                similitud=round(float(row["sim"]), 3),
            ))
    except Exception as e:
        # pg_trgm might not be installed — fallback to ILIKE
        parties_query = text("""
            SELECT cp.id, cp.nombre_completo, cp.rol_procesal,
                   c.id as caso_id, c.resumen as caso_titulo
            FROM case_parties cp
            JOIN cases c ON c.id = cp.expediente_id
            WHERE cp.tenant_id = :tenant_id
              AND cp.nombre_completo ILIKE :pattern
            LIMIT 20
        """)
        result = await db.execute(parties_query, {
            "tenant_id": str(tenant_id), "pattern": f"%{nombre}%"
        })
        for row in result.mappings():
            matches.append(ConflictMatch(
                tabla="case_parties",
                id=str(row["id"]),
                nombre=row["nombre_completo"],
                caso_id=str(row["caso_id"]) if row.get("caso_id") else None,
                caso_titulo=row.get("caso_titulo"),
                similitud=0.5,
            ))

    # --- Search in client_profiles (uses razon_social) ---
    try:
        clients_query = text("""
            SELECT cp.id, COALESCE(cp.razon_social, cp.nombre_comercial, u.nombre_completo) as nombre,
                   cp.tipo_persona, cp.cedula_identidad,
                   similarity(COALESCE(cp.razon_social, cp.nombre_comercial, u.nombre_completo, ''), :nombre) as sim
            FROM client_profiles cp
            LEFT JOIN users u ON u.id = cp.user_id
            WHERE cp.tenant_id = :tenant_id
              AND similarity(COALESCE(cp.razon_social, cp.nombre_comercial, u.nombre_completo, ''), :nombre) > :threshold
            ORDER BY sim DESC
            LIMIT 10
        """)
        result = await db.execute(clients_query, {
            "nombre": nombre, "tenant_id": str(tenant_id), "threshold": threshold
        })
        for row in result.mappings():
            matches.append(ConflictMatch(
                tabla="client_profiles",
                id=str(row["id"]),
                nombre=row["nombre"] or "Sin nombre",
                similitud=round(float(row["sim"]), 3),
            ))
    except Exception:
        clients_query = text("""
            SELECT cp.id, COALESCE(cp.razon_social, cp.nombre_comercial) as nombre
            FROM client_profiles cp
            WHERE cp.tenant_id = :tenant_id
              AND (cp.razon_social ILIKE :pattern OR cp.nombre_comercial ILIKE :pattern)
            LIMIT 10
        """)
        result = await db.execute(clients_query, {
            "tenant_id": str(tenant_id), "pattern": f"%{nombre}%"
        })
        for row in result.mappings():
            matches.append(ConflictMatch(
                tabla="client_profiles",
                id=str(row["id"]),
                nombre=row["nombre"] or "Sin nombre",
                similitud=0.5,
            ))

    # --- Also check by document ID if provided ---
    if data.documento:
        doc_query = text("""
            SELECT cp.id, cp.nombre_completo, c.id as caso_id, c.resumen as caso_titulo
            FROM case_parties cp
            JOIN cases c ON c.id = cp.expediente_id
            WHERE cp.tenant_id = :tenant_id AND cp.documento_identidad = :doc
            LIMIT 10
        """)
        result = await db.execute(doc_query, {
            "tenant_id": str(tenant_id), "doc": data.documento
        })
        for row in result.mappings():
            if not any(m.id == str(row["id"]) for m in matches):
                matches.append(ConflictMatch(
                    tabla="case_parties",
                    id=str(row["id"]),
                    nombre=row["nombre_completo"],
                    caso_id=str(row["caso_id"]) if row.get("caso_id") else None,
                    caso_titulo=row.get("caso_titulo"),
                    similitud=1.0,
                ))

    tiene_conflicto = len(matches) > 0

    # Save result for audit
    check_result = ConflictCheckResult(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        expediente_id=data.expediente_id,
        nombre_buscado=nombre,
        documento_buscado=data.documento,
        tiene_conflicto=tiene_conflicto,
        coincidencias=[m.model_dump() for m in matches],
        verificado_por_id=current_user.id,
    )
    db.add(check_result)
    await db.flush()

    return ConflictCheckResponse(
        id=check_result.id,
        tiene_conflicto=tiene_conflicto,
        nombre_buscado=nombre,
        coincidencias=matches,
        total_coincidencias=len(matches),
    )


# ═══════════════════════════════════════════════════════════════
#  PLANTILLAS (Lectura para admin)
# ═══════════════════════════════════════════════════════════════

@router.get("/workflow/templates", response_model=list[TemplateResponse])
async def list_templates(
    tipo_servicio: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("settings.manage"))
):
    """Listar plantillas de workflow configuradas."""
    query = select(PlantillaWorkflow).where(
        PlantillaWorkflow.tenant_id == current_user.tenant_id
    )
    if tipo_servicio:
        query = query.where(PlantillaWorkflow.tipo_servicio == tipo_servicio)
    result = await db.execute(query.order_by(PlantillaWorkflow.tipo_servicio))
    return [TemplateResponse.model_validate(t) for t in result.scalars().all()]
