"""
Main FastAPI application with performance middleware.

This application demonstrates the use of a custom performance middleware
to track API request durations and provide performance metrics.

Features:
- Performance middleware captures total request processing time
- Performance metrics are logged for each API endpoint
- Metrics include timestamp, endpoint, duration, and HTTP method
- Performance data is stored in memory with configurable retention
- Designed for minimal overhead (< 5% performance impact)

Run with:
    uvicorn main:app --reload
"""
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.middleware.performance import PerformanceMiddleware
from app.routers import performance, sample

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="API with performance tracking middleware",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add performance middleware
app.add_middleware(PerformanceMiddleware)

# Register routers
app.include_router(performance.router)
app.include_router(sample.router)

@app.get("/", tags=["root"])
async def root():
    """Root endpoint, returns basic application info."""
    return {
        "app_name": settings.APP_NAME,
        "description": "API with performance tracking middleware",
        "version": "1.0.0",
        "documentation": "/api/docs",
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler to log all unhandled exceptions.

    Note: Exceptions are still tracked by the performance middleware,
    which records the request duration even if an error occurs.
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."}
    )

if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting {settings.APP_NAME}")
    logger.info(f"Performance metrics {'enabled' if settings.PERFORMANCE_METRICS_ENABLED else 'disabled'}")
    logger.info(f"Metrics retention: {settings.PERFORMANCE_METRICS_RETENTION} requests")

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)