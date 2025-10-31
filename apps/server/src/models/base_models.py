from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class APIMetadata(BaseModel):
    """
    Common metadata returned by ALL Open-Meteo endpoints
    
    Explanation:
    - latitude, longitude: The exact coordinates for the data
    - generationtime_ms: How long it took Open-Meteo to generate the response
    - utc_offset_seconds: Timezone offset from UTC
    - timezone: Timezone name (e.g., "Europe/Madrid")
    """
    latitude: float = Field(..., description="Location latitude")
    longitude: float = Field(..., description="Location longitude")
    generationtime_ms: float = Field(..., description="API response generation time in milliseconds")
    utc_offset_seconds: int = Field(..., description="UTC offset in seconds")
    timezone: str = Field(..., description="Timezone name")
    
class HourlyDataPoint(BaseModel):
    """
    Generic hourly data point with time and value
    
    Explanation:
    - time: ISO 8601 format timestamp (e.g., "2025-10-30T14:00")
    - value: The actual measurement
    """
    time: str = Field(..., description="Valid time in ISO 8601 format")
    value: Optional[float] = Field(None, description="Measured value")
    
class DailyDataPoint(BaseModel):
    """
    Generic daily data point
    
    Explanation:
    - date: ISO 8601 date format (e.g., "2025-10-30")
    - value: The aggregated daily value
    """
    date: str = Field(..., description="Valid date in ISO 8601 format")
    value: Optional[float] = Field(None, description="Aggregated daily value")