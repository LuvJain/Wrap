from fastapi import FastAPI, Response
from app.routers import auth, health
from app.core.database import create_tables

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

    - Returns 200 OK status code
    - Returns 'pong' as the response (plain text)
    - Publicly accessible without authentication
    - Used for basic API reachability checks
    """
    return Response(content="pong", media_type="text/plain")