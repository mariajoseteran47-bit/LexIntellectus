from fastapi import APIRouter, Depends, HTTPException, Query, status, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional
from uuid import UUID
from datetime import date

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.rbac import require_permission
from app.core.security import decode_token
from app.models.user import Usuario
from app.models.case import PlazoFatal, Expediente
from app.schemas.deadline import (
    DeadlineCreate,
    DeadlineUpdate,
    DeadlineResponse,
    DeadlineListResponse,
    DeadlineCalculateRequest,
    DeadlineCalculateResponse,
)
from app.services.deadline_service import NicaraguaProceduralCalculator
from app.services.calendar_service import CalendarService

router = APIRouter(prefix="/deadlines", tags=["Deadlines"])


@router.get("/holidays")
async def get_judicial_holidays(
    year: int = Query(default_factory=lambda: date.today().year, ge=2020, le=2050),
    municipio: str = Query("managua"),
    incluir_vacaciones_judiciales: bool = Query(True),
    current_user: Usuario = Depends(get_current_user),
):
    """Lista los feriados nacionales, patronales y vacaciones judiciales CSJ para el año indicado."""
    holidays_map = NicaraguaProceduralCalculator.get_holidays_for_year(
        year=year,
        municipio=municipio,
        incluir_vacaciones_judiciales=incluir_vacaciones_judiciales,
    )
    items = [
        {"fecha": d.isoformat(), "motivo": reason}
        for d, reason in sorted(holidays_map.items(), key=lambda x: x[0])
    ]
    return {
        "year": year,
        "municipio": municipio,
        "incluir_vacaciones_judiciales": incluir_vacaciones_judiciales,
        "total": len(items),
        "items": items,
    }


