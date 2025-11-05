"""
Air Quality Update Task

Periodic job to fetch and update air quality data for all monitored locations.

Performs:
1. Fetch current air quality for all active locations
2. Fetch hourly air quality forecasts

Schedule:
    Run every 6 hours via cron:
    0 */6 * * * cd /home/ronald/data-viento/apps/server && python -m src.tasks.air_quality_update_task

Usage:
    python -m src.tasks.air_quality_update_task
    python -m src.tasks.air_quality_update_task --current-only
    python -m src.tasks.air_quality_update_task --hourly-only
"""

import sys
import asyncio
import argparse
from typing import Dict, Any, List
from src.tasks.base_task import BaseTask
from src.services.air_quality_service import AirQualityService


class AirQualityUpdateTask(BaseTask):
    """
    Periodic air quality data update task
    
    Updates air quality data for all active locations
    
    Workflow:
    1. Get all locations from database
    2. For each location:
       - Fetch current air quality (PM2.5, PM10, AQI, pollutants)
       - Fetch hourly forecast (if requested)
    3. Save to database (air_quality_current + air_quality_forecasts + air_quality_data)
    4. Log results
    """
    
    def __init__(
        self,
        include_current: bool = True,
        include_hourly: bool = False,
        forecast_days: int = 5,
        domains: str = "auto"
    ):
        """
        Initialize air quality update task
        
        Args:
            include_current: Fetch current air quality
            include_hourly: Fetch hourly forecast
            forecast_days: Number of forecast days (1-5)
            domains: Data domain ('cams_europe', 'cams_global', 'auto')
        """
        super().__init__(task_name="air_quality_update_task")
        
        self.include_current = include_current
        self.include_hourly = include_hourly
        self.forecast_days = forecast_days
        self.domains = domains
        self.service = AirQualityService()
    
    def execute(self) -> Dict[str, Any]:
        """
        Execute air quality update for all locations
        
        Returns:
            Dictionary with update results
        
        Example Result:
            {
                'success': True,
                'message': 'Updated 5/5 locations',
                'details': {
                    'locations_processed': 5,
                    'locations_succeeded': 5,
                    'locations_failed': 0,
                    'errors': []
                }
            }
        """
        result = {
            'success': False,
            'message': '',
            'details': {
                'locations_processed': 0,
                'locations_succeeded': 0,
                'locations_failed': 0,
                'errors': []
            }
        }
        
        try:
            # Get all active locations
            locations = self._get_active_locations()
            
            if not locations:
                self.logger.warning("No active locations found")
                result['success'] = True
                result['message'] = "No locations to update"
                return result
            
            self.logger.info(f"Found {len(locations)} active locations to update")
            
            # ✅ Run all location updates in a SINGLE event loop
            asyncio.run(self._update_all_locations(locations, result))
            
            # Success if at least one location updated
            result['success'] = result['details']['locations_succeeded'] > 0
            result['message'] = (
                f"Updated {result['details']['locations_succeeded']}/{len(locations)} locations"
            )
        
        except Exception as e:
            result['success'] = False
            result['message'] = f"Update task failed: {e}"
            result['details']['errors'].append(str(e))
            self.logger.error(f"Update task error: {e}", exc_info=True)
        
        finally:
            # Close service connection (but NOT inside async loop)
            self.service.db.disconnect()
        
        return result
    
    async def _update_all_locations(
        self, 
        locations: List[Dict[str, Any]], 
        result: Dict[str, Any]
    ):
        """
        Update all locations in a single event loop
        
        Args:
            locations: List of location dictionaries
            result: Result dictionary to update
        
        Explanation:
        - Processes each location sequentially
        - Updates result dictionary with success/failure counts
        - Logs errors for failed locations
        """
        # Update each location
        for location in locations:
            try:
                await self._update_location(location)
                result['details']['locations_succeeded'] += 1
            
            except Exception as e:
                self.logger.error(
                    f"Failed to update location {location['name']}: {e}",
                    exc_info=True
                )
                result['details']['locations_failed'] += 1
                result['details']['errors'].append({
                    'location': location['name'],
                    'error': str(e)
                })
            
            finally:
                result['details']['locations_processed'] += 1
    
    def _get_active_locations(self) -> List[Dict[str, Any]]:
        """
        Get all active locations from database
        
        Returns:
            List of location dictionaries
        
        Example:
            [
                {
                    'location_id': 1,
                    'name': 'Madrid',
                    'latitude': 40.4168,
                    'longitude': -3.7038,
                    'timezone': 'Europe/Madrid',
                    'country': 'ES'
                },
                ...
            ]
        
        Note:
        - Only gets locations with coordinates
        - Orders by location_id for consistent processing
        - Timezone defaults to 'auto' if not set
        """
        query = """
        SELECT location_id, name, latitude, longitude, timezone, country
        FROM locations
        ORDER BY location_id
        """
        
        rows = self.service.db.execute_query(query)
        
        if not rows:
            return []
        
        locations = []
        for row in rows:
            locations.append({
                'location_id': row[0],
                'name': row[1],
                'latitude': row[2],
                'longitude': row[3],
                'timezone': row[4] or 'auto',
                'country': row[5]
            })
        
        return locations
    
    async def _update_location(self, location: Dict[str, Any]):
        """
        Update air quality data for a single location
        
        Args:
            location: Location dictionary with name, lat, lon, etc.
        
        Explanation:
        - Calls air_quality_service.fetch_and_save_air_quality()
        - Logs success/failure
        - Raises exception on failure (caught by _update_all_locations)
        
        Example Flow:
        1. Fetch current air quality (PM2.5, PM10, AQI, NO2, O3, etc.)
        2. Save to air_quality_current (ON DUPLICATE KEY UPDATE)
        3. If hourly requested:
           - Create forecast batch (air_quality_forecasts)
           - Save hourly data (air_quality_data)
        """
        self.logger.info(f"Updating {location['name']}...")
        
        result = await self.service.fetch_and_save_air_quality(
            location_name=location['name'],
            latitude=location['latitude'],
            longitude=location['longitude'],
            include_current=self.include_current,
            include_hourly=self.include_hourly,
            forecast_days=self.forecast_days,
            domains=self.domains,
            timezone=location['timezone']
        )
        
        if result['success']:
            self.logger.info(
                f"✓ {location['name']}: "
                f"current={result['current_saved']}, "
                f"hourly={result['hourly_saved']}"
            )
        else:
            raise Exception(result.get('error', 'Unknown error'))


