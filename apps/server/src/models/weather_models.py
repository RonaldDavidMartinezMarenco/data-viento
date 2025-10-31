from pydantic import BaseModel, Field
from typing import Optional, List
from models.base_models import APIMetadata

# ==================== CURRENT WEATHER ====================

class CurrentWeatherData(BaseModel):
    """
    Current weather conditions from Open-Meteo
    
    Maps to: current_weather table
    
    Explanation of fields:
    - temperature_2m: Air temperature 2 meters above ground (°C)
    - relative_humidity_2m: Moisture in air as percentage (0-100%)
    - apparent_temperature: "Feels like" temperature (°C)
    - precipitation: Current precipitation amount (mm)
    - weather_code: WMO Weather Code (integer mapping to weather type)
    - cloud_cover: Cloud coverage percentage (0-100%)
    - wind_speed_10m: Wind speed at 10 meters height (km/h)
    - wind_direction_10m: Wind direction in degrees (0-360°)
    """
    temperature_2m: Optional[float] = Field(None, ge=-60, le=60, description="Temperature at 2m height (°C)")
    relative_humidity_2m: Optional[int] = Field(None, ge=0, le=100, description="Humidity percentage (0-100%)")
    apparent_temperature: Optional[float] = Field(None, ge=-60, le=60, description="Apparent/feels-like temperature (°C)")
    precipitation: Optional[float] = Field(None, ge=0, description="Precipitation amount (mm)")
    weather_code: Optional[int] = Field(None, description="WMO weather code")
    cloud_cover: Optional[int] = Field(None, ge=0, le=100, description="Cloud cover percentage (0-100%)")
    wind_speed_10m: Optional[float] = Field(None, ge=0, description="Wind speed at 10m (km/h)")
    wind_direction_10m: Optional[int] = Field(None, ge=0, le=360, description="Wind direction (0-360°)")


class HourlyWeatherData(BaseModel):
    """
    Hourly weather forecast data from Open-Meteo
    
    Maps to: weather_forecasts + forecast_data tables
    
    Explanation:
    - Each field is a LIST of values, one per hour
    - time: List of timestamps (e.g., ["2025-10-30T14:00", "2025-10-30T15:00", ...])
    - temperature_2m: List of hourly temperatures
    - All lists are synchronized (index 0 = first hour for all fields)
    """
    time: List[str] = Field(..., description="List of hourly timestamps")
    temperature_2m: Optional[List[Optional[float]]] = Field(None, description="Hourly temperature at 2m (°C)")
    relative_humidity_2m: Optional[List[Optional[int]]] = Field(None, description="Hourly humidity (0-100%)")
    precipitation_probability: Optional[List[Optional[int]]] = Field(None, description="Precipitation probability (0-100%)")
    precipitation: Optional[List[Optional[float]]] = Field(None, description="Hourly precipitation (mm)")
    weather_code: Optional[List[Optional[int]]] = Field(None, description="Hourly WMO weather codes")
    wind_speed_10m: Optional[List[Optional[float]]] = Field(None, description="Hourly wind speed (km/h)")
    wind_direction_10m: Optional[List[Optional[int]]] = Field(None, description="Hourly wind direction (0-360°)")


class DailyWeatherData(BaseModel):
    """
    Daily weather forecast aggregates from Open-Meteo
    
    Maps to: weather_forecasts_daily table
    
    Explanation:
    - Each field is a LIST of daily values
    - time: List of dates (e.g., ["2025-10-30", "2025-10-31", ...])
    - temperature_2m_max: Daily maximum temperature
    - temperature_2m_min: Daily minimum temperature
    - sunrise/sunset: Times in ISO 8601 format
    """
    time: List[str] = Field(..., description="List of daily dates (YYYY-MM-DD)")
    temperature_2m_max: Optional[List[Optional[float]]] = Field(None, description="Daily max temperature (°C)")
    temperature_2m_min: Optional[List[Optional[float]]] = Field(None, description="Daily min temperature (°C)")
    precipitation_sum: Optional[List[Optional[float]]] = Field(None, description="Daily precipitation total (mm)")
    precipitation_probability_max: Optional[List[Optional[int]]] = Field(None, description="Max precipitation probability (0-100%)")
    weather_code: Optional[List[Optional[int]]] = Field(None, description="Daily dominant weather code")
    sunrise: Optional[List[Optional[str]]] = Field(None, description="Sunrise time (HH:MM)")
    sunset: Optional[List[Optional[str]]] = Field(None, description="Sunset time (HH:MM)")
    sunshine_duration: Optional[List[Optional[int]]] = Field(None, description="Hours of sunshine")
    uv_index_max: Optional[List[Optional[int]]] = Field(None, description="Maximum UV index")
    wind_speed_10m_max: Optional[List[Optional[float]]] = Field(None, description="Max wind speed (km/h)")
    wind_gusts_10m_max: Optional[List[Optional[float]]] = Field(None, description="Max wind gusts (km/h)")
    wind_direction_10m_dominant: Optional[List[Optional[int]]] = Field(None, description="Dominant wind direction (0-360°)")


class ForecastResponse(APIMetadata):
    """
    Complete weather forecast response from Open-Meteo
    
    Maps to: current_weather, weather_forecasts, weather_forecasts_daily tables
    
    Structure:
    - Inherits APIMetadata (latitude, longitude, timezone, etc.)
    - current: Current conditions (optional)
    - hourly: Hourly forecasts (optional)
    - daily: Daily forecasts (optional)
    """
    current: Optional[CurrentWeatherData] = Field(None, description="Current weather data")
    hourly: Optional[HourlyWeatherData] = Field(None, description="Hourly forecast data")
    daily: Optional[DailyWeatherData] = Field(None, description="Daily forecast data")