import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import date
from decimal import Decimal
import logging

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.config import settings
from app.models.user import Usuario
from app.models.billing import Factura
from app.models.integrations import PagoFactura
from app.services.payment_service import payment_service
from app.services.webhook_service import webhook_service
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


class BankTransferReportRequest(BaseModel):
    invoice_id: UUID
    banco_origen: str = Field(..., min_length=2, max_length=80)
    numero_referencia: str = Field(..., min_length=3, max_length=120)
    monto: Optional[float] = None
    notas: Optional[str] = None


async def _record_invoice_payment_and_webhooks(
    db: AsyncSession,
    invoice: Factura,
    metodo_pago: str,
    referencia_externa: str,
    plataforma_origen: str,
    notas: Optional[str] = None,
    monto_override: Optional[Decimal] = None,
) -> PagoFactura:
    """
    Registra el asiento de pago en `invoice_payments` (PagoFactura), actualiza el estado
    de la factura a 'pagada' y despacha los eventos de webhook 'payment.received' e 'invoice.paid'.
    """
    inv_id = invoice.id
    tenant_id = invoice.tenant_id
    inv_num = invoice.numero_factura
    inv_moneda = invoice.moneda or "NIO"
    monto_val = monto_override if monto_override is not None else Decimal(str(invoice.neto_a_pagar or invoice.total_factura or 0))

    pago = PagoFactura(
        tenant_id=tenant_id,
        factura_id=inv_id,
        monto=monto_val,
        moneda=inv_moneda,
        metodo_pago=metodo_pago,
        referencia_externa=referencia_externa,
        plataforma_origen=plataforma_origen,
        notas=notas,
        fecha_pago=date.today(),
    )
    db.add(pago)
    invoice.estado = "pagada"
    await db.commit()
    await db.refresh(pago)
    await db.refresh(invoice)

    pago_id_str = str(pago.id)
    try:
        await webhook_service.dispatch_event(
            db=db,
            tenant_id=tenant_id,
            event_type="payment.received",
            data={
                "payment_id": pago_id_str,
                "factura_id": str(inv_id),
                "numero_factura": inv_num,
                "monto": float(monto_val),
                "moneda": inv_moneda,
                "metodo_pago": metodo_pago,
                "plataforma_origen": plataforma_origen,
                "referencia_externa": referencia_externa,
            },
        )
        await webhook_service.dispatch_event(
            db=db,
            tenant_id=tenant_id,
            event_type="invoice.paid",
            data={
                "factura_id": str(inv_id),
                "numero_factura": inv_num,
                "estado": "pagada",
                "neto_a_pagar": float(monto_val),
                "moneda": inv_moneda,
                "plataforma_origen": plataforma_origen,
            },
        )
    except Exception as wh_err:
        logger.warning(f"Webhook dispatch warning after payment: {wh_err}")

    return pago


@router.post("/create-session")
async def create_payment_session(
    body: PaymentSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Create a payment session or order for Stripe or PayPal."""
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
            pago = await _record_invoice_payment_and_webhooks(
                db=db,
                invoice=invoice,
                metodo_pago="paypal",
                referencia_externa=body.order_id,
                plataforma_origen="paypal",
                notas="Pago en línea verificado vía PayPal Checkout",
            )
            return {
                "status": "success",
                "invoice_status": invoice.estado,
                "payment_id": str(pago.id),
            }
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

    if body.session_id.startswith("cs_test_mock_") or body.session_id == "mock_session_id":
        pago = await _record_invoice_payment_and_webhooks(
            db=db,
            invoice=invoice,
            metodo_pago="tarjeta",
            referencia_externa=body.session_id,
            plataforma_origen="stripe",
            notas="Pago con tarjeta procesado vía Stripe Checkout (Sandbox)",
        )
        return {
            "status": "success",
            "invoice_status": invoice.estado,
            "payment_id": str(pago.id),
            "is_mock": True,
        }

    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        session = stripe.checkout.Session.retrieve(body.session_id)

        if session.payment_status == "paid":
            pago = await _record_invoice_payment_and_webhooks(
                db=db,
                invoice=invoice,
                metodo_pago="tarjeta",
                referencia_externa=body.session_id,
                plataforma_origen="stripe",
                notas="Pago con tarjeta verificado vía Stripe Checkout",
            )
            return {
                "status": "success",
                "invoice_status": invoice.estado,
                "payment_id": str(pago.id),
                "is_mock": False,
            }
        else:
            return {"status": "pending", "payment_status": session.payment_status}
    except Exception as e:
        logger.error(f"Error verifying Stripe session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bank-transfer")
async def report_bank_transfer_payment(
    body: BankTransferReportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Registra un pago por transferencia bancaria o depósito directo desde el Portal del Cliente
    o desde el Backoffice del despacho.
    """
    query = select(Factura).where(
        Factura.id == body.invoice_id,
        Factura.tenant_id == current_user.tenant_id,
    )
    result = await db.execute(query)
    invoice = result.scalar_one_or_none()

    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    if current_user.tipo_usuario == "cliente" and invoice.client_id != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado para reportar pago de esta factura")

    if invoice.estado == "pagada":
        raise HTTPException(status_code=400, detail="La factura ya se encuentra pagada")

    monto_override = Decimal(str(body.monto)) if body.monto and body.monto > 0 else None
    notas_comp = f"Transferencia Bancaria ({body.banco_origen}) - Ref: {body.numero_referencia}"
    if body.notas:
        notas_comp += f" | {body.notas}"

    pago = await _record_invoice_payment_and_webhooks(
        db=db,
        invoice=invoice,
        metodo_pago="transferencia",
        referencia_externa=f"{body.banco_origen}:{body.numero_referencia}",
        plataforma_origen="portal_transferencia",
        notas=notas_comp,
        monto_override=monto_override,
    )

    return {
        "status": "success",
        "message": "Comprobante de transferencia bancaria registrado y aplicado con éxito.",
        "invoice_status": invoice.estado,
        "payment_id": str(pago.id),
        "referencia": body.numero_referencia,
        "banco": body.banco_origen,
    }


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
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session.get("metadata", {})
        invoice_id_str = metadata.get("invoice_id")

        if invoice_id_str:
            try:
                invoice_id = UUID(invoice_id_str)
                query = select(Factura).where(Factura.id == invoice_id)
                result = await db.execute(query)
                invoice = result.scalar_one_or_none()

                if invoice and invoice.estado != "pagada":
                    await _record_invoice_payment_and_webhooks(
                        db=db,
                        invoice=invoice,
                        metodo_pago="tarjeta",
                        referencia_externa=session.get("id", "stripe_webhook"),
                        plataforma_origen="stripe",
                        notas="Pago confirmado vía Stripe Webhook",
                    )
                    logger.info(f"Invoice {invoice_id} successfully marked as PAID via Stripe Webhook")
            except Exception as e:
                logger.error(f"Error handling checkout session in webhook: {str(e)}")

    return {"status": "success"}
