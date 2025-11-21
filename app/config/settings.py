"""
Configuration settings for the application.
This module loads environment variables and provides configuration
settings for various components of the application.
"""

import os
from enum import Enum
from functools import lru_cache
from typing import Optional

from pydantic import BaseSettings, Field, SecretStr


class EnvironmentType(str, Enum):
    """Supported environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Environment variables are loaded from .env file if present.
    """
    # Application settings
    APP_NAME: str = "Payment API"
    ENVIRONMENT: EnvironmentType = Field(
        default=EnvironmentType.DEVELOPMENT,
        description="Application environment (development, staging, production)"
    )
    DEBUG: bool = Field(default=False, description="Debug mode flag")

    # Stripe settings
    STRIPE_API_KEY: SecretStr = Field(
        description="Stripe API key (secret key)"
    )
    STRIPE_PUBLIC_KEY: str = Field(
        description="Stripe publishable key"
    )
    STRIPE_WEBHOOK_SECRET: Optional[SecretStr] = Field(
        default=None,
        description="Stripe webhook secret for verifying webhook events"
    )

    class Config:
        """Configuration for the settings class."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    """
    Returns cached application settings.

    Using lru_cache to avoid loading .env file multiple times.
    """
    return Settings()