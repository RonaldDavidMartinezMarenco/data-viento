"""
User Service - Business logic for user management

Handles:
- User registration and authentication
- Profile management
- User preferences management
- User locations (favorite locations)
- Password management
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


from typing import Optional, Dict, Any, List
from datetime import datetime

from src.models.users import (
    UserCreate, UserUpdate, UserResponse,
    UserPreferencesCreate, UserPreferencesUpdate, UserPreferencesResponse,
    UserLocationCreate, UserLocationUpdate, UserLocationResponse,
    MAX_USER_LOCATIONS
)

from src.services.base_service import BaseService
from src.utils.auth import AuthUtils
from src.constants.default_locations import ALLOWED_FAVORITE_LOCATION_IDS


class UserService(BaseService):
    """
    Service class for user management operations
    
    Provides methods for:
    - User CRUD operations
    - Authentication and authorization
    - User preferences management
    - User locations management
    """
    
    def __init__(self):
        """Initialize UserService with database connection"""
        super().__init__()
        self.auth_utils = AuthUtils()
    
    
    # ========================================
    # USER CRUD OPERATIONS
    # ========================================
    
    def create_user(self, user_data: UserCreate) -> Dict[str, Any]:
        """
        Create a new user account
        
        Process:
        1. Check if username/email already exists
        2. Hash password (never store plain text!)
        3. Insert user into database
        4. Create default preferences for user
        5. Return created user data (without password)
        
        Args:
            user_data: UserCreate model with validated data
            
        Returns:
            dict: Created user data
            
        Raises:
            ValueError: If username/email already exists
            Exception: If database operation fails
        """
        try:
            # Step 1: Check if username already exists
            check_username = "SELECT user_id FROM users WHERE username = %s"
            existing_username = self.db.execute_query(check_username, (user_data.username,))
            
            if existing_username:
                self.logger.warning(f"Username already exists: {user_data.username}")
                raise ValueError(f"Username '{user_data.username}' is already taken")
            
            # Step 2: Check if email already exists
            check_email = "SELECT user_id FROM users WHERE email = %s"
            existing_email = self.db.execute_query(check_email, (user_data.email,))
            
            if existing_email:
                self.logger.warning(f"email already exists: {user_data.email}")
                raise ValueError(f"Email '{user_data.email}' is already registered")
            
            # Step 3: Hash password
            password_hash = self.auth_utils.hash_password(user_data.password)
            self.logger.debug("Password hashed successfully")
            
            # Step 4: Insert user into database
            insert_query = """
            INSERT INTO users 
            (username, email, password_hash, full_name, user_type, preferred_units, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, TRUE)
            """
            
            user_id = self.db.execute_insert(
                insert_query,
                (
                    user_data.username,
                    user_data.email,
                    password_hash,
                    user_data.full_name,
                    user_data.user_type.value,
                    user_data.preferred_units.value
                )
            )
            if user_id == -1:
                self.logger.error("Failed to insert user into database")
                raise Exception("Failed to insert user into database")
        
            # Step 5: Get created user
            user = self.get_user_by_id(user_id)
            
            if not user:
                self.logger.error(f"Failed to retrieve created user with ID: {user_id}")
                raise Exception("Failed to retrieve created user")
            
            # Step 6: Create default preferences for user
            self._create_default_preferences(user_id, user_data.preferred_units.value)
            self.logger.info(f"Default preferences created for user ID: {user_id}")
            
            return user
        
        except ValueError as e:
            # Re-raise validation errors
            raise e
        except Exception as e:
            self.logger.error(f"Error creating user: {str(e)}", exc_info=True)
            raise Exception(f"Failed to create user: {str(e)}")
    
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user by ID
        
        Args:
            user_id: User's unique ID
            
        Returns:
            dict: User data (without password) or None if not found
        """
        query = """
        SELECT 
            user_id, username, email, full_name, user_type, preferred_units,
            is_active, created_at, updated_at
        FROM users
        WHERE user_id = %s
        """
        
        result = self.db.execute_query(query, (user_id,))
        
        if not result:
            return None
        
        return self._map_user_row(result[0])
    
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get user by username (public method)
        
        Args:
            username: Username to search for
            
        Returns:
            dict: User data or None if not found
        """
        return self._get_user_by_username(username)
    
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email
        
        Args:
            email: Email to search for
            
        Returns:
            dict: User data or None if not found
        """
        query = """
        SELECT 
            user_id, username, email, full_name, user_type, preferred_units,
            is_active, created_at, updated_at
        FROM users
        WHERE email = %s
        """
        
        result = self.db.execute_query(query, (email,))
        
        if not result:
            return None
        
        return self._map_user_row(result[0])
    
    
    def update_user(self, user_id: int, user_data: UserUpdate) -> Dict[str, Any]:
        """
        Update user profile
        
        Only updates fields that are provided (not None).
        Password updates are handled separately.
        
        Args:
            user_id: User ID to update
            user_data: UserUpdate model with fields to update
            
        Returns:
            dict: Updated user data
            
        Raises:
            ValueError: If user not found or email already taken
        """
        # Check user exists
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Build dynamic update query based on provided fields
        update_fields = []
        params = []
        
        if user_data.email is not None:
            # Check email not taken by another user
            existing = self.get_user_by_email(user_data.email)
            if existing and existing['user_id'] != user_id:
                raise ValueError(f"Email '{user_data.email}' is already in use")
            
            update_fields.append("email = %s")
            params.append(user_data.email)
        
        if user_data.full_name is not None:
            update_fields.append("full_name = %s")
            params.append(user_data.full_name)
        
        if user_data.preferred_units is not None:
            update_fields.append("preferred_units = %s")
            params.append(user_data.preferred_units.value)
        
        if user_data.is_active is not None:
            update_fields.append("is_active = %s")
            params.append(user_data.is_active)
        
        # If nothing to update, return current user
        if not update_fields:
            return user
        
        # Add updated_at
        update_fields.append("updated_at = NOW()")
        
        # Build and execute query
        query = f"""
        UPDATE users 
        SET {', '.join(update_fields)}
        WHERE user_id = %s
        """
        params.append(user_id)
        
        self.db.execute_update(query, tuple(params))
        
        # Return updated user
        return self.get_user_by_id(user_id)
    
    
    def delete_user(self, user_id: int, soft_delete: bool = True) -> bool:
        """
        Delete user account
        
        Args:
            user_id: User ID to delete
            soft_delete: If True, set is_active=False. If False, hard delete.
            
        Returns:
            bool: True if deleted successfully
            
        Raises:
            ValueError: If user not found
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        if soft_delete:
            # Soft delete: deactivate account
            query = "UPDATE users SET is_active = FALSE WHERE user_id = %s"
        else:
            # Hard delete: remove from database
            # Note: This will cascade delete user_preferences and user_locations
            # if foreign keys are set up with ON DELETE CASCADE
            query = "DELETE FROM users WHERE user_id = %s"
        
        self.db.execute_update(query, (user_id,))
        return True
    
    
    # ========================================
    # AUTHENTICATION
    # ========================================
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user with username/email and password
        
        Args:
            username: Username or email
            password: Plain text password
            
        Returns:
            dict: User data if authentication successful, None otherwise
        """
        # Try to find user by username or email
        user = self._get_user_by_username(username)
        if not user:
            user = self.get_user_by_email(username)
        
        if not user:
            return None
        
        # Check if account is active
        if not user.get('is_active', False):
            return None
        
        # Get password hash from database
        query = "SELECT password_hash FROM users WHERE user_id = %s"
        result = self.db.execute_query(query, (user['user_id'],))
        
        if not result:
            return None
        
        password_hash = result[0][0]
        
        # Verify password
        if self.auth_utils.verify_password(password, password_hash):
            return user
        
        return None
    
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """
        Change user password
        
        Args:
            user_id: User ID
            current_password: Current password for verification
            new_password: New password (already validated by Pydantic)
            
        Returns:
            bool: True if password changed successfully
            
        Raises:
            ValueError: If current password is incorrect or user not found
        """
        # Get user's current password hash
        query = "SELECT password_hash FROM users WHERE user_id = %s"
        result = self.db.execute_query(query, (user_id,))
        
        if not result:
            raise ValueError("User not found")
        
        current_hash = result[0][0]
        
        # Verify current password
        if not self.auth_utils.verify_password(current_password, current_hash):
            raise ValueError("Current password is incorrect")
        
        # Hash new password
        new_hash = self.auth_utils.hash_password(new_password)
        
        # Update password
        update_query = """
        UPDATE users 
        SET password_hash = %s, updated_at = NOW()
        WHERE user_id = %s
        """
        
        self.db.execute_update(update_query, (new_hash, user_id))
        return True
    
    
    # ========================================
    # USER PREFERENCES
    # ========================================
    
    def get_user_preferences(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user's weather display preferences
        
        Args:
            user_id: User ID
            
        Returns:
            dict: User preferences or None if not found
        """
        query = """
        SELECT 
            preference_id, user_id, preferred_temperature_unit,
            preferred_wind_speed_unit, preferred_precipitation_unit,
            default_timezone, notification_enabled, created_at
        FROM user_preferences
        WHERE user_id = %s
        """
        
        result = self.db.execute_query(query, (user_id,))
        
        if not result:
            return None
        
        row = result[0]
        return {
            'preference_id': row[0],
            'user_id': row[1],
            'preferred_temperature_unit': row[2],
            'preferred_wind_speed_unit': row[3],
            'preferred_precipitation_unit': row[4],
            'default_timezone': row[5],
            'notification_enabled': bool(row[6]),
            'created_at': row[7]
        }
    
    
    def update_user_preferences(
        self, 
        user_id: int, 
        prefs_data: UserPreferencesUpdate
    ) -> Dict[str, Any]:
        """
        Update user preferences
        
        Args:
            user_id: User ID
            prefs_data: UserPreferencesUpdate model with fields to update
            
        Returns:
            dict: Updated preferences
            
        Raises:
            ValueError: If preferences not found
        """
        # Check preferences exist
        existing = self.get_user_preferences(user_id)
        if not existing:
            raise ValueError(f"Preferences not found for user {user_id}")
        
        # Build dynamic update query
        update_fields = []
        params = []
        
        if prefs_data.preferred_temperature_unit is not None:
            update_fields.append("preferred_temperature_unit = %s")
            params.append(prefs_data.preferred_temperature_unit.value)
        
        if prefs_data.preferred_wind_speed_unit is not None:
            update_fields.append("preferred_wind_speed_unit = %s")
            params.append(prefs_data.preferred_wind_speed_unit.value)
        
        if prefs_data.preferred_precipitation_unit is not None:
            update_fields.append("preferred_precipitation_unit = %s")
            params.append(prefs_data.preferred_precipitation_unit.value)
        
        if prefs_data.default_timezone is not None:
            update_fields.append("default_timezone = %s")
            params.append(prefs_data.default_timezone)
        
        if prefs_data.notification_enabled is not None:
            update_fields.append("notification_enabled = %s")
            params.append(prefs_data.notification_enabled)
        
        # If nothing to update, return current preferences
        if not update_fields:
            return existing
        
        # Build and execute query
        query = f"""
        UPDATE user_preferences 
        SET {', '.join(update_fields)}
        WHERE user_id = %s
        """
        params.append(user_id)
        
        self.db.execute_update(query, tuple(params))
        
        # Return updated preferences
        return self.get_user_preferences(user_id)
    
    
    # ========================================
    # USER LOCATIONS (Favorites)
    # ========================================
    
    def add_user_location(
        self, 
        user_id: int, 
        location_data: UserLocationCreate
    ) -> Dict[str, Any]:
        """
        Add a location to user's favorites
        
        Validation:
        1. Location ID is in ALLOWED_FAVORITE_LOCATION_IDS (Pydantic handles this)
        2. User doesn't already have this location
        3. User hasn't reached MAX_USER_LOCATIONS (10)
        4. If is_primary=True, unset other primary locations
        
        Args:
            user_id: User ID
            location_data: UserLocationCreate model with validated data
            
        Returns:
            dict: Created user_location record
            
        Raises:
            ValueError: If validation fails
        """
        # Step 1: Check if user already has this location
        check_duplicate = """
        SELECT user_location_id 
        FROM user_locations 
        WHERE user_id = %s AND location_id = %s
        """
        duplicate = self.db.execute_query(
            check_duplicate, 
            (user_id, location_data.location_id)
        )
        
        if duplicate:
            raise ValueError(
                f"Location {location_data.location_id} is already in your favorites"
            )
        
        # Step 2: Check if user has reached maximum locations (10)
        count_query = "SELECT COUNT(*) FROM user_locations WHERE user_id = %s"
        count_result = self.db.execute_query(count_query, (user_id,))
        current_count = count_result[0][0] if count_result else 0
        
        if current_count >= MAX_USER_LOCATIONS:
            raise ValueError(
                f"Maximum {MAX_USER_LOCATIONS} locations allowed. "
                f"Please delete a location before adding a new one."
            )
        
        # Step 3: If is_primary=True, unset other primary locations
        if location_data.is_primary:
            unset_primary = """
            UPDATE user_locations 
            SET is_primary = FALSE 
            WHERE user_id = %s AND is_primary = TRUE
            """
            self.db.execute_update(unset_primary, (user_id,))
        
        # Step 4: Insert new location
        insert_query = """
        INSERT INTO user_locations 
        (user_id, location_id, custom_name, is_primary, notification_enabled)
        VALUES (%s, %s, %s, %s, %s)
        """
        
        self.db.execute_insert(
            insert_query,
            (
                user_id,
                location_data.location_id,
                location_data.custom_name,
                location_data.is_primary,
                location_data.notification_enabled
            )
        )
        
        # Get the created record
        get_created = """
        SELECT user_location_id, user_id, location_id, custom_name, 
               is_primary, notification_enabled, created_at, last_accessed
        FROM user_locations 
        WHERE user_id = %s AND location_id = %s
        """
        result = self.db.execute_query(
            get_created, 
            (user_id, location_data.location_id)
        )
        
        if result:
            return self._map_user_location_row(result[0])
        
        raise Exception("Failed to retrieve created location")
    
    
    def get_user_locations(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all favorite locations for a user
        
        Returns locations ordered by:
        1. Primary location first
        2. Then by creation date (oldest first)
        
        Args:
            user_id: User ID
            
        Returns:
            list: User's saved locations (max 10)
        """
        query = """
        SELECT user_location_id, user_id, location_id, custom_name,
               is_primary, notification_enabled, created_at, last_accessed
        FROM user_locations
        WHERE user_id = %s
        ORDER BY is_primary DESC, created_at ASC
        """
        
        results = self.db.execute_query(query, (user_id,))
        
        locations = []
        for row in results:
            locations.append(self._map_user_location_row(row))
        
        return locations
    
    
    def update_user_location(
        self,
        user_id: int,
        user_location_id: int,
        location_data: UserLocationUpdate
    ) -> Dict[str, Any]:
        """
        Update user location settings
        
        Args:
            user_id: User ID (for authorization)
            user_location_id: User location record ID
            location_data: UserLocationUpdate model with fields to update
            
        Returns:
            dict: Updated user_location record
            
        Raises:
            ValueError: If location not found or doesn't belong to user
        """
        # Check location exists and belongs to user
        check_query = """
        SELECT user_location_id 
        FROM user_locations 
        WHERE user_location_id = %s AND user_id = %s
        """
        exists = self.db.execute_query(check_query, (user_location_id, user_id))
        
        if not exists:
            raise ValueError("Location not found or doesn't belong to you")
        
        # If setting as primary, unset other primary locations
        if location_data.is_primary is True:
            unset_primary = """
            UPDATE user_locations 
            SET is_primary = FALSE 
            WHERE user_id = %s AND is_primary = TRUE
            """
            self.db.execute_update(unset_primary, (user_id,))
        
        # Build dynamic update query
        update_fields = []
        params = []
        
        if location_data.custom_name is not None:
            update_fields.append("custom_name = %s")
            params.append(location_data.custom_name)
        
        if location_data.is_primary is not None:
            update_fields.append("is_primary = %s")
            params.append(location_data.is_primary)
        
        if location_data.notification_enabled is not None:
            update_fields.append("notification_enabled = %s")
            params.append(location_data.notification_enabled)
        
        # If nothing to update, get current location
        if not update_fields:
            get_query = """
            SELECT user_location_id, user_id, location_id, custom_name,
                   is_primary, notification_enabled, created_at, last_accessed
            FROM user_locations
            WHERE user_location_id = %s
            """
            result = self.db.execute_query(get_query, (user_location_id,))
            return self._map_user_location_row(result[0]) if result else None
        
        # Build and execute update query
        query = f"""
        UPDATE user_locations 
        SET {', '.join(update_fields)}
        WHERE user_location_id = %s AND user_id = %s
        """
        params.extend([user_location_id, user_id])
        
        self.db.execute_update(query, tuple(params))
        
        # Return updated location
        get_updated = """
        SELECT user_location_id, user_id, location_id, custom_name,
               is_primary, notification_enabled, created_at, last_accessed
        FROM user_locations
        WHERE user_location_id = %s
        """
        result = self.db.execute_query(get_updated, (user_location_id,))
        
        if result:
            return self._map_user_location_row(result[0])
        
        raise Exception("Failed to retrieve updated location")
    
    
    def delete_user_location(self, user_id: int, user_location_id: int) -> bool:
        """
        Delete a location from user's favorites
        
        Args:
            user_id: User ID (for authorization)
            user_location_id: User location record ID
            
        Returns:
            bool: True if deleted successfully
            
        Raises:
            ValueError: If location not found or doesn't belong to user
        """
        # Check location exists and belongs to user
        check_query = """
        SELECT user_location_id 
        FROM user_locations 
        WHERE user_location_id = %s AND user_id = %s
        """
        exists = self.db.execute_query(check_query, (user_location_id, user_id))
        
        if not exists:
            raise ValueError("Location not found or doesn't belong to you")
        
        # Delete location
        delete_query = """
        DELETE FROM user_locations 
        WHERE user_location_id = %s AND user_id = %s
        """
        
        self.db.execute_update(delete_query, (user_location_id, user_id))
        return True
    
    
    def update_location_access(self, user_id: int, location_id: int) -> None:
        """
        Update last_accessed timestamp when user views a location
        
        Args:
            user_id: User ID
            location_id: Location ID
        """
        query = """
        UPDATE user_locations 
        SET last_accessed = NOW()
        WHERE user_id = %s AND location_id = %s
        """
        
        self.db.execute_update(query, (user_id, location_id))
    
    
    # ========================================
    # PRIVATE HELPER METHODS
    # ========================================
    
    def _get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Internal method to get user by username"""
        query = """
        SELECT 
            user_id, username, email, full_name, user_type, preferred_units,
            is_active, created_at, updated_at
        FROM users
        WHERE username = %s
        """
        
        result = self.db.execute_query(query, (username,))
        
        if not result:
            return None
        
        return self._map_user_row(result[0])
    
    
    def _map_user_row(self, row: tuple) -> Dict[str, Any]:
        """Map database row to user dictionary"""
        return {
            'user_id': row[0],
            'username': row[1],
            'email': row[2],
            'full_name': row[3],
            'user_type': row[4],
            'preferred_units': row[5],
            'is_active': bool(row[6]),
            'created_at': row[7],
            'updated_at': row[8]
        }
    
    
    def _map_user_location_row(self, row: tuple) -> Dict[str, Any]:
        """Map database row to user_location dictionary"""
        return {
            'user_location_id': row[0],
            'user_id': row[1],
            'location_id': row[2],
            'custom_name': row[3],
            'is_primary': bool(row[4]),
            'notification_enabled': bool(row[5]),
            'created_at': row[6],
            'last_accessed': row[7]
        }
    
    
    def _create_default_preferences(self, user_id: int, preferred_units: str = 'metric') -> None:
        """
        Create default preferences for new user
        
        Called automatically when a user is created.
        
        Args:
            user_id: User ID for new preferences
        """
        if preferred_units == 'imperial':
            temperature_unit = 'fahrenheit'
            wind_speed_unit = 'mph'
            precipitation_unit = 'inch'
        else:
            temperature_unit = 'celsius'
            wind_speed_unit = 'kmh'
            precipitation_unit = 'mm'
            
        query = """
        INSERT INTO user_preferences 
        (user_id, preferred_temperature_unit, preferred_wind_speed_unit,
         preferred_precipitation_unit, default_timezone, notification_enabled)
        VALUES (%s, %s, %s, %s, 'auto', TRUE)
        """
        
        result = self.db.execute_insert(query, (user_id,temperature_unit,wind_speed_unit,precipitation_unit))
        
        if result == -1:
            self.logger.error(f"Failed to create default preferences for user {user_id}")
            raise Exception("Failed to create default preferences")
    
        self.logger.info(
            f"Created {preferred_units} preferences for user {user_id}: "
            f"{temperature_unit}, {wind_speed_unit}, {precipitation_unit}"
        )
        
        
    def __del__(self):
        """Cleanup: Disconnect database on object destruction"""
        if hasattr(self, 'db'):
            self.db.disconnect()