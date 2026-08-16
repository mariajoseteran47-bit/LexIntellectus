import httpx
import stripe
import uuid
import logging
from typing import Optional, Dict, Any
from app.core.config import settings
from app.models.billing import Factura

logger = logging.getLogger("payment_service")

class PaymentService:
    """Service to handle Stripe Checkout and PayPal Sandbox integrations with standard sandbox test fallbacks."""

    def __init__(self):
        # Configure Stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY

    def is_stripe_placeholder(self) -> bool:
        return settings.STRIPE_SECRET_KEY.startswith("mock_stripe") or settings.STRIPE_SECRET_KEY == "placeholder"

    def is_paypal_placeholder(self) -> bool:
        return settings.PAYPAL_CLIENT_ID.startswith("placeholder") or settings.PAYPAL_CLIENT_SECRET.startswith("placeholder")

    async def create_stripe_checkout_session(self, invoice: Factura) -> Dict[str, Any]:
        """
        Creates a Stripe Checkout Session for the invoice.
        If Stripe credentials are placeholders, it falls back to a sandbox mockup flow.
        """
        if self.is_stripe_placeholder():
            logger.info(f"Stripe credentials are placeholders. Generating Mock Stripe session for invoice {invoice.id}")
            # Mock redirect URL that simulates successful payment redirection back to our frontend billing page
            mock_session_id = f"cs_test_{uuid.uuid4()}"
            return {
                "id": mock_session_id,
                "url": f"http://localhost:3000/portal/billing?status=success&provider=stripe&session_id={mock_session_id}&invoice_id={invoice.id}&mock=true",
                "is_mock": True
            }

        try:
            # Neto a pagar must be in cents. Make sure we round to integer.
            amount_in_cents = int(round(invoice.neto_a_pagar * 100))
            
            # Default currency is NIO, but Stripe doesn't support NIO natively in all countries.
            # In test mode we default to USD if not supported, but let's pass down whatever currency is on the invoice.
            # Usually legal portals in Nicaragua use USD or NIO (converted). Stripe supports NIO but depends on account setup.
            currency = invoice.moneda.lower()

            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': currency,
                        'product_data': {
                            'name': f"Factura {invoice.numero_factura}",
                            'description': f"Servicios Legales - LexIntellectus. Caso: {invoice.case.numero_causa if invoice.case else 'General'}",
                        },
                        'unit_amount': amount_in_cents,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=f"http://localhost:3000/portal/billing?status=success&provider=stripe&session_id={{CHECKOUT_SESSION_ID}}&invoice_id={invoice.id}",
                cancel_url="http://localhost:3000/portal/billing?status=cancel",
                metadata={
                    "invoice_id": str(invoice.id),
                    "tenant_id": str(invoice.tenant_id)
                }
            )
            return {
                "id": session.id,
                "url": session.url,
                "is_mock": False
            }
        except Exception as e:
            logger.error(f"Error creating Stripe checkout session: {str(e)}")
            raise Exception(f"Error al crear sesión de pago en Stripe: {str(e)}")

    async def get_paypal_access_token(self) -> str:
        """Fetch an access token from the PayPal Sandbox endpoint."""
        url = "https://api-m.sandbox.paypal.com/v1/oauth2/token"
        headers = {
            "Accept": "application/json",
            "Accept-Language": "en_US",
        }
        data = {"grant_type": "client_credentials"}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=headers,
                data=data,
                auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET),
                timeout=10.0
            )
            if response.status_code != 200:
                logger.error(f"Failed to get PayPal token: {response.text}")
                raise Exception("Error al autenticar con PayPal Sandbox")
            
            return response.json()["access_token"]

    async def create_paypal_order(self, invoice: Factura) -> Dict[str, Any]:
        """
        Creates a PayPal Order for Sandbox payment.
        Falls back to a sandbox mockup flow if PayPal keys are placeholders.
        """
        if self.is_paypal_placeholder():
            logger.info(f"PayPal credentials are placeholders. Generating Mock PayPal order for invoice {invoice.id}")
            mock_order_id = f"PAY-MOCK-{uuid.uuid4().hex[:12].upper()}"
            approve_url = f"http://localhost:3000/portal/billing?status=success&provider=paypal&order_id={mock_order_id}&invoice_id={invoice.id}&mock=true"
            return {
                "id": mock_order_id,
                "url": approve_url,
                "is_mock": True
            }

        try:
            access_token = await self.get_paypal_access_token()
            url = "https://api-m.sandbox.paypal.com/v2/checkout/orders"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
                "Prefer": "return=representation"
            }
            
            # PayPal currency code support (NIO isn't standard in PayPal, so we convert/default to USD or use the invoice currency)
            # PayPal supports standard currencies like USD, EUR, etc. If currency is NIO, let's treat it as USD in Sandbox for testing,
            # or pass it along if the user has custom setup. Standard Sandbox requires USD. Let's do a safe conversion or log warning.
            currency = invoice.moneda
            amount_val = str(invoice.neto_a_pagar)
            if currency == "NIO":
                # In sandbox, PayPal does not support NIO. Let's convert to USD at a mock rate of 36.8 NIO/USD for testing convenience.
                logger.warning("PayPal does not support NIO in Sandbox. Simulating conversion to USD (1 USD = 36.8 NIO)")
                currency = "USD"
                amount_val = f"{round(invoice.neto_a_pagar / 36.8, 2):.2f}"

            body = {
                "intent": "CAPTURE",
                "purchase_units": [{
                    "reference_id": str(invoice.id),
                    "amount": {
                        "currency_code": currency,
                        "value": amount_val
                    },
                    "description": f"Factura {invoice.numero_factura} - LexIntellectus"
                }],
                "application_context": {
                    "brand_name": "LexIntellectus ERP",
                    "landing_page": "BILLING",
                    "user_action": "PAY_NOW",
                    "return_url": f"http://localhost:3000/portal/billing?status=success&provider=paypal&invoice_id={invoice.id}",
                    "cancel_url": "http://localhost:3000/portal/billing?status=cancel"
                }
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=body, timeout=10.0)
                if response.status_code not in (200, 201):
                    logger.error(f"PayPal order creation failed: {response.text}")
                    raise Exception(f"PayPal error: {response.text}")
                
                order_data = response.json()
                order_id = order_data["id"]
                
                # Extract approve link
                approve_url = None
                for link in order_data.get("links", []):
                    if link["rel"] == "approve":
                        approve_url = link["href"]
                        break
                
                if not approve_url:
                    approve_url = f"http://localhost:3000/portal/billing?status=success&provider=paypal&order_id={order_id}&invoice_id={invoice.id}"

                return {
                    "id": order_id,
                    "url": approve_url,
                    "is_mock": False
                }
        except Exception as e:
            logger.error(f"Error creating PayPal order: {str(e)}")
            raise Exception(f"Error al crear orden de pago en PayPal: {str(e)}")

    async def capture_paypal_order(self, order_id: str) -> Dict[str, Any]:
        """Capture a PayPal order to confirm payment."""
        if order_id.startswith("PAY-MOCK-"):
            return {"status": "COMPLETED", "is_mock": True}

        try:
            access_token = await self.get_paypal_access_token()
            url = f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{order_id}/capture"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json={}, timeout=10.0)
                if response.status_code not in (200, 201):
                    logger.error(f"PayPal order capture failed: {response.text}")
                    raise Exception(f"PayPal capture error: {response.text}")
                
                capture_data = response.json()
                return {
                    "status": capture_data.get("status"),
                    "id": order_id,
                    "is_mock": False
                }
        except Exception as e:
            logger.error(f"Error capturing PayPal order {order_id}: {str(e)}")
            raise Exception(f"Error al capturar orden de pago de PayPal: {str(e)}")

payment_service = PaymentService()
