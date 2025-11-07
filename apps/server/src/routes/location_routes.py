import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Dict, Any
from src.services.location_service import LocationService


router = APIRouter(
    prefix="/locations",
    tags=["Locations"]
)

@router.get(
    "/available",
    response_model=List[Dict[str, Any]],
    summary="Get available locations",
    description="Get all default locations available for user selection (10 locations)"
)
def get_available_locations() -> List[Dict[str, Any]]:
    """
    Get available default locations
    
    Returns the 10 pre-configured locations that users can add
    to their favorites. These are the only locations allowed.
    
    Returns:
        List of 10 locations with:
        - location_id: Location ID (1-10)
        - name: City name
        - latitude: Latitude coordinate
        - longitude: Longitude coordinate
        - country: Country code (ES)
        - country_name: Country name (Spain)
        - timezone: Timezone (Europe/Madrid)
    
    Authentication:
        Not required - public endpoint
    
    Example Response:
        [
            {
                "location_id": 1,
                "name": "Madrid",
                "latitude": 40.4168,
                "longitude": -3.7038,
                "country": "ES",
                "country_name": "Spain",
                "timezone": "Europe/Madrid"
            },
            {
                "location_id": 2,
                "name": "Barcelona",
                "latitude": 41.3874,
                "longitude": 2.1686,
                "country": "ES",
                "country_name": "Spain",
                "timezone": "Europe/Madrid"
            },
            ...
        ]
    """
    try:
        location_service = LocationService()
        locations = location_service.get_available_locations()
        
        if not locations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No locations available. Please contact administrator."
            )
        
        return locations
    
    except HTTPException:
        raise
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch locations: {str(e)}"
        )