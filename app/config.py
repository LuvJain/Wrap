"""
Configuration settings for the API application.
"""
from pydantic_settings import BaseSettings
from typing import Dict, List, Optional
import os
from datetime import timedelta
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

    # Performance retention in hours (24 hours by default)
    PERFORMANCE_DATA_RETENTION_HOURS: int = int(os.getenv("PERFORMANCE_DATA_RETENTION_HOURS", "24"))

    # Performance alerting configuration
    PERFORMANCE_ALERTING_ENABLED: bool = os.getenv("PERFORMANCE_ALERTING_ENABLED", "True").lower() in ("true", "1", "t")

    # Default threshold in milliseconds for alerting (endpoints exceeding this will trigger alerts)
    PERFORMANCE_THRESHOLD_MS: float = float(os.getenv("PERFORMANCE_THRESHOLD_MS", "500"))

    # Default deviation percentage for alerting (e.g., 20% means alert if 20% above baseline)
    PERFORMANCE_DEVIATION_PERCENT: float = float(os.getenv("PERFORMANCE_DEVIATION_PERCENT", "20"))

    # Custom thresholds for specific endpoints (overrides the default)
    # Format: {"endpoint_path": threshold_in_ms}
    PERFORMANCE_CUSTOM_THRESHOLDS: Dict[str, float] = {
        # Example: "/api/sample/heavy": 1000
    }

    # Export configuration
    PERFORMANCE_EXPORT_PATH: str = os.getenv("PERFORMANCE_EXPORT_PATH", "./exports")

settings = Settings()