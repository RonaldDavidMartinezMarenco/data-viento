"""
Air Quality Routes

Provides API endpoints for air quality data:
1. GET /air-quality/current/{location_id} - Current air quality
2. GET /air-quality/hourly/{location_id} - Hourly forecast
3. GET /air-quality/all/{location_id} - All air quality data (current + hourly)

Maps to tables:
- air_quality_current
- air_quality_forecasts + air_quality_data (hourly)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional, List

from src.services.air_quality_service import AirQualityService
from src.db.database import DatabaseConnection

# Create router
router = APIRouter(
    prefix="/air-quality",
    tags=["Air Quality Data"]
)



# ========================================
# ROUTES
# ========================================

@router.get("/current/{location_id}")
async def get_current_air_quality(
    location_id: int
) -> Dict[str, Any]:
    """
    Get current air quality for a location
    
    Args:
        location_id: Location ID
    
    Returns:
        Current air quality data
    
    Example:
        GET /air-quality/current/1
        
        Response:
        {
            "success": true,
            "data": {
                "pm2_5": 12.5,
                "pm10": 25.3,
                "european_aqi": 45,
                "us_aqi": 52,
                ...
            }
        }
    """
    
    service = AirQualityService()
    
    try:
        current = service.get_current_air_quality(location_id)
        
        if not current:
            raise HTTPException(
                status_code=404,
                detail=f"No current air quality data found for location {location_id}"
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
async def get_hourly_air_quality(
    location_id: int,
    hours: int = Query(default=24, ge=1, le=120),
    parameters: Optional[List[str]] = Query(default=None)
) -> Dict[str, Any]:
    """
    Get hourly air quality forecast for a location
    
    Args:
        location_id: Location ID
        hours: Number of forecast hours (1-120, default: 24)
        parameters: List of parameter codes (optional)
    
    Returns:
        Hourly air quality forecast data
    
    Example:
        GET /air-quality/hourly/1?hours=24&parameters=pm2_5&parameters=pm10
        
        Response:
        {
            "success": true,
            "data": {
                "parameters": {
                    "pm2_5": {
                        "name": "PM2.5",
                        "unit": "µg/m³",
                        "values": [12.5, 13.2, ...],
                        "times": ["2025-11-07T14:00:00", ...],
                        "categories": ["good", "good", ...],
                        "health_impacts": ["low", "low", ...]
                    }
                }
            }
        }
    """
    service = AirQualityService()
    try:
        hourly = service.get_hourly_air_quality(
            location_id=location_id,
            hours=hours,
            parameters=parameters
        )
        
        if not hourly:
            raise HTTPException(
                status_code=404,
                detail=f"No hourly air quality data found for location {location_id}"
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


@router.get("/all/{location_id}")
async def get_all_air_quality(
    location_id: int,
    hours: int = Query(default=24, ge=1, le=120)
) -> Dict[str, Any]:
    """
    Get all air quality data for a location (current + hourly)
    
    **This is the main endpoint the frontend uses**
    
    Args:
        location_id: Location ID
        hours: Number of forecast hours (default: 24)
    
    Returns:
        Complete air quality data
    
    Example:
        GET /air-quality/all/1?hours=24
        
        Response:
        {
            "success": true,
            "location_id": 1,
            "current": {
                "pm2_5": 12.5,
                "european_aqi": 45,
                ...
            },
            "hourly": {
                "parameters": {
                    "pm2_5": {
                        "values": [...],
                        "times": [...]
                    }
                }
            },
            "timestamp": "2025-11-07T14:30:00"
        }
    """
    service = AirQualityService()
    try:
        air_quality = service.get_all_air_quality_data(
            location_id=location_id,
            hours=hours
        )
        
        if not air_quality:
            raise HTTPException(
                status_code=404,
                detail=f"No air quality data found for location {location_id}"
            )
        
        return air_quality
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        service.db.disconnect()