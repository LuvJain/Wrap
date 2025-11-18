"""
Performance metrics models.
"""
from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Optional

class RequestMetric(BaseModel):
    """Model representing a single API request performance metric."""
    timestamp: datetime
    endpoint: str
    http_method: str
    duration_ms: float
    status_code: int

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-11-17T10:00:00.123456",
                "endpoint": "/api/v1/items",
                "http_method": "GET",
                "duration_ms": 42.5,
                "status_code": 200
            }
        }

class PerformanceStats(BaseModel):
    """Model representing aggregate performance statistics."""
    endpoint: str
    http_method: str
    count: int
    avg_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    p95_duration_ms: Optional[float] = None
    p99_duration_ms: Optional[float] = None

    class Config:
        json_schema_extra = {
            "example": {
                "endpoint": "/api/v1/items",
                "http_method": "GET",
                "count": 100,
                "avg_duration_ms": 45.7,
                "min_duration_ms": 12.3,
                "max_duration_ms": 150.2,
                "p95_duration_ms": 98.5,
                "p99_duration_ms": 130.1
            }
        }

class PerformanceSummary(BaseModel):
    """Model representing a summary of performance metrics."""
    total_requests: int
    endpoints: List[PerformanceStats]
    last_updated: datetime