"""
Middleware for tracking API request performance.

This middleware captures:
- Total request processing time
- Performance metrics for each API endpoint
- Metrics include timestamp, endpoint, duration, and HTTP method
- In-memory storage with configurable retention
- Performance reporting and alerting
- JSON and CSV export capabilities
"""
import time
import logging
import uuid
import os
import json
import csv
from io import StringIO
from collections import deque, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Callable, Optional, Deque, Set, Tuple, Any, Union
from fastapi import Request, Response
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from app.config import settings
from app.models.performance import (
    RequestMetric, PerformanceStats, PerformanceSummary,
    PerformanceAlert, AlertSeverity, AlertStatus, PerformanceReport,
    ExportFormat, ExportResponse
)

# Configure logging
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(settings.PERFORMANCE_LOG_LEVEL)

class PerformanceStore:
    """In-memory storage for API performance metrics with configurable retention and alerting."""

    def __init__(self, max_size: int = settings.PERFORMANCE_METRICS_RETENTION):
        """
        Initialize the performance store.

        Args:
            max_size: Maximum number of metrics to keep in memory
        """
        self.metrics: Deque[RequestMetric] = deque(maxlen=max_size)
        self.max_size = max_size
        self.endpoint_stats: Dict[str, Dict[str, List[float]]] = {}  # {endpoint: {method: [durations]}}
        self.endpoint_baselines: Dict[str, Dict[str, float]] = {}  # {endpoint: {method: baseline_duration_ms}}
        self.alerts: List[PerformanceAlert] = []
        self.reports: Dict[str, PerformanceReport] = {}  # {report_id: report}
        self.exports: Dict[str, ExportResponse] = {}  # {export_id: export_response}

        # Create exports directory if it doesn't exist
        os.makedirs(settings.PERFORMANCE_EXPORT_PATH, exist_ok=True)

    def add_metric(self, metric: RequestMetric) -> None:
        """
        Add a new performance metric to the store and check for potential alerts.

        Args:
            metric: The request metric to add
        """
        # Add metric to the queue
        self.metrics.append(metric)

        # Update endpoint statistics
        endpoint_key = f"{metric.endpoint}"
        method_key = metric.http_method

        if endpoint_key not in self.endpoint_stats:
            self.endpoint_stats[endpoint_key] = {}

        if method_key not in self.endpoint_stats[endpoint_key]:
            self.endpoint_stats[endpoint_key][method_key] = []

        self.endpoint_stats[endpoint_key][method_key].append(metric.duration_ms)

        # Clean old metrics (older than 24 hours)
        self._clean_old_metrics()

        # Calculate or update baseline
        if settings.PERFORMANCE_ALERTING_ENABLED:
            self._update_endpoint_baseline(endpoint_key, method_key)

            # Check for potential performance issues
            self._check_for_alerts(metric)

    def get_metrics(self, limit: Optional[int] = None,
                   since: Optional[datetime] = None) -> List[RequestMetric]:
        """
        Get the most recent metrics, optionally filtered by time.

        Args:
            limit: Maximum number of metrics to return (default: all)
            since: Only return metrics after this time

        Returns:
            List of request metrics, most recent first
        """
        metrics_list = list(self.metrics)
        metrics_list.reverse()  # Most recent first

        if since:
            metrics_list = [m for m in metrics_list if m.timestamp >= since]

        if limit:
            return metrics_list[:limit]
        return metrics_list

    def get_stats(self, since: Optional[datetime] = None) -> PerformanceSummary:
        """
        Get aggregated performance statistics, optionally filtered by time.

        Args:
            since: Only include metrics after this time

        Returns:
            Summary of performance metrics
        """
        stats = []

        # Get recent metrics if 'since' is specified
        recent_metrics = self.get_metrics(since=since) if since else None

        # Build endpoint metrics map if filtering by time
        endpoint_method_map = {}
        if since:
            for metric in recent_metrics:
                key = (metric.endpoint, metric.http_method)
                if key not in endpoint_method_map:
                    endpoint_method_map[key] = []
                endpoint_method_map[key].append(metric.duration_ms)

        # Process each endpoint and method
        for endpoint, methods in self.endpoint_stats.items():
            for method, durations in methods.items():
                # Use filtered durations if 'since' is specified
                if since:
                    key = (endpoint, method)
                    if key in endpoint_method_map:
                        durations = endpoint_method_map[key]
                    else:
                        continue  # Skip if no recent data for this endpoint/method

                if durations:
                    sorted_durations = sorted(durations)
                    count = len(durations)

                    # Calculate percentiles if we have enough data
                    p95 = p99 = None
                    if count >= 20:
                        p95_idx = int(count * 0.95)
                        p95 = sorted_durations[p95_idx]

                        p99_idx = int(count * 0.99)
                        p99 = sorted_durations[p99_idx]

                    stats.append(PerformanceStats(
                        endpoint=endpoint,
                        http_method=method,
                        count=count,
                        avg_duration_ms=sum(durations) / count,
                        min_duration_ms=sorted_durations[0],
                        max_duration_ms=sorted_durations[-1],
                        p95_duration_ms=p95,
                        p99_duration_ms=p99
                    ))

        return PerformanceSummary(
            total_requests=sum(s.count for s in stats),
            endpoints=stats,
            last_updated=datetime.now()
        )

    def clear(self) -> None:
        """Clear all stored metrics, but retain alerts and reports."""
        self.metrics.clear()
        self.endpoint_stats.clear()
        self.endpoint_baselines.clear()

    def _clean_old_metrics(self) -> None:
        """Remove metrics older than the retention period (24 hours)."""
        retention_cutoff = datetime.now() - timedelta(hours=settings.PERFORMANCE_DATA_RETENTION_HOURS)

        # Remove old metrics from the deque
        # Since deque doesn't support filtering directly, we need to rebuild it
        current_metrics = list(self.metrics)
        new_metrics = [m for m in current_metrics if m.timestamp >= retention_cutoff]

        # Clear and repopulate the deque
        self.metrics.clear()
        for metric in new_metrics:
            self.metrics.append(metric)

        # Update endpoint stats to remove old data
        for endpoint in self.endpoint_stats:
            for method in self.endpoint_stats[endpoint]:
                # We don't have timestamps in the endpoint_stats, so we can't easily filter
                # Instead, ensure we don't exceed the max size
                if len(self.endpoint_stats[endpoint][method]) > self.max_size:
                    self.endpoint_stats[endpoint][method] = \
                        self.endpoint_stats[endpoint][method][-self.max_size:]

    def _update_endpoint_baseline(self, endpoint: str, method: str) -> None:
        """
        Update the baseline performance for an endpoint.

        Args:
            endpoint: The endpoint path
            method: The HTTP method
        """
        durations = self.endpoint_stats[endpoint][method]
        if not durations or len(durations) < 10:
            # Not enough data to establish a reliable baseline
            return

        # Initialize the baseline dictionary if needed
        if endpoint not in self.endpoint_baselines:
            self.endpoint_baselines[endpoint] = {}

        # Calculate the baseline as the average of recent durations
        avg_duration = sum(durations) / len(durations)
        self.endpoint_baselines[endpoint][method] = avg_duration

    def _check_for_alerts(self, metric: RequestMetric) -> None:
        """
        Check if the given metric exceeds thresholds and generate alerts if needed.

        Args:
            metric: The request metric to check
        """
        # Don't alert on non-200 responses
        if metric.status_code >= 400:
            return

        endpoint = metric.endpoint
        method = metric.http_method

        # Get the threshold for this endpoint
        threshold = settings.PERFORMANCE_THRESHOLD_MS
        if endpoint in settings.PERFORMANCE_CUSTOM_THRESHOLDS:
            threshold = settings.PERFORMANCE_CUSTOM_THRESHOLDS[endpoint]

        # Get the baseline if available
        baseline = None
        if (endpoint in self.endpoint_baselines and
            method in self.endpoint_baselines[endpoint]):
            baseline = self.endpoint_baselines[endpoint][method]

        # Check if the duration exceeds the absolute threshold
        if metric.duration_ms > threshold:
            # Determine severity based on how much it exceeds the threshold
            severity = AlertSeverity.INFO
            if metric.duration_ms > threshold * 1.5:
                severity = AlertSeverity.WARNING
            if metric.duration_ms > threshold * 2:
                severity = AlertSeverity.CRITICAL

            # Calculate deviation percentage if baseline exists
            deviation_percent = None
            if baseline:
                deviation_percent = ((metric.duration_ms - baseline) / baseline) * 100
                # Only alert if deviation exceeds the configured percentage
                if deviation_percent < settings.PERFORMANCE_DEVIATION_PERCENT:
                    return

            # Create alert message
            if deviation_percent is not None:
                message = (f"Endpoint response time ({metric.duration_ms:.2f}ms) "
                          f"exceeded threshold ({threshold:.2f}ms) by {deviation_percent:.1f}%")
            else:
                message = (f"Endpoint response time ({metric.duration_ms:.2f}ms) "
                          f"exceeded threshold ({threshold:.2f}ms)")

            # Create the alert
            alert = PerformanceAlert(
                id=f"alert-{uuid.uuid4().hex[:8]}",
                timestamp=datetime.now(),
                endpoint=endpoint,
                http_method=method,
                severity=severity,
                status=AlertStatus.ACTIVE,
                current_value=metric.duration_ms,
                threshold_value=threshold,
                deviation_percent=deviation_percent,
                message=message
            )

            # Add to alerts list
            self.alerts.append(alert)

            # Log the alert
            logger.warning(f"Performance alert: {message} - Endpoint: {endpoint} {method}")

    def get_alerts(self, status: Optional[AlertStatus] = None,
                  severity: Optional[AlertSeverity] = None,
                  since: Optional[datetime] = None,
                  limit: Optional[int] = None) -> List[PerformanceAlert]:
        """
        Get performance alerts with optional filtering.

        Args:
            status: Filter by alert status
            severity: Filter by alert severity
            since: Only include alerts after this time
            limit: Maximum number of alerts to return

        Returns:
            List of performance alerts
        """
        filtered_alerts = self.alerts

        if status:
            filtered_alerts = [a for a in filtered_alerts if a.status == status]

        if severity:
            filtered_alerts = [a for a in filtered_alerts if a.severity == severity]

        if since:
            filtered_alerts = [a for a in filtered_alerts if a.timestamp >= since]

        # Sort by timestamp, newest first
        filtered_alerts.sort(key=lambda a: a.timestamp, reverse=True)

        if limit:
            return filtered_alerts[:limit]
        return filtered_alerts

    def resolve_alert(self, alert_id: str) -> Optional[PerformanceAlert]:
        """
        Mark an alert as resolved.

        Args:
            alert_id: The ID of the alert to resolve

        Returns:
            The resolved alert or None if not found
        """
        for alert in self.alerts:
            if alert.id == alert_id and alert.status == AlertStatus.ACTIVE:
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = datetime.now()
                return alert
        return None

    def generate_report(self, time_period: str = "24h") -> PerformanceReport:
        """
        Generate a performance report for the specified time period.

        Args:
            time_period: Time period for the report (e.g., "24h", "1h")

        Returns:
            The generated performance report
        """
        # Parse the time period
        hours = 24
        if time_period.endswith('h'):
            try:
                hours = int(time_period[:-1])
            except ValueError:
                pass

        since = datetime.now() - timedelta(hours=hours)

        # Get performance stats for the period
        performance_summary = self.get_stats(since=since)

        # Get alerts for the period
        period_alerts = self.get_alerts(since=since)

        # Count alerts by severity
        alert_counts = {
            AlertSeverity.INFO: 0,
            AlertSeverity.WARNING: 0,
            AlertSeverity.CRITICAL: 0
        }
        for alert in period_alerts:
            alert_counts[alert.severity] += 1

        # Find top slowest endpoints
        endpoints = performance_summary.endpoints
        endpoints.sort(key=lambda e: e.avg_duration_ms, reverse=True)
        top_slowest = endpoints[:5] if len(endpoints) >= 5 else endpoints

        # Calculate overall average response time
        total_count = sum(e.count for e in endpoints)
        avg_response_time = sum(e.avg_duration_ms * e.count for e in endpoints) / total_count if total_count > 0 else 0

        # Create the report
        report = PerformanceReport(
            report_id=f"report-{uuid.uuid4().hex[:8]}",
            generated_at=datetime.now(),
            time_period=f"Last {hours} hours",
            total_requests=performance_summary.total_requests,
            average_response_time=avg_response_time,
            top_slowest_endpoints=top_slowest,
            alerts_summary=alert_counts,
            performance_summary=performance_summary
        )

        # Store the report
        self.reports[report.report_id] = report

        return report

    def get_report(self, report_id: str) -> Optional[PerformanceReport]:
        """
        Retrieve a previously generated report.

        Args:
            report_id: The ID of the report to retrieve

        Returns:
            The report or None if not found
        """
        return self.reports.get(report_id)

    def get_reports(self, limit: Optional[int] = None) -> List[PerformanceReport]:
        """
        Get all generated reports.

        Args:
            limit: Maximum number of reports to return

        Returns:
            List of reports, newest first
        """
        reports = list(self.reports.values())
        reports.sort(key=lambda r: r.generated_at, reverse=True)

        if limit:
            return reports[:limit]
        return reports

    def export_metrics(self, format_type: ExportFormat,
                       time_period: str = "24h",
                       include_alerts: bool = True,
                       endpoints: Optional[List[str]] = None) -> ExportResponse:
        """
        Export metrics to the specified format.

        Args:
            format_type: Export format (JSON or CSV)
            time_period: Time period for the export (e.g., "24h", "1h")
            include_alerts: Whether to include alerts in the export
            endpoints: List of endpoints to include (None means all)

        Returns:
            Export response with file details
        """
        # Parse the time period
        hours = 24
        if time_period.endswith('h'):
            try:
                hours = int(time_period[:-1])
            except ValueError:
                pass

        since = datetime.now() - timedelta(hours=hours)

        # Get metrics for the period
        metrics = self.get_metrics(since=since)

        # Filter by endpoints if specified
        if endpoints:
            metrics = [m for m in metrics if m.endpoint in endpoints]

        # Generate a unique export ID
        export_id = f"export-{uuid.uuid4().hex[:8]}"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format_type == ExportFormat.JSON:
            # Export to JSON
            filename = f"performance_metrics_{timestamp}.json"
            filepath = os.path.join(settings.PERFORMANCE_EXPORT_PATH, filename)

            export_data = {
                "metrics": [m.dict() for m in metrics],
                "generated_at": datetime.now().isoformat(),
                "time_period": f"Last {hours} hours",
                "total_records": len(metrics)
            }

            # Include alerts if requested
            if include_alerts:
                alerts = self.get_alerts(since=since)
                if endpoints:
                    alerts = [a for a in alerts if a.endpoint in endpoints]
                export_data["alerts"] = [a.dict() for a in alerts]

            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, default=str, indent=2)

            # Get file size
            file_size = os.path.getsize(filepath)

        elif format_type == ExportFormat.CSV:
            # Export to CSV
            filename = f"performance_metrics_{timestamp}.csv"
            filepath = os.path.join(settings.PERFORMANCE_EXPORT_PATH, filename)

            # Create CSV file
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ["timestamp", "endpoint", "http_method", "duration_ms", "status_code"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for metric in metrics:
                    writer.writerow({
                        "timestamp": metric.timestamp.isoformat(),
                        "endpoint": metric.endpoint,
                        "http_method": metric.http_method,
                        "duration_ms": metric.duration_ms,
                        "status_code": metric.status_code
                    })

                # Add alerts if requested
                if include_alerts:
                    alerts = self.get_alerts(since=since)
                    if endpoints:
                        alerts = [a for a in alerts if a.endpoint in endpoints]

                    if alerts:
                        # Add a separator
                        writer.writerow({
                            "timestamp": "",
                            "endpoint": "",
                            "http_method": "",
                            "duration_ms": "",
                            "status_code": ""
                        })
                        writer.writerow({
                            "timestamp": "ALERTS",
                            "endpoint": "",
                            "http_method": "",
                            "duration_ms": "",
                            "status_code": ""
                        })

                        # Write alerts header
                        alert_fieldnames = ["timestamp", "endpoint", "http_method", "severity",
                                           "current_value", "threshold_value", "message"]
                        writer = csv.DictWriter(csvfile, fieldnames=alert_fieldnames)
                        writer.writeheader()

                        # Write alerts data
                        for alert in alerts:
                            writer.writerow({
                                "timestamp": alert.timestamp.isoformat(),
                                "endpoint": alert.endpoint,
                                "http_method": alert.http_method,
                                "severity": alert.severity,
                                "current_value": alert.current_value,
                                "threshold_value": alert.threshold_value,
                                "message": alert.message
                            })

            # Get file size
            file_size = os.path.getsize(filepath)

        # Create the export response
        export_response = ExportResponse(
            export_id=export_id,
            format=format_type,
            file_name=filename,
            file_size=file_size,
            download_url=f"/api/performance/exports/{export_id}/download",
            exported_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=7),
            record_count=len(metrics)
        )

        # Store the export response
        self.exports[export_id] = export_response

        return export_response

    def get_export(self, export_id: str) -> Optional[ExportResponse]:
        """
        Get details about a specific export.

        Args:
            export_id: The ID of the export

        Returns:
            Export response or None if not found
        """
        return self.exports.get(export_id)

