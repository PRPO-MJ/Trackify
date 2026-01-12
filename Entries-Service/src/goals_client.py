"""Goals Service Client for validating goals"""

import httpx
from uuid import UUID
from config import GOALS_SERVICE_URL
from fastapi import HTTPException, status

async def validate_goal_ownership(goal_id: UUID, token: str) -> bool:
    """
    Validate that a goal belongs to the current user
    
    Args:
        goal_id: ID of the goal
        token: JWT token for authentication
    
    Returns:
        True if goal belongs to user, False otherwise
    
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
                return True
            elif response.status_code == 404:
                return False
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
