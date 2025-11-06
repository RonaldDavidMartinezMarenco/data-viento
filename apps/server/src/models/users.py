"""
User Models - Pydantic schemas for user management

This module defines data models for:
- User authentication and profile management
- User preferences (temperature units, wind speed units, etc.)
- User-location associations (favorite locations)

Based on schema.txt tables:
- users
- user_preferences  
- user_locations
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pydantic import BaseModel, EmailStr, Field, field_validator,model_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

from src.constants.default_locations import ALLOWED_FAVORITE_LOCATION_IDS

MAX_USER_LOCATIONS = 10 


# Enums type definitions from schema

class UserType(str, Enum):
    """User role types"""
    ADMIN = "admin"
    STANDARD_USER = "standard_user"


class PreferredUnits(str, Enum):
    """Overall unit system preference"""
    METRIC = "metric"
    IMPERIAL = "imperial"


class TemperatureUnit(str, Enum):
    """Temperature measurement units"""
    CELSIUS = "celsius"
    FAHRENHEIT = "fahrenheit"
    KELVIN = "kelvin"


class WindSpeedUnit(str, Enum):
    """Wind speed measurement units"""
    KMH = "kmh"      # Kilometers per hour
    MPH = "mph"      # Miles per hour
    MS = "ms"        # Meters per second
    KNOTS = "knots"  # Nautical miles per hour


class PrecipitationUnit(str, Enum):
    """Precipitation measurement units"""
    MM = "mm"        # Millimeters
    INCH = "inch"    # Inches
    
    
# user preferences models    

class UserPreferencesBase(BaseModel):
    """
    Base model for user preferences
    
    Contains all weather display preferences:
    - Temperature unit (celsius, fahrenheit, kelvin)
    - Wind speed unit (kmh, mph, m/s, knots)
    - Precipitation unit (mm, inches)
    - Timezone preference
    - Notification settings
    """
    preferred_temperature_unit: TemperatureUnit = Field(
        default=TemperatureUnit.CELSIUS,
        description="Preferred temperature display unit"
    )
    preferred_wind_speed_unit: WindSpeedUnit = Field(
        default=WindSpeedUnit.KMH,
        description="Preferred wind speed display unit"
    )
    preferred_precipitation_unit: PrecipitationUnit = Field(
        default=PrecipitationUnit.MM,
        description="Preferred precipitation display unit"
    )
    default_timezone: str = Field(
        default="auto",
        max_length=50,
        description="Default timezone (e.g., 'America/Bogota' or 'auto' for location-based)"
    )
    notification_enabled: bool = Field(
        default=True,
        description="Enable/disable all notifications"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "preferred_temperature_unit": "celsius",
                "preferred_wind_speed_unit": "kmh",
                "preferred_precipitation_unit": "mm",
                "default_timezone": "America/Bogota",
                "notification_enabled": True
            }
        }
    }


class UserPreferencesCreate(UserPreferencesBase):
    """
    Schema for creating new user preferences
    
    Inherits all fields from UserPreferencesBase.
    Used when a new user registers.
    """
    pass


class UserPreferencesUpdate(BaseModel):
    """
    Schema for updating user preferences
    
    All fields are optional - only send what needs to be updated.
    Used in PATCH /api/users/{user_id}/preferences endpoint.
    """
    preferred_temperature_unit: Optional[TemperatureUnit] = None
    preferred_wind_speed_unit: Optional[WindSpeedUnit] = None
    preferred_precipitation_unit: Optional[PrecipitationUnit] = None
    default_timezone: Optional[str] = Field(None, max_length=50)
    notification_enabled: Optional[bool] = None


class UserPreferencesResponse(UserPreferencesBase):
    """
    Schema for returning user preferences from API
    
    Includes database metadata:
    - preference_id: Database primary key
    - user_id: Foreign key to users table
    - created_at: When preferences were created
    """
    preference_id: int = Field(..., description="Preference record ID")
    user_id: int = Field(..., description="Owner user ID")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = {
        "from_attributes": True 
    }

# user locations models

class UserLocationBase(BaseModel):
    """
    Base model for user-location associations
    
    Allows users to:
    - Save favorite locations (max 10)
    - Set custom names (e.g., "Home", "Office", "Beach House")
    - Mark primary location (default for weather display)
    - Enable/disable notifications per location
    
    Restrictions:
    - location_id must be in ALLOWED_FAVORITE_LOCATION_IDS (1-10)
    - Users can only save max 10 locations
    """
    location_id: int = Field(
        ..., 
        description="Reference to locations table (must be in allowed list)",
        gt=0
    )
    custom_name: Optional[str] = Field(
        None,
        max_length=100,
        description="User's custom name for this location (e.g., 'Home', 'Office')"
    )
    is_primary: bool = Field(
        default=False,
        description="Is this the user's primary/default location?"
    )
    notification_enabled: bool = Field(
        default=True,
        description="Receive alerts for this location?"
    )

    @field_validator('location_id')
    @classmethod
    def validate_location_id(cls, v: int) -> int:
        """
        Validate location_id is in allowed list
        
        Ensures users can only select from the 10 default locations.
        Raises ValueError if location_id is not in ALLOWED_FAVORITE_LOCATION_IDS.
        
        Args:
            v: location_id to validate
            
        Returns:
            int: Valid location_id
            
        Raises:
            ValueError: If location_id not in allowed list
        """
        if v not in ALLOWED_FAVORITE_LOCATION_IDS:
            raise ValueError(
                f"Location ID {v} is not available. "
                f"Please choose from: {sorted(ALLOWED_FAVORITE_LOCATION_IDS)}"
            )
        return v

    @field_validator('custom_name')
    @classmethod
    def validate_custom_name(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate custom_name field
        
        Ensures:
        - No empty strings (use None instead)
        - Trimmed whitespace
        - Reasonable length
        
        Args:
            v: custom_name to validate
            
        Returns:
            Optional[str]: Cleaned custom_name or None
        """
        if v is not None:
            # Strip whitespace
            v = v.strip()
            # Convert empty string to None
            if not v:
                return None
            # Check length after stripping
            if len(v) > 100:
                raise ValueError("Custom name must be 100 characters or less")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "location_id": 1,
                "custom_name": "Home",
                "is_primary": True,
                "notification_enabled": True
            }
        }
    }