# Create global instance of the performance store
performance_store = PerformanceStore(max_size=settings.PERFORMANCE_METRICS_RETENTION)

class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    Middleware for tracking API request performance.

    This middleware captures:
    - Total request processing time
    - Performance metrics for each API endpoint
    - Metrics include timestamp, endpoint, duration, and HTTP method
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process the request and measure its duration.

        Args:
            request: The incoming request
            call_next: The next middleware in the chain

        Returns:
            The response from the next middleware
        """
        if not settings.PERFORMANCE_METRICS_ENABLED:
            return await call_next(request)

        start_time = time.time()

        try:
            # Process the request
            response = await call_next(request)

            # Calculate duration in milliseconds
            duration_ms = (time.time() - start_time) * 1000

            # Create and store the metric
            metric = RequestMetric(
                timestamp=datetime.now(),
                endpoint=request.url.path,
                http_method=request.method,
                duration_ms=duration_ms,
                status_code=response.status_code
            )

            performance_store.add_metric(metric)

            # Log the request
            logger.debug(
                f"Request completed: {request.method} {request.url.path} - "
                f"{duration_ms:.2f}ms - {response.status_code}"
            )

            return response

        except Exception as e:
            # If an exception occurs, still log the duration
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Request failed: {request.method} {request.url.path} - "
                f"{duration_ms:.2f}ms - Error: {str(e)}"
            )
            raise