"""Authentication module for the API.

This module provides JWT-based authentication for both REST endpoints
and WebSocket connections as described in MESSAGING.md.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext

from ..utils.settings import Settings


class AuthManager:
    """Manages authentication and JWT token operations."""
    
    def __init__(self, settings: Optional[Settings] = None):
        """Initialize the authentication manager.
        
        Args:
            settings: Optional settings instance. If None, creates a new one.
        """
        self.settings = settings or Settings()
        self.secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        
        # Password hashing
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Security scheme
        self.security = HTTPBearer()
        
        # In-memory user storage (replace with real database in production)
        self.fake_users_db: Dict[str, Dict[str, str]] = {
            "testuser": {
                "username": "testuser",
                "hashed_password": self.pwd_context.hash("testpass"),
                "email": "test@example.com",
                "full_name": "Test User"
            }
        }
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash.
        
        Args:
            plain_password: Plain text password.
            hashed_password: Hashed password from database.
            
        Returns:
            True if password matches, False otherwise.
        """
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password.
        
        Args:
            password: Plain text password.
            
        Returns:
            Hashed password.
        """
        return self.pwd_context.hash(password)
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, str]]:
        """Authenticate a user with username and password.
        
        Args:
            username: Username to authenticate.
            password: Password to verify.
            
        Returns:
            User data if authentication successful, None otherwise.
        """
        user = self.fake_users_db.get(username)
        if not user:
            return None
        if not self.verify_password(password, user["hashed_password"]):
            return None
        return user
    
    def create_access_token(self, data: Dict[str, str]) -> str:
        """Create a JWT access token.
        
        Args:
            data: Data to encode in the token.
            
        Returns:
            JWT access token.
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[str]:
        """Verify a JWT token and return the username.
        
        Args:
            token: JWT token to verify.
            
        Returns:
            Username if token is valid, None otherwise.
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            if username is None:
                return None
            return username
        except JWTError:
            return None
    
    def get_user(self, username: str) -> Optional[Dict[str, str]]:
        """Get user data by username.
        
        Args:
            username: Username to look up.
            
        Returns:
            User data if found, None otherwise.
        """
        return self.fake_users_db.get(username)
    
    def create_user(self, username: str, password: str, email: str, full_name: str) -> Dict[str, str]:
        """Create a new user.
        
        Args:
            username: Username for the new user.
            password: Plain text password.
            email: User's email address.
            full_name: User's full name.
            
        Returns:
            Created user data.
            
        Raises:
            ValueError: If username already exists.
        """
        if username in self.fake_users_db:
            raise ValueError("Username already exists")
        
        hashed_password = self.get_password_hash(password)
        user_data = {
            "username": username,
            "hashed_password": hashed_password,
            "email": email,
            "full_name": full_name
        }
        self.fake_users_db[username] = user_data
        return user_data


# Global auth manager instance
auth_manager = AuthManager()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(auth_manager.security)
) -> str:
    """Get the current authenticated user from JWT token.
    
    Args:
        credentials: HTTP authorization credentials.
        
    Returns:
        Username of the authenticated user.
        
    Raises:
        HTTPException: If authentication fails.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        username = auth_manager.verify_token(token)
        if username is None:
            raise credentials_exception
        return username
    except Exception:
        raise credentials_exception


async def get_current_user_websocket(token: str) -> Optional[str]:
    """Get the current authenticated user from JWT token for WebSocket.
    
    Args:
        token: JWT token string.
        
    Returns:
        Username if token is valid, None otherwise.
    """
    return auth_manager.verify_token(token)
