"""Entries Service Client"""

import httpx
from uuid import UUID
from config import ENTRIES_SERVICE_URL
from fastapi import HTTPException, status

async def get_user_time_stats(token: str) -> dict:
    """
    Fetch user time statistics from Entries Service
    
    Args:
        token: JWT token for authentication
    
    Returns:
        User time statistics
    
    Raises:
        HTTPException: If request fails
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ENTRIES_SERVICE_URL}/api/entries/summary",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "total_hours": 0,
                    "total_entries": 0,
                    "by_goal": []
                }
    
    except (httpx.RequestError, httpx.TimeoutException):
        return {
            "total_hours": 0,
            "total_entries": 0,
            "by_goal": []
        }

async def get_goal_total_hours(goal_id: UUID, token: str) -> dict:
    """
    Fetch total hours for a specific goal
    
    Args:
        goal_id: ID of the goal
        token: JWT token for authentication
    
    Returns:
        Goal time statistics
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ENTRIES_SERVICE_URL}/api/entries/goal/{goal_id}/total",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "total_hours": 0,
                    "total_minutes": 0
                }
    
    except (httpx.RequestError, httpx.TimeoutException):
        return {
            "total_hours": 0,
            "total_minutes": 0
        }
