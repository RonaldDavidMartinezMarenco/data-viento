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
            
        
        
        
