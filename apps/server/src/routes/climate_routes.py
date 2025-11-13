"""
Climate Projection Routes

Provides API endpoints for climate change projection data:
1. GET /climate/projection/{location_id} - Get specific projection by model and date range
2. GET /climate/statistics/{location_id} - Get aggregated statistics
3. GET /climate/projections/{location_id} - List all available projections
4. GET /climate/all/{location_id} - All climate data (projection + statistics + list)

Maps to tables:
- climate_projections (metadata)
- climate_daily (daily values)

Note: Climate data is HISTORICAL + FUTURE (not "current" like weather)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional

from src.services.climate_service import ClimateService
from src.db.database import DatabaseConnection

# Create router
router = APIRouter(
    prefix="/climate",
    tags=["Climate Projections Data"]
)


# ========================================
# ROUTES
# ========================================

@router.get("/projection/{location_id}")
async def get_climate_projection(
    location_id: int,
    model: str = Query(default='EC_Earth3P_HR', description="Climate model code"),
    start_date: str = Query(default= '2022-01-01', description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(default = '2026-12-31', description="End date (YYYY-MM-DD)"),
) -> Dict[str, Any]:
    """
    Get climate projection for a specific model and date range
    
    Args:
        location_id: Location ID
        model: Climate model code (e.g., 'CMCC_CM2_VHR4', 'MRI_AGCM3_2_S', 'EC_Earth3P_HR')
        start_date: Start date (YYYY-MM-DD) - REQUIRED
        end_date: End date (YYYY-MM-DD) - REQUIRED
    
    Returns:
        Climate projection data
    
    Example:
        GET /climate/projection/1?model=CMCC_CM2_VHR4&start_date=2050-01-01&end_date=2050-12-31
        
        Response:
        {
            "success": true,
            "data": {
                "climate_id": 1,
                "model_code": "CMCC_CM2_VHR4",
                "model_name": "CMCC-CM2-VHR4",
                "start_date": "2050-01-01",
                "end_date": "2050-12-31",
                "total_days": 365,
                "daily_data": [
                    {
                        "valid_date": "2050-01-01",
                        "temperature_2m_max": 15.2,
                        "temperature_2m_min": 5.8,
                        "temperature_2m_mean": 10.5,
                        "precipitation_sum": 2.5,
                        "rain_sum": 2.5,
                        "snowfall_sum": 0.0,
                        ...
                    },
                    ...
                ]
            }
        }
    
    Available Models:
        - CMCC_CM2_VHR4: Italian model (25km)
        - MRI_AGCM3_2_S: Japanese model (20km)
        - EC_Earth3P_HR: European model (25km)
        - FGOALS_f3_H: Chinese model (28km)
        - HiRAM_SIT_HR: US model (25km)
        - NICAM_AMIP: Japanese non-hydrostatic (14km)
    """
    service = ClimateService()
    
    try:
        projection = service.get_climate_projection(
            location_id=location_id,
            model_code=model,
            start_date=start_date,
            end_date=end_date
        )
        
        if not projection:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"No climate projection found for location {location_id}, "
                    f"model {model}, {start_date} to {end_date}"
                )
            )
        
        return {
            "success": True,
            "data": projection
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        service.db.disconnect()


@router.get("/statistics/{location_id}")
async def get_climate_statistics(
    location_id: int,
    model: str = Query(default='EC_Earth3P_HR', description="Climate model code"),
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)")
) -> Dict[str, Any]:
    """
    Get aggregated climate statistics for a date range
    
    Args:
        location_id: Location ID
        model: Climate model code
        start_date: Start date (YYYY-MM-DD) - REQUIRED
        end_date: End date (YYYY-MM-DD) - REQUIRED
    
    Returns:
        Statistical summary of climate data
    
    Example:
        GET /climate/statistics/1?model=CMCC_CM2_VHR4&start_date=2050-01-01&end_date=2050-12-31
        
        Response:
        {
            "success": true,
            "data": {
                "location_id": 1,
                "model_code": "CMCC_CM2_VHR4",
                "period": "2050-01-01 to 2050-12-31",
                "total_days": 365,
                "avg_temp_max": 18.5,
                "avg_temp_min": 8.2,
                "avg_temp_mean": 13.4,
                "total_precipitation": 650.5,
                "total_rain": 580.2,
                "total_snowfall": 70.3,
                "avg_humidity": 65.5,
                "avg_wind_speed": 12.3,
                "avg_pressure": 1013.2,
                "avg_cloud_cover": 55.0,
                "total_radiation": 4520.5
            }
        }
    """
    service = ClimateService()
    
    try:
        statistics = service.get_climate_statistics(
            location_id=location_id,
            model_code=model,
            start_date=start_date,
            end_date=end_date
        )
        
        if not statistics:
            raise HTTPException(
                status_code=404,
                detail=(
                    f"No climate data found for statistics calculation: "
                    f"location {location_id}, model {model}, {start_date} to {end_date}"
                )
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


@router.get("/projections/{location_id}")
async def list_climate_projections(
    location_id: int
) -> Dict[str, Any]:
    """
    List all available climate projections for a location
    
    Useful to discover what data is available before querying specific projections
    
    Args:
        location_id: Location ID
    
    Returns:
        List of available projections
    
    Example:
        GET /climate/projections/1
        
        Response:
        {
            "success": true,
            "data": [
                {
                    "climate_id": 1,
                    "model_code": "CMCC_CM2_VHR4",
                    "model_name": "CMCC-CM2-VHR4",
                    "start_date": "2050-01-01",
                    "end_date": "2050-12-31",
                    "total_days": 365
                },
                {
                    "climate_id": 2,
                    "model_code": "MRI_AGCM3_2_S",
                    "model_name": "MRI-AGCM3.2-S",
                    "start_date": "2070-01-01",
                    "end_date": "2070-12-31",
                    "total_days": 365
                }
            ],
            "count": 2
        }
    """
    service = ClimateService()
    try:
        projections = service.list_available_projections(location_id)
        
        if not projections:
            raise HTTPException(
                status_code=404,
                detail=f"No climate projections found for location {location_id}"
            )
        
        return {
            "success": True,
            "data": projections,
            "count": len(projections)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        service.db.disconnect()


@router.get("/all/{location_id}")
async def get_all_climate(
    location_id: int,
    model: str = Query(default='EC_Earth3P_HR', description="Climate model code"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
) -> Dict[str, Any]:
    """
    Get all climate data for a location
    
    **This is the main endpoint the frontend uses**
    
    Includes:
    - Climate projection data (daily values)
    - Statistical summary
    - List of all available projections
    
    Args:
        location_id: Location ID
        model: Climate model code (default: 'EC_Earth3P_HR')
        start_date: Start date (YYYY-MM-DD) - if omitted, uses most recent
        end_date: End date (YYYY-MM-DD) - if omitted, uses most recent
    
    Returns:
        Complete climate data
    
    Example:
        GET /climate/all/1?model=CMCC_CM2_VHR4&start_date=2050-01-01&end_date=2050-12-31
        
        Response:
        {
            "success": true,
            "location_id": 1,
            "projection": {
                "climate_id": 1,
                "model_code": "CMCC_CM2_VHR4",
                "start_date": "2050-01-01",
                "end_date": "2050-12-31",
                "total_days": 365,
                "daily_data": [...]
            },
            "statistics": {
                "avg_temp_max": 18.5,
                "total_precipitation": 650.5,
                ...
            },
            "available_projections": [
                {
                    "climate_id": 1,
                    "model_code": "CMCC_CM2_VHR4",
                    "start_date": "2050-01-01",
                    "end_date": "2050-12-31"
                },
                ...
            ],
            "timestamp": "2025-11-07T14:30:00"
        }
    """
    service = ClimateService()
    try:
        climate = service.get_all_climate_data(
            location_id=location_id,
            model_code=model,
            start_date=start_date,
            end_date=end_date
        )
        
        if not climate:
            raise HTTPException(
                status_code=404,
                detail=f"No climate data found for location {location_id}"
            )
        
        return climate
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        service.db.disconnect()