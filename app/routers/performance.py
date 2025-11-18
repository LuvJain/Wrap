"""
API routes for accessing performance metrics.
"""
from fastapi import APIRouter, Query
from typing import List, Optional

from app.middleware.performance import performance_store
from app.models.performance import RequestMetric, PerformanceStats, PerformanceSummary

router = APIRouter(prefix="/api/performance", tags=["performance"])

@router.get("/metrics", response_model=List[RequestMetric])
async def get_metrics(limit: Optional[int] = Query(50, ge=1, le=1000)):
    """
    Get the most recent API request performance metrics.

    Args:
        limit: Maximum number of metrics to return (default: 50, max: 1000)

    Returns:
        List of request metrics, most recent first
    """
    return performance_store.get_metrics(limit=limit)

@router.get("/stats", response_model=PerformanceSummary)
async def get_stats():
    """
    Get aggregated performance statistics.

    Returns:
        Summary of performance metrics
    """
    return performance_store.get_stats()

@router.delete("/metrics", status_code=204)
async def clear_metrics():
    """
    Clear all stored performance metrics.

    Returns:
        204 No Content
    """
    performance_store.clear()
    return None