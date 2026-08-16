import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
import logging

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.config import settings
from app.models.user import Usuario
from app.models.billing import Factura
from app.services.payment_service import payment_service
from app.core.rate_limit import default_rate_limiter

logger = logging.getLogger("payments_api")
router = APIRouter(prefix="/payments", tags=["Payments"], dependencies=[Depends(default_rate_limiter)])

class PaymentSessionCreate(BaseModel):
    invoice_id: UUID
    provider: str  # "stripe" or "paypal"

class PayPalCaptureRequest(BaseModel):
    order_id: str
    invoice_id: UUID

class StripeConfirmRequest(BaseModel):
    session_id: str
    invoice_id: UUID

@router.post("/create-session")
async def create_payment_session(
    body: PaymentSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Create a payment session or order for Stripe or PayPal."""
    # Fetch invoice
    query = select(Factura).options(selectinload(Factura.case)).where(
        Factura.id == body.invoice_id,
        Factura.tenant_id == current_user.tenant_id
    )
    result = await db.execute(query)
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Factura no encontrada"
        )

    # Security check: clients can only pay their own invoices
    if current_user.tipo_usuario == "cliente" and invoice.client_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene autorización para pagar esta factura"
        )

    if invoice.estado == "pagada":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La factura ya ha sido pagada"
        )

    provider = body.provider.lower()
    try:
        if provider == "stripe":
            session_data = await payment_service.create_stripe_checkout_session(invoice)
            return {
                "url": session_data["url"],
                "session_id": session_data["id"],
                "is_mock": session_data.get("is_mock", False),
                "provider": "stripe"
            }
        elif provider == "paypal":
            order_data = await payment_service.create_paypal_order(invoice)
            return {
                "url": order_data["url"],
                "order_id": order_data["id"],
                "is_mock": order_data.get("is_mock", False),
                "provider": "paypal"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Proveedor de pago no soportado. Use 'stripe' o 'paypal'."
            )
    except Exception as e:
        logger.error(f"Error creating payment session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/paypal-capture")
async def capture_paypal_payment(
    body: PayPalCaptureRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Capture a PayPal order to confirm payment and mark the invoice as paid."""
    query = select(Factura).where(
        Factura.id == body.invoice_id,
        Factura.tenant_id == current_user.tenant_id
    )
    result = await db.execute(query)
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    if current_user.tipo_usuario == "cliente" and invoice.client_id != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado")

    try:
        capture_result = await payment_service.capture_paypal_order(body.order_id)
        
        if capture_result.get("status") == "COMPLETED" or capture_result.get("is_mock"):
            invoice.estado = "pagada"
            await db.commit()
            await db.refresh(invoice)
            return {"status": "success", "invoice_status": invoice.estado}
        else:
            return {"status": "pending", "paypal_status": capture_result.get("status")}
    except Exception as e:
        logger.error(f"Error capturing PayPal payment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stripe-confirm")
async def confirm_stripe_payment(
    body: StripeConfirmRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Direct confirm endpoint for local development/fallback.
    Verifies Checkout session status and marks invoice as paid.
    """
    query = select(Factura).where(
        Factura.id == body.invoice_id,
        Factura.tenant_id == current_user.tenant_id
    )
    result = await db.execute(query)
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    if current_user.tipo_usuario == "cliente" and invoice.client_id != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado")

    # If mock session or valid session
    if body.session_id.startswith("cs_test_mock_") or body.session_id == "mock_session_id":
        invoice.estado = "pagada"
        await db.commit()
        await db.refresh(invoice)
        return {"status": "success", "invoice_status": invoice.estado, "is_mock": True}

    try:
        # Retrieve Stripe session
        stripe.api_key = settings.STRIPE_SECRET_KEY
        session = stripe.checkout.Session.retrieve(body.session_id)
        
        if session.payment_status == "paid":
            invoice.estado = "pagada"
            await db.commit()
            await db.refresh(invoice)
            return {"status": "success", "invoice_status": invoice.estado, "is_mock": False}
        else:
            return {"status": "pending", "payment_status": session.payment_status}
    except Exception as e:
        logger.error(f"Error verifying Stripe session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stripe-webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Production-ready Stripe webhook endpoint.
    Processes checkout.session.completed events to mark invoices as paid.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle completion event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session.get("metadata", {})
        invoice_id_str = metadata.get("invoice_id")
        
        if invoice_id_str:
            try:
                invoice_id = UUID(invoice_id_str)
                # Find invoice in DB
                query = select(Factura).where(Factura.id == invoice_id)
                result = await db.execute(query)
                invoice = result.scalar_one_or_none()
                
                if invoice:
                    invoice.estado = "pagada"
                    await db.commit()
                    logger.info(f"Invoice {invoice_id} successfully marked as PAID via Stripe Webhook")
            except Exception as e:
                logger.error(f"Error handling checkout session in webhook: {str(e)}")

    return {"status": "success"}
