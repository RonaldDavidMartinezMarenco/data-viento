"""
Marine Routes

Provides API endpoints for marine weather data:
1. GET /marine/current/{location_id} - Current marine conditions
2. GET /marine/hourly/{location_id} - Hourly forecast
3. GET /marine/daily/{location_id} - Daily forecast
4. GET /marine/all/{location_id} - All marine data (current + hourly + daily)

Maps to tables:
- marine_current
- marine_forecasts + marine_data (hourly)
- marine_forecasts_daily
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional, List

from src.services.marine_service import MarineService
from src.db.database import DatabaseConnection

# Create router
router = APIRouter(
    prefix="/marine",
    tags=["Marine Weather Data"]
)




# ========================================
# ROUTES
# ========================================

@router.get("/current/{location_id}")
async def get_current_marine(
    location_id: int
) -> Dict[str, Any]:
    """
    Get current marine conditions for a location
    
    Args:
        location_id: Location ID
    
    Returns:
        Current marine data
    
    Example:
        GET /marine/current/1
        
        Response:
        {
            "success": true,
            "data": {
                "wave_height": 1.5,
                "wave_direction": 270,
                "swell_wave_height": 1.2,
                "sea_surface_temperature": 18.5,
                ...
            }
        }
    """
    
    service = MarineService()
    try:
        current = service.get_current_marine(location_id)
        
        if not current:
            raise HTTPException(
                status_code=404,
                detail=f"No current marine data found for location {location_id}"
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
async def get_hourly_marine_forecast(
    location_id: int,
    hours: int = Query(default=24, ge=1, le=168),
    parameters: Optional[List[str]] = Query(default=None)
) -> Dict[str, Any]:
    """
    Get hourly marine forecast for a location
    
    Args:
        location_id: Location ID
        hours: Number of forecast hours (1-168, default: 24)
        parameters: List of parameter codes (optional)
    
    Returns:
        Hourly marine forecast data
    
    Example:
        GET /marine/hourly/1?hours=24&parameters=wave_height&parameters=swell_wave_height
        
        Response:
        {
            "success": true,
            "data": {
                "parameters": {
                    "wave_height": {
                        "name": "Wave Height",
                        "unit": "m",
                        "values": [1.5, 1.6, 1.8, ...],
                        "times": ["2025-11-07T14:00:00", ...],
                        "wave_components": [null, null, ...],
                        "sea_conditions": [null, null, ...]
                    }
                }
            }
        }
    """
    service = MarineService()
    try:
        hourly = service.get_hourly_marine_forecast(
            location_id=location_id,
            hours=hours,
            parameters=parameters
        )
        
        if not hourly:
            raise HTTPException(
                status_code=404,
                detail=f"No hourly marine forecast data found for location {location_id}"
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
async def get_daily_marine_forecast(
    location_id: int,
    days: int = Query(default=7, ge=1, le=10)
) -> Dict[str, Any]:
    """
    Get daily marine forecast for a location
    
    Args:
        location_id: Location ID
        days: Number of forecast days (1-10, default: 7)
    
    Returns:
        Daily marine forecast data
    
    Example:
        GET /marine/daily/1?days=7
        
        Response:
        {
            "success": true,
            "data": [
                {
                    "valid_date": "2025-11-07",
                    "wave_height_max": 2.5,
                    "wave_direction_dominant": 270,
                    "swell_wave_height_max": 2.0,
                    ...
                }
            ],
            "count": 7
        }
    """
    service = MarineService()
    
    try:
        daily = service.get_daily_marine_forecast(
            location_id=location_id,
            days=days
        )
        
        if not daily:
            raise HTTPException(
                status_code=404,
                detail=f"No daily marine forecast data found for location {location_id}"
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
async def get_all_marine(
    location_id: int,
    days: int = Query(default=7, ge=1, le=10),
    hours: int = Query(default=24, ge=1, le=168)
) -> Dict[str, Any]:
    """
    Get all marine data for a location (current + hourly + daily)
    
    **This is the main endpoint the frontend uses**
    
    Args:
        location_id: Location ID
        days: Number of forecast days (default: 7)
        hours: Number of forecast hours (default: 24)
    
    Returns:
        Complete marine data
    
    Example:
        GET /marine/all/1?days=7&hours=24
        
        Response:
        {
            "success": true,
            "location_id": 1,
            "current": {
                "wave_height": 1.5,
                "swell_wave_height": 1.2,
                ...
            },
            "hourly": {
                "parameters": {
                    "wave_height": {
                        "values": [...],
                        "times": [...]
                    }
                }
            },
            "daily": [...],
            "timestamp": "2025-11-07T14:30:00"
        }
    """
    service = MarineService()
    try:
        marine = service.get_all_marine_data(
            location_id=location_id,
            days=days,
            hours=hours
        )
        
        if not marine:
            raise HTTPException(
                status_code=404,
                detail=f"No marine data found for location {location_id}"
            )
        
        return marine
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        service.db.disconnect()