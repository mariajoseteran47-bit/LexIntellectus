"""
LexIntellectus — API: Workflow Administration
Full CRUD for configurable workflow stages per service type.
Allows each tenant to customize their own workflows.
"""

import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, update, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_db
from app.core.rbac import require_permission
from app.models.user import Usuario
from app.models.case_extended import EtapaProcesal
from app.schemas.workflow import (
    WorkflowStageCreate, WorkflowStageUpdate, WorkflowStageResponse,
    WorkflowStageListResponse, WorkflowStageReorder
)

router = APIRouter(prefix="/workflow", tags=["Workflow Administration"])


# ═══════════════════════════════════════════════════════════════
# LIST — All stages, filtered by service type/ramo
# ═══════════════════════════════════════════════════════════════

@router.get("/stages", response_model=WorkflowStageListResponse)
async def list_stages(
    tipo_servicio: Optional[str] = None,
    ramo: Optional[str] = None,
    tipo_proceso: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("cases.read"))
):
    """Listar etapas de workflow configuradas para el tenant.
    
    Filtrar por tipo_servicio (escritura, contrato, etc.) o por ramo (civil, penal, etc.) para litigio.
    """
    tenant_id = current_user.tenant_id

    query = select(EtapaProcesal).where(EtapaProcesal.tenant_id == tenant_id)

    if tipo_servicio:
        query = query.where(EtapaProcesal.tipo_servicio == tipo_servicio)
    if ramo:
        query = query.where(EtapaProcesal.ramo == ramo)
    if tipo_proceso:
        query = query.where(EtapaProcesal.tipo_proceso == tipo_proceso)

    query = query.order_by(EtapaProcesal.orden)

    result = await db.execute(query)
    stages = result.scalars().all()

    # Count total
    count_query = select(func.count()).select_from(EtapaProcesal).where(
        EtapaProcesal.tenant_id == tenant_id
    )
    if tipo_servicio:
        count_query = count_query.where(EtapaProcesal.tipo_servicio == tipo_servicio)
    if ramo:
        count_query = count_query.where(EtapaProcesal.ramo == ramo)

    count_result = await db.execute(count_query)
    total = count_result.scalar()

    return WorkflowStageListResponse(
        items=[WorkflowStageResponse.model_validate(s) for s in stages],
        total=total
    )


# ═══════════════════════════════════════════════════════════════
# GET — Single stage by ID
# ═══════════════════════════════════════════════════════════════

@router.get("/stages/{stage_id}", response_model=WorkflowStageResponse)
async def get_stage(
    stage_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("cases.read"))
):
    """Obtener una etapa de workflow por su ID."""
    tenant_id = current_user.tenant_id
    
    result = await db.execute(
        select(EtapaProcesal).where(
            EtapaProcesal.id == stage_id,
            EtapaProcesal.tenant_id == tenant_id
        )
    )
    stage = result.scalar_one_or_none()

    if not stage:
        raise HTTPException(status_code=404, detail="Etapa no encontrada")

    return WorkflowStageResponse.model_validate(stage)


# ═══════════════════════════════════════════════════════════════
# CREATE — Add a new stage to a workflow
# ═══════════════════════════════════════════════════════════════

@router.post("/stages", response_model=WorkflowStageResponse, status_code=201)
async def create_stage(
    data: WorkflowStageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("settings.manage"))
):
    """Crear una nueva etapa de workflow.
    
    Se requiere al menos tipo_servicio o ramo.
    El código debe ser único dentro del mismo tipo_servicio/ramo del tenant.
    """
    tenant_id = current_user.tenant_id

    # Validate: at least one of tipo_servicio or ramo must be set
    if not data.tipo_servicio and not data.ramo:
        raise HTTPException(
            status_code=400,
            detail="Se requiere tipo_servicio o ramo para crear una etapa"
        )

    # Check for duplicate codigo within same scope
    dup_query = select(EtapaProcesal).where(
        EtapaProcesal.tenant_id == tenant_id,
        EtapaProcesal.codigo == data.codigo
    )
    if data.tipo_servicio:
        dup_query = dup_query.where(EtapaProcesal.tipo_servicio == data.tipo_servicio)
    if data.ramo:
        dup_query = dup_query.where(EtapaProcesal.ramo == data.ramo)

    dup_result = await db.execute(dup_query)
    if dup_result.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"Ya existe una etapa con código '{data.codigo}' en este flujo"
        )

    stage = EtapaProcesal(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        tipo_servicio=data.tipo_servicio,
        ramo=data.ramo,
        tipo_proceso=data.tipo_proceso,
        codigo=data.codigo,
        nombre=data.nombre,
        descripcion=data.descripcion,
        orden=data.orden,
        dias_plazo_legal=data.dias_plazo_legal,
        tipo_dias=data.tipo_dias,
        base_legal=data.base_legal,
        es_final=data.es_final,
        acciones_requeridas=data.acciones_requeridas,
        plantillas_sugeridas=data.plantillas_sugeridas,
    )
    db.add(stage)
    await db.flush()

    return WorkflowStageResponse.model_validate(stage)


