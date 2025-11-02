import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pydantic import BaseModel, Field
from typing import Optional, List
from src.models.base_models import APIMetadata

# ==================== SATELLITE RADIATION ====================

class SatelliteRadiationHourly(BaseModel):
    """
    Hourly satellite radiation data from Open-Meteo
    
    Maps to: satellite_radiation_data table
    
    Explanation of fields:
    - time: Hourly timestamps (15-30 minute resolution possible)
    - shortwave_radiation: Total solar radiation reaching surface (W/m²)
    - direct_radiation: Direct beam radiation from sun (W/m²)
    - diffuse_radiation: Scattered radiation from sky (W/m²)
    - direct_normal_irradiance (DNI): Direct radiation perpendicular to sun (W/m²)
      Used for: Concentrated solar power (CSP) plants
    - global_tilted_irradiance (GTI): Solar radiation on tilted surface (W/m²)
      Used for: Solar panel efficiency calculations
    - terrestrial_radiation: Heat radiation from Earth surface (W/m²)
    """
    time: List[str] = Field(..., description="List of timestamps (can be 10-30 minute intervals)")
    shortwave_radiation: Optional[List[Optional[float]]] = Field(None, ge=0, description="Shortwave radiation (W/m²)")
    direct_radiation: Optional[List[Optional[float]]] = Field(None, ge=0, description="Direct radiation (W/m²)")
    diffuse_radiation: Optional[List[Optional[float]]] = Field(None, ge=0, description="Diffuse radiation (W/m²)")
    direct_normal_irradiance: Optional[List[Optional[float]]] = Field(None, ge=0, description="Direct Normal Irradiance - DNI (W/m²)")
    global_tilted_irradiance: Optional[List[Optional[float]]] = Field(None, ge=0, description="Global Tilted Irradiance - GTI (W/m²)")
    terrestrial_radiation: Optional[List[Optional[float]]] = Field(None, ge=0, description="Terrestrial radiation (W/m²)")


class SatelliteResponse(APIMetadata):
    """
    Complete satellite radiation response from Open-Meteo
    
    Maps to: satellite_radiation_data table
    
    Note: This endpoint only returns hourly data (no current or daily aggregates)
    """
    hourly: Optional[SatelliteRadiationHourly] = Field(None, description="Hourly solar radiation data")