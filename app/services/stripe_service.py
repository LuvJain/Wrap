"""
Stripe payment service module.

This module provides initialization and utility functions for interacting
with the Stripe API across different environments.
"""

import logging
from functools import lru_cache

import stripe

from app.config.settings import EnvironmentType, get_settings

# Configure logger for this module
logger = logging.getLogger(__name__)


class StripeService:
    """
    Stripe API service for handling payment operations.

    This service initializes Stripe API with the appropriate API key based on
    the current environment and provides utility functions for common Stripe
    operations.
    """

    def __init__(self):
        """
        Initialize Stripe API with settings from environment.
        """
        self.settings = get_settings()
        self.init_stripe()
        self.is_test_mode = self.settings.ENVIRONMENT != EnvironmentType.PRODUCTION
        logger.info(
            f"Stripe initialized in {'TEST' if self.is_test_mode else 'LIVE'} mode"
        )

    def init_stripe(self):
        """
        Initialize Stripe with API key from settings.
        """
        stripe.api_key = self.settings.STRIPE_API_KEY.get_secret_value()

        # Configure API version if needed
        # stripe.api_version = "2022-11-15"

        # Log API request telemetry for debugging in dev/staging
        if self.settings.ENVIRONMENT != EnvironmentType.PRODUCTION:
            stripe.log = 'info'

        # Set app info (optional but recommended by Stripe)
        stripe.set_app_info(
            self.settings.APP_NAME,
            version="0.1.0",
            url="https://yourdomain.com"
        )

    @property
    def public_key(self):
        """
        Get the appropriate publishable key for the current environment.
        """
        return self.settings.STRIPE_PUBLIC_KEY

    @property
    def webhook_secret(self):
        """
        Get the webhook secret if configured.
        """
        if self.settings.STRIPE_WEBHOOK_SECRET:
            return self.settings.STRIPE_WEBHOOK_SECRET.get_secret_value()
        return None

    def create_payment_intent(self, amount, currency="usd", metadata=None):
        """
        Create a Stripe PaymentIntent.

        Args:
            amount (int): Amount in smallest currency unit (e.g., cents for USD)
            currency (str, optional): Three-letter ISO currency code. Defaults to "usd".
            metadata (dict, optional): Additional metadata for the payment intent. Defaults to None.

        Returns:
            dict: The created PaymentIntent object.
        """
        try:
            return stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                metadata=metadata or {},
            )
        except stripe.error.StripeError as e:
            logger.error(f"Error creating payment intent: {str(e)}")
            raise

    def construct_event(self, payload, sig_header):
        """
        Construct and verify a Stripe webhook event.

        Args:
            payload (bytes): The request body from Stripe webhook.
            sig_header (str): The Stripe signature header.

        Returns:
            stripe.Event: The verified Stripe event.

        Raises:
            ValueError: If the webhook secret is not configured.
            stripe.error.SignatureVerificationError: If the signature verification fails.
        """
        if not self.webhook_secret:
            raise ValueError("Stripe webhook secret is not configured")

        try:
            return stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {str(e)}")
            raise


@lru_cache
def get_stripe_service() -> StripeService:
    """
    Factory function for StripeService with caching.

    Returns:
        StripeService: Initialized Stripe service singleton.
    """
    return StripeService()