# ═══════════════════════════════════════════════════════════════
# UPDATE — Edit an existing stage
# ═══════════════════════════════════════════════════════════════

@router.patch("/stages/{stage_id}", response_model=WorkflowStageResponse)
async def update_stage(
    stage_id: UUID,
    data: WorkflowStageUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("settings.manage"))
):
    """Actualizar una etapa de workflow existente.
    
    Solo se actualizan los campos enviados (partial update).
    """
    tenant_id = current_user.tenant_id

    result = await db.execute(
        select(EtapaProcesal).where(
            EtapaProcesal.id == stage_id,
            EtapaProcesal.tenant_id == tenant_id
        )
    )
    stage = result.scalar_one_or_none()

    if not stage:
        raise HTTPException(status_code=404, detail="Etapa no encontrada")

    # Apply partial updates
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(stage, field, value)

    await db.flush()
    return WorkflowStageResponse.model_validate(stage)


# ═══════════════════════════════════════════════════════════════
# DELETE — Remove a stage (with safety check)
# ═══════════════════════════════════════════════════════════════

@router.delete("/stages/{stage_id}", status_code=204)
async def delete_stage(
    stage_id: UUID,
    force: bool = Query(False, description="Si true, elimina aunque haya casos en esta etapa"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("settings.manage"))
):
    """Eliminar una etapa de workflow.
    
    Por seguridad, no se puede eliminar si hay expedientes en esa etapa,
    salvo que se pase force=true.
    """
    tenant_id = current_user.tenant_id

    result = await db.execute(
        select(EtapaProcesal).where(
            EtapaProcesal.id == stage_id,
            EtapaProcesal.tenant_id == tenant_id
        )
    )
    stage = result.scalar_one_or_none()

    if not stage:
        raise HTTPException(status_code=404, detail="Etapa no encontrada")

    # Safety check: are there cases currently at this stage?
    if not force:
        from app.models.case import Expediente
        cases_query = select(func.count()).select_from(Expediente).where(
            Expediente.etapa_actual_id == stage_id
        )
        cases_result = await db.execute(cases_query)
        cases_count = cases_result.scalar()

        if cases_count > 0:
            raise HTTPException(
                status_code=409,
                detail=f"No se puede eliminar: hay {cases_count} expediente(s) en esta etapa. "
                       f"Use force=true para forzar la eliminación."
            )

    await db.delete(stage)
    await db.flush()


# ═══════════════════════════════════════════════════════════════
# REORDER — Bulk reorder stages (drag & drop support)
# ═══════════════════════════════════════════════════════════════

@router.put("/stages/reorder", response_model=List[WorkflowStageResponse])
async def reorder_stages(
    data: WorkflowStageReorder,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("settings.manage"))
):
    """Reordenar etapas de un workflow.
    
    Recibe una lista de stage_ids en el nuevo orden.
    Asigna automáticamente los valores de 'orden' (1, 2, 3...).
    """
    tenant_id = current_user.tenant_id

    if not data.stage_ids:
        raise HTTPException(status_code=400, detail="La lista de IDs no puede estar vacía")

    # Verify all stages belong to this tenant
    result = await db.execute(
        select(EtapaProcesal).where(
            EtapaProcesal.id.in_(data.stage_ids),
            EtapaProcesal.tenant_id == tenant_id
        )
    )
    stages = {str(s.id): s for s in result.scalars().all()}

    if len(stages) != len(data.stage_ids):
        raise HTTPException(
            status_code=400,
            detail="Algunos IDs no pertenecen a este tenant o no existen"
        )

    # Update order
    for new_order, stage_id in enumerate(data.stage_ids, start=1):
        stage = stages[str(stage_id)]
        stage.orden = new_order

    await db.flush()

    # Return stages in new order
    ordered = [stages[str(sid)] for sid in data.stage_ids]
    return [WorkflowStageResponse.model_validate(s) for s in ordered]


