from fastapi import FastAPI
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