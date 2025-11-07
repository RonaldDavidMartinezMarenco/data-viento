"""
Location Service

Handles location management operations:
- Get or create locations
- Query locations by ID or coordinates
- Geocoding (converting names to coordinates)

Maps to tables:
- locations
- location_names
"""

import logging
import sys
from typing import Optional, Dict, Any, Tuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.services.base_service import BaseService
from src.db.database import DatabaseConnection


class LocationService(BaseService):
    """
    Service for location management
    
    Purpose:
    - Ensure location exists before saving weather data
    - Avoid duplicate locations
    - Link all weather data to proper location_id
    """
    
    def __init__(self, db: Optional[DatabaseConnection] = None):
        """Initialize location service"""
        super().__init__(db)
    
    def get_or_create_location(
        self,
        name: str,
        latitude: float,
        longitude: float,
        **kwargs
    ) -> int:
        """
        Get existing location or create new one
        
        Args:
            name: Location name (e.g., "Madrid")
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            **kwargs: Optional fields (elevation, timezone, country_name, etc.)
        
        Returns:
            location_id: ID of existing or newly created location
        
        Explanation:
        - First checks if location exists by coordinates
        - If exists: returns existing location_id
        - If not: creates new location and returns new location_id
        
        Example:
            >>> location_service = LocationService()
            >>> location_id = location_service.get_or_create_location(
            ...     "Madrid", 40.4168, -3.7038,
            ...     timezone="Europe/Madrid",
            ...     country="ES"
            ... )
            >>> print(location_id)
            1
        """
        
        # Step 1: Check if location already exists
        existing_location = self._get_location_by_coords(latitude, longitude)
        
        if existing_location:
            self.logger.info(f"Location exists: {name} (ID: {existing_location['location_id']})")
            return existing_location['location_id']
        
        # Step 2: Create new location
        self.logger.info(f"Creating new location: {name} ({latitude}, {longitude})")
        
        query = """
        INSERT INTO locations (
            name, latitude, longitude, elevation, country, country_name,
            state, timezone, admin1, admin2, admin3, admin4, postcodes,
            feature_code, population, created_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
        )
        """
        
        params = (
            name,
            latitude,
            longitude,
            kwargs.get('elevation'),
            kwargs.get('country'),
            kwargs.get('country_name'),
            kwargs.get('state'),
            kwargs.get('timezone', 'auto'),
            kwargs.get('admin1'),
            kwargs.get('admin2'),
            kwargs.get('admin3'),
            kwargs.get('admin4'),
            kwargs.get('postcodes'),
            kwargs.get('feature_code'),
            kwargs.get('population'),
        )
        
        location_id = self.db.execute_insert(query, params)
        
        if location_id > 0:
            self.logger.info(f"✓ Location created: {name} (ID: {location_id})")
            return location_id
        else:
            self.logger.error(f"✗ Failed to create location: {name}")
            raise Exception(f"Failed to create location: {name}")
    
    def _get_location_by_coords(
        self,
        latitude: float,
        longitude: float,
        tolerance: float = 0.01
    ) -> Optional[Dict[str, Any]]:
        """
        Get location by coordinates (with small tolerance)
        
        Args:
            latitude: Latitude to search
            longitude: Longitude to search
            tolerance: Coordinate difference tolerance (default: 0.01 degrees ≈ 1km)
        
        Returns:
            Dictionary with location data, or None if not found
        
        Explanation:
        - Tolerance allows for small coordinate differences
        - 0.01 degrees ≈ 1.1 km at equator
        - Prevents duplicate locations for slightly different coordinates
        """
        
        query = """
        SELECT * FROM locations
        WHERE ABS(latitude - %s) < %s
          AND ABS(longitude - %s) < %s
        LIMIT 1
        """
        
        result = self.db.execute_query(query, (latitude, tolerance, longitude, tolerance))
        
        if result:
            columns = [
                'location_id', 'name', 'latitude', 'longitude', 'elevation',
                'country', 'country_name', 'state', 'timezone', 'admin1',
                'admin2', 'admin3', 'admin4', 'postcodes', 'feature_code',
                'population', 'created_at', 'updated_at'
            ]
            return dict(zip(columns, result[0]))
        
        return None
    
    def get_location_by_id(self, location_id: int) -> Optional[Dict[str, Any]]:
        """
        Get location by ID
        
        Args:
            location_id: Location ID to retrieve
        
        Returns:
            Dictionary with location data, or None if not found
        """
        
        query = "SELECT * FROM locations WHERE location_id = %s"
        result = self.db.execute_query(query, (location_id,))
        
        if result:
            columns = [
                'location_id', 'name', 'latitude', 'longitude', 'elevation',
                'country', 'country_name', 'state', 'timezone', 'admin1',
                'admin2', 'admin3', 'admin4', 'postcodes', 'feature_code',
                'population', 'created_at', 'updated_at'
            ]
            return dict(zip(columns, result[0]))
        
        return None
    
    def get_available_locations(self) -> list[Dict[str, Any]]:
        """
        Get all available default locations for user selection
        
        Returns only the 10 pre-configured locations (IDs 1-10)
        that users can add to their favorites.
        
        Returns:
            list: List of available locations with:
                - location_id: Unique ID
                - name: Location name (e.g., "Madrid")
                - latitude: Latitude coordinate
                - longitude: Longitude coordinate
                - country: Country code (e.g., "ES")
                - country_name: Full country name (e.g., "Spain")
                - timezone: Timezone (e.g., "Europe/Madrid")
        
        Example Response:
            [
                {
                    "location_id": 1,
                    "name": "Madrid",
                    "latitude": 40.4168,
                    "longitude": -3.7038,
                    "country": "ES",
                    "country_name": "Spain",
                    "timezone": "Europe/Madrid"
                },
                ...
            ]
        """
        
        self.logger.info("Fetching available default locations (IDs 1-10)")
        query = """
        SELECT 
            location_id,
            name,
            latitude,
            longitude,
            country,
            country_name,
            timezone
        FROM locations
        WHERE location_id BETWEEN 1 AND 10
        ORDER BY location_id ASC
        """
        
        results = self.db.execute_query(query)
        
        if not results:
            self.logger.warning("No default locations found in database")
            return []
        
        locations = []
        
        for row in results:
            locations.append({
                'location_id': row[0],
                'name': row[1],
                'latitude': row[2],
                'longitude': row[3],
                'country': row[4],
                'country_name': row[5],
                'timezone': row[6]
            })
        
        self.logger.info(f"Found {len(locations)} default locations")
        return locations