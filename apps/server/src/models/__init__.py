"""
Models module for data-viento
Contains all Pydantic models for API responses
"""

from .base_models import APIMetadata, HourlyDataPoint, DailyDataPoint
from .weather_models import (
    CurrentWeatherData,
    HourlyWeatherData,
    DailyWeatherData,
    ForecastResponse,
)
from .air_quality_models import (
    AirQualityCurrent,
    AirQualityHourly,
    AirQualityResponse,
)
from .marine_models import (
    MarineCurrent,
    MarineHourly,
    MarineDaily,
    MarineResponse,
)
from .satellite_models import (
    SatelliteRadiation,
    SatelliteResponse,
)
from .climate_models import (
    ClimateDaily,
    ClimateResponse,
)

__all__ = [
    # Base models
    "APIMetadata",
    "HourlyDataPoint",
    "DailyDataPoint",
    # Weather models
    "CurrentWeatherData",
    "HourlyWeatherData",
    "DailyWeatherData",
    "ForecastResponse",
    # Air quality models
    "AirQualityCurrent",
    "AirQualityHourly",
    "AirQualityResponse",
    # Marine models
    "MarineCurrent",
    "MarineHourly",
    "MarineDaily",
    "MarineResponse",
    # Satellite models
    "SatelliteRadiationHourly",
    "SatelliteResponse",
    # Climate models
    "ClimateDaily",
    "ClimateResponse",
]