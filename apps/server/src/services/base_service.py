"""
Base Service Class

Provides common functionality for all data services:
- Database connection management
- API client initialization
- Error handling
- Logging

All specific services (WeatherService, AirQualityService, etc.) inherit from this.
"""

import logging
import sys
from typing import Optional
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.db.database import DatabaseConnection
from src.api import OpenMeteoClient
from src.constants.open_meteo_params import WEATHER_PARAMETERS_DATA

class BaseService:
    """
    Base class for all data services
    
    Features:
    - Manages database connection
    - Manages API client
    - Provides common error handling
    - Centralized logging
    
    Why this matters:
    - Prevents code duplication
    - Ensures consistent error handling
    - Makes it easy to add new services
    """

    def __init__(self,db: Optional[DatabaseConnection]= None):
        """
        Initialize base service
        
        Args:
            db: Database connection (creates new if None)
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        if db is None:
            self.db = DatabaseConnection()
            self.db.connect()
            self._owns_db = True
        else:
            self.db = db
            self._owns_db = False
        
        self._api_client: Optional[OpenMeteoClient] = None
        
    @property
    def api_client (self) -> OpenMeteoClient:
        """
        Lazy-load API client (only create when needed)
            
        Returns:
        OpenMeteoClient instance
        """
        if self._api_client is None:
            self._api_client = OpenMeteoClient()
        return self._api_client
    
    async def close(self):
        """
        Close connections
        
        Explanation:
        - Closes API client if created
        - Closes database if we created it
        """
        if self._api_client:
            await self._api_client.close()
            self._api_client = None
        
        if self._owns_db:
            self.db.disconnect()
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    def _log_db_error(self, operation: str, error: Exception):
        """
        Log database errors consistently
        
        Args:
            operation: What operation failed (e.g., "insert_weather_data")
            error: The exception that occurred
        """
        self.logger.error(f"Database error in {operation}: {error}")
    
    def _log_api_error(self, operation: str, error: Exception):
        """
        Log API errors consistently
        
        Args:
            operation: What operation failed (e.g., "fetch_weather_forecast")
            error: The exception that occurred
        """
        self.logger.error(f"API error in {operation}: {error}")
            
    def _get_or_create_parameter(self, param_code: str, api_field: str) -> Optional[int]:
        """
        Get parameter_id from weather_parameters table (or create if not exists)
        
        Args:
            param_code: Our internal parameter code (e.g., 'temp_2m')
            api_field: Open-Meteo API field name (e.g., 'temperature_2m')
        
        Returns:
            parameter_id, or None if error
        
        Explanation:
        - Checks if parameter exists in weather_parameters
        - If not, creates it using data from WEATHER_PARAMETERS_DATA
        - Returns parameter_id for use in forecast_data table
        """
        
        # Check if parameter exists
        query = "SELECT parameter_id FROM weather_parameters WHERE parameter_code = %s"
        result = self.db.execute_query(query, (param_code,))
        
        if result:
            return result[0][0]
        
        # Find parameter definition
        param_def = None
        for param_tuple in WEATHER_PARAMETERS_DATA:
            if param_tuple[0] == param_code:
                param_def = param_tuple
                break
        
        if param_def is None:
            self.logger.error(f"Parameter definition not found for: {param_code}")
            return None
        
        # Create parameter
        insert_query = """
        INSERT INTO weather_parameters (
            parameter_code, parameter_name, description, unit, parameter_category,
            data_type, altitude_level, is_surface, api_endpoint,
            created_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
        )
        """
        #("temp_2m", "Temperature 2m", "°C", "temperature", "float", "2m", True, "forecast"),
        insert_params = (
            param_def[0],  # parameter_code
            param_def[1],  # parameter_name
            None ,         # description
            param_def[2],  # unit 
            param_def[3],  # parameter_category
            param_def[4],  # data_type
            param_def[5],  # altitude_level
            param_def[6],  # is_surface
            param_def[7],  # api_endpoint
        )
        
        parameter_id = self.db.execute_insert(insert_query, insert_params)
        
        if parameter_id > 0:
            self.logger.info(f"✓ Created weather parameter: {param_code} (ID: {parameter_id})")
            return parameter_id
        
        return None
        
        
