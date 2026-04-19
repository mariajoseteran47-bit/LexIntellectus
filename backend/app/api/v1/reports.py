"""
LexIntellectus - Reports API
Generates real statistical data from the database for the reports module.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case as sql_case, extract, and_
from datetime import date, timedelta, datetime
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.rbac import require_permission
from app.models.user import Usuario
from app.models.case import Expediente, PlazoFatal, ParteProcesal, EstadoExpediente
from app.models.document import Documento
from app.models.audit import LogAuditoria

router = APIRouter(prefix="/reports", tags=["Reports"])


def _get_date_range(period: str) -> tuple[date, date]:
    """Calculate start/end date for a given period."""
    today = date.today()
    if period == "week":
        start = today - timedelta(days=today.weekday())
        return start, today
    elif period == "month":
        start = today.replace(day=1)
        return start, today
    elif period == "quarter":
        quarter_start_month = ((today.month - 1) // 3) * 3 + 1
        start = today.replace(month=quarter_start_month, day=1)
        return start, today
    else:  # year
        start = today.replace(month=1, day=1)
        return start, today


@router.get("/overview")
async def get_reports_overview(
    period: str = Query("month", regex="^(week|month|quarter|year)$"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_permission("cases.read"))
):
    """
    Comprehensive report overview with real data.
    Returns KPIs, case distribution by ramo, status distribution,
    and monthly activity data.
    """
    tenant_id = current_user.tenant_id
    start_date, end_date = _get_date_range(period)
    today = date.today()

    # === 1. KPIs ===

    # Active cases (no fecha_cierre)
    active_cases = await db.scalar(
        select(func.count()).where(
            Expediente.tenant_id == tenant_id,
            Expediente.fecha_cierre == None
        )
    )

    # Cases opened this period
    new_cases_period = await db.scalar(
        select(func.count()).where(
            Expediente.tenant_id == tenant_id,
            Expediente.fecha_apertura >= start_date
        )
    )

    # Pending deadlines
    pending_deadlines = await db.scalar(
        select(func.count()).select_from(PlazoFatal).join(Expediente).where(
            Expediente.tenant_id == tenant_id,
            PlazoFatal.status == "pendiente"
        )
    )

    # Urgent deadlines (due within 7 days)
    urgent_deadlines = await db.scalar(
        select(func.count()).select_from(PlazoFatal).join(Expediente).where(
            Expediente.tenant_id == tenant_id,
            PlazoFatal.status == "pendiente",
            PlazoFatal.fecha_vencimiento <= today + timedelta(days=7)
        )
    )

    # Overdue deadlines
    overdue_deadlines = await db.scalar(
        select(func.count()).select_from(PlazoFatal).join(Expediente).where(
            Expediente.tenant_id == tenant_id,
            PlazoFatal.status == "pendiente",
            PlazoFatal.fecha_vencimiento < today
        )
    )

    # Cases closed this period
    closed_cases_period = await db.scalar(
        select(func.count()).where(
            Expediente.tenant_id == tenant_id,
            Expediente.fecha_cierre >= start_date,
            Expediente.fecha_cierre <= end_date
        )
    )

    # Total cases
    total_cases = await db.scalar(
        select(func.count()).where(
            Expediente.tenant_id == tenant_id
        )
    )

    # Resolution rate
    total_closed = await db.scalar(
        select(func.count()).where(
            Expediente.tenant_id == tenant_id,
            Expediente.fecha_cierre != None
        )
    )
    resolution_rate = round((total_closed / total_cases * 100), 1) if total_cases > 0 else 0.0

    # Documents uploaded this period
    docs_period = await db.scalar(
        select(func.count()).where(
            Documento.tenant_id == tenant_id,
            Documento.created_at >= datetime.combine(start_date, datetime.min.time())
        )
    )

    # Total clients
    active_clients = await db.scalar(
        select(func.count()).where(
            Usuario.tenant_id == tenant_id,
            Usuario.tipo_usuario == "cliente",
            Usuario.status == "activo"
        )
    )

    # === 2. Cases by Ramo ===
    ramo_query = (
        select(
            Expediente.ramo,
            func.count().label("count")
        )
        .where(Expediente.tenant_id == tenant_id)
        .group_by(Expediente.ramo)
        .order_by(func.count().desc())
    )
    ramo_result = await db.execute(ramo_query)
    ramo_data = ramo_result.all()

    ramo_total = sum(r.count for r in ramo_data) if ramo_data else 1
    cases_by_ramo = [
        {
            "name": r.ramo.capitalize() if r.ramo else "Sin clasificar",
            "count": r.count,
            "pct": round(r.count / ramo_total * 100)
        }
        for r in ramo_data
    ]

    # === 3. Status Distribution ===
    status_query = (
        select(
            EstadoExpediente.nombre,
            EstadoExpediente.color_hex,
            EstadoExpediente.es_final,
            func.count(Expediente.id).label("count")
        )
        .outerjoin(Expediente, and_(
            Expediente.estado_id == EstadoExpediente.id,
            Expediente.tenant_id == tenant_id
        ))
        .where(EstadoExpediente.tenant_id == tenant_id)
        .group_by(EstadoExpediente.nombre, EstadoExpediente.color_hex, EstadoExpediente.es_final)
        .order_by(func.count(Expediente.id).desc())
    )
    status_result = await db.execute(status_query)
    status_data = status_result.all()

    status_total = sum(s.count for s in status_data) if status_data else 1
    status_distribution = [
        {
            "label": s.nombre,
            "count": s.count,
            "color_hex": s.color_hex,
            "es_final": s.es_final,
            "pct": round(s.count / status_total * 100)
        }
        for s in status_data
    ]

    # === 4. Monthly Activity (last 6 months) ===
    monthly_activity = []
    for i in range(5, -1, -1):
        month_date = today.replace(day=1) - timedelta(days=i * 30)
        month_start = month_date.replace(day=1)
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(days=1)

        cases_opened = await db.scalar(
            select(func.count()).where(
                Expediente.tenant_id == tenant_id,
                Expediente.fecha_apertura >= month_start,
                Expediente.fecha_apertura <= month_end
            )
        )

        deadlines_due = await db.scalar(
            select(func.count()).select_from(PlazoFatal).join(Expediente).where(
                Expediente.tenant_id == tenant_id,
                PlazoFatal.fecha_vencimiento >= month_start,
                PlazoFatal.fecha_vencimiento <= month_end
            )
        )

        months_es = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
                      'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        monthly_activity.append({
            "month": months_es[month_start.month - 1],
            "year": month_start.year,
            "cases": cases_opened or 0,
            "deadlines": deadlines_due or 0
        })

    # === 5. Priority Distribution ===
    priority_query = (
        select(
            Expediente.prioridad,
            func.count().label("count")
        )
        .where(
            Expediente.tenant_id == tenant_id,
            Expediente.fecha_cierre == None
        )
        .group_by(Expediente.prioridad)
    )
    priority_result = await db.execute(priority_query)
    priority_data = priority_result.all()

    priority_distribution = [
        {"priority": p.prioridad or "normal", "count": p.count}
        for p in priority_data
    ]

    # === 6. Top Lawyers by Caseload ===
    lawyer_query = (
        select(
            Usuario.nombre,
            Usuario.apellido,
            func.count(Expediente.id).label("case_count")
        )
        .join(Expediente, Expediente.abogado_responsable_id == Usuario.id)
        .where(
            Expediente.tenant_id == tenant_id,
            Expediente.fecha_cierre == None
        )
        .group_by(Usuario.nombre, Usuario.apellido)
        .order_by(func.count(Expediente.id).desc())
        .limit(5)
    )
    lawyer_result = await db.execute(lawyer_query)
    lawyer_data = lawyer_result.all()

    top_lawyers = [
        {
            "nombre": f"{l.nombre} {l.apellido}",
            "case_count": l.case_count
        }
        for l in lawyer_data
    ]

    return {
        "period": period,
        "date_range": {"start": str(start_date), "end": str(end_date)},
        "kpis": {
            "active_cases": active_cases or 0,
            "new_cases_period": new_cases_period or 0,
            "closed_cases_period": closed_cases_period or 0,
            "pending_deadlines": pending_deadlines or 0,
            "urgent_deadlines": urgent_deadlines or 0,
            "overdue_deadlines": overdue_deadlines or 0,
            "resolution_rate": resolution_rate,
            "docs_period": docs_period or 0,
            "active_clients": active_clients or 0,
            "total_cases": total_cases or 0,
        },
        "cases_by_ramo": cases_by_ramo,
        "status_distribution": status_distribution,
        "monthly_activity": monthly_activity,
        "priority_distribution": priority_distribution,
        "top_lawyers": top_lawyers,
    }