@router.post("/calculate", response_model=DeadlineCalculateResponse)
async def calculate_procedural_deadline(
    payload: DeadlineCalculateRequest,
    current_user: Usuario = Depends(get_current_user),
):
    """
    Motor de Cómputo de Plazos Procesales de Nicaragua (CPCN Arts. 129-135 y LOPJ Art. 90).
    Calcula la fecha de vencimiento excluyendo fines de semana, feriados oficiales y vacaciones CSJ.
    """
    try:
        result = NicaraguaProceduralCalculator.calculate_due_date(
            fecha_inicio=payload.fecha_inicio,
            cantidad_dias=payload.cantidad_dias,
            dias_tipo=payload.dias_tipo,
            municipio=payload.municipio,
            incluir_vacaciones_judiciales=payload.incluir_vacaciones_judiciales,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/ical.ics")
async def export_all_deadlines_ical(
    request: Request,
    token: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Exporta todos los plazos pendientes del despacho en formato iCalendar (.ics) RFC 5545."""
    auth_header = request.headers.get("Authorization", "")
    raw_token = token
    if not raw_token and auth_header.startswith("Bearer "):
        raw_token = auth_header.split(" ", 1)[1].strip()

    if not raw_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token requerido")

    payload = decode_token(raw_token)
    if not payload or not payload.get("sub"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    user_res = await db.execute(select(Usuario).where(Usuario.id == payload.get("sub")))
    current_user = user_res.scalar_one_or_none()
    if not current_user or current_user.status != "activo":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no autorizado")

    query = (
        select(PlazoFatal)
        .options(selectinload(PlazoFatal.expediente))
        .join(Expediente)
        .where(
            Expediente.tenant_id == current_user.tenant_id,
            PlazoFatal.status == "pendiente",
        )
        .order_by(PlazoFatal.fecha_vencimiento.asc())
    )
    res = await db.execute(query)
    deadlines = res.scalars().all()

    ical_content = CalendarService.generate_ical(
        deadlines,
        calendar_name="LexIntellectus - Agenda Judicial del Despacho",
    )
    return Response(
        content=ical_content,
        media_type="text/calendar",
        headers={"Content-Disposition": "attachment; filename=lexintellectus_agenda.ics"},
    )


@router.get("", response_model=DeadlineListResponse)
async def list_deadlines(
    request: Request,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    expediente_id: Optional[UUID] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("deadlines.read")),
):
    tenant_id = request.state.tenant_id
    skip = (page - 1) * size

    query = select(PlazoFatal).join(Expediente).where(Expediente.tenant_id == tenant_id)

    if expediente_id:
        query = query.where(PlazoFatal.expediente_id == expediente_id)

    if status_filter:
        query = query.where(PlazoFatal.status == status_filter)

    if start_date:
        query = query.where(PlazoFatal.fecha_vencimiento >= start_date)
    if end_date:
        query = query.where(PlazoFatal.fecha_vencimiento <= end_date)

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    if total == 0:
        return {"items": [], "total": 0, "page": page, "size": size}

    query = query.order_by(PlazoFatal.fecha_vencimiento.asc()).offset(skip).limit(size)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
    }


@router.post("", response_model=DeadlineResponse, status_code=status.HTTP_201_CREATED)
async def create_deadline(
    request: Request,
    deadline_in: DeadlineCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("deadlines.read")),
):
    tenant_id = request.state.tenant_id

    # Verify expediente belongs to tenant
    expediente = await db.execute(
        select(Expediente).where(
            Expediente.id == deadline_in.expediente_id,
            Expediente.tenant_id == tenant_id,
        )
    )
    if not expediente.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Expediente not found")

    data = deadline_in.model_dump(
        exclude={"cantidad_dias", "municipio", "incluir_vacaciones_judiciales"}
    )

    # Auto-calculate due date using NicaraguaProceduralCalculator if fecha_vencimiento is not provided
    if not data.get("fecha_vencimiento"):
        if not deadline_in.cantidad_dias:
            raise HTTPException(
                status_code=400,
                detail="Debe proporcionar fecha_vencimiento o cantidad_dias para calcular el plazo.",
            )
        start_d = data.get("fecha_inicio") or date.today()
        calc = NicaraguaProceduralCalculator.calculate_due_date(
            fecha_inicio=start_d,
            cantidad_dias=deadline_in.cantidad_dias,
            dias_tipo=data.get("dias_tipo") or "habiles",
            municipio=deadline_in.municipio or "managua",
            incluir_vacaciones_judiciales=(
                True
                if deadline_in.incluir_vacaciones_judiciales is None
                else deadline_in.incluir_vacaciones_judiciales
            ),
        )
        data["fecha_inicio"] = start_d
        data["fecha_vencimiento"] = date.fromisoformat(calc["fecha_vencimiento"])
        if not data.get("base_legal"):
            data["base_legal"] = calc["base_legal_aplicada"]

    new_deadline = PlazoFatal(**data)
    db.add(new_deadline)
    await db.commit()
    await db.refresh(new_deadline)
    return new_deadline


@router.get("/{id}", response_model=DeadlineResponse)
async def get_deadline(
    request: Request,
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("deadlines.read")),
):
    tenant_id = request.state.tenant_id

    query = select(PlazoFatal).join(Expediente).where(
        PlazoFatal.id == id,
        Expediente.tenant_id == tenant_id,
    )
    result = await db.execute(query)
    deadline = result.scalar_one_or_none()

    if not deadline:
        raise HTTPException(status_code=404, detail="Deadline not found")

    return deadline


@router.patch("/{id}", response_model=DeadlineResponse)
async def update_deadline(
    request: Request,
    id: UUID,
    deadline_in: DeadlineUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("deadlines.read")),
):
    tenant_id = request.state.tenant_id

    query = select(PlazoFatal).join(Expediente).where(
        PlazoFatal.id == id,
        Expediente.tenant_id == tenant_id,
    )
    result = await db.execute(query)
    deadline = result.scalar_one_or_none()

    if not deadline:
        raise HTTPException(status_code=404, detail="Deadline not found")

    update_data = deadline_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(deadline, field, value)

    await db.commit()
    await db.refresh(deadline)
    return deadline


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deadline(
    request: Request,
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("deadlines.read")),
):
    tenant_id = request.state.tenant_id

    query = select(PlazoFatal).join(Expediente).where(
        PlazoFatal.id == id,
        Expediente.tenant_id == tenant_id,
    )
    result = await db.execute(query)
    deadline = result.scalar_one_or_none()

    if not deadline:
        raise HTTPException(status_code=404, detail="Deadline not found")

    await db.delete(deadline)
    await db.commit()
