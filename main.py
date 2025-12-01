from fastapi import FastAPI
from app.routers import auth, health
from app.core.database import create_tables
from datetime import datetime
from pydantic import BaseModel
import random

class NameRequest(BaseModel):
    name: str

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

@app.post("/name")
async def process_name(name_request: NameRequest):
    """
    POST endpoint that takes a name and returns it.

    Request body format:
    ```json
    {
        "name": "string"
    }
    ```

    Returns the provided name in the response.
    """
    return {"name": name_request.name}

@app.get("/funny")
async def funny():
    """
    Funny endpoint that returns a random joke or humorous response.

    Used to bring a smile to your day and demonstrate endpoint creation.
    """
    funny_responses = [
        {"joke": "Why don't scientists trust atoms? Because they make up everything!"},
        {"joke": "Why did the developer go broke? Because he used up all his cache!"},
        {"joke": "Why was the JavaScript developer sad? Because he didn't Node how to Express himself!"},
        {"joke": "Why do programmers prefer dark mode? Because light attracts bugs!"},
        {"joke": "What's a programmer's favorite hang out place? The Foo Bar!"},
        {"joke": "How many programmers does it take to change a light bulb? None, that's a hardware problem!"},
        {"joke": "What do you call eight hobbits? A hobbyte!"},
        {"quote": "!false - It's funny because it's true."},
        {"quote": "There are 10 types of people in this world: those who understand binary and those who don't."}
    ]

    return random.choice(funny_responses)