class UserLocationCreate(UserLocationBase):
    """
    Schema for adding a location to user's favorites
    
    Used in POST /api/users/{user_id}/locations endpoint.
    
    Validation:
    - Checks location_id is in ALLOWED_FAVORITE_LOCATION_IDS
    - Service layer should check user doesn't exceed MAX_USER_LOCATIONS (10)
    """
    pass


class UserLocationUpdate(BaseModel):
    """
    Schema for updating user location settings
    
    All fields optional - only update what changed.
    Used in PATCH /api/users/{user_id}/locations/{user_location_id} endpoint.
    
    Note: location_id cannot be changed (must delete and re-add)
    """
    custom_name: Optional[str] = Field(None, max_length=100)
    is_primary: Optional[bool] = None
    notification_enabled: Optional[bool] = None

    @field_validator('custom_name')
    @classmethod
    def validate_custom_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean custom_name"""
        if v is not None:
            v = v.strip()
            if not v:
                return None
            if len(v) > 100:
                raise ValueError("Custom name must be 100 characters or less")
        return v


class UserLocationResponse(UserLocationBase):
    """
    Schema for returning user location from API
    
    Includes:
    - user_location_id: Database primary key
    - user_id: Owner user ID
    - created_at: When location was added
    - last_accessed: Last time user viewed this location
    """
    user_location_id: int = Field(..., description="User location record ID")
    user_id: int = Field(..., description="Owner user ID")
    created_at: datetime = Field(..., description="When location was added")
    last_accessed: Optional[datetime] = Field(None, description="Last accessed timestamp")

    model_config = {
        "from_attributes": True
    }
    

# user models
class UserBase(BaseModel):
    """
    Base model for user account
    
    Contains public user information:
    - username: Unique identifier for login
    - email: For notifications and password recovery
    - full_name: Display name
    - user_type: admin or standard_user
    - preferred_units: metric or imperial (overall preference)
    
    Does NOT include password_hash (security).
    """
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Unique username for login"
    )
    email: EmailStr = Field(
        ...,
        description="User's email address (unique)"
    )
    full_name: Optional[str] = Field(
        None,
        max_length=150,
        description="User's full display name"
    )
    user_type: UserType = Field(
        default=UserType.STANDARD_USER,
        description="User role: admin or standard_user"
    )
    preferred_units: PreferredUnits = Field(
        default=PreferredUnits.METRIC,
        description="Overall unit system preference"
    )

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """
        Validate username field
        
        Rules:
        - Must be alphanumeric (can include underscores)
        - No spaces
        - Lowercase only
        - 3-50 characters
        
        Args:
            v: username to validate
            
        Returns:
            str: Cleaned and validated username
            
        Raises:
            ValueError: If username doesn't meet requirements
        """
        # Strip whitespace
        v = v.strip()
        
        # Convert to lowercase
        v = v.lower()
        
        # Check for valid characters
        if not v.replace('_', '').isalnum():
            raise ValueError("Username can only contain letters, numbers, and underscores")
        
        # Check length
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        if len(v) > 50:
            raise ValueError("Username must be 50 characters or less")
        
        return v

    @field_validator('full_name')
    @classmethod
    def validate_full_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean full_name"""
        if v is not None:
            v = v.strip()
            if not v:
                return None
            if len(v) > 150:
                raise ValueError("Full name must be 150 characters or less")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "ronald_mendez",
                "email": "ronald@dataviento.com",
                "full_name": "Ronald Mendez",
                "user_type": "standard_user",
                "preferred_units": "metric"
            }
        }
    }


