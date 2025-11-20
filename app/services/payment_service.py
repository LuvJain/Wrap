import logging
import stripe
from functools import lru_cache
from typing import Dict, Any, List, Optional

from app.config.stripe_config import get_stripe_config
from app.utils.security import mask_sensitive_data

logger = logging.getLogger(__name__)

class PaymentService:
    """
    Service for handling Stripe payment operations.
    This demonstrates secure usage of the Stripe client.
    """
    def __init__(self):
        # Get the Stripe configuration singleton
        stripe_config = get_stripe_config()

        # Get the initialized Stripe client
        self.stripe = stripe_config.get_stripe_client()

        # Store the environment for logging purposes
        self.environment = stripe_config.environment

        # Store the public key for client-side operations
        self.public_key = stripe_config.public_key

        logger.info(f"Payment service initialized in {self.environment} environment")

    def create_payment_intent(self, amount: int, currency: str = "usd",
                             metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a PaymentIntent for a payment.

        Args:
            amount: Amount in smallest currency unit (e.g., cents for USD)
            currency: Three-letter ISO currency code
            metadata: Optional metadata to attach to the payment

        Returns:
            Created PaymentIntent object
        """
        try:
            # Create a new PaymentIntent
            intent = self.stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                metadata=metadata or {},
            )

            # Log success without exposing full intent details
            logger.info(
                f"Created PaymentIntent for {amount/100} {currency.upper()}, "
                f"ID: {intent.id}"
            )

            return intent

        except stripe.error.StripeError as e:
            # Log error without exposing sensitive details
            masked_error = mask_sensitive_data(str(e))
            logger.error(f"Stripe error creating PaymentIntent: {masked_error}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating PaymentIntent: {type(e).__name__}")
            raise

    def get_payment_method(self, payment_method_id: str) -> Dict[str, Any]:
        """
        Retrieve a payment method securely.

        Args:
            payment_method_id: The Stripe PaymentMethod ID

        Returns:
            PaymentMethod object
        """
        try:
            # Retrieve the PaymentMethod
            payment_method = self.stripe.PaymentMethod.retrieve(payment_method_id)

            # Log success without sensitive data
            logger.info(f"Retrieved PaymentMethod: {payment_method_id}")

            return payment_method

        except stripe.error.StripeError as e:
            # Log error without exposing sensitive details
            masked_error = mask_sensitive_data(str(e))
            logger.error(f"Stripe error retrieving PaymentMethod: {masked_error}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error retrieving PaymentMethod: {type(e).__name__}")
            raise

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify Stripe webhook signature.

        Args:
            payload: Raw request payload as bytes
            signature: Signature from Stripe-Signature header

        Returns:
            True if signature is valid
        """
        stripe_config = get_stripe_config()
        webhook_secret = stripe_config.credentials.webhook_secret

        if not webhook_secret:
            logger.warning("Webhook secret not configured, skipping signature verification")
            return False

        try:
            # Verify the event
            self.stripe.Webhook.construct_event(
                payload, signature, webhook_secret
            )
            return True
        except stripe.error.SignatureVerificationError:
            logger.warning("Invalid webhook signature")
            return False
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {type(e).__name__}")
            return False


@lru_cache()
def get_payment_service() -> PaymentService:
    """
    Get or create a PaymentService singleton.

    Returns:
        Initialized PaymentService instance
    """
    return PaymentService()