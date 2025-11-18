"""
Performance metrics models.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Union, Any

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

class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class AlertStatus(str, Enum):
    """Alert status types."""
    ACTIVE = "active"
    RESOLVED = "resolved"

class PerformanceAlert(BaseModel):
    """Model representing a performance alert."""
    id: str
    timestamp: datetime
    endpoint: str
    http_method: str
    severity: AlertSeverity
    status: AlertStatus
    current_value: float
    threshold_value: float
    deviation_percent: Optional[float] = None
    message: str
    resolved_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "alert-123456",
                "timestamp": "2025-11-17T10:00:00.123456",
                "endpoint": "/api/sample/heavy",
                "http_method": "GET",
                "severity": "warning",
                "status": "active",
                "current_value": 650.5,
                "threshold_value": 500.0,
                "deviation_percent": 30.1,
                "message": "Endpoint response time exceeded threshold by 30.1%",
                "resolved_at": None
            }
        }

class PerformanceReport(BaseModel):
    """Model representing a performance report."""
    report_id: str
    generated_at: datetime
    time_period: str  # e.g., "Last 24 hours", "Last hour"
    total_requests: int
    average_response_time: float
    top_slowest_endpoints: List[PerformanceStats] = Field(..., max_items=5)
    alerts_summary: Dict[AlertSeverity, int]  # Count of alerts by severity
    performance_summary: PerformanceSummary

    class Config:
        json_schema_extra = {
            "example": {
                "report_id": "report-123456",
                "generated_at": "2025-11-17T10:00:00.123456",
                "time_period": "Last 24 hours",
                "total_requests": 5000,
                "average_response_time": 45.7,
                "top_slowest_endpoints": [{"endpoint": "/api/sample/heavy", "http_method": "GET", "count": 50,
                                          "avg_duration_ms": 350.5, "min_duration_ms": 120.3, "max_duration_ms": 780.2}],
                "alerts_summary": {"info": 5, "warning": 2, "critical": 1},
                "performance_summary": {"total_requests": 5000, "endpoints": [], "last_updated": "2025-11-17T10:00:00.123456"}
            }
        }

class ExportFormat(str, Enum):
    """Export format types."""
    JSON = "json"
    CSV = "csv"

class ExportRequest(BaseModel):
    """Model for requesting an export of performance data."""
    format: ExportFormat
    time_period: Optional[str] = "24h"  # Default to last 24 hours
    include_alerts: bool = True
    endpoints: Optional[List[str]] = None  # Filter by specific endpoints, None means all

class ExportResponse(BaseModel):
    """Model for export operation response."""
    export_id: str
    format: ExportFormat
    file_name: str
    file_size: int
    download_url: str
    exported_at: datetime
    expires_at: Optional[datetime] = None
    record_count: int