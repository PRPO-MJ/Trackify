"""Authentication module for JWT and Google OAuth"""

import jwt
import requests
import google.auth.transport.requests
from google.oauth2 import id_token
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
from database import User, get_db

security = HTTPBearer()

def create_access_token(user_id: str, expires_delta: timedelta | None = None) -> str:
    """Create JWT access token"""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"sub": user_id, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> str:
    """Verify JWT token and return user_id"""
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

def verify_google_token(token: str) -> dict:
    """Verify Google ID token (frontend token)"""
    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            google.auth.transport.requests.Request(),
            GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=10
        )
        
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
        
        return idinfo
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google token: {str(e)}"
        )

def exchange_code_for_token(code: str, redirect_uri: str) -> dict:
    """Exchange authorization code for Google tokens (server-side OAuth)"""
    try:
        token_url = "https://oauth2.googleapis.com/token"
        
        payload = {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        
        response = requests.post(token_url, data=payload)
        response.raise_for_status()
        
        token_data = response.json()
        
        id_token_str = token_data.get("id_token")
        if not id_token_str:
            raise ValueError("No ID token in response")
        
        idinfo = id_token.verify_oauth2_token(
            id_token_str,
            google.auth.transport.requests.Request(),
            GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=10
        )
        
        return idinfo
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Failed to exchange code for token: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authorization code: {str(e)}"
        )

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    user_id = verify_token(token)
    
    user = db.query(User).filter(User.google_sub == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user
