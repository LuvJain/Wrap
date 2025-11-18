"""
Middleware for tracking API request performance.

This middleware captures:
- Total request processing time
- Performance metrics for each API endpoint
- Metrics include timestamp, endpoint, duration, and HTTP method
- In-memory storage with configurable retention
"""
import time
import logging
from collections import deque
from datetime import datetime
from typing import Dict, List, Callable, Optional, Deque
from fastapi import Request, Response
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from app.config import settings
from app.models.performance import RequestMetric, PerformanceStats, PerformanceSummary

# Configure logging
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(settings.PERFORMANCE_LOG_LEVEL)

class PerformanceStore:
    """In-memory storage for API performance metrics with configurable retention."""

    def __init__(self, max_size: int = settings.PERFORMANCE_METRICS_RETENTION):
        """
        Initialize the performance store.

        Args:
            max_size: Maximum number of metrics to keep in memory
        """
        self.metrics: Deque[RequestMetric] = deque(maxlen=max_size)
        self.max_size = max_size
        self.endpoint_stats: Dict[str, Dict[str, List[float]]] = {}  # {endpoint: {method: [durations]}}

    def add_metric(self, metric: RequestMetric) -> None:
        """
        Add a new performance metric to the store.

        Args:
            metric: The request metric to add
        """
        self.metrics.append(metric)

        # Update endpoint statistics
        endpoint_key = f"{metric.endpoint}"
        method_key = metric.http_method

        if endpoint_key not in self.endpoint_stats:
            self.endpoint_stats[endpoint_key] = {}

        if method_key not in self.endpoint_stats[endpoint_key]:
            self.endpoint_stats[endpoint_key][method_key] = []

        self.endpoint_stats[endpoint_key][method_key].append(metric.duration_ms)

        # Trim to keep only recent data if necessary
        if len(self.endpoint_stats[endpoint_key][method_key]) > self.max_size:
            self.endpoint_stats[endpoint_key][method_key] = self.endpoint_stats[endpoint_key][method_key][-self.max_size:]

    def get_metrics(self, limit: Optional[int] = None) -> List[RequestMetric]:
        """
        Get the most recent metrics.

        Args:
            limit: Maximum number of metrics to return (default: all)

        Returns:
            List of request metrics, most recent first
        """
        metrics_list = list(self.metrics)
        metrics_list.reverse()  # Most recent first
        if limit:
            return metrics_list[:limit]
        return metrics_list

    def get_stats(self) -> PerformanceSummary:
        """
        Get aggregated performance statistics.

        Returns:
            Summary of performance metrics
        """
        stats = []

        for endpoint, methods in self.endpoint_stats.items():
            for method, durations in methods.items():
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
            total_requests=len(self.metrics),
            endpoints=stats,
            last_updated=datetime.now()
        )

    def clear(self) -> None:
        """Clear all stored metrics."""
        self.metrics.clear()
        self.endpoint_stats.clear()

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