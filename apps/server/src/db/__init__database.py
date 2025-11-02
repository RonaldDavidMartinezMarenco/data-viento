"""
Database Initialization Script

Run this ONCE after creating the database schema to:
1. Populate weather_models table
2. Populate weather_parameters table
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import logging
from src.services.weather_service import WeatherService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Initialize database with models and parameters"""
    
    print("\n" + "="*60)
    print("DATABASE INITIALIZATION")
    print("="*60 + "\n")
    
    weather_service = WeatherService()
    
    try:
        # Initialize weather models
        print("Initializing weather models...")
        if weather_service.initialize_weather_models():
            print("✓ Weather models initialized\n")
        else:
            print("✗ Failed to initialize weather models\n")
        
        # Initialize weather parameters
        print("Initializing weather parameters...")
        if weather_service.initialize_weather_parameters():
            print("✓ Weather parameters initialized\n")
        else:
            print("✗ Failed to initialize weather parameters\n")
        
        print("="*60)
        print("DATABASE INITIALIZATION COMPLETE")
        print("="*60)
    
    finally:
        weather_service.db.disconnect()

if __name__ == "__main__":
    main()