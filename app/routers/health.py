from fastapi import APIRouter
from datetime import datetime
import time

router = APIRouter(
    prefix="/health",
    tags=["health"],
)


@router.get("", status_code=200)
async def health_check():
    """
    Health check endpoint that returns server status and current timestamp.

    - Returns 200 OK status code
    - Includes 'status': 'up' in the JSON response
    - Publicly accessible without authentication
    - Designed for response time under 100ms
    - Returns current server timestamp
    """
    # Get current timestamp
    current_time = datetime.now()
    timestamp = int(current_time.timestamp() * 1000)  # milliseconds

    # Return health status
    return {
        "status": "up",
        "timestamp": timestamp
    }