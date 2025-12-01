from fastapi import FastAPI
from app.routers import auth, health
from app.core.database import create_tables
from datetime import datetime

# Create FastAPI application
app = FastAPI(
    title="User Auth API",
    description="API for user authentication and authorization",
    version="0.1.0"
)

# Include routers
app.include_router(auth.router)
app.include_router(health.router)

# Create database tables
create_tables()

@app.get("/")
async def root():
    return {"message": "Welcome to the User Auth API"}

@app.get("/ping")
async def ping():
    """
    Simple ping endpoint that returns 'pong'.

    Used for basic connectivity testing.
    """
    return "pong"

@app.get("/pong")
async def pong():
    """
    Pong endpoint that returns the current time.

    Used for time synchronization and connectivity testing.
    """
    current_time = datetime.now()
    return {"time": current_time.isoformat()}