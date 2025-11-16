import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

from src.services.weather_service import WeatherService
from src.middleware.auth_middleware import get_current_user
from src.services.ai_service import AIService


router = APIRouter(
    prefix="/ai",
    tags=["AI-CHAT"]
)


# ========================================
# REQUEST/RESPONSE MODELS
# ========================================

class ChatRequest(BaseModel):
    """Request model for AI chat"""
    query: str = Field(..., description="User's question or query")
    location_id: Optional[int] = Field(None, description="Location context")
    chart_type: Optional[str] = Field(None, description="Type of chart (weather_daily, marine_hourly, etc.)")
    chart_id:  Optional[str] = Field(None, description="Type of chart (weatherTemp,etc.)")
    chart_data:Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = Field(None, description="Current chart data for context")
    session_id: Optional[str] = Field(None, description="Session identifier")
    
    class Config:
        populate_by_name = True  # Allow using both 'query' and 'query_text'

class RatingRequest(BaseModel):
    """Request model for rating a response"""
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    
    
@router.post("/chat")
async def chat_with_ai(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Send a query to AI assistant and get response
    
    Supports context from different chart types:
    - weather_daily: Daily weather forecast
    - weather_hourly: Hourly weather forecast
    - air_quality: Air quality data
    - marine_daily: Daily marine forecast
    - marine_hourly: Hourly marine forecast
    - satellite: Solar radiation data
    - climate: Climate projections
    """
    service = AIService()
    
    try:
        
        print(f"  Received chat request:")
        print(f"  User: {current_user['user_id']}")
        print(f"  Query: {request.query}")
        print(f"  Location: {request.location_id}")
        print(f"  Chart Type: {request.chart_type}")
        print(f"  Chart ID: {request.chart_id}")
        print(f"  Has Chart Data: {request.chart_data is not None}")
        
        response = service.chat(
            user_id=current_user['user_id'],
            query_text=request.query,
            location_id=request.location_id,
            chart_type=request.chart_type,
            chart_id=request.chart_id,
            chart_data=request.chart_data,
            session_id=request.session_id
        )
        
        print(f" Response generated: query_id={response.get('query_id')}")
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        service.db.disconnect()

@router.post("/rate/{query_id}")
async def rate_query_response(
    query_id: int,
    request: RatingRequest,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Rate an AI response (1-5 stars)
    """
    service = AIService()
    
    try:
        success = service.rate_response(query_id, request.rating)
        
        return {
            'success': success,
            'message': f'Response rated {request.rating}/5'
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        service.db.disconnect()

@router.get("/history")
async def get_query_history(
    limit: int = 20,
    session_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get user's query history
    
    Args:
        limit: Maximum number of queries to return (default: 20)
        session_id: Optional filter by session
    """
    service = AIService()
    
    try:
        history = service.get_query_history(
            user_id=current_user['user_id'],
            limit=limit,
            session_id=session_id
        )
        
        return {
            'success': True,
            'data': history,
            'count': len(history)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        service.db.disconnect()

@router.get("/stats")
async def get_query_statistics(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get statistics about user's AI queries
    """
    service = AIService()
    
    try:
        stats = service.get_query_stats(current_user['user_id'])
        
        return {
            'success': True,
            'data': stats
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        service.db.disconnect()