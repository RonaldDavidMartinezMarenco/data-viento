"""
Authentication Middleware for FastAPI

Provides JWT token validation and user authentication.
Use as a dependency in protected routes.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.auth import AuthUtils


# Security scheme for Swagger UI
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Dependency to get current authenticated user from JWT token
    
    Validates JWT token from Authorization header and returns user info.
    
    Args:
        credentials: HTTP Bearer token from Authorization header
        
    Returns:
        dict: User info from token (user_id, username, user_type)
        
    Raises:
        HTTPException 401: If token is invalid or expired
        
    Usage in routes:
        @router.get("/profile")
        def get_profile(current_user: dict = Depends(get_current_user)):
            user_id = current_user['user_id']
            # ... fetch and return user profile
    
    Token format in request:
        Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    """
    # Extract token from credentials
    token = credentials.credentials
    
    # Validate and decode token
    user_info = AuthUtils.get_user_from_token(token)
    
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user_info


def require_admin(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Dependency to require admin user type
    
    Use this dependency for admin-only routes.
    
    Args:
        current_user: User info from get_current_user dependency
        
    Returns:
        dict: User info if user is admin
        
    Raises:
        HTTPException 403: If user is not an admin
        
    Usage in routes:
        @router.delete("/users/{user_id}")
        def delete_user(
            user_id: int,
            admin_user: dict = Depends(require_admin)
        ):
            # Only admins can delete users
            # ... delete user logic
    """
    if current_user.get('user_type') != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return current_user


def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))
) -> Dict[str, Any] | None:
    """
    Dependency to get current user if token is provided (optional)
    
    Useful for routes that work for both authenticated and anonymous users,
    but show different data based on authentication.
    
    Args:
        credentials: Optional HTTP Bearer token
        
    Returns:
        dict: User info if valid token provided, None otherwise
        
    Usage in routes:
        @router.get("/weather")
        def get_weather(
            location_id: int,
            current_user: dict | None = Depends(get_optional_user)
        ):
            if current_user:
                # Return personalized weather with user preferences
            else:
                # Return default weather data
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    return AuthUtils.get_user_from_token(token)