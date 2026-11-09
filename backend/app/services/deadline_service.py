"""
LexIntellectus - Deadline Service
Background tasks to check for expiring deadlines (PlazoFatal) and trigger notifications,
plus the Nicaragua Procedural Deadline Calculator (CPCN Art. 129-135 & Ley 260 LOPJ).
"""

from datetime import date, timedelta
from typing import Dict, List, Optional, Any
import asyncio
from sqlalchemy import select
from app.worker import celery_app
from app.core.database import AsyncSessionLocal as async_session_maker
from app.models.case import PlazoFatal, Expediente
from app.models.user import Usuario
from app.services.email_service import send_email
from app.services.webhook_service import webhook_service


class NicaraguaProceduralCalculator:
    """
    Motor de Cómputo de Plazos Procesales para la República de Nicaragua.
    Aplica:
    - Art. 129-135 Código Procesal Civil de Nicaragua (Ley 902 - CPCN)
    - Art. 90 Ley Orgánica del Poder Judicial (Ley 260 - LOPJ)
    - Código del Trabajo y Ley 1118 (Feriados Nacionales y Locales)
    """

    FIXED_NATIONAL_HOLIDAYS: Dict[tuple[int, int], str] = {
        (1, 1): "Año Nuevo",
        (5, 1): "Día Internacional de los Trabajadores",
        (5, 30): "Día de las Madres Nicaragüenses (Ley 1118)",
        (7, 19): "Día de la Liberación Nacional",
        (9, 14): "Batalla de San Jacinto",
        (9, 15): "Día de la Independencia de Centroamérica",
        (12, 8): "Inmaculada Concepción de María",
        (12, 25): "Navidad",
    }

    MUNICIPAL_HOLIDAYS: Dict[str, Dict[tuple[int, int], str]] = {
        "managua": {
            (8, 1): "Bajada de Santo Domingo de Guzmán (Managua)",
            (8, 10): "Subida de Santo Domingo de Guzmán (Managua)",
        },
        "leon": {
            (9, 24): "Día de la Virgen de la Merced (León)",
        },
        "granada": {
            (8, 15): "Día de la Virgen de la Asunción (Granada)",
        },
        "masaya": {
            (9, 30): "Día de San Jerónimo (Masaya)",
        },
        "chinandega": {
            (7, 26): "Día de Santa Ana (Chinandega)",
        },
        "esteli": {
            (10, 7): "Día de la Virgen del Rosario (Estelí)",
        },
        "matagalpa": {
            (9, 24): "Día de la Virgen de la Merced (Matagalpa)",
        },
    }

    @staticmethod
    def compute_easter_sunday(year: int) -> date:
        """Calcula el Domingo de Pascua mediante el algoritmo de Meeus/Jones/Butcher."""
        a = year % 19
        b = year // 100
        c = year % 100
        d = b // 4
        e = b % 4
        f = (b + 8) // 25
        g = (b - f + 1) // 3
        h = (19 * a + b - d - g + 15) % 30
        i = c // 4
        k = c % 4
        l = (32 + 2 * e + 2 * i - h - k) % 7
        m = (a + 11 * h + 22 * l) // 451
        month = (h + l - 7 * m + 114) // 31
        day = ((h + l - 7 * m + 114) % 31) + 1
        return date(year, month, day)

    @classmethod
    def get_holidays_for_year(
        cls,
        year: int,
        municipio: str = "managua",
        incluir_vacaciones_judiciales: bool = True,
    ) -> Dict[date, str]:
        """Devuelve todos los días inhábiles oficiales del año indicado."""
        holidays: Dict[date, str] = {}

        # 1. Feriados nacionales fijos
        for (month, day), name in cls.FIXED_NATIONAL_HOLIDAYS.items():
            holidays[date(year, month, day)] = name

        # 2. Jueves y Viernes Santo (móviles)
        easter = cls.compute_easter_sunday(year)
        holidays[easter - timedelta(days=3)] = "Jueves Santo (Feriado Nacional)"
        holidays[easter - timedelta(days=2)] = "Viernes Santo (Feriado Nacional)"

        # 3. Feriados patronales municipales
        muni_key = (municipio or "managua").strip().lower()
        for (month, day), name in cls.MUNICIPAL_HOLIDAYS.get(muni_key, {}).items():
            holidays[date(year, month, day)] = name

        # 4. Vacaciones Judiciales CSJ (LOPJ Art. 90 / CPCN Art. 131)
        if incluir_vacaciones_judiciales:
            # Semana Santa completa (Lunes Santo a Sábado Santo)
            for offset in range(6, 0, -1):
                d = easter - timedelta(days=offset)
                if d not in holidays:
                    holidays[d] = "Suspensión Vacacional CSJ (Semana Santa)"
            # Vacaciones de Fin de Año (24 de diciembre al 6 de enero)
            for day_num in range(1, 7):
                d_jan = date(year, 1, day_num)
                if d_jan not in holidays:
                    holidays[d_jan] = "Suspensión Vacacional CSJ (Fin de Año / Epifanía)"
            for day_num in range(24, 32):
                d_dec = date(year, 12, day_num)
                if d_dec not in holidays:
                    holidays[d_dec] = "Suspensión Vacacional CSJ (Navidad y Fin de Año)"

        return holidays

    @classmethod
    def is_non_working_day(
        cls,
        target_date: date,
        municipio: str = "managua",
        incluir_vacaciones_judiciales: bool = True,
    ) -> Optional[str]:
        """Retorna el motivo si la fecha es inhábil, o None si es día hábil."""
        if target_date.weekday() == 5:
            return "Sábado (Inhábil Procesal CPCN Art. 131)"
        if target_date.weekday() == 6:
            return "Domingo (Inhábil Procesal CPCN Art. 131)"

        holidays = cls.get_holidays_for_year(
            target_date.year,
            municipio=municipio,
            incluir_vacaciones_judiciales=incluir_vacaciones_judiciales,
        )
        return holidays.get(target_date)

    @classmethod
    def calculate_due_date(
        cls,
        fecha_inicio: date,
        cantidad_dias: int,
        dias_tipo: str = "habiles",
        municipio: str = "managua",
        incluir_vacaciones_judiciales: bool = True,
    ) -> Dict[str, Any]:
        """
        Calcula la fecha de vencimiento legal comenzando a contar desde el día
        siguiente al de la notificación (Art. 132 CPCN: dies a quo non computatur in termino).
        """
        if cantidad_dias <= 0:
            raise ValueError("La cantidad de días debe ser mayor a 0")

        dias_excluidos: List[Dict[str, str]] = []
        dias_computados: List[str] = []
        current = fecha_inicio

        if dias_tipo == "calendario":
            for _ in range(cantidad_dias):
                current = current + timedelta(days=1)
                dias_computados.append(current.isoformat())
            # Art. 132 CPCN: Si el último día de un plazo calendario cae en inhábil, se prorroga al siguiente hábil
            while True:
                reason = cls.is_non_working_day(
                    current,
                    municipio=municipio,
                    incluir_vacaciones_judiciales=incluir_vacaciones_judiciales,
                )
                if not reason:
                    break
                dias_excluidos.append({
                    "fecha": current.isoformat(),
                    "motivo": f"Prórroga al siguiente día hábil ({reason})",
                })
                current = current + timedelta(days=1)
        else:
            counted = 0
            while counted < cantidad_dias:
                current = current + timedelta(days=1)
                reason = cls.is_non_working_day(
                    current,
                    municipio=municipio,
                    incluir_vacaciones_judiciales=incluir_vacaciones_judiciales,
                )
                if reason:
                    dias_excluidos.append({
                        "fecha": current.isoformat(),
                        "motivo": reason,
                    })
                else:
                    counted += 1
                    dias_computados.append(current.isoformat())

        return {
            "fecha_inicio": fecha_inicio.isoformat(),
            "fecha_vencimiento": current.isoformat(),
            "cantidad_dias": cantidad_dias,
            "dias_tipo": dias_tipo,
            "municipio": municipio,
            "incluir_vacaciones_judiciales": incluir_vacaciones_judiciales,
            "dias_computados": dias_computados,
            "dias_excluidos": dias_excluidos,
            "total_dias_calendario_transcurridos": (current - fecha_inicio).days,
            "base_legal_aplicada": (
                "Arts. 129-135 CPCN (Ley 902) y Art. 90 LOPJ (Ley 260): "
                "El cómputo inicia al día hábil siguiente de la notificación y excluye fines de semana, "
                "feriados nacionales/locales y vacaciones judiciales."
                if dias_tipo == "habiles"
                else "Art. 132 CPCN: Plazo en días calendario con prórroga automática si el vencimiento cae en día inhábil."
            ),
        }

