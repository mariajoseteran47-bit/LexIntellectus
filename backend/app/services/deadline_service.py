"""
LexIntellectus - Deadline Service
Background tasks to check for expiring deadlines (PlazoFatal) and trigger notifications.
"""

from datetime import date, timedelta
import asyncio
from sqlalchemy import select
from app.worker import celery_app
from app.core.database import async_session_maker
from app.models.case import PlazoFatal, Expediente
from app.models.user import Usuario
from app.services.email_service import send_email

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
                
        await session.commit()


@celery_app.task(name="app.services.deadline_service.check_and_notify_deadlines")
def check_and_notify_deadlines():
    """
    Synchronous wrapper for the async deadline checker.
    Executed daily by Celery Beat.
    """
    asyncio.run(_check_deadlines_async())
