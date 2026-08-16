"""
LexIntellectus - Email Service
Integration for sending emails via SMTP.
Functions are registered as Celery tasks for background processing.
"""

import smtplib
import os
from email.message import EmailMessage
from app.worker import celery_app

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "noreply@lexintellectus.com")

@celery_app.task(name="app.services.email_service.send_email")
def send_email(to_email: str, subject: str, html_content: str):
    """
    Sends an email synchronously. Designed to be run by Celery.
    """
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        print(f"[Email Service] Simulating email to {to_email} (No SMTP credentials)")
        print(f"Subject: {subject}\nContent:\n{html_content}")
        return True

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email
    msg.set_content(html_content, subtype='html')

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"[Email Service] Error sending email to {to_email}: {str(e)}")
        # In a real app we might retry using Celery's autoretry_for
        return False
