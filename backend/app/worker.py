"""
LexIntellectus - Celery Worker Configuration
Handles asynchronous background tasks like sending emails and generating reports.
"""

import os
from celery import Celery

# Use the same Redis URL as the app cache, or a specific DB if preferred
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "lex_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.services.email_service", "app.services.deadline_service"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Managua",
    enable_utc=True,
)

from celery.schedules import crontab
import subprocess

@celery_app.task(name="app.worker.run_daily_backup")
def run_daily_backup():
    """Runs the daily encrypted postgres database backup and uploads it to MinIO."""
    script_path = "/app/database/backup.sh"
    if not os.path.exists(script_path):
        script_path = "./database/backup.sh" # fallback
        
    print(f"Executing automated encrypted backup from {script_path}...")
    try:
        result = subprocess.run(
            ["bash", script_path],
            capture_output=True,
            text=True,
            check=True
        )
        print("Backup complete!")
        return {"status": "success", "output": result.stdout}
    except subprocess.CalledProcessError as e:
        print(f"Backup failed! Code {e.returncode}")
        print("Error output:", e.stderr)
        return {"status": "error", "error": e.stderr}

celery_app.conf.beat_schedule = {
    'check-deadlines-every-day-morning': {
        'task': 'app.services.deadline_service.check_and_notify_deadlines',
        'schedule': crontab(hour=7, minute=0),  # Run every day at 7:00 AM
    },
    'run-daily-backup-midnight': {
        'task': 'app.worker.run_daily_backup',
        'schedule': crontab(hour=0, minute=0),  # Run every day at midnight
    },
}
