import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config.stripe_config import StripeConfig, get_stripe_config
from app.utils.security import setup_secure_logging
from app.routers import payments

# Set up secure logging first
setup_secure_logging()
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Payment Integration API")

# Initialize Stripe configuration
stripe_config = get_stripe_config()
logger.info(f"Application starting with Stripe in {stripe_config.environment} mode")

# Include routers
app.include_router(payments.router, prefix="/api/payments", tags=["payments"])

@app.get("/")
async def root():
    return {"message": "Payment Integration API"}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to prevent leaking sensitive information"""
    logger.error(f"Unhandled exception: {type(exc).__name__}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)