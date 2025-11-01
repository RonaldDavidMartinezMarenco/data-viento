"""
Test script for OpenMeteoClient
"""

import sys
from pathlib import Path
import asyncio
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api import OpenMeteoClient
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_weather_forecast():
    """Test weather forecast endpoint"""
    
    print("\n" + "="*60)
    print("TEST 1: Weather Forecast")
    print("="*60 + "\n")
    
    async with OpenMeteoClient() as client:
        # Test with Madrid, Spain
        data = await client.get_weather_forecast(
            latitude=40.4168,
            longitude=-3.7038,
            include_current=True,
            include_daily=True,
            forecast_days=3,
        )
        
        if data:
            print("✓ Weather forecast retrieved successfully!\n")
            print(f"Location: {data.get('latitude')}, {data.get('longitude')}")
            print(f"Timezone: {data.get('timezone')}\n")
            
            if "current" in data:
                print("Current Weather:")
                print(f"  Temperature: {data['current'].get('temperature_2m')} °C")
                print(f"  Humidity: {data['current'].get('relative_humidity_2m')} %")
                print(f"  Wind Speed: {data['current'].get('wind_speed_10m')} km/h\n")
            
            if "daily" in data:
                print(f"Daily Forecast ({len(data['daily']['time'])} days):")
                for i, date in enumerate(data['daily']['time'][:3]):
                    print(f"  {date}:")
                    print(f"    Max: {data['daily']['temperature_2m_max'][i]} °C")
                    print(f"    Min: {data['daily']['temperature_2m_min'][i]} °C")
                    print(f"    Precipitation: {data['daily']['precipitation_sum'][i]} mm")
            
            return True
        else:
            print("✗ Failed to retrieve weather forecast")
            return False


async def test_air_quality():
    """Test air quality endpoint"""
    
    print("\n" + "="*60)
    print("TEST 2: Air Quality")
    print("="*60 + "\n")
    
    async with OpenMeteoClient() as client:
        # Test with New York
        data = await client.get_air_quality(
            latitude=40.7128,
            longitude=-74.0060,
            include_current=True,
        )
        
        if data:
            print("✓ Air quality data retrieved successfully!\n")
            
            if "current" in data:
                print("Current Air Quality:")
                print(f"  PM2.5: {data['current'].get('pm2_5')} µg/m³")
                print(f"  PM10: {data['current'].get('pm10')} µg/m³")
                print(f"  European AQI: {data['current'].get('european_aqi')}")
                print(f"  US AQI: {data['current'].get('us_aqi')}\n")
            
            return True
        else:
            print("✗ Failed to retrieve air quality")
            return False


async def test_marine_forecast():
    """Test marine forecast endpoint"""
    
    print("\n" + "="*60)
    print("TEST 3: Marine Forecast")
    print("="*60 + "\n")
    
    async with OpenMeteoClient() as client:
        # Test with coastal location (Miami)
        data = await client.get_marine_forecast(
            latitude=25.7617,
            longitude=-80.1918,
            include_current=True,
            forecast_days=3,
        )
        
        if data:
            print("✓ Marine forecast retrieved successfully!\n")
            
            if "current" in data:
                print("Current Marine Conditions:")
                print(f"  Wave Height: {data['current'].get('wave_height')} m")
                print(f"  Sea Temperature: {data['current'].get('sea_surface_temperature')} °C")
                print(f"  Wave Period: {data['current'].get('wave_period')} s\n")
            
            return True
        else:
            print("✗ Failed to retrieve marine forecast")
            return False


async def run_all_tests():
    """Run all test functions"""
    
    print("\n" + "="*60)
    print("OPEN-METEO API CLIENT TEST SUITE")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(await test_weather_forecast())
    results.append(await test_air_quality())
    results.append(await test_marine_forecast())
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Passed: {sum(results)}/{len(results)}")
    print(f"Failed: {len(results) - sum(results)}/{len(results)}")
    
    if all(results):
        print("\n✓ All tests passed!")
    else:
        print("\n✗ Some tests failed")
    
    return all(results)


if __name__ == "__main__":
    """Run tests when script is executed directly"""
    
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)