# ═══════════════════════════════════════════════════════════════
# CLONE — Copy a full workflow to use as template for subtypes
# ═══════════════════════════════════════════════════════════════

@router.post("/stages/clone", response_model=WorkflowStageListResponse)
async def clone_workflow(
    source_tipo_servicio: str = Query(..., description="Tipo de servicio fuente"),
    target_tipo_proceso: str = Query(..., description="Subtipo destino (ej: compraventa_inmueble)"),
    source_ramo: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("settings.manage"))
):
    """Clonar un workflow completo para crear un subtipo.
    
    Ejemplo: clonar el workflow de 'escritura' para crear un flujo específico
    para 'compraventa_inmueble' con etapas personalizadas.
    """
    tenant_id = current_user.tenant_id

    # Get source stages
    source_query = select(EtapaProcesal).where(
        EtapaProcesal.tenant_id == tenant_id,
        EtapaProcesal.tipo_servicio == source_tipo_servicio
    )
    if source_ramo:
        source_query = source_query.where(EtapaProcesal.ramo == source_ramo)
    source_query = source_query.order_by(EtapaProcesal.orden)

    result = await db.execute(source_query)
    source_stages = result.scalars().all()

    if not source_stages:
        raise HTTPException(
            status_code=404,
            detail=f"No hay etapas para tipo_servicio='{source_tipo_servicio}'"
        )

    # Check if target already has stages
    check_query = select(func.count()).select_from(EtapaProcesal).where(
        EtapaProcesal.tenant_id == tenant_id,
        EtapaProcesal.tipo_servicio == source_tipo_servicio,
        EtapaProcesal.tipo_proceso == target_tipo_proceso
    )
    check_result = await db.execute(check_query)
    if check_result.scalar() > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Ya existen etapas para subtipo '{target_tipo_proceso}'. Elimínelas primero."
        )

    # Clone
    new_stages = []
    for src in source_stages:
        new_stage = EtapaProcesal(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            tipo_servicio=src.tipo_servicio,
            ramo=src.ramo,
            tipo_proceso=target_tipo_proceso,
            codigo=f"{src.codigo}-{target_tipo_proceso[:3].upper()}",
            nombre=src.nombre,
            descripcion=src.descripcion,
            orden=src.orden,
            dias_plazo_legal=src.dias_plazo_legal,
            tipo_dias=src.tipo_dias,
            base_legal=src.base_legal,
            es_final=src.es_final,
            acciones_requeridas=src.acciones_requeridas,
            plantillas_sugeridas=src.plantillas_sugeridas,
        )
        db.add(new_stage)
        new_stages.append(new_stage)

    await db.flush()

    return WorkflowStageListResponse(
        items=[WorkflowStageResponse.model_validate(s) for s in new_stages],
        total=len(new_stages)
    )


# ═══════════════════════════════════════════════════════════════
# SUMMARY — Overview of all configured workflows
# ═══════════════════════════════════════════════════════════════

@router.get("/summary")
async def workflow_summary(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("cases.read"))
):
    """Resumen de todos los workflows configurados para este tenant.
    
    Devuelve cuántas etapas tiene cada tipo de servicio/ramo.
    """
    tenant_id = current_user.tenant_id

    result = await db.execute(
        select(
            EtapaProcesal.tipo_servicio,
            EtapaProcesal.ramo,
            EtapaProcesal.tipo_proceso,
            func.count().label("total_etapas"),
            func.sum(func.cast(EtapaProcesal.es_final, Integer)).label("etapas_finales")
        ).where(
            EtapaProcesal.tenant_id == tenant_id
        ).group_by(
            EtapaProcesal.tipo_servicio,
            EtapaProcesal.ramo,
            EtapaProcesal.tipo_proceso
        ).order_by(
            EtapaProcesal.tipo_servicio,
            EtapaProcesal.ramo
        )
    )

    summary = []
    for row in result.all():
        summary.append({
            "tipo_servicio": row.tipo_servicio,
            "ramo": row.ramo,
            "tipo_proceso": row.tipo_proceso,
            "total_etapas": row.total_etapas,
            "etapas_finales": row.etapas_finales or 0,
            "configurado": row.total_etapas > 0,
        })

    return summary
