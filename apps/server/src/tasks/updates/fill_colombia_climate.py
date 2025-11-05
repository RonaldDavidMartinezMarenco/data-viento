"""
Task: Fill Colombia Climate Projections

Fetches climate data for all locations in database (2022-2026)
Using EC_Earth3P_HR model (European climate model, 29km resolution)

Date Range: 2022-01-01 to 2026-12-31 (5 years)

Run with:
    cd /home/ronald/data-viento/apps/server
    python tasks/fill_colombia_climate.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import asyncio
import logging
from datetime import datetime
from src.services.climate_service import ClimateService
from src.db.database import DatabaseConnection  

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


CLIMATE_CONFIG = {
    'start_date': '2022-01-01',
    'end_date': '2026-12-31',
    'model': 'EC_Earth3P_HR',
    'disable_bias_correction': False,
    'cell_selection': 'land'
}


async def get_locations():
    """
    Fetch all locations from database and format them for climate data fetching
    
    Returns:
        list: List of location dictionaries matching COLOMBIA_LOCATIONS format
    """
    db = DatabaseConnection()
    db.connect()
    try:
        query = """
        SELECT 
            location_id,
            name,
            latitude,
            longitude,
            timezone,
            country,
            country_name,
            state,
            elevation
        FROM locations
        ORDER BY location_id
        """
        
        results = db.execute_query(query)
        
        if not results:
            logger.warning("No locations found in database")
            return []
        
        locations = []
        for row in results:
            # Build description from available data
            description_parts = []
            if row[7]:  # state
                description_parts.append(row[7])
            if row[8]:  # elevation
                description_parts.append(f"Elevation: {row[8]}m")
            
            description = " - ".join(description_parts) if description_parts else "No description"
            
            location = {
                'name': row[1],
                'latitude': float(row[2]),
                'longitude': float(row[3]),
                'timezone': row[4] if row[4] else 'UTC',
                'country': row[5] if row[5] else 'XX',
                'country_name': row[6] if row[6] else 'Unknown',
                'description': description
            }
            locations.append(location)
        
        logger.info(f"Loaded {len(locations)} locations from database")
        return locations
    
    except Exception as e:
        logger.error(f"Error fetching locations: {e}", exc_info=True)
        return []
    
    finally:
        db.disconnect()


async def fill_colombia_climate_data():
    """
    Main task: Fetch and save climate data for all locations
    
    Process:
    1. Fetch locations from database
    2. Initialize climate service
    3. Loop through each location
    4. Fetch climate data (2022-2026)
    5. Save to database (climate_projections + climate_daily)
    6. Display progress and summary
    """
    
    logger.info("=" * 70)
    logger.info("  COLOMBIA CLIMATE PROJECTIONS - DATA FILL TASK")
    logger.info("=" * 70)
    logger.info(f"Date Range: {CLIMATE_CONFIG['start_date']} to {CLIMATE_CONFIG['end_date']}")
    logger.info(f"Climate Model: {CLIMATE_CONFIG['model']}")

    locations = await get_locations()
    
    if not locations:
        logger.error("No locations found in database. Exiting.")
        return
    
    logger.info(f"Cities: {len(locations)}")
    logger.info("=" * 70)
    
    # Initialize service
    climate_service = ClimateService()
    
    # Track results
    results = {
        'total_cities': len(locations),
        'successful': 0,
        'failed': 0,
        'total_days_saved': 0,
        'errors': []
    }
    
    try:
        # Process each city
        for i, location in enumerate(locations, 1):
            logger.info(f"\n[{i}/{len(locations)}] Processing {location['name']}...")
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
                if i < len(locations):
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
    logger.info(f"Total Days Saved: {results['total_days_saved']:,}")
    
    # Estimate database size
    estimated_size_mb = (results['total_days_saved'] * 200) / (1024 * 1024)
    logger.info(f"Estimated Database Size: ~{estimated_size_mb:.2f} MB")
    
    if results['errors']:
        logger.info("\nErrors:")
        for error in results['errors']:
            logger.info(f"   • {error}")
    
    logger.info("\n" + "=" * 70)
    
    if results['failed'] == 0:
        logger.info("ALL CITIES PROCESSED SUCCESSFULLY!")
    else:
        logger.info(f"{results['failed']} city(ies) failed to process")
    
    logger.info("=" * 70)
    

async def verify_data():
    """
    Verify that climate data was saved correctly
    """
    
    logger.info("\n" + "=" * 70)
    logger.info("  VERIFICATION")
    logger.info("=" * 70)
    
    climate_service = ClimateService()

    locations = await get_locations()
    
    try:
        # Check each city
        for location in locations:
            logger.info(f"\nChecking {location['name']}...")
            
            # Get location ID
            loc = climate_service.location_service._get_location_by_coords(location['latitude'], location['longitude'])
            
            if not loc:
                logger.warning(f"Location not found: {location['name']}")
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
                logger.warning(f"  ✗ No climate data found")
    
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
    
    logger.info(f"\nTotal Execution Time: {duration:.2f} seconds")


if __name__ == "__main__":
    asyncio.run(main())