async def _check_deadlines_async():
    today = date.today()
    in_3_days = today + timedelta(days=3)
    in_1_day = today + timedelta(days=1)
    
    async with async_session_maker() as session:
        # Find pending deadlines due in 3 days or 1 day
        query = select(PlazoFatal, Expediente, Usuario).join(
            Expediente, PlazoFatal.expediente_id == Expediente.id
        ).outerjoin(
            Usuario, PlazoFatal.usuario_responsable_id == Usuario.id
        ).where(
            PlazoFatal.status == 'pendiente',
            PlazoFatal.fecha_vencimiento.in_([in_3_days, in_1_day])
        )
        
        result = await session.execute(query)
        deadlines = result.all()
        
        for plazo, exp, user in deadlines:
            if not user or not user.email:
                continue
                
            days_left = (plazo.fecha_vencimiento - today).days
            
            # Check if we already sent the alert
            if days_left == 3 and plazo.alerta_72h_enviada:
                continue
            if days_left == 1 and plazo.alerta_24h_enviada:
                continue
                
            # Send email
            subject = f"Alerta de Vencimiento: {exp.numero_interno} - {plazo.descripcion}"
            html_content = f"""
            <h3>Recordatorio de Vencimiento de Plazo</h3>
            <p>Estimado/a {user.nombre} {user.apellido},</p>
            <p>El plazo <strong>{plazo.descripcion}</strong> para el expediente <strong>{exp.numero_interno} ({exp.juzgado})</strong> vence en {days_left} día(s).</p>
            <p><strong>Fecha de vencimiento:</strong> {plazo.fecha_vencimiento}</p>
            <p>Por favor, tome las acciones necesarias.</p>
            <br>
            <p>Saludos,<br>LexIntellectus</p>
            """
            
            # Queue email task
            send_email.delay(user.email, subject, html_content)
            
            # Update alert flags
            if days_left == 3:
                plazo.alerta_72h_enviada = True
            elif days_left == 1:
                plazo.alerta_24h_enviada = True

            await webhook_service.dispatch_event(
                db=session,
                tenant_id=exp.tenant_id,
                event_type="deadline.approaching",
                data={
                    "deadline_id": str(plazo.id),
                    "expediente_id": str(exp.id),
                    "numero_interno": exp.numero_interno,
                    "descripcion": plazo.descripcion,
                    "fecha_vencimiento": str(plazo.fecha_vencimiento),
                    "days_left": days_left,
                },
            )

        # Also check expired deadlines
        expired_query = select(PlazoFatal, Expediente).join(
            Expediente, PlazoFatal.expediente_id == Expediente.id
        ).where(
            PlazoFatal.status == 'pendiente',
            PlazoFatal.fecha_vencimiento < today
        )
        expired_res = await session.execute(expired_query)
        for plazo_exp, exp_obj in expired_res.all():
            plazo_exp.status = 'vencido'
            await webhook_service.dispatch_event(
                db=session,
                tenant_id=exp_obj.tenant_id,
                event_type="deadline.expired",
                data={
                    "deadline_id": str(plazo_exp.id),
                    "expediente_id": str(exp_obj.id),
                    "numero_interno": exp_obj.numero_interno,
                    "descripcion": plazo_exp.descripcion,
                    "fecha_vencimiento": str(plazo_exp.fecha_vencimiento),
                },
            )
                
        await session.commit()


@celery_app.task(name="app.services.deadline_service.check_and_notify_deadlines")
def check_and_notify_deadlines():
    """
    Synchronous wrapper for the async deadline checker.
    Executed daily by Celery Beat.
    """
    asyncio.run(_check_deadlines_async())
