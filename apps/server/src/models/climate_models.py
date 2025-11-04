import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pydantic import BaseModel, Field
from typing import Optional, List
from src.models.base_models import APIMetadata

# ==================== CLIMATE PROJECTIONS ====================

class ClimateDaily(BaseModel):
    """
    Daily climate change projections from Open-Meteo
    
    Maps to: climate_projections + climate_daily tables
    
    Explanation:
    - These are FUTURE predictions (not current data)
    - Based on climate models (CMCC, MRI, etc.)
    - Can be historical or future projections
    - Each field is a list of daily values
    
    Fields explained:
    - temperature_2m_max/min/mean: Daily air temperature extremes and average (°C)
    - precipitation_sum: Total rain for the day (mm)
    - rain_sum: Rain only (vs snow) (mm)
    - snowfall_sum: Snow equivalent water (mm)
    - relative_humidity_2m_*: Humidity extremes and average (%)
    - wind_speed_10m_*: Wind speed average and maximum (km/h)
    - pressure_msl_mean: Mean atmospheric pressure (hPa)
    - cloud_cover_mean: Average cloud coverage (%)
    - shortwave_radiation_sum: Total solar energy received (MJ/m²)
    - soil_moisture_0_to_10cm_mean: Soil water content in top 10cm (m³/m³)
    """
    time: List[str] = Field(..., description="List of daily dates (YYYY-MM-DD)")
    temperature_2m_max: Optional[List[Optional[float]]] = Field(None, description="Daily max temperature (°C)")
    temperature_2m_min: Optional[List[Optional[float]]] = Field(None, description="Daily min temperature (°C)")
    temperature_2m_mean: Optional[List[Optional[float]]] = Field(None, description="Daily mean temperature (°C)")
    precipitation_sum: Optional[List[Optional[float]]] = Field(None, description="Total precipitation (mm)")
    rain_sum: Optional[List[Optional[float]]] = Field(None,  description="Rain total (mm)")
    snowfall_sum: Optional[List[Optional[float]]] = Field(None, description="Snowfall (mm water equivalent)")
    relative_humidity_2m_max: Optional[List[Optional[float]]] = Field(None,description="Max humidity (%)")
    relative_humidity_2m_min: Optional[List[Optional[float]]] = Field(None, description="Min humidity (%)")
    relative_humidity_2m_mean: Optional[List[Optional[float]]] = Field(None, description="Mean humidity (%)")
    wind_speed_10m_mean: Optional[List[Optional[float]]] = Field(None, description="Mean wind speed (km/h)")
    wind_speed_10m_max: Optional[List[Optional[float]]] = Field(None, description="Max wind speed (km/h)")
    pressure_msl_mean: Optional[List[Optional[float]]] = Field(None, description="Mean pressure (hPa)")
    cloud_cover_mean: Optional[List[Optional[float]]] = Field(None, description="Mean cloud cover (%)")
    shortwave_radiation_sum: Optional[List[Optional[float]]] = Field(None, description="Total solar radiation (MJ/m²)")
    soil_moisture_0_to_10cm_mean: Optional[List[Optional[float]]] = Field(None, description="Soil moisture (0-1 m³/m³)")


class ClimateResponse(APIMetadata):
    """
    Complete climate projection response from Open-Meteo
    
    Maps to: climate_projections + climate_daily tables
    
    Note: 
    - start_date and end_date are passed as REQUEST parameters, not in response
    - This endpoint requires specific date ranges
    - Response is ALWAYS daily (no hourly climate data available)
    """
    daily: Optional[ClimateDaily] = Field(None, description="Daily climate projection data")