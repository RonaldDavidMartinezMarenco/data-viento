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

async def test_climate_api_response():
    """
    Test script for Open-Meteo Climate API

    Purpose: Inspect actual API response to understand available fields

    This helps us:
    1. See what fields the Climate API actually returns
    2. Verify which parameters are available
    3. Understand the data structure
    4. Check for rain_sum and snowfall_sum availability

    Run with:
    cd /home/ronald/data-viento/apps/server
    python tests/test_climate_api.py
    """
    
    print("\n" + "="*70)
    print("  OPEN-METEO CLIMATE API - RESPONSE INSPECTION")
    print("="*70 + "\n")
    
    async with OpenMeteoClient() as client:
        
        # Test location: Bogotá, Colombia
        print("Test Location: Bogotá, Colombia")
        print("Coordinates: 4.7110, -74.0721")
        print("Date Range: 2024-01-01 to 2024-01-07 (7 days)")
        print("Model: EC_Earth3P_HR (European Climate Model)")
        print("\n" + "-"*70 + "\n")
        
        # Fetch climate data
        data = await client.get_climate_projection(
            latitude=4.7110,
            longitude=-74.0721,
            start_date="2024-01-01",
            end_date="2024-01-07",
            models="EC_Earth3P_HR",
            timezone="America/Bogota"
        )
        
        if not data:
            print("✗ Failed to retrieve climate data")
            return False
        
        print("✓ Climate data retrieved successfully!\n")
        
        # ==================== METADATA ====================
        print("="*70)
        print("  RESPONSE METADATA")
        print("="*70 + "\n")
        
        metadata_fields = [
            'latitude', 'longitude', 'elevation', 
            'timezone', 'timezone_abbreviation',
            'utc_offset_seconds', 'generationtime_ms'
        ]
        
        for field in metadata_fields:
            if field in data:
                print(f"  {field}: {data[field]}")
        
        # ==================== DAILY FIELDS ====================
        print("\n" + "="*70)
        print("  AVAILABLE DAILY FIELDS")
        print("="*70 + "\n")
        
        if 'daily' in data:
            daily_fields = list(data['daily'].keys())
            
            print(f"Total fields: {len(daily_fields)}\n")
            
            for i, field in enumerate(daily_fields, 1):
                # Get sample value (first day)
                sample_value = data['daily'][field][0] if data['daily'][field] else None
                print(f"  {i:2d}. {field:40s} → {sample_value}")
            
            # ==================== CHECK SPECIFIC FIELDS ====================
            print("\n" + "="*70)
            print("  FIELD AVAILABILITY CHECK")
            print("="*70 + "\n")
            
            fields_to_check = [
                ('precipitation_sum', '✓ Total precipitation'),
                ('rain_sum', '✓ Rain only (separate from snow)'),
                ('snowfall_sum', '✓ Snowfall only'),
                ('temperature_2m_max', '✓ Max temperature'),
                ('temperature_2m_min', '✓ Min temperature'),
                ('temperature_2m_mean', '✓ Mean temperature'),
                ('relative_humidity_2m_mean', '✓ Mean humidity'),
                ('wind_speed_10m_mean', '✓ Mean wind speed'),
                ('pressure_msl_mean', '✓ Mean pressure'),
                ('cloud_cover_mean', '✓ Mean cloud cover'),
                ('shortwave_radiation_sum', '✓ Solar radiation'),
                ('soil_moisture_0_to_10cm_mean', '✓ Soil moisture')
            ]
            
            available = []
            missing = []
            
            for field, description in fields_to_check:
                if field in data['daily']:
                    status = "✓ AVAILABLE"
                    available.append(field)
                else:
                    status = "✗ MISSING"
                    missing.append(field)
                
                print(f"  {status:15s} {field:40s} {description}")
            
            # ==================== CRITICAL CHECK ====================
            print("\n" + "="*70)
            print("  RAIN/SNOW SEPARATION CHECK")
            print("="*70 + "\n")
            
            has_rain = 'rain_sum' in data['daily']
            has_snow = 'snowfall_sum' in data['daily']
            has_precip = 'precipitation_sum' in data['daily']
            
            print(f"  precipitation_sum:  {'✓ YES' if has_precip else '✗ NO'}")
            print(f"  rain_sum:           {'✓ YES' if has_rain else '✗ NO'}")
            print(f"  snowfall_sum:       {'✗ NO' if has_snow else '✗ NO'}")
            
            if not has_rain or not has_snow:
                print("\n  ⚠️  WARNING: Climate API does NOT separate rain/snow!")
                print("      Only total precipitation (precipitation_sum) is available.")
                print("      This is expected for climate projections.")
            
        
            # ==================== RAW JSON ====================
            print("\n" + "="*70)
            print("  RAW JSON RESPONSE (Truncated)")
            print("="*70 + "\n")
            
            # Pretty print first 2 days of daily data
            truncated_data = {
                'latitude': data.get('latitude'),
                'longitude': data.get('longitude'),
                'timezone': data.get('timezone'),
                'daily': {
                    'time': data['daily']['time'][:2],
                    **{
                        key: values[:2] 
                        for key, values in data['daily'].items() 
                        if key != 'time'
                    }
                }
            }
            
            print(json.dumps(truncated_data, indent=2))
            
            # ==================== SUMMARY ====================
            print("\n" + "="*70)
            print("  SUMMARY")
            print("="*70 + "\n")
            
            print(f"  Total daily fields:     {len(daily_fields)}")
            print(f"  Available parameters:   {len(available)}")
            print(f"  Missing parameters:     {len(missing)}")
            print(f"  Days of data:           {len(data['daily']['time'])}")
            
            if missing:
                print(f"\n  ⚠️  Missing fields:")
                for field in missing:
                    print(f"      • {field}")
            
            print("\n" + "="*70)
            
            return True
        
        else:
            print("✗ No daily data in response")
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
    results.append(await test_climate_api_response())
    
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