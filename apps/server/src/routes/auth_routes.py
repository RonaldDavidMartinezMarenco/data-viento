"""
Authentication Routes

Endpoints:
- POST /auth/register - Create new user account
- POST /auth/login - Authenticate and get tokens
- POST /auth/refresh - Refresh access token
- POST /auth/logout - Invalidate tokens (optional)
- GET /auth/verify - Verify if token is valid
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any

import sys
import traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.users import (
    UserCreate, UserResponse, UserLogin,
    TokenResponse, MessageResponse
)
from src.services.user_service import UserService
from src.utils.auth import AuthUtils
from src.middleware.auth_middleware import get_current_user


# Create router
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account with username, email, and password"
)
def register_user(user_data: UserCreate) -> UserResponse:
    """
    Register a new user account

    Process:
    1. Validate user data (Pydantic handles this)
    2. Check username/email uniqueness
    3. Hash password
    4. Create user in database
    5. Create default preferences
    6. Return user data (without password)

    Args:
        user_data: UserCreate model with registration data

    Returns:
        UserResponse: Created user data

    Raises:
        HTTPException 400: If username/email already exists
        HTTPException 500: If database error occurs

    Example Request:
        POST /auth/register
        {
            "username": "ronald_mendez",
            "email": "ronald@dataviento.com",
            "password": "SecurePass123!",
            "full_name": "Ronald Mendez",
            "user_type": "standard_user",
            "preferred_units": "metric"
        }

    Example Response:
        {
            "user_id": 1,
            "username": "ronald_mendez",
            "email": "ronald@dataviento.com",
            "full_name": "Ronald Mendez",
            "user_type": "standard_user",
            "preferred_units": "metric",
            "is_active": true,
            "created_at": "2024-11-05T10:00:00",
            "updated_at": "2024-11-05T10:00:00"
        }
    """
    try:
        user_service = UserService()
        created_user = user_service.create_user(user_data)
        return UserResponse(**created_user)

    except ValueError as e:
        # Username/email already exists
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:
        # Database or other error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}",
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User login",
    description="Authenticate user and receive access token + refresh token",
)
def login(credentials: UserLogin) -> TokenResponse:
    """
    Authenticate user and generate tokens

    Process:
    1. Validate username and password
    2. Generate access token (expires in 1 hour)
    3. Generate refresh token (expires in 30 days)
    4. Return tokens + user data

    Args:
        credentials: UserLogin model with username and password

    Returns:
        TokenResponse: Access token, refresh token, and user data

    Raises:
        HTTPException 401: If credentials are invalid

    Example Request:
        POST /auth/login
        {
            "username": "ronald_mendez",
            "password": "SecurePass123!"
        }

    Example Response:
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "expires_in": 3600,
            "user": {
                "user_id": 1,
                "username": "ronald_mendez",
                "email": "ronald@dataviento.com",
                "full_name": "Ronald Mendez",
                "user_type": "standard_user",
                "preferred_units": "metric",
                "is_active": true,
                "created_at": "2024-11-05T10:00:00",
                "updated_at": "2024-11-05T10:00:00"
            }
        }

    Client Usage:
        1. Store access_token for API requests
        2. Store refresh_token securely (httpOnly cookie recommended)
        3. Include access_token in Authorization header:
           Authorization: Bearer {access_token}
    """
    try:
        print(f"Login attempt for user: {credentials}")
        user_service = UserService()

        # Authenticate user
        user = user_service.authenticate_user(credentials.username, credentials.password)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Generate tokens
        access_token = AuthUtils.create_access_token(
            user_id=user["user_id"], username=user["username"], user_type=user["user_type"]
        )

        refresh_token = AuthUtils.create_refresh_token(
            user_id=user["user_id"], username=user["username"]
        )

        # Return response
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=AuthUtils.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
            user=UserResponse(**user),
        )

    except HTTPException:
        raise

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Login failed: {str(e)}"
        )


@router.post(
    "/refresh",
    response_model=Dict[str, str],
    summary="Refresh access token",
    description="Get new access token using refresh token",
)
def refresh_token(refresh_token: str) -> Dict[str, str]:
    """
    Refresh access token using refresh token

    When access token expires (after 1 hour), use this endpoint
    to get a new access token without requiring user to log in again.

    Args:
        refresh_token: Valid refresh token from login

    Returns:
        dict: New access token and token type

    Raises:
        HTTPException 401: If refresh token is invalid or expired

    Example Request:
        POST /auth/refresh
        {
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        }

    Example Response:
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "expires_in": 3600
        }

    Usage Flow:
        1. Access token expires (API returns 401)
        2. Client sends refresh token to /auth/refresh
        3. Server validates refresh token
        4. Server generates new access token
        5. Client uses new access token for API requests
        6. Repeat when access token expires again
        7. If refresh token expires (30 days), user must log in again
    """
    try:
        # Generate new access token from refresh token
        new_access_token = AuthUtils.refresh_access_token(refresh_token)

        if not new_access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": AuthUtils.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}",
        )


@router.get(
    "/verify",
    response_model=MessageResponse,
    summary="Verify token",
    description="Check if current token is valid",
)
def verify_token(current_user: Dict[str, Any] = Depends(get_current_user)) -> MessageResponse:
    """
    Verify if the provided token is valid

    Protected route that requires valid JWT token.
    If token is invalid or expired, returns 401.
    If token is valid, returns success message.

    Args:
        current_user: User info from token (injected by dependency)

    Returns:
        MessageResponse: Success message with user info

    Example Request:
        GET /auth/verify
        Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

    Example Response:
        {
            "message": "Token is valid. Authenticated as ronald_mendez (user_id: 1)",
            "success": true
        }

    Usage:
        - Check token validity before making API requests
        - Verify user is still authenticated
        - Get current user info from token
    """
    return MessageResponse(
        message=f"Token is valid. Authenticated as {current_user['username']} (user_id: {current_user['user_id']})",
        success=True,
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="User logout",
    description="Logout user (client should delete tokens)",
)
def logout(current_user: Dict[str, Any] = Depends(get_current_user)) -> MessageResponse:
    """
    Logout user

    Note: JWT tokens are stateless, so we can't invalidate them server-side
    without a token blacklist. This endpoint is mainly for the client to
    confirm logout action and delete stored tokens.

    For production, implement:
    - Token blacklist in Redis/database
    - Short token expiration times
    - Refresh token rotation

    Args:
        current_user: User info from token (injected by dependency)

    Returns:
        MessageResponse: Success message

    Example Request:
        POST /auth/logout
        Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

    Example Response:
        {
            "message": "Logged out successfully",
            "success": true
        }

    Client Action:
        1. Call this endpoint
        2. Delete stored access_token
        3. Delete stored refresh_token
        4. Redirect to login page
    """
    # In production, add token to blacklist here
    # Example: redis.set(f"blacklist:{token}", "1", ex=3600)

    return MessageResponse(
        message="Logged out successfully",
        success=True
    )