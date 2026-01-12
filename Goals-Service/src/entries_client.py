"""Entries Service Client for retrieving time entry data"""

import httpx
from typing import Optional
from uuid import UUID
from config import ENTRIES_SERVICE_URL
from fastapi import HTTPException, status
from decimal import Decimal

async def get_goal_total_hours(goal_id: UUID, token: str) -> Optional[Decimal]:
    """
    Fetch total hours tracked for a goal from Entries Service
    
    Args:
        goal_id: ID of the goal
        token: JWT token for authentication
    
    Returns:
        Total hours as Decimal, None if not available
    
    Raises:
        HTTPException: If request fails
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ENTRIES_SERVICE_URL}/api/entries/goal/{goal_id}/total",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return Decimal(str(data.get("total_hours", 0)))
            elif response.status_code == 404:
                return Decimal(0)
            else:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Entries Service error: {response.status_code}"
                )
    
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to connect to Entries Service: {str(e)}"
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Entries Service request timed out"
        )

async def get_goal_entries_count(goal_id: UUID, token: str) -> int:
    """
    Get count of time entries for a goal
    
    Args:
        goal_id: ID of the goal
        token: JWT token for authentication
    
    Returns:
        Number of entries
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ENTRIES_SERVICE_URL}/api/entries/goal/{goal_id}/count",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("count", 0)
            else:
                return 0
    
    except Exception:
        return 0
