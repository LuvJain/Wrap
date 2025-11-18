"""
Configuration settings for the API application.
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Settings(BaseSettings):
    """Application settings"""
    APP_NAME: str = "API Performance Tracking Demo"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

    # Performance middleware configuration
    PERFORMANCE_METRICS_ENABLED: bool = True
    PERFORMANCE_METRICS_RETENTION: int = 1000  # Number of requests to keep in memory
    PERFORMANCE_LOG_LEVEL: str = "INFO"

settings = Settings()