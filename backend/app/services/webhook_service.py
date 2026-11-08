"""
LexIntellectus - Outbound Webhook Dispatcher Service
Plan Estratégico Maestro v4.1 / Sprint 6 — API Pública + Webhooks
Handles HMAC-SHA256 signing, async delivery, exponential backoff retries,
and delivery audit logs for all 14 domain events.
"""

import asyncio
import hashlib
import hmac
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.integrations import (
    SUPPORTED_WEBHOOK_EVENTS,
    WebhookDeliveryLog,
    WebhookSubscription,
)

logger = logging.getLogger("webhook_service")


class WebhookService:
    """
    Service for signing and dispatching real-time webhook notifications
    to external ERP/accounting integrations.
    """

    @staticmethod
    def compute_signature(secret: str, payload_bytes: bytes) -> str:
        """
        Compute HMAC-SHA256 signature prefixed with 'sha256='.
        """
        digest = hmac.new(
            secret.encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()
        return f"sha256={digest}"

    @classmethod
    def verify_signature(cls, secret: str, payload_bytes: bytes, signature_header: str) -> bool:
        """
        Constant-time verification of X-LexIntellectus-Signature header.
        """
        if not signature_header:
            return False
        expected = cls.compute_signature(secret, payload_bytes)
        return hmac.compare_digest(expected, signature_header)

    async def _send_http_post(
        self,
        url: str,
        content: bytes,
        headers: Dict[str, str],
    ) -> tuple[int, str]:
        """Perform the outbound HTTP POST request to the external webhook receiver."""
        async with httpx.AsyncClient(timeout=8.0) as http_client:
            resp = await http_client.post(url, content=content, headers=headers)
            return resp.status_code, (resp.text or "")[:1000]

    async def deliver_single(
        self,
        db: AsyncSession,
        subscription: WebhookSubscription,
        event_type: str,
        data: Dict[str, Any],
        max_attempts: int = 3,
    ) -> WebhookDeliveryLog:
        """
        Sign and deliver an event payload to a single WebhookSubscription with retries.
        """
        delivery_id = uuid.uuid4()
        envelope = {
            "id": str(delivery_id),
            "event": event_type,
            "tenant_id": str(subscription.tenant_id),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data": data,
        }
        payload_bytes = json.dumps(envelope, default=str, separators=(",", ":"), sort_keys=True).encode("utf-8")
        signature = self.compute_signature(subscription.secret, payload_bytes)

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "LexIntellectus-Webhook/1.0",
            "X-LexIntellectus-Delivery": str(delivery_id),
            "X-LexIntellectus-Event": event_type,
            "X-LexIntellectus-Signature": signature,
        }

        response_status: Optional[int] = None
        response_body: Optional[str] = None
        success = False
        attempt = 0

        for attempt in range(1, max_attempts + 1):
            try:
                response_status, response_body = await self._send_http_post(
                    subscription.url,
                    payload_bytes,
                    headers,
                )
                if 200 <= response_status < 300:
                    success = True
                    break
            except Exception as exc:
                response_status = 0
                response_body = f"Connection error: {str(exc)[:500]}"
                logger.warning(
                    f"Webhook delivery attempt {attempt}/{max_attempts} failed for {subscription.url}: {exc}"
                )

            if attempt < max_attempts:
                await asyncio.sleep(0.2 * (2 ** (attempt - 1)))

        # Update subscription state
        subscription.last_triggered_at = datetime.utcnow()
        if success:
            subscription.failure_count = 0
        else:
            subscription.failure_count = (subscription.failure_count or 0) + 1

        log_entry = WebhookDeliveryLog(
            id=delivery_id,
            tenant_id=subscription.tenant_id,
            subscription_id=subscription.id,
            event_type=event_type,
            payload=envelope,
            signature=signature,
            response_status=response_status,
            response_body=response_body,
            attempt_count=attempt,
            success=success,
            delivered_at=datetime.utcnow(),
        )
        db.add(subscription)
        db.add(log_entry)
        await db.flush()
        return log_entry

    async def dispatch_event(
        self,
        db: AsyncSession,
        tenant_id: UUID,
        event_type: str,
        data: Dict[str, Any],
    ) -> List[WebhookDeliveryLog]:
        """
        Dispatch an event to all active subscriptions of the tenant that listen to event_type.
        """
        query = select(WebhookSubscription).where(
            WebhookSubscription.tenant_id == tenant_id,
            WebhookSubscription.activo == True,
        )
        result = await db.execute(query)
        subscriptions = result.scalars().all()

        logs: List[WebhookDeliveryLog] = []
        for sub in subscriptions:
            subscribed_events = sub.events or []
            if event_type in subscribed_events or "*" in subscribed_events:
                log_entry = await self.deliver_single(
                    db=db,
                    subscription=sub,
                    event_type=event_type,
                    data=data,
                    max_attempts=2,
                )
                logs.append(log_entry)

        if logs:
            await db.commit()
        return logs


webhook_service = WebhookService()
