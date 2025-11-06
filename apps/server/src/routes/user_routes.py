"""
User Management Routes

Endpoints:
- GET /users/me - Get current user profile
- PATCH /users/me - Update current user profile
- DELETE /users/me - Delete current user account
- GET /users/me/preferences - Get user preferences
- PATCH /users/me/preferences - Update user preferences
- GET /users/me/locations - Get user favorite locations
- POST /users/me/locations - Add location to favorites
- PATCH /users/me/locations/{location_id} - Update user location
- DELETE /users/me/locations/{location_id} - Remove location from favorites
- POST /users/me/change-password - Change user password
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Dict, Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.users import (
    UserResponse, UserUpdate, UserWithPreferences, UserWithLocations,
    UserPreferencesResponse, UserPreferencesUpdate,
    UserLocationResponse, UserLocationCreate, UserLocationUpdate,
    PasswordChange, MessageResponse
)

from src.services.user_service import UserService
from src.middleware.auth_middleware import get_current_user


# Create router
router = APIRouter(
    prefix="/users",
    tags=["User Management"]
)


# ========================================
# USER PROFILE ENDPOINTS
# ========================================

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Get authenticated user's profile information"
)
def get_my_profile(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> UserResponse:
    """
    Get current user's profile
    
    Returns full user profile including username, email, preferences, etc.
    
    Args:
        current_user: User info from JWT token
        
    Returns:
        UserResponse: User profile data
        
    Example Request:
        GET /users/me
        Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    
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
        user = user_service.get_user_by_id(current_user['user_id'])
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(**user)
    
    except HTTPException:
        raise
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch profile: {str(e)}"
        )


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
    description="Update authenticated user's profile information"
)
def update_my_profile(
    user_data: UserUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> UserResponse:
    """
    Update current user's profile
    
    Only updates fields that are provided. Password updates are handled
    separately via /users/me/change-password endpoint.
    
    Args:
        user_data: UserUpdate model with fields to update
        current_user: User info from JWT token
        
    Returns:
        UserResponse: Updated user profile
        
    Raises:
        HTTPException 400: If email already taken by another user
        
    Example Request:
        PATCH /users/me
        Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
        {
            "email": "new.email@dataviento.com",
            "full_name": "Ronald A. Mendez",
            "preferred_units": "imperial"
        }
    """
    try:
        user_service = UserService()
        updated_user = user_service.update_user(current_user['user_id'], user_data)
        return UserResponse(**updated_user)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )


@router.delete(
    "/me",
    response_model=MessageResponse,
    summary="Delete current user account",
    description="Delete authenticated user's account (soft delete)"
)
def delete_my_account(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> MessageResponse:
    """
    Delete current user's account
    
    Performs soft delete (sets is_active = FALSE) by default.
    User data is retained but account is deactivated.
    
    Args:
        current_user: User info from JWT token
        
    Returns:
        MessageResponse: Success message
        
    Example Request:
        DELETE /users/me
        Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    """
    try:
        user_service = UserService()
        user_service.delete_user(current_user['user_id'], soft_delete=True)
        
        return MessageResponse(
            message="Account deleted successfully",
            success=True
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}"
        )


@router.post(
    "/me/change-password",
    response_model=MessageResponse,
    summary="Change user password",
    description="Change authenticated user's password"
)
def change_my_password(
    password_data: PasswordChange,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> MessageResponse:
    """
    Change current user's password
    
    Requires current password for verification.
    New password must meet strength requirements (validated by Pydantic).
    
    Args:
        password_data: PasswordChange model with current and new passwords
        current_user: User info from JWT token
        
    Returns:
        MessageResponse: Success message
        
    Raises:
        HTTPException 400: If current password is incorrect
        
    Example Request:
        POST /users/me/change-password
        Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
        {
            "current_password": "OldPass123!",
            "new_password": "NewSecurePass456!"
        }
    
    Security Note:
        After password change, user should re-login to get new tokens.
    """
    try:
        user_service = UserService()
        user_service.change_password(
            current_user['user_id'],
            password_data.current_password,
            password_data.new_password
        )
        
        return MessageResponse(
            message="Password changed successfully. Please log in again.",
            success=True
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to change password: {str(e)}"
        )


# ========================================
# USER PREFERENCES ENDPOINTS
# ========================================

@router.get(
    "/me/preferences",
    response_model=UserPreferencesResponse,
    summary="Get user preferences",
    description="Get authenticated user's weather display preferences"
)
def get_my_preferences(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> UserPreferencesResponse:
    """
    Get current user's weather display preferences
    
    Returns preferences for temperature units, wind speed units, etc.
    
    Args:
        current_user: User info from JWT token
        
    Returns:
        UserPreferencesResponse: User preferences
    """
    try:
        user_service = UserService()
        preferences = user_service.get_user_preferences(current_user['user_id'])
        
        if not preferences:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Preferences not found"
            )
        
        return UserPreferencesResponse(**preferences)
    
    except HTTPException:
        raise
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch preferences: {str(e)}"
        )


