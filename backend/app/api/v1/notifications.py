from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date, timedelta

from app.core.database import get_db
from app.core.dependencies import get_current_active_admin
from app.models.case import PlazoFatal, Expediente
from app.models.user import Usuario
from app.services.email import email_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.post("/check-deadlines")
async def check_deadlines(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    # current_user: Usuario = Depends(get_current_active_admin) # cron might need api key or local access
):
    """
    Check for deadlines approaching and send notifications.
    This endpoint should be called called by a cron job or scheduler daily.
    """
    today = date.today()
    in_3_days = today + timedelta(days=3)
    in_1_day = today + timedelta(days=1)
    
    # Logic to find deadlines
    # 1. Find deadlines due in 3 days that haven't had 72h alert sent
    query_72h = select(PlazoFatal).where(
        PlazoFatal.fecha_vencimiento == in_3_days,
        PlazoFatal.alerta_72h_enviada == False,
        PlazoFatal.status == "pendiente"
    )
    result_72h = await db.execute(query_72h)
    deadlines_72h = result_72h.scalars().all()
    
    for deadline in deadlines_72h:
        # Check explicit responsible or case responsible
        # For simplicity, we just log/mock send for now as strict responsible logic requires joins
        background_tasks.add_task(send_deadline_alert, deadline.id, "72 hours")
        # In real world, we would update alerta_72h_enviada = True here or in task
        
    return {"message": f"Checked deadlines. Found {len(deadlines_72h)} due in 72h."}

async def send_deadline_alert(deadline_id, timeframe):
    # This task would actually fetch the user email and send it
    # For MVP, we just rely on the service logging
    email_service.send_email(
        "lawyer@example.com", 
        f"Deadline approaching in {timeframe}", 
        f"Deadline {deadline_id} is due."
    )
