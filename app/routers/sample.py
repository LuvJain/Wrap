"""
Sample API endpoints for testing performance middleware.
"""
import time
from typing import Dict, List, Optional
import random
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/sample", tags=["sample"])

# Dummy data for testing
items = {
    i: {"id": i, "name": f"Item {i}", "description": f"This is item {i}"}
    for i in range(1, 101)
}

@router.get("/items", response_model=List[Dict])
async def get_items(limit: Optional[int] = Query(10, ge=1, le=100)):
    """
    Get a list of items.

    Args:
        limit: Maximum number of items to return

    Returns:
        List of items
    """
    # Add a small random delay to simulate processing time
    time.sleep(random.uniform(0.005, 0.05))

    return list(items.values())[:limit]

@router.get("/items/{item_id}", response_model=Dict)
async def get_item(item_id: int):
    """
    Get a specific item by ID.

    Args:
        item_id: The ID of the item to retrieve

    Returns:
        Item details

    Raises:
        HTTPException: If the item is not found
    """
    # Add a small random delay to simulate processing time
    time.sleep(random.uniform(0.001, 0.03))

    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")

    return items[item_id]

@router.post("/items", response_model=Dict, status_code=201)
async def create_item(item: Dict):
    """
    Create a new item.

    Args:
        item: The item to create

    Returns:
        The created item
    """
    # Add a small random delay to simulate processing time
    time.sleep(random.uniform(0.01, 0.1))

    item_id = max(items.keys()) + 1 if items else 1
    new_item = {
        "id": item_id,
        "name": item.get("name", f"Item {item_id}"),
        "description": item.get("description", "")
    }
    items[item_id] = new_item

    return new_item

@router.get("/heavy", response_model=Dict)
async def heavy_operation():
    """
    Simulate a heavy operation with varying response times.

    Returns:
        Operation result
    """
    # Simulate a more intensive operation
    processing_time = random.uniform(0.1, 0.5)
    time.sleep(processing_time)

    return {
        "status": "success",
        "message": f"Heavy operation completed in {processing_time:.2f} seconds"
    }