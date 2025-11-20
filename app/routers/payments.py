import logging
from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

from app.services.payment_service import get_payment_service, PaymentService
from app.config.stripe_config import get_stripe_config
from app.utils.security import mask_sensitive_data

router = APIRouter()
logger = logging.getLogger(__name__)

# Models for payment-related requests and responses
class PaymentIntentRequest(BaseModel):
    amount: int = Field(..., gt=0, description="Amount in cents")
    currency: str = Field(default="usd", min_length=3, max_length=3, description="Currency code (3 letters)")
    metadata: Optional[Dict[str, str]] = Field(default=None, description="Optional metadata")

class PaymentIntentResponse(BaseModel):
    id: str
    client_secret: str
    amount: int
    currency: str
    status: str

class ConfigResponse(BaseModel):
    """Public configuration for client-side use"""
    public_key: str
    environment: str

@router.get("/config")
async def get_payment_config() -> ConfigResponse:
    """
    Get public payment configuration for client-side integration.
    Only exposes non-sensitive configuration.
    """
    stripe_config = get_stripe_config()

    return ConfigResponse(
        public_key=stripe_config.public_key,
        environment=stripe_config.environment
    )

@router.post("/create-payment-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    request: PaymentIntentRequest,
    payment_service: PaymentService = Depends(get_payment_service)
) -> Dict[str, Any]:
    """
    Create a payment intent for processing a payment.
    """
    try:
        # Log the sanitized request
        logger.info(f"Creating payment intent for: {request.amount/100} {request.currency.upper()}")

        # Create the payment intent via the service
        intent = payment_service.create_payment_intent(
            amount=request.amount,
            currency=request.currency,
            metadata=request.metadata
        )

        # Return only necessary fields for client-side use
        return {
            "id": intent.id,
            "client_secret": intent.client_secret,
            "amount": intent.amount,
            "currency": intent.currency,
            "status": intent.status
        }

    except Exception as e:
        # Log the error with sensitive data masked
        logger.error(f"Error creating payment intent: {mask_sensitive_data(str(e))}")
        # Re-raise as HTTP exception
        raise HTTPException(status_code=400, detail="Failed to create payment intent")

@router.post("/webhooks")
async def handle_stripe_webhook(request: Request):
    """
    Handle incoming Stripe webhooks.
    """
    payment_service = get_payment_service()

    # Get the signature from headers
    signature = request.headers.get("stripe-signature", "")

    # Get the raw request body as bytes
    payload = await request.body()

    # Verify the webhook signature
    if not signature or not payment_service.verify_webhook_signature(payload, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Process the event
    try:
        # Parse the webhook event
        stripe_config = get_stripe_config()
        stripe = stripe_config.get_stripe_client()
        event = stripe.Event.construct_from(
            await request.json(),
            stripe_config.credentials.secret_key
        )

        # Log the event type (safe to log)
        logger.info(f"Processing Stripe webhook: {event.type}")

        # Handle different event types
        if event.type == "payment_intent.succeeded":
            payment_intent = event.data.object
            logger.info(f"Payment succeeded: {payment_intent.id}")
            # Process the successful payment

        elif event.type == "payment_intent.payment_failed":
            payment_intent = event.data.object
            logger.info(f"Payment failed: {payment_intent.id}")
            # Handle the failed payment

        # Return a success response
        return {"success": True}

    except Exception as e:
        # Log the error with sensitive data masked
        logger.error(f"Error processing webhook: {mask_sensitive_data(str(e))}")
        # Re-raise as HTTP exception
        raise HTTPException(status_code=400, detail="Failed to process webhook")