@router.patch(
    "/me/preferences",
    response_model=UserPreferencesResponse,
    summary="Update user preferences",
    description="Update authenticated user's weather display preferences"
)
def update_my_preferences(
    prefs_data: UserPreferencesUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> UserPreferencesResponse:
    """
    Update current user's preferences
    
    Only updates fields that are provided.
    
    Args:
        prefs_data: UserPreferencesUpdate model with fields to update
        current_user: User info from JWT token
        
    Returns:
        UserPreferencesResponse: Updated preferences
        
    Example Request:
        PATCH /users/me/preferences
        Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
        {
            "preferred_temperature_unit": "fahrenheit",
            "preferred_wind_speed_unit": "mph",
            "default_timezone": "America/New_York"
        }
    """
    try:
        user_service = UserService()
        updated_prefs = user_service.update_user_preferences(
            current_user['user_id'],
            prefs_data
        )
        
        return UserPreferencesResponse(**updated_prefs)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update preferences: {str(e)}"
        )


# ========================================
# USER LOCATIONS (FAVORITES) ENDPOINTS
# ========================================

@router.get(
    "/me/locations",
    response_model=List[UserLocationResponse],
    summary="Get user favorite locations",
    description="Get authenticated user's saved favorite locations (max 10)"
)
def get_my_locations(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[UserLocationResponse]:
    """
    Get current user's favorite locations
    
    Returns all saved locations ordered by:
    1. Primary location first
    2. Then by creation date
    
    Args:
        current_user: User info from JWT token
        
    Returns:
        List[UserLocationResponse]: User's favorite locations (max 10)
    """
    try:
        user_service = UserService()
        locations = user_service.get_user_locations(current_user['user_id'])
        
        return [UserLocationResponse(**loc) for loc in locations]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch locations: {str(e)}"
        )


@router.post(
    "/me/locations",
    response_model=UserLocationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add favorite location",
    description="Add a location to authenticated user's favorites (max 10 locations)"
)
def add_my_location(
    location_data: UserLocationCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> UserLocationResponse:
    """
    Add a location to user's favorites
    
    Restrictions:
    - Maximum 10 locations per user
    - location_id must be in ALLOWED_FAVORITE_LOCATION_IDS (1-10)
    - Cannot add duplicate locations
    
    Args:
        location_data: UserLocationCreate model with location info
        current_user: User info from JWT token
        
    Returns:
        UserLocationResponse: Created user location
        
    Raises:
        HTTPException 400: If validation fails or max locations reached
        
    Example Request:
        POST /users/me/locations
        Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
        {
            "location_id": 1,
            "custom_name": "Home",
            "is_primary": true,
            "notification_enabled": true
        }
    """
    try:
        user_service = UserService()
        created_location = user_service.add_user_location(
            current_user['user_id'],
            location_data
        )
        
        return UserLocationResponse(**created_location)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add location: {str(e)}"
        )


@router.patch(
    "/me/locations/{user_location_id}",
    response_model=UserLocationResponse,
    summary="Update user location",
    description="Update a saved location's settings"
)
def update_my_location(
    user_location_id: int,
    location_data: UserLocationUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> UserLocationResponse:
    """
    Update a saved location
    
    Can update:
    - custom_name: Location nickname
    - is_primary: Set as primary location
    - notification_enabled: Enable/disable notifications
    
    Args:
        user_location_id: User location record ID
        location_data: UserLocationUpdate model with fields to update
        current_user: User info from JWT token
        
    Returns:
        UserLocationResponse: Updated user location
        
    Raises:
        HTTPException 404: If location not found or doesn't belong to user
    """
    try:
        user_service = UserService()
        updated_location = user_service.update_user_location(
            current_user['user_id'],
            user_location_id,
            location_data
        )
        
        return UserLocationResponse(**updated_location)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update location: {str(e)}"
        )


@router.delete(
    "/me/locations/{user_location_id}",
    response_model=MessageResponse,
    summary="Remove favorite location",
    description="Remove a location from authenticated user's favorites"
)
def delete_my_location(
    user_location_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> MessageResponse:
    """
    Remove a location from user's favorites
    
    Args:
        user_location_id: User location record ID
        current_user: User info from JWT token
        
    Returns:
        MessageResponse: Success message
        
    Raises:
        HTTPException 404: If location not found or doesn't belong to user
    """
    try:
        user_service = UserService()
        user_service.delete_user_location(
            current_user['user_id'],
            user_location_id
        )
        
        return MessageResponse(
            message="Location removed from favorites",
            success=True
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete location: {str(e)}"
        )