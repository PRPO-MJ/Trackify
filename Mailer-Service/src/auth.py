"""Authentication module for JWT verification"""

import jwt
import httpx
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import SECRET_KEY, ALGORITHM, USER_SERVICE_URL

security = HTTPBearer()

def create_access_token(user_id: str, expires_delta: timedelta = None) -> str:
    """Create JWT access token for testing purposes"""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=24)
    
    to_encode = {"sub": user_id, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> str:
    """
    Verify JWT token and return user_id
    This token comes from the User Service
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user_id",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    FastAPI dependency to extract and verify current user from Bearer token
    """
    token = credentials.credentials
    user_id = verify_token(token)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{USER_SERVICE_URL}/api/auth/verify",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5.0
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token verification failed with User Service",
                    headers={"WWW-Authenticate": "Bearer"},
                )
    except httpx.RequestError:
        pass
    
    return user_id

async def get_current_user_with_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> tuple[str, str]:
    """
    FastAPI dependency to extract and verify current user and return both user_id and token
    Returns: (user_id, token)
    """
    token = credentials.credentials
    user_id = verify_token(token)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{USER_SERVICE_URL}/api/auth/verify",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5.0
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token verification failed with User Service",
                    headers={"WWW-Authenticate": "Bearer"},
                )
    except httpx.RequestError:
        pass
    
    return user_id, token
