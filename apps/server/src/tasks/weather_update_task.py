"""
Weather Update Task

Periodic job to fetch and update weather data for all monitored locations.

Performs:
1. Fetch current weather for all active locations
2. Fetch daily forecasts
3. Fetch hourly forecasts (optional)

Schedule:
    Run every 3 hours via cron:
    0 */3 * * * cd /home/ronald/data-viento/apps/server && python -m src.tasks.weather_update_task

Usage:
    python -m src.tasks.weather_update_task
    python -m src.tasks.weather_update_task --include-hourly
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import asyncio
import argparse
from typing import Dict, Any, List
from src.tasks.base_task import BaseTask
from src.services.weather_service import WeatherService


class WeatherUpdateTask(BaseTask):
    """
    Periodic weather data update task
    
    Updates weather data for all active locations
    """
    
    def __init__(
        self,
        include_current: bool = True,
        include_hourly: bool = False,
        include_daily: bool = True,
        forecast_days: int = 5
    ):
        """
        Initialize weather update task
        
        Args:
            include_current: Fetch current weather
            include_hourly: Fetch hourly forecast
            include_daily: Fetch daily forecast
            forecast_days: Number of forecast days
        """
        super().__init__(task_name="weather_update_task")
        
        self.include_current = include_current
        self.include_hourly = include_hourly
        self.include_daily = include_daily
        self.forecast_days = forecast_days
        self.service = WeatherService()
    
    def execute(self) -> Dict[str, Any]:
        """
        Execute weather update for all locations
        
        Returns:
            Dictionary with update results
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
            
            # ✅ FIX: Run all location updates in a SINGLE event loop
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
    
    async def _update_all_locations(self, locations: List[Dict[str, Any]], result: Dict[str, Any]):
        """
        Update all locations in a single event loop
        
        Args:
            locations: List of location dictionaries
            result: Result dictionary to update
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
        Update weather data for a single location
        
        Args:
            location: Location dictionary with name, lat, lon, etc.
        """
        self.logger.info(f"Updating {location['name']}...")
        
        result = await self.service.fetch_and_save_weather(
            location_name=location['name'],
            latitude=location['latitude'],
            longitude=location['longitude'],
            include_current=self.include_current,
            include_hourly=self.include_hourly,
            include_daily=self.include_daily,
            forecast_days=self.forecast_days,
            timezone=location['timezone']
        )
        
        if result['success']:
            self.logger.info(
                f"✓ {location['name']}: "
                f"current={result['current_saved']}, "
                f"hourly={result['hourly_saved']}, "
                f"daily={result['daily_saved']}"
            )
        else:
            raise Exception(result.get('error', 'Unknown error'))


def main():
    """Main entry point for weather update task"""
    
    parser = argparse.ArgumentParser(
        description='Update weather data for all locations'
    )
    
    # Mode selection (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group()
    
    mode_group.add_argument(
        '--current-only',
        action='store_true',
        help='Update only current weather (runs every 15 min)'
    )
    
    mode_group.add_argument(
        '--hourly-only',
        action='store_true',
        help='Update only hourly forecast (runs every 3 hours)'
    )
    
    mode_group.add_argument(
        '--daily-only',
        action='store_true',
        help='Update only daily forecast (runs once per day)'
    )
    
    # General options
    parser.add_argument(
        '--include-hourly',
        action='store_true',
        help='Include hourly forecast (for complete updates)'
    )
    
    parser.add_argument(
        '--forecast-days',
        type=int,
        default=7,
        help='Number of forecast days (default: 7)'
    )
    
    args = parser.parse_args()
    
    # Determine what to fetch based on mode
    if args.current_only:
        # Mode 1: Only current weather (every 15 min)
        task = WeatherUpdateTask(
            include_current=True,
            include_hourly=False,
            include_daily=False,
            forecast_days=0
        )
    
    elif args.hourly_only:
        # Mode 2: Only hourly forecast (every 3 hours)
        task = WeatherUpdateTask(
            include_current=False,
            include_hourly=True,
            include_daily=False,
            forecast_days=3
        )
    
    elif args.daily_only:
        # Mode 3: Only daily forecast (once per day)
        task = WeatherUpdateTask(
            include_current=False,
            include_hourly=False,
            include_daily=True,
            forecast_days=5
        )
    
    else:
        # Mode 4: Complete update (current + daily, optionally hourly)
        task = WeatherUpdateTask(
            include_current=True,
            include_hourly=args.include_hourly,
            include_daily=True,
            forecast_days=args.forecast_days
        )
    
    result = task.run()
    
    sys.exit(0 if result['success'] else 1)
if __name__ == "__main__":
    main()