class UserCreate(UserBase):
    """
    Schema for user registration
    
    Includes password field (plain text) which will be:
    1. Validated for strength
    2. Hashed before storing in database (never store plain text!)
    
    Used in POST /api/auth/register endpoint.
    """
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="User password (will be hashed before storage)"
    )

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """
        Validate password strength
        
        Requirements:
        - At least 8 characters
        - Contains uppercase letter
        - Contains lowercase letter
        - Contains number
        
        Args:
            v: password to validate
            
        Returns:
            str: Valid password
            
        Raises:
            ValueError: If password doesn't meet requirements
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        
        # Check for uppercase
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        
        # Check for lowercase
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        
        # Check for number
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "ronald_mendez",
                "email": "ronald@dataviento.com",
                "full_name": "Ronald Mendez",
                "password": "SecurePass123!",
                "user_type": "standard_user",
                "preferred_units": "metric"
            }
        }
    }


class UserUpdate(BaseModel):
    """
    Schema for updating user profile
    
    All fields optional - only update what changed.
    Password is handled separately via change password endpoint.
    
    Used in PATCH /api/users/{user_id} endpoint.
    """
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=150)
    preferred_units: Optional[PreferredUnits] = None
    is_active: Optional[bool] = None

    @field_validator('full_name')
    @classmethod
    def validate_full_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean full_name"""
        if v is not None:
            v = v.strip()
            if not v:
                return None
            if len(v) > 150:
                raise ValueError("Full name must be 150 characters or less")
        return v


class UserResponse(UserBase):
    """
    Schema for returning user data from API
    
    Includes:
    - user_id: Database primary key
    - is_active: Account status (for soft deletes)
    - created_at: Account creation timestamp
    - updated_at: Last profile update timestamp
    
    Does NOT include:
    - password_hash (security - never expose!)
    """
    user_id: int = Field(..., description="User's unique ID")
    is_active: bool = Field(..., description="Is account active?")
    created_at: datetime = Field(..., description="Account creation date")
    updated_at: datetime = Field(..., description="Last update date")

    model_config = {
        "from_attributes": True
    }


class UserWithPreferences(UserResponse):
    """
    Extended user response including preferences
    
    Combines user profile + preferences in one response.
    Useful for dashboard/profile page where both are needed.
    """
    preferences: Optional[UserPreferencesResponse] = Field(
        None,
        description="User's weather display preferences"
    )

    model_config = {
        "from_attributes": True
    }


