"""
API routes for accessing performance metrics, reports, and alerts.
"""
from fastapi import APIRouter, Query, Path, Body, HTTPException, Response, Depends, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from typing import List, Optional, Dict, Union
from datetime import datetime, timedelta
import os
import json

from app.middleware.performance import performance_store
from app.config import settings
from app.models.performance import (
    RequestMetric, PerformanceStats, PerformanceSummary,
    PerformanceAlert, AlertSeverity, AlertStatus, PerformanceReport,
    ExportFormat, ExportRequest, ExportResponse
)

router = APIRouter(prefix="/api/performance", tags=["performance"])

# --- Metrics Endpoints ---

@router.get("/metrics", response_model=List[RequestMetric])
async def get_metrics(
    limit: Optional[int] = Query(50, ge=1, le=1000),
    hours: Optional[int] = Query(None, ge=1, le=72, description="Get metrics from the last X hours")
):
    """
    Get the most recent API request performance metrics.

    Args:
        limit: Maximum number of metrics to return (default: 50, max: 1000)
        hours: Get metrics from the last X hours (optional)

    Returns:
        List of request metrics, most recent first
    """
    since = None
    if hours:
        since = datetime.now() - timedelta(hours=hours)

    return performance_store.get_metrics(limit=limit, since=since)

@router.get("/stats", response_model=PerformanceSummary)
async def get_stats(
    hours: Optional[int] = Query(None, ge=1, le=72, description="Get statistics from the last X hours")
):
    """
    Get aggregated performance statistics.

    Args:
        hours: Get statistics from the last X hours (optional)

    Returns:
        Summary of performance metrics
    """
    since = None
    if hours:
        since = datetime.now() - timedelta(hours=hours)

    return performance_store.get_stats(since=since)

@router.delete("/metrics", status_code=204)
async def clear_metrics():
    """
    Clear all stored performance metrics.

    Returns:
        204 No Content
    """
    performance_store.clear()
    return None

# --- Alert Endpoints ---

@router.get("/alerts", response_model=List[PerformanceAlert])
async def get_alerts(
    status: Optional[AlertStatus] = Query(None, description="Filter alerts by status"),
    severity: Optional[AlertSeverity] = Query(None, description="Filter alerts by severity"),
    hours: Optional[int] = Query(None, ge=1, le=72, description="Get alerts from the last X hours"),
    limit: Optional[int] = Query(50, ge=1, le=1000, description="Maximum number of alerts to return")
):
    """
    Get performance alerts with optional filtering.

    Args:
        status: Filter alerts by status (active or resolved)
        severity: Filter alerts by severity (info, warning, critical)
        hours: Get alerts from the last X hours
        limit: Maximum number of alerts to return

    Returns:
        List of performance alerts, most recent first
    """
    since = None
    if hours:
        since = datetime.now() - timedelta(hours=hours)

    return performance_store.get_alerts(
        status=status,
        severity=severity,
        since=since,
        limit=limit
    )

@router.patch("/alerts/{alert_id}/resolve", response_model=PerformanceAlert)
async def resolve_alert(alert_id: str = Path(..., description="The ID of the alert to resolve")):
    """
    Mark an alert as resolved.

    Args:
        alert_id: The ID of the alert to resolve

    Returns:
        The resolved alert

    Raises:
        HTTPException: If the alert is not found or already resolved
    """
    alert = performance_store.resolve_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found or already resolved")
    return alert

# --- Report Endpoints ---

@router.post("/reports", response_model=PerformanceReport)
async def generate_report(
    time_period: str = Query("24h", description="Time period for the report (e.g., '24h', '12h', '6h')")
):
    """
    Generate a new performance report.

    Args:
        time_period: Time period for the report, in hours with 'h' suffix

    Returns:
        The generated performance report
    """
    return performance_store.generate_report(time_period=time_period)

@router.get("/reports", response_model=List[PerformanceReport])
async def get_reports(
    limit: Optional[int] = Query(10, ge=1, le=100, description="Maximum number of reports to return")
):
    """
    Get all generated reports.

    Args:
        limit: Maximum number of reports to return

    Returns:
        List of reports, newest first
    """
    return performance_store.get_reports(limit=limit)

@router.get("/reports/{report_id}", response_model=PerformanceReport)
async def get_report(report_id: str = Path(..., description="The ID of the report to retrieve")):
    """
    Get a specific report by ID.

    Args:
        report_id: The ID of the report to retrieve

    Returns:
        The requested performance report

    Raises:
        HTTPException: If the report is not found
    """
    report = performance_store.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

# --- Export Endpoints ---

@router.post("/exports", response_model=ExportResponse)
async def export_metrics(export_request: ExportRequest = Body(...)):
    """
    Export performance metrics to JSON or CSV format.

    Args:
        export_request: Export configuration

    Returns:
        Export response with file details
    """
    return performance_store.export_metrics(
        format_type=export_request.format,
        time_period=export_request.time_period,
        include_alerts=export_request.include_alerts,
        endpoints=export_request.endpoints
    )

@router.get("/exports/{export_id}", response_model=ExportResponse)
async def get_export(export_id: str = Path(..., description="The ID of the export")):
    """
    Get details about a specific export.

    Args:
        export_id: The ID of the export

    Returns:
        Export response with file details

    Raises:
        HTTPException: If the export is not found
    """
    export = performance_store.get_export(export_id)
    if not export:
        raise HTTPException(status_code=404, detail="Export not found")
    return export

@router.get("/exports/{export_id}/download")
async def download_export(export_id: str = Path(..., description="The ID of the export")):
    """
    Download an exported file.

    Args:
        export_id: The ID of the export

    Returns:
        The exported file as a download

    Raises:
        HTTPException: If the export is not found or the file doesn't exist
    """
    export = performance_store.get_export(export_id)
    if not export:
        raise HTTPException(status_code=404, detail="Export not found")

    file_path = os.path.join(settings.PERFORMANCE_EXPORT_PATH, export.file_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Export file not found")

    media_type = "application/json" if export.format == ExportFormat.JSON else "text/csv"
    return FileResponse(
        path=file_path,
        filename=export.file_name,
        media_type=media_type
    )

# --- Configuration Endpoints ---

@router.get("/config", response_model=Dict)
async def get_performance_config():
    """
    Get the current performance configuration settings.

    Returns:
        Dictionary of performance configuration settings
    """
    return {
        "metrics_enabled": settings.PERFORMANCE_METRICS_ENABLED,
        "metrics_retention": settings.PERFORMANCE_METRICS_RETENTION,
        "data_retention_hours": settings.PERFORMANCE_DATA_RETENTION_HOURS,
        "alerting_enabled": settings.PERFORMANCE_ALERTING_ENABLED,
        "threshold_ms": settings.PERFORMANCE_THRESHOLD_MS,
        "deviation_percent": settings.PERFORMANCE_DEVIATION_PERCENT,
        "custom_thresholds": settings.PERFORMANCE_CUSTOM_THRESHOLDS,
        "export_path": settings.PERFORMANCE_EXPORT_PATH
    }