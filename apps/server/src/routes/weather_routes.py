"""
Weather Routes

Provides API endpoints for weather data:
1. GET /weather/current/{location_id} - Current weather
2. GET /weather/hourly/{location_id} - Hourly forecast
3. GET /weather/daily/{location_id} - Daily forecast
4. GET /weather/all/{location_id} - All weather data (current + hourly + daily)

Maps to tables:
- current_weather
- weather_forecasts + forecast_data (hourly)
- weather_forecasts_daily
"""


import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from src.services.weather_service import WeatherService

router = APIRouter(
    prefix="/weather",
    tags=["Weather Data"]
)



# ========================================
# ROUTES
# ========================================

@router.get("/current/{location_id}")
async def get_current_weather(
    location_id: int,
) -> Dict[str, Any]:
    """
    Get current weather for a location
    
    Args:
        location_id: Location ID
    
    Returns:
        Current weather data
    
    Example:
        GET /weather/current/1
        
        Response:
        {
            "success": true,
            "data": {
                "temperature_2m": 22.5,
                "wind_speed_10m": 12.3,
                ...
            }
        }
    """
    
    try:
        service = WeatherService()
        current = service.get_current_weather(location_id)
        
        if not current:
            raise HTTPException(
                status_code=404,
                detail=f"No current weather data found for location {location_id}"
            )
        
        return {
            "success": True,
            "data": current
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        service.db.disconnect()


@router.get("/hourly/{location_id}")
async def get_hourly_forecast(
    location_id: int,
    hours: int = Query(default=24, ge=1, le=168),
    parameters: Optional[List[str]] = Query(default=None)
) -> Dict[str, Any]:
    """
    Get hourly weather forecast for a location
    
    Args:
        location_id: Location ID
        hours: Number of forecast hours (1-168, default: 24)
        parameters: List of parameter codes (optional)
    
    Returns:
        Hourly forecast data
    
    Example:
        GET /weather/hourly/1?hours=24&parameters=temp_2m&parameters=wind_speed_10m
        
        Response:
        {
            "success": true,
            "data": {
                "parameters": {
                    "temp_2m": {
                        "values": [22.5, 23.1, ...],
                        "times": ["2025-11-07T14:00:00", ...]
                    }
                }
            }
        }
    """
    service = WeatherService()
    try:
        hourly = service.get_hourly_forecast(
            location_id=location_id,
            hours=hours,
            parameters=parameters
        )
        
        if not hourly:
            raise HTTPException(
                status_code=404,
                detail=f"No hourly forecast data found for location {location_id}"
            )
        
        return {
            "success": True,
            "data": hourly
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        service.db.disconnect()


@router.get("/daily/{location_id}")
async def get_daily_forecast(
    location_id: int,
    days: int = Query(default=7, ge=1, le=16),
) -> Dict[str, Any]:
    """
    Get daily weather forecast for a location
    
    Args:
        location_id: Location ID
        days: Number of forecast days (1-16, default: 7)
    
    Returns:
        Daily forecast data
    
    Example:
        GET /weather/daily/1?days=7
        
        Response:
        {
            "success": true,
            "data": [
                {
                    "valid_date": "2025-11-07",
                    "temperature_2m_max": 25.0,
                    "temperature_2m_min": 15.0,
                    ...
                }
            ],
            "count": 7
        }
    """
    service = WeatherService()
    try:
        daily = service.get_daily_forecast(
            location_id=location_id,
            days=days
        )
        
        if not daily:
            raise HTTPException(
                status_code=404,
                detail=f"No daily forecast data found for location {location_id}"
            )
        
        return {
            "success": True,
            "data": daily,
            "count": len(daily)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        service.db.disconnect()


@router.get("/all/{location_id}")
async def get_all_weather(
    location_id: int,
    days: int = Query(default=7, ge=1, le=16),
    hours: int = Query(default=24, ge=1, le=168)
) -> Dict[str, Any]:
    """
    Get all weather data for a location (current + hourly + daily)
    
    **This is the main endpoint the frontend uses**
    
    Args:
        location_id: Location ID
        days: Number of forecast days (default: 7)
        hours: Number of forecast hours (default: 24)
    
    Returns:
        Complete weather data
    
    Example:
        GET /weather/all/1?days=7&hours=24
        
        Response:
        {
            "success": true,
            "location_id": 1,
            "current": { ... },
            "hourly": { ... },
            "daily": [ ... ],
            "timestamp": "2025-11-07T14:30:00"
        }
    """
    service = WeatherService()
    try:
        weather = service.get_all_weather_data(
            location_id=location_id,
            days=days,
            hours=hours
        )
        
        if not weather:
            raise HTTPException(
                status_code=404,
                detail=f"No weather data found for location {location_id}"
            )
        
        return weather
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        service.db.disconnect()