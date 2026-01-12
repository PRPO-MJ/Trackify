"""User Service Client"""

import httpx
from uuid import UUID
from config import USER_SERVICE_URL
from fastapi import HTTPException, status

async def get_user_data(user_id: UUID, token: str) -> dict:
    """
    Fetch user data from User Service
    
    Args:
        user_id: ID of the user
        token: JWT token for authentication
    
    Returns:
        User data dictionary
    
    Raises:
        HTTPException: If request fails
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{USER_SERVICE_URL}/api/users/{user_id}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"User Service error: {response.status_code}"
                )
    
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to connect to User Service: {str(e)}"
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="User Service request timed out"
        )
