"""
Task: Fill Colombia Climate Projections

Fetches climate data for 5 major Colombian cities (2022-2026)
Using EC_Earth3P_HR model (European climate model, 29km resolution)

Coverage:
- Bogotá (Andean highlands)
- Medellín (Mountain valley)
- Cali (Tropical savanna)
- Barranquilla (Caribbean coast)
- Leticia (Amazon rainforest)

Date Range: 2022-01-01 to 2026-12-31 (5 years)
Expected Data: ~9,130 daily records (~1.8 MB)

Run with:
    cd /home/ronald/data-viento/apps/server
    python tasks/fill_colombia_climate.py
"""


import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import asyncio
import logging
from datetime import datetime
from src.services.climate_service import ClimateService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

COLOMBIA_LOCATIONS = [
    {
        'name': 'Bogotá',
        'latitude': 4.7110,
        'longitude': -74.0721,
        'timezone': 'America/Bogota',
        'country': 'CO',
        'country_name': 'Colombia',
        'description': 'Capital - Andean highlands (cool, wet climate)'
    },
    {
        'name': 'Medellín',
        'latitude': 6.2476,
        'longitude': -75.5658,
        'timezone': 'America/Bogota',
        'country': 'CO',
        'country_name': 'Colombia',
        'description': 'Mountain valley (eternal spring climate)'
    },
    {
        'name': 'Cali',
        'latitude': 3.4516,
        'longitude': -76.5320,
        'timezone': 'America/Bogota',
        'country': 'CO',
        'country_name': 'Colombia',
        'description': 'Tropical savanna (hot, humid climate)'
    },
    {
        'name': 'Barranquilla',
        'latitude': 10.9639,
        'longitude': -74.7964,
        'timezone': 'America/Bogota',
        'country': 'CO',
        'country_name': 'Colombia',
        'description': 'Caribbean coast (hot, dry climate)'
    },
    {
        'name': 'Leticia',
        'latitude': -4.2153,
        'longitude': -69.9406,
        'timezone': 'America/Bogota',
        'country': 'CO',
        'country_name': 'Colombia',
        'description': 'Amazon rainforest (hot, very wet climate)'
    }
]

CLIMATE_CONFIG = {
    'start_date': '2022-01-01',
    'end_date': '2026-12-31',
    'model': 'EC_Earth3P_HR',  # European climate model (29km resolution)
    'disable_bias_correction': False,
    'cell_selection': 'land'
}

async def fill_colombia_climate_data():
    """
    Main task: Fetch and save climate data for Colombian cities
    
    Process:
    1. Initialize climate service
    2. Loop through each Colombian city
    3. Fetch climate data (2022-2026)
    4. Save to database (climate_projections + climate_daily)
    5. Display progress and summary
    
    Expected Results:
    - 5 climate_projections records (metadata)
    - ~9,130 climate_daily records (1,826 days × 5 cities)
    - ~1.8 MB database storage
    """
    
    logger.info("=" * 70)
    logger.info("  COLOMBIA CLIMATE PROJECTIONS - DATA FILL TASK")
    logger.info("=" * 70)
    logger.info(f"Date Range: {CLIMATE_CONFIG['start_date']} to {CLIMATE_CONFIG['end_date']}")
    logger.info(f"Climate Model: {CLIMATE_CONFIG['model']}")
    logger.info(f"Cities: {len(COLOMBIA_LOCATIONS)}")
    logger.info("=" * 70)
    
    # Initialize service
    climate_service = ClimateService()
    
    # Track results
    results = {
        'total_cities': len(COLOMBIA_LOCATIONS),
        'successful': 0,
        'failed': 0,
        'total_days_saved': 0,
        'errors': []
    }
    
    try:
        # Process each city
        for i, location in enumerate(COLOMBIA_LOCATIONS, 1):
            logger.info(f"\n[{i}/{len(COLOMBIA_LOCATIONS)}] Processing {location['name']}...")
            logger.info(f"    Coordinates: ({location['latitude']}, {location['longitude']})")
            logger.info(f"    Climate Zone: {location['description']}")
            
            try:
                # Fetch and save climate data
                result = await climate_service.fetch_and_save_climate_data(
                    location_name=location['name'],
                    latitude=location['latitude'],
                    longitude=location['longitude'],
                    start_date=CLIMATE_CONFIG['start_date'],
                    end_date=CLIMATE_CONFIG['end_date'],
                    model=CLIMATE_CONFIG['model'],
                    disable_bias_correction=CLIMATE_CONFIG['disable_bias_correction'],
                    cell_selection=CLIMATE_CONFIG['cell_selection'],
                    timezone=location['timezone'],
                    country=location['country'],
                    country_name=location['country_name']
                )
                
                if result['success']:
                    results['successful'] += 1
                    results['total_days_saved'] += result['days_saved']
                    
                    logger.info(f"    ✓ SUCCESS: {location['name']}")
                    logger.info(f"      Location ID: {result['location_id']}")
                    logger.info(f"      Climate ID: {result['climate_id']}")
                    logger.info(f"      Days saved: {result['days_saved']}")
                else:
                    results['failed'] += 1
                    error_msg = f"{location['name']}: {result.get('error', 'Unknown error')}"
                    results['errors'].append(error_msg)
                    logger.error(f"    ✗ FAILED: {error_msg}")
                
                # Rate limiting (be nice to Open-Meteo API)
                if i < len(COLOMBIA_LOCATIONS):
                    logger.info("    Waiting 2 seconds (rate limiting)...")
                    await asyncio.sleep(2)
            
            except Exception as e:
                results['failed'] += 1
                error_msg = f"{location['name']}: {str(e)}"
                results['errors'].append(error_msg)
                logger.error(f"    ✗ ERROR: {error_msg}", exc_info=True)
    
    finally:
        # Close service
        await climate_service.close()
    
    # Print summary
    print_summary(results)
    
    
