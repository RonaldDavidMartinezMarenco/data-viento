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
    """Get current authenticated user from JWT token"""
    
    token = credentials.credentials
    
    # 🔍 DEBUG: Print token info
    print(f"\n{'='*60}")
    print(f"🔍 DEBUG: Token received")
    print(f"   First 30 chars: {token[:30]}...")
    print(f"   Last 30 chars: ...{token[-30:]}")
    print(f"   Total length: {len(token)}")
    print(f"{'='*60}\n")
    
    # Try to decode token
    try:
        # 🔍 DEBUG: Try decoding manually first
        
        print("🔍 Attempting to decode token...")
        payload = AuthUtils.decode_token(token)
        
        print(f"🔍 Decoded payload: {payload}")
        
        if not payload:
            print("❌ Payload is None - token decode failed!")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        print(f"✅ Payload decoded successfully")
        print(f"   Contents: {payload}")
        
    except Exception as e:
        print(f"💥 Exception during decode: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Get user info from token
    print("🔍 Extracting user info from payload...")
    user_info = AuthUtils.get_user_from_token(token)
    
    print(f"🔍 User info result: {user_info}")
    
    if not user_info:
        print("❌ user_info is None!")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    print(f"✅ User authenticated: {user_info.get('username')}")
    print(f"{'='*60}\n")
    
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