"""
Satellite Radiation Routes

Provides API endpoints for satellite radiation data:
1. GET /satellite/latest/{location_id} - Latest radiation data (serves as "current")
2. GET /satellite/daily/{location_id} - Daily radiation history
3. GET /satellite/all/{location_id} - All satellite data (latest + daily + statistics)

Maps to table:
- satellite_radiation_daily
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any

from src.services.satellite_service import SatelliteService
from src.db.database import DatabaseConnection

# Create router
router = APIRouter(
    prefix="/satellite",
    tags=["Satellite Radiation Data"]
)


# ========================================
# ROUTES
# ========================================

@router.get("/latest/{location_id}")
async def get_latest_satellite(
    location_id: int,
) -> Dict[str, Any]:
    """
    Get latest satellite radiation data for a location
    
    Since satellite data is daily, this returns the most recent day's data
    and serves as the "current" endpoint
    
    Args:
        location_id: Location ID
    
    Returns:
        Latest satellite radiation data
    
    Example:
        GET /satellite/latest/1
        
        Response:
        {
            "success": true,
            "data": {
                "valid_date": "2025-11-07",
                "shortwave_radiation": 245.5,
                "direct_radiation": 180.2,
                "diffuse_radiation": 65.3,
                "direct_normal_irradiance": 210.8,
                "global_tilted_irradiance": 250.1,
                "terrestrial_radiation": 380.0,
                "quality_flag": "good",
                ...
            }
        }
    """
    service = SatelliteService()
    try:
        latest = service.get_latest_satellite_radiation(location_id)
        
        if not latest:
            raise HTTPException(
                status_code=404,
                detail=f"No satellite radiation data found for location {location_id}"
            )
        
        return {
            "success": True,
            "data": latest
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        service.db.disconnect()


@router.get("/daily/{location_id}")
async def get_daily_satellite(
    location_id: int,
    days: int = Query(default=7, ge=1, le=365)
) -> Dict[str, Any]:
    """
    Get daily satellite radiation history for a location
    
    Args:
        location_id: Location ID
        days: Number of days to retrieve (1-365, default: 7)
    
    Returns:
        Daily satellite radiation data
    
    Example:
        GET /satellite/daily/1?days=7
        
        Response:
        {
            "success": true,
            "data": [
                {
                    "valid_date": "2025-11-07",
                    "shortwave_radiation": 245.5,
                    "direct_radiation": 180.2,
                    "diffuse_radiation": 65.3,
                    "direct_normal_irradiance": 210.8,
                    "global_tilted_irradiance": 250.1,
                    "terrestrial_radiation": 380.0,
                    "panel_tilt_angle": 0,
                    "panel_azimuth_angle": 0,
                    "quality_flag": "good"
                },
                ...
            ],
            "count": 7
        }
    """
    service = SatelliteService()
    try:
        daily = service.get_daily_satellite_radiation(
            location_id=location_id,
            days=days
        )
        
        if not daily:
            raise HTTPException(
                status_code=404,
                detail=f"No daily satellite radiation data found for location {location_id}"
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


@router.get("/statistics/{location_id}")
async def get_satellite_statistics(
    location_id: int,
    start_date: str = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(None, description="End date (YYYY-MM-DD)")
) -> Dict[str, Any]:
    """
    Get aggregated satellite radiation statistics for a location
    
    Args:
        location_id: Location ID
        start_date: Start date (YYYY-MM-DD) - optional
        end_date: End date (YYYY-MM-DD) - optional
    
    Returns:
        Statistical summary of radiation data
    
    Example:
        GET /satellite/statistics/1?start_date=2025-01-01&end_date=2025-01-31
        
        Response:
        {
            "success": true,
            "data": {
                "location_id": 1,
                "total_days": 31,
                "avg_shortwave_radiation": 245.5,
                "avg_direct_radiation": 180.2,
                "avg_diffuse_radiation": 65.3,
                "avg_dni": 210.8,
                "avg_gti": 250.1,
                "max_dni": 850.2,
                "min_dni": 50.3,
                "date_range": "2025-01-01 to 2025-01-31"
            }
        }
    """
    service = SatelliteService()
    try:
        statistics = service.get_satellite_statistics(
            location_id=location_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if not statistics:
            raise HTTPException(
                status_code=404,
                detail=f"No satellite radiation data found for location {location_id}"
            )
        
        return {
            "success": True,
            "data": statistics
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        service.db.disconnect()


@router.get("/all/{location_id}")
async def get_all_satellite(
    location_id: int,
    days: int = Query(default=7, ge=1, le=365)
) -> Dict[str, Any]:
    """
    Get all satellite radiation data for a location
    
    **This is the main endpoint the frontend uses**
    
    Includes:
    - Latest radiation data (most recent day)
    - Daily radiation history
    - Statistical summary
    
    Args:
        location_id: Location ID
        days: Number of days to retrieve (default: 7)
    
    Returns:
        Complete satellite radiation data
    
    Example:
        GET /satellite/all/1?days=7
        
        Response:
        {
            "success": true,
            "location_id": 1,
            "latest": {
                "valid_date": "2025-11-07",
                "shortwave_radiation": 245.5,
                ...
            },
            "daily": [
                {
                    "valid_date": "2025-11-07",
                    "shortwave_radiation": 245.5,
                    ...
                },
                ...
            ],
            "daily_count": 7,
            "statistics": {
                "total_days": 7,
                "avg_dni": 210.8,
                ...
            },
            "timestamp": "2025-11-07T14:30:00"
        }
    """
    service = SatelliteService()
    try:
        satellite = service.get_all_satellite_data(
            location_id=location_id,
            days=days
        )
        
        if not satellite:
            raise HTTPException(
                status_code=404,
                detail=f"No satellite radiation data found for location {location_id}"
            )
        
        return satellite
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        service.db.disconnect()