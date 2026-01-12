"""PDF Service Client"""

import httpx
from typing import Optional
from uuid import UUID
from config import PDF_SERVICE_URL
from fastapi import HTTPException, status

async def generate_report_pdf(goal_id: UUID, year: int, month: int, token: str) -> bytes:
    """
    Generate PDF report from PDF Service for a specific goal
    Note: Year and month parameters are currently not used by the PDF Service,
    but kept for potential future enhancements
    
    Args:
        goal_id: ID of the goal to generate PDF for
        year: Year for the report (currently unused)
        month: Month for the report (1-12) (currently unused)
        token: JWT token for authentication
    
    Returns:
        PDF binary data
    
    Raises:
        HTTPException: If PDF service request fails
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{PDF_SERVICE_URL}/api/pdf/goal/{goal_id}/stream",
                headers={"Authorization": f"Bearer {token}"},
                timeout=60.0
            )
            
            if response.status_code == 200:
                return response.content
            else:
                error_detail = response.text
                try:
                    error_detail = response.json().get("detail", response.text)
                except:
                    pass
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"PDF Service error: {error_detail}"
                )
    
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to connect to PDF Service: {str(e)}"
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="PDF Service request timed out"
        )

async def fetch_pdf_from_service(goal_id: UUID, token: str) -> Optional[bytes]:
    """
    Fetch PDF from PDF Service for a given goal
    
    Args:
        goal_id: ID of the goal to generate PDF for
        token: JWT token for authentication
    
    Returns:
        PDF binary data if successful, None otherwise
    
    Raises:
        HTTPException: If PDF service request fails
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{PDF_SERVICE_URL}/api/pdf/goal/{goal_id}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=30.0
            )
            
            if response.status_code == 200:
                return response.content
            elif response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"PDF not found for goal {goal_id}"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"PDF Service error: {response.status_code}"
                )
    
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to connect to PDF Service: {str(e)}"
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="PDF Service request timed out"
        )

async def generate_pdf_sync(goal_id: UUID, token: str) -> Optional[bytes]:
    """
    Request synchronous PDF generation from PDF Service
    
    Args:
        goal_id: ID of the goal
        token: JWT token for authentication
    
    Returns:
        PDF binary data
    
    Raises:
        HTTPException: If request fails
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{PDF_SERVICE_URL}/api/pdf/generate",
                json={"goal_id": str(goal_id)},
                headers={"Authorization": f"Bearer {token}"},
                timeout=30.0
            )
            
            if response.status_code == 200:
                return response.content
            else:
                error_detail = response.json().get("detail", response.text)
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"PDF Service error: {error_detail}"
                )
    
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to connect to PDF Service: {str(e)}"
        )
