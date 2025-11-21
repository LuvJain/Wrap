"""
Payment models for the application.
"""

from enum import Enum
from typing import Dict, Optional, Any

from pydantic import BaseModel, Field


class Currency(str, Enum):
    """Supported currency types."""
    USD = "usd"
    EUR = "eur"
    GBP = "gbp"
    CAD = "cad"
    AUD = "aud"
    JPY = "jpy"


class PaymentStatus(str, Enum):
    """Payment status values."""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class PaymentIntentRequest(BaseModel):
    """
    Data model for creating a payment intent.
    """
    amount: int = Field(..., description="Amount in smallest currency unit (e.g., cents for USD)")
    currency: Currency = Field(default=Currency.USD, description="Payment currency")
    description: Optional[str] = Field(default=None, description="Description of the payment")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata for the payment intent"
    )


class PaymentIntentResponse(BaseModel):
    """
    Data model for payment intent response.
    """
    id: str = Field(..., description="Stripe PaymentIntent ID")
    client_secret: str = Field(..., description="Client secret for payment confirmation")
    amount: int = Field(..., description="Amount in smallest currency unit")
    currency: str = Field(..., description="Payment currency")
    status: str = Field(..., description="PaymentIntent status")
    created: int = Field(..., description="Timestamp of creation")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class WebhookEvent(BaseModel):
    """
    Data model for webhook event processing.
    """
    id: str = Field(..., description="Stripe Event ID")
    type: str = Field(..., description="Event type")
    data: Dict[str, Any] = Field(..., description="Event data")
    created: int = Field(..., description="Timestamp of creation")