def main():
    """
    Main entry point for air quality update task
    
    Command-line arguments:
    --current-only: Update only current air quality (runs every 1-3 hours)
    --hourly-only: Update only hourly forecast (runs every 6 hours)
    --forecast-days: Number of forecast days (default: 5, max: 5)
    --domains: Data domain ('cams_europe', 'cams_global', 'auto')
    
    Examples:
        # Update current + hourly (default)
        python -m src.tasks.air_quality_update_task
        
        # Update only current air quality
        python -m src.tasks.air_quality_update_task --current-only
        
        # Update only hourly forecast
        python -m src.tasks.air_quality_update_task --hourly-only
        
        # Update with 3-day forecast
        python -m src.tasks.air_quality_update_task --forecast-days 3
        
        # Force European domain
        python -m src.tasks.air_quality_update_task --domains cams_europe
    """
    
    parser = argparse.ArgumentParser(
        description='Update air quality data for all locations'
    )
    
    # Mode selection (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group()
    
    mode_group.add_argument(
        '--current-only',
        action='store_true',
        help='Update only current air quality (runs every 3 hours)'
    )
    
    mode_group.add_argument(
        '--hourly-only',
        action='store_true',
        help='Update only hourly forecast (runs every 6 hours)'
    )
    
    # General options
    parser.add_argument(
        '--forecast-days',
        type=int,
        default=5,
        choices=[1,3,5,7],
        help='Number of forecast days (default: 5, max: 5)'
    )
    
    parser.add_argument(
        '--domains',
        type=str,
        default='auto',
        choices=['auto', 'cams_europe', 'cams_global'],
        help='Data domain (default: auto)'
    )
    
    args = parser.parse_args()
    
    # Determine what to fetch based on mode
    if args.current_only:
        # Mode 1: Only current air quality (every 3 hours)
        task = AirQualityUpdateTask(
            include_current=True,
            include_hourly=False,
            forecast_days=0,
            domains=args.domains
        )
    
    elif args.hourly_only:
        # Mode 2: Only hourly forecast (every 6 hours)
        task = AirQualityUpdateTask(
            include_current=False,
            include_hourly=True,
            forecast_days=args.forecast_days,
            domains=args.domains
        )
    
    else:
        # Mode 3: Complete update (current + hourly)
        task = AirQualityUpdateTask(
            include_current=True,
            include_hourly=True,
            forecast_days=args.forecast_days,
            domains=args.domains
        )
    
    result = task.run()
    
    sys.exit(0 if result['success'] else 1)


if __name__ == "__main__":
    main()
    