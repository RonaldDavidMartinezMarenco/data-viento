from pydantic import BaseModel, Field
from typing import Optional, List
from models.base_models import APIMetadata

# ==================== AIR QUALITY CURRENT ====================

class AirQualityCurrent(BaseModel):
    """
    Current air quality measurements from Open-Meteo
    
    Maps to: air_quality_current table
    
    Explanation of fields:
    - pm2_5: Fine particulate matter < 2.5 micrometers (µg/m³)
      Health impact: Can penetrate deep into lungs and bloodstream
    - pm10: Particulate matter < 10 micrometers (µg/m³)
      Health impact: Can penetrate into lungs
    - european_aqi: European Air Quality Index (0-500 scale)
    - us_aqi: US EPA Air Quality Index (0-500 scale)
    - nitrogen_dioxide (NO2): Toxic gas from combustion (µg/m³)
    - ozone (O3): Ground-level ozone, respiratory irritant (µg/m³)
    - sulphur_dioxide (SO2): Acid rain precursor (µg/m³)
    - carbon_monoxide (CO): Invisible toxic gas (µg/m³)
    """
    pm2_5: Optional[float] = Field(None, ge=0, description="PM2.5 particulate matter (µg/m³)")
    pm10: Optional[float] = Field(None, ge=0, description="PM10 particulate matter (µg/m³)")
    european_aqi: Optional[int] = Field(None, ge=0, le=500, description="European AQI (0-500)")
    us_aqi: Optional[int] = Field(None, ge=0, le=500, description="US AQI (0-500)")
    nitrogen_dioxide: Optional[float] = Field(None, ge=0, description="NO2 (µg/m³)")
    ozone: Optional[float] = Field(None, ge=0, description="O3 (µg/m³)")
    sulphur_dioxide: Optional[float] = Field(None, ge=0, description="SO2 (µg/m³)")
    carbon_monoxide: Optional[float] = Field(None, ge=0, description="CO (µg/m³)")
    dust: Optional[float] = Field(None, ge=0, description="Dust (µg/m³)")
    ammonia: Optional[float] = Field(None, ge=0, description="NH3 (µg/m³)")


class AirQualityHourly(BaseModel):
    """
    Hourly air quality forecast from Open-Meteo
    
    Maps to: air_quality_forecasts + air_quality_data tables
    
    Explanation:
    - time: List of hourly timestamps
    - aqi: List of AQI values (aggregated index)
    - pm2_5, pm10, etc.: Lists of hourly measurements for each pollutant
    """
    time: List[str] = Field(..., description="List of hourly timestamps")
    aqi: Optional[List[Optional[int]]] = Field(None, description="Hourly AQI values")
    pm2_5: Optional[List[Optional[float]]] = Field(None, description="Hourly PM2.5 (µg/m³)")
    pm10: Optional[List[Optional[float]]] = Field(None, description="Hourly PM10 (µg/m³)")
    european_aqi: Optional[List[Optional[int]]] = Field(None, description="Hourly European AQI")
    us_aqi: Optional[List[Optional[int]]] = Field(None, description="Hourly US AQI")
    nitrogen_dioxide: Optional[List[Optional[float]]] = Field(None, description="Hourly NO2 (µg/m³)")
    ozone: Optional[List[Optional[float]]] = Field(None, description="Hourly O3 (µg/m³)")
    sulphur_dioxide: Optional[List[Optional[float]]] = Field(None, description="Hourly SO2 (µg/m³)")
    carbon_monoxide: Optional[List[Optional[float]]] = Field(None, description="Hourly CO (µg/m³)")


class AirQualityResponse(APIMetadata):
    """
    Complete air quality response from Open-Meteo
    
    Maps to: air_quality_current, air_quality_forecasts, air_quality_data tables
    """
    current: Optional[AirQualityCurrent] = Field(None, description="Current air quality")
    hourly: Optional[AirQualityHourly] = Field(None, description="Hourly air quality forecast")