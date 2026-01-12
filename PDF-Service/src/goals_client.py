"""Goals Service Client"""

import httpx
from uuid import UUID
from config import GOALS_SERVICE_URL
from fastapi import HTTPException, status

async def get_user_goals(token: str) -> list:
    """
    Fetch all goals for the current user from Goals Service
    
    Args:
        token: JWT token for authentication
    
    Returns:
        List of goals
    
    Raises:
        HTTPException: If request fails
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GOALS_SERVICE_URL}/api/goals?page_size=1000",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("goals", [])
            else:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Goals Service error: {response.status_code}"
                )
    
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to connect to Goals Service: {str(e)}"
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Goals Service request timed out"
        )

async def get_goal_by_id(goal_id: UUID, token: str) -> dict:
    """
    Fetch a specific goal
    
    Args:
        goal_id: ID of the goal
        token: JWT token for authentication
    
    Returns:
        Goal data dictionary
    
    Raises:
        HTTPException: If request fails
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GOALS_SERVICE_URL}/api/goals/{goal_id}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Goal not found"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Goals Service error: {response.status_code}"
                )
    
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to connect to Goals Service: {str(e)}"
        )