def print_summary(results: dict):
    """Print task execution summary"""
    
    logger.info("\n" + "=" * 70)
    logger.info("  TASK SUMMARY")
    logger.info("=" * 70)
    
    logger.info(f"Total Cities: {results['total_cities']}")
    logger.info(f"✓ Successful: {results['successful']}")
    logger.info(f"✗ Failed: {results['failed']}")
    logger.info(f"📊 Total Days Saved: {results['total_days_saved']:,}")
    
    # Estimate database size
    estimated_size_mb = (results['total_days_saved'] * 200) / (1024 * 1024)
    logger.info(f"💾 Estimated Database Size: ~{estimated_size_mb:.2f} MB")
    
    if results['errors']:
        logger.info("\n❌ Errors:")
        for error in results['errors']:
            logger.info(f"   • {error}")
    
    logger.info("\n" + "=" * 70)
    
    if results['failed'] == 0:
        logger.info("🎉 ALL CITIES PROCESSED SUCCESSFULLY!")
    else:
        logger.info(f"⚠️  {results['failed']} city(ies) failed to process")
    
    logger.info("=" * 70)
    
async def verify_data():
    """
    Verify that climate data was saved correctly
    
    Checks:
    1. climate_projections table has 5 records
    2. climate_daily table has expected number of days
    3. All Colombian cities are present
    """
    
    logger.info("\n" + "=" * 70)
    logger.info("  VERIFICATION")
    logger.info("=" * 70)
    
    climate_service = ClimateService()
    
    try:
        # Check each city
        for location in COLOMBIA_LOCATIONS:
            logger.info(f"\nChecking {location['name']}...")
            
            # Get location ID
            loc = climate_service.location_service._get_location_by_coords(location['latitude'], location['longitude'])
            
            if not loc:
                logger.warning(f"  ⚠️  Location not found: {location['name']}")
                continue
            
            location_id = loc['location_id']
            
            # Get climate statistics
            stats = climate_service.get_climate_statistics(
                location_id=location_id,
                model_code=CLIMATE_CONFIG['model'],
                start_date=CLIMATE_CONFIG['start_date'],
                end_date=CLIMATE_CONFIG['end_date']
            )
            
            if stats:
                logger.info(f"  ✓ Data found:")
                logger.info(f"    Total days: {stats['total_days']}")
                logger.info(f"    Avg temp: {stats['avg_temp_mean']}°C")
                logger.info(f"    Total precip: {stats['total_precipitation']} mm")
            else:
                logger.warning(f"  ⚠️  No climate data found")
    
    finally:
        await climate_service.close()
    
    logger.info("\n" + "=" * 70)
    
    
async def main():
    """Main task runner"""
    
    start_time = datetime.now()
    
    # Fill climate data
    await fill_colombia_climate_data()
    
    # Verify data
    await verify_data()
    
    # Calculate execution time
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    logger.info(f"\n⏱️  Total Execution Time: {duration:.2f} seconds")


if __name__ == "__main__":
    asyncio.run(main())