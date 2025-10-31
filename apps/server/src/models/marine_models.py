from pydantic import BaseModel, Field
from typing import Optional, List
from models.base_models import APIMetadata

# ==================== MARINE CURRENT ====================

class MarineCurrent(BaseModel):
    """
    Current marine weather conditions from Open-Meteo
    
    Maps to: marine_current table
    
    Explanation of fields:
    - wave_height: Height of surface waves (meters)
    - wave_direction: Direction waves are coming from (0-360°)
    - wave_period: Time between wave crests (seconds)
    - swell_wave_*: Longer-period waves (ocean swells from distant storms)
    - wind_wave_*: Shorter-period waves from local wind
    - sea_surface_temperature: Water temperature (°C)
    - ocean_current_*: Water movement direction and speed
    """
    wave_height: Optional[float] = Field(None, ge=0, description="Wave height (m)")
    wave_direction: Optional[int] = Field(None, ge=0, le=360, description="Wave direction (0-360°)")
    wave_period: Optional[float] = Field(None, ge=0, description="Wave period (s)")
    swell_wave_height: Optional[float] = Field(None, ge=0, description="Swell wave height (m)")
    swell_wave_direction: Optional[int] = Field(None, ge=0, le=360, description="Swell direction (0-360°)")
    swell_wave_period: Optional[float] = Field(None, ge=0, description="Swell period (s)")
    wind_wave_height: Optional[float] = Field(None, ge=0, description="Wind wave height (m)")
    sea_surface_temperature: Optional[float] = Field(None, description="Water temperature (°C)")
    ocean_current_velocity: Optional[float] = Field(None, ge=0, description="Current speed (m/s)")
    ocean_current_direction: Optional[int] = Field(None, ge=0, le=360, description="Current direction (0-360°)")


class MarineHourly(BaseModel):
    """
    Hourly marine forecast from Open-Meteo
    
    Maps to: marine_forecasts + marine_data tables
    """
    time: List[str] = Field(..., description="List of hourly timestamps")
    wave_height: Optional[List[Optional[float]]] = Field(None, description="Hourly wave height (m)")
    wave_direction: Optional[List[Optional[int]]] = Field(None, description="Hourly wave direction (0-360°)")
    wave_period: Optional[List[Optional[float]]] = Field(None, description="Hourly wave period (s)")
    swell_wave_height: Optional[List[Optional[float]]] = Field(None, description="Hourly swell height (m)")
    swell_wave_direction: Optional[List[Optional[int]]] = Field(None, description="Hourly swell direction (0-360°)")
    swell_wave_period: Optional[List[Optional[float]]] = Field(None, description="Hourly swell period (s)")
    wind_wave_height: Optional[List[Optional[float]]] = Field(None, description="Hourly wind wave height (m)")
    sea_surface_temperature: Optional[List[Optional[float]]] = Field(None, description="Hourly water temp (°C)")


class MarineDaily(BaseModel):
    """
    Daily marine forecast aggregates from Open-Meteo
    
    Maps to: marine_forecasts_daily table
    """
    time: List[str] = Field(..., description="List of daily dates (YYYY-MM-DD)")
    wave_height_max: Optional[List[Optional[float]]] = Field(None, description="Daily max wave height (m)")
    wave_direction_dominant: Optional[List[Optional[int]]] = Field(None, description="Dominant wave direction (0-360°)")
    wave_period_max: Optional[List[Optional[float]]] = Field(None, description="Max wave period (s)")
    swell_wave_height_max: Optional[List[Optional[float]]] = Field(None, description="Max swell height (m)")
    swell_wave_direction_dominant: Optional[List[Optional[int]]] = Field(None, description="Dominant swell direction (0-360°)")
    sea_surface_temperature_mean: Optional[List[Optional[float]]] = Field(None, description="Mean water temp (°C)")
    ocean_current_velocity_max: Optional[List[Optional[float]]] = Field(None, description="Max current speed (m/s)")


class MarineResponse(APIMetadata):
    """
    Complete marine response from Open-Meteo
    
    Maps to: marine_current, marine_forecasts, marine_data, marine_forecasts_daily tables
    """
    current: Optional[MarineCurrent] = Field(None, description="Current marine conditions")
    hourly: Optional[MarineHourly] = Field(None, description="Hourly marine forecast")
    daily: Optional[MarineDaily] = Field(None, description="Daily marine forecast")