class UserWithLocations(UserResponse):
    """
    Extended user response including saved locations
    
    Combines user profile + favorite locations (max 10).
    Useful for user dashboard showing all saved locations.
    """
    locations: List[UserLocationResponse] = Field(
        default_factory=list,
        description="User's saved locations (max 10)"
    )

    @model_validator(mode='after')
    def validate_location_count(self) -> 'UserWithLocations':
        """
        Validate user doesn't exceed maximum locations
        
        Ensures users can't have more than MAX_USER_LOCATIONS (10).
        This is a safety check - should be enforced at creation too.
        
        Returns:
            UserWithLocations: Validated instance
            
        Raises:
            ValueError: If user has more than 10 locations
        """
        if len(self.locations) > MAX_USER_LOCATIONS:
            raise ValueError(
                f"User cannot have more than {MAX_USER_LOCATIONS} locations. "
                f"Found: {len(self.locations)}"
            )
        return self

    model_config = {
        "from_attributes": True
    }


class UserFull(UserResponse):
    """
    Complete user profile with all related data
    
    Includes:
    - User profile
    - Preferences
    - Saved locations (max 10)
    
    Used for admin panel or detailed user profile page.
    """
    preferences: Optional[UserPreferencesResponse] = None
    locations: List[UserLocationResponse] = Field(
        default_factory=list,
        description="User's saved locations (max 10)"
    )

    @model_validator(mode='after')
    def validate_location_count(self) -> 'UserFull':
        """Validate user doesn't exceed maximum locations"""
        if len(self.locations) > MAX_USER_LOCATIONS:
            raise ValueError(
                f"User cannot have more than {MAX_USER_LOCATIONS} locations. "
                f"Found: {len(self.locations)}"
            )
        return self

    model_config = {
        "from_attributes": True
    }

# authentication models


class UserLogin(BaseModel):
    """
    Schema for user login
    
    Used in POST /api/auth/login endpoint.
    Returns JWT token on success.
    """
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="User password")

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "ronald_mendez",
                "password": "SecurePass123!"
            }
        }
    }


class TokenResponse(BaseModel):
    """
    Schema for authentication token response
    
    Returned after successful login.
    Client should include token in Authorization header for protected routes.
    """
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: UserResponse = Field(..., description="Authenticated user data")

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {
                    "user_id": 1,
                    "username": "ronald_mendez",
                    "email": "ronald@dataviento.com",
                    "full_name": "Ronald Mendez",
                    "user_type": "standard_user",
                    "preferred_units": "metric",
                    "is_active": True,
                    "created_at": "2024-11-05T10:00:00",
                    "updated_at": "2024-11-05T10:00:00"
                }
            }
        }
    }


class PasswordChange(BaseModel):
    """
    Schema for changing user password
    
    Used in POST /api/users/{user_id}/change-password endpoint.
    
    Security:
    - Requires current password (prevents unauthorized changes)
    - New password must meet strength requirements
    - Will invalidate existing tokens (force re-login)
    """
    current_password: str = Field(..., description="Current password for verification")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="New password"
    )

    @model_validator(mode='after')
    def validate_passwords(self) -> 'PasswordChange':
        """
        ✅ Validate new password meets requirements and differs from current
        
        Returns:
            PasswordChange: Validated instance
            
        Raises:
            ValueError: If validation fails
        """
        new_pwd = self.new_password
        
        # Check strength
        if len(new_pwd) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in new_pwd):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in new_pwd):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in new_pwd):
            raise ValueError("Password must contain at least one number")
        
        # Check it's different from current
        if new_pwd == self.current_password:
            raise ValueError("New password must be different from current password")
        
        return self

    model_config = {
        "json_schema_extra": {
            "example": {
                "current_password": "OldPass123!",
                "new_password": "NewSecurePass456!"
            }
        }
    }


class PasswordReset(BaseModel):
    """
    Schema for password reset (forgot password flow)
    
    Two-step process:
    1. POST /api/auth/forgot-password (send reset email)
    2. POST /api/auth/reset-password (set new password with token)
    
    This model is for step 2.
    """
    reset_token: str = Field(..., description="Token from password reset email")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="New password"
    )

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        return v


# utility
class MessageResponse(BaseModel):
    """
    Generic success/error message response
    
    Used for operations that don't return data:
    - DELETE operations
    - Password changes
    - Account activation/deactivation
    """
    message: str = Field(..., description="Success or error message")
    success: bool = Field(default=True, description="Operation success status")

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "User location deleted successfully",
                "success": True
            }
        }
    }
    
    