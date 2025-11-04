"""
Open-Meteo API Client

Fetches weather, air quality, marine, satellite, and climate data from Open-Meteo API.
Uses parameter definitions from constants/open_meteo_params.py.

Documentation: https://open-meteo.com/en/docs
"""

import logging
import sys 
from typing import Optional, Dict, Any
from datetime import datetime, date


from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.api import BaseAPIClient
from src.constants import (
    WEATHER_CURRENT_PARAMS,
    WEATHER_HOURLY_PARAMS,
    WEATHER_DAILY_PARAMS,
    AIR_QUALITY_CURRENT_PARAMS,
    AIR_QUALITY_HOURLY_PARAMS,
    MARINE_CURRENT_PARAMS,
    MARINE_HOURLY_PARAMS,
    MARINE_DAILY_PARAMS,
    SATELLITE_RADIATION_PARAMS,
    CLIMATE_DAILY_PARAMS,
)

logger = logging.getLogger(__name__)
   
class OpenMeteoClient(BaseAPIClient):
    """
    Client for Open-Meteo API
    
    Features:
    Yes my friend
    """
    # Base URLs for different Open-Meteo endpoints
    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
    AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
    MARINE_URL = "https://marine-api.open-meteo.com/v1/marine"
    SOLAR_URL = "https://satellite-api.open-meteo.com/v1/archive"
    CLIMATE_URL = "https://climate-api.open-meteo.com/v1/climate"
    
    def __init__(self, timeout: int = 30):
        """
        Initialize Open-Meteo client
        
        Args:
            timeout: Request timeout in seconds
        """
        
        super().__init__(timeout=timeout)
        self.logger = logging.getLogger(__name__)
        
    # ==================== WEATHER FORECAST ====================
    
    async def get_weather_forecast(
        self,
        latitude: float,
        longitude: float,
        include_current: bool = True,
        include_hourly: bool = False,
        include_daily: bool = False,
        timezone: str = "auto",
        forecast_days: int = 7,
        
    ) -> Optional[Dict[str,Any]]:
        
        """
        Get weather forecast data
        
        Args:
            latitude: Location latitude (-90 to 90)
            longitude: Location longitude (-180 to 180)
            include_current: Include current weather conditions
            include_hourly: Include hourly forecast (48-168 hours)
            include_daily: Include daily forecast (1-16 days)
            timezone: Timezone (e.g., "Europe/Madrid", "America/New_York", or "auto")
            forecast_days: Number of forecast days (1-16, default: 7)
        
        Returns:
            JSON response from Open-Meteo API
        
        Example:
            >>> client = OpenMeteoClient()
            >>> data = await client.get_weather_forecast(40.7128, -74.0060)
            >>> print(data["current"]["temperature_2m"])
            15.2
        """
        
        params = {
            "latitude" : latitude,
            "longitude":longitude,
            "timezone":timezone,
            "forecast_days":min(forecast_days,16),
        }
        
        # Add parameter lists from open_meteo_params.py
        if include_current:
            params["current"] = WEATHER_CURRENT_PARAMS["api_params"]
            
        if include_hourly:
            params["hourly"] = WEATHER_HOURLY_PARAMS["api_params"]
            
        if include_daily:
            params["daily"] = WEATHER_DAILY_PARAMS["api_params"]
            
        self.logger.info(
            f"Requesting weather forecast for ({latitude}, {longitude}) - "
            f"current: {include_current}, hourly: {include_hourly}, daily: {include_daily}"
        )
        
        try:
            # Make the request (using base_client's _make_request method)
            original_url = self.BASE_URL
            self.BASE_URL = self.FORECAST_URL
            response = await self._make_request("GET", "", params)
            self.BASE_URL = original_url
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error fetching weather forecast: {e}")
            return None
        
    # ==================== AIR QUALITY ====================
    
    async def get_air_quality(
        self,
        latitude: float,
        longitude: float,
        include_current: bool = True,
        include_hourly: bool = False,
        timezone: str = "auto",
        forecast_days: int = 5,
    ) -> Optional[Dict[str, Any]]:
        """
        Get air quality data
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            include_current: Include current air quality
            include_hourly: Include hourly air quality forecast
            timezone: Timezone
            forecast_days: Number of forecast days (1-5, default: 5)
        
        Returns:
            JSON response from Open-Meteo Air Quality API
        
        Example:
            >>> client = OpenMeteoClient()
            >>> data = await client.get_air_quality(40.7128, -74.0060)
            >>> print(data["current"]["pm2_5"])
            12.3
        """
        
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "timezone": timezone,
            "forecast_days": min(forecast_days, 5),  # Max 5 days for air quality
        }
        
        if include_current:
            params["current"] = AIR_QUALITY_CURRENT_PARAMS["api_params"]
        
        if include_hourly:
            params["hourly"] = AIR_QUALITY_HOURLY_PARAMS["api_params"]
        
        self.logger.info(
            f"Requesting air quality for ({latitude}, {longitude})"
        )
        
        try:
            original_url = self.BASE_URL
            self.BASE_URL = self.AIR_QUALITY_URL
            response = await self._make_request("GET", "", params)
            self.BASE_URL = original_url
            
            return response
        
        except Exception as e:
            self.logger.error(f"Error fetching air quality: {e}")
            return None        
        
    # ==================== MARINE ====================
    
    async def get_marine_forecast(
        self,
        latitude: float,
        longitude: float,
        include_current: bool = True,
        include_hourly: bool = False,
        include_daily: bool = False,
        timezone: str = "auto",
        forecast_days: int = 7,
    ) -> Optional[Dict[str, Any]]:
        """
        Get marine weather data (waves, sea temperature, currents)
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            include_current: Include current marine conditions
            include_hourly: Include hourly marine forecast
            include_daily: Include daily marine forecast
            timezone: Timezone
            forecast_days: Number of forecast days (1-10, default: 7)
        
        Returns:
            JSON response from Open-Meteo Marine API
        
        Example:
            >>> client = OpenMeteoClient()
            >>> data = await client.get_marine_forecast(40.7128, -74.0060)
            >>> print(data["current"]["wave_height"])
            1.5
        """
        
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "timezone": timezone,
            "forecast_days": min(forecast_days, 7),  # Max 7 days
        }
        
        if include_current:
            params["current"] = MARINE_CURRENT_PARAMS["api_params"]
        
        if include_hourly:
            params["hourly"] = MARINE_HOURLY_PARAMS["api_params"]
        
        if include_daily:
            params["daily"] = MARINE_DAILY_PARAMS["api_params"]
        
        self.logger.info(
            f"Requesting marine forecast for ({latitude}, {longitude})"
        )
        
        try:
            original_url = self.BASE_URL
            self.BASE_URL = self.MARINE_URL
            response = await self._make_request("GET", "", params)
            self.BASE_URL = original_url
            
            return response
        
        except Exception as e:
            self.logger.error(f"Error fetching marine forecast: {e}")
            return None
    
    # ==================== SATELLITE RADIATION ====================
    async def get_solar_radiation(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        timezone: str = "auto",
        tilt: int = 35,
        azimuth: int = 0,
    ) -> Optional[Dict[str, Any]]:
        """
        Get solar radiation data (for solar energy calculations)
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            timezone: Timezone
            tilt: Solar panel tilt angle (0-90 degrees, default: 35)
            azimuth: Solar panel azimuth (0-360 degrees, 0=North, default: 0)
        
        Returns:
            JSON response with solar radiation data
        
        Example:
            >>> client = OpenMeteoClient()
            >>> data = await client.get_solar_radiation(
            ...     40.7128, -74.0060, "2024-01-01", "2024-01-07"
            ... )
            >>> print(data["hourly"]["shortwave_radiation"][0])
            450.2
        """
        
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "timezone": timezone,
            "hourly": SATELLITE_RADIATION_PARAMS["api_params"],
            "tilt": tilt,
            "azimuth": azimuth,
        }
        
        self.logger.info(
            f"Requesting solar radiation for ({latitude}, {longitude}) "
            f"from {start_date} to {end_date}"
        )
        
        try:
            # Solar radiation uses the forecast endpoint with different parameters
            original_url = self.BASE_URL
            self.BASE_URL = self.SOLAR_URL
            response = await self._make_request("GET", "", params)
            self.BASE_URL = original_url
            
            return response
        
        except Exception as e:
            self.logger.error(f"Error fetching solar radiation: {e}")
            return None
        
    # ==================== CLIMATE PROJECTIONS ====================
    async def get_climate_projection(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        models: str = "EC_Earth3P_HR",
        timezone: str = "auto",
    ) -> Optional[Dict[str, Any]]:
        """
        Get climate change projections (historical and future data)
        
        Args:
            latitude: Location latitude
            longitude: Location longitude
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            models: Climate model to use (default: CMCC_CM2_VR4)
            timezone: Timezone
        
        Returns:
            JSON response with climate projection data
        
        Example:
            >>> client = OpenMeteoClient()
            >>> data = await client.get_climate_projection(
            ...     40.7128, -74.0060, "2020-01-01", "2024-12-31"
            ... )
            >>> print(data["daily"]["temperature_2m_mean"][0])
            8.5
        
        Note: This endpoint requires date ranges and is for historical/future analysis
        """
        
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "daily": CLIMATE_DAILY_PARAMS["api_params"],
            "models": models,
            "timezone": timezone,
        }
        
        self.logger.info(
            f"Requesting climate projection for ({latitude}, {longitude}) "
            f"from {start_date} to {end_date}"
        )
        
        try:
            original_url = self.BASE_URL
            self.BASE_URL = self.CLIMATE_URL
            response = await self._make_request("GET", "", params)
            self.BASE_URL = original_url
            
            return response
        
        except Exception as e:
            self.logger.error(f"Error fetching climate projection: {e}")
            return None
        
def debug():
    print(WEATHER_CURRENT_PARAMS['api_params'])
    
debug()