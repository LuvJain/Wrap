import os
import logging
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv
import stripe
from functools import lru_cache

# Load environment variables from .env file
load_dotenv()

class StripeCredentials(BaseModel):
    """Secure container for Stripe API credentials with validation."""
    public_key: str
    secret_key: str
    webhook_secret: Optional[str] = None
    api_version: Optional[str] = None

    @field_validator('public_key')
    @classmethod
    def validate_public_key(cls, v: str) -> str:
        if not v.startswith(('pk_test_', 'pk_live_')):
            raise ValueError("Invalid Stripe public key format")
        return v

    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if not v.startswith(('sk_test_', 'sk_live_')):
            raise ValueError("Invalid Stripe secret key format")
        return v

    @field_validator('webhook_secret')
    @classmethod
    def validate_webhook_secret(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.startswith('whsec_'):
            raise ValueError("Invalid Stripe webhook secret format")
        return v

    def __str__(self) -> str:
        # Override string representation to hide sensitive information
        return f"StripeCredentials(public_key='{self.public_key[:8]}...', secret_key='***', webhook_secret='***')"

    def __repr__(self) -> str:
        # Override repr to hide sensitive information
        return self.__str__()


class StripeConfig:
    """Configuration handler for Stripe API with environment switching."""
    def __init__(self, environment: Optional[str] = None):
        # Determine environment (default from .env or override)
        self.environment = environment or os.getenv("ENVIRONMENT", "development")

        # Validate environment
        if self.environment not in ["development", "production"]:
            logging.warning(f"Invalid environment: {self.environment}. Defaulting to development.")
            self.environment = "development"

        # Load appropriate credentials
        self.credentials = self._load_credentials()

        # Initialize Stripe client
        self._initialize_stripe()

    def _load_credentials(self) -> StripeCredentials:
        """Load Stripe credentials for current environment."""
        try:
            if self.environment == "development":
                credentials = StripeCredentials(
                    public_key=os.getenv("STRIPE_PUBLIC_KEY_DEV", ""),
                    secret_key=os.getenv("STRIPE_SECRET_KEY_DEV", ""),
                    webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET", None),
                    api_version=os.getenv("STRIPE_API_VERSION", None)
                )
                logging.info("Loaded Stripe development credentials")
            else:  # production
                credentials = StripeCredentials(
                    public_key=os.getenv("STRIPE_PUBLIC_KEY_PROD", ""),
                    secret_key=os.getenv("STRIPE_SECRET_KEY_PROD", ""),
                    webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET", None),
                    api_version=os.getenv("STRIPE_API_VERSION", None)
                )
                logging.info("Loaded Stripe production credentials")

            return credentials

        except ValueError as e:
            logging.error(f"Stripe credentials validation error: {str(e)}")
            raise

    def _initialize_stripe(self) -> None:
        """Initialize the Stripe client with current credentials."""
        try:
            # Configure Stripe with API key
            stripe.api_key = self.credentials.secret_key

            # Set API version if provided
            if self.credentials.api_version:
                stripe.api_version = self.credentials.api_version

            logging.info(f"Stripe client initialized for {self.environment} environment")
        except Exception as e:
            # Log error without exposing sensitive information
            logging.error(f"Failed to initialize Stripe client: {type(e).__name__}")
            raise

    def get_stripe_client(self):
        """Return the initialized Stripe client module."""
        return stripe

    @property
    def public_key(self) -> str:
        """Return the current public key (safe to expose)."""
        return self.credentials.public_key


@lru_cache()
def get_stripe_config() -> StripeConfig:
    """Cached singleton accessor for StripeConfig."""
    return StripeConfig()