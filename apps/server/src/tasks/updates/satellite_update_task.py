"""
Satellite Radiation Update Task

Periodic job to fetch and update satellite radiation data for all monitored locations.

Performs:
1. Fetch satellite radiation data for all active locations
2. Process hourly data into daily aggregates
3. Calculate radiation statistics (shortwave, DNI, GTI, etc.)

Schedule:
    Run daily at 5 AM via cron:
    0 5 * * * cd /home/ronald/data-viento/apps/server && python -m src.tasks.updates.satellite_update_task

Usage:
    python -m src.tasks.updates.satellite_update_task
    python -m src.tasks.updates.satellite_update_task --days 7
    python -m src.tasks.updates.satellite_update_task --start-date 2024-01-01 --end-date 2024-01-31
"""

import sys
import asyncio
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from src.tasks.base_task import BaseTask
from src.services.satellite_service import SatelliteService


class SatelliteUpdateTask(BaseTask):
    """
    Periodic satellite radiation data update task
    
    Updates satellite radiation data for all active locations
    
    Workflow:
    1. Get all locations from database
    2. For each location:
       - Fetch hourly satellite radiation data
       - Process into daily aggregates (mean calculations)
       - Handle NULL values gracefully
    3. Save to database (satellite_radiation_daily)
    4. Log results
    
    Special Features:
    - Fetches historical data (yesterday by default)
    - Can backfill multiple days
    - Processes hourly data into daily means
    - Handles missing/NULL radiation values
    """
    
    def __init__(
        self,
        days_back: int = 1,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ):
        """
        Initialize satellite update task
        
        Args:
            days_back: Number of days back to fetch (default: 1 = yesterday)
            start_date: Manual start date (YYYY-MM-DD)
            end_date: Manual end date (YYYY-MM-DD)
        
        Explanation:
        - If start_date/end_date provided, use those
        - Otherwise, fetch last N days (days_back parameter)
        - Default: Fetch yesterday's data (satellite data has ~1 day lag)
        """
        super().__init__(task_name="satellite_update_task")
        
        self.days_back = days_back
        self.start_date = start_date
        self.end_date = end_date
        self.service = SatelliteService()
        
        # Calculate date range if not provided
        if not self.start_date or not self.end_date:
            self._calculate_date_range()
    
    def _calculate_date_range(self):
        """
        Calculate start_date and end_date based on days_back
        
        Explanation:
        - Satellite data typically has 1-2 day lag
        - Default: Fetch yesterday's data (days_back=1)
        - For backfill: Use days_back > 1
        
        Example:
            days_back=1 → yesterday only
            days_back=7 → last 7 days (including yesterday)
        """
        today = datetime.now().date()
        
        # End date: Yesterday (satellite data has lag)
        self.end_date = (today - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Start date: N days before end_date
        start = today - timedelta(days=self.days_back)
        self.start_date = start.strftime('%Y-%m-%d')
        
        self.logger.info(f"Date range: {self.start_date} to {self.end_date}")
    
    def execute(self) -> Dict[str, Any]:
        """
        Execute satellite update for all locations
        
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
                    'total_days_processed': 5,
                    'date_range': '2024-11-03 to 2024-11-03',
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
                'total_days_processed': 0,
                'date_range': f"{self.start_date} to {self.end_date}",
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
            
            self.logger.info(
                f"Found {len(locations)} active locations to update "
                f"({self.start_date} to {self.end_date})"
            )
            
            # Run all location updates in a SINGLE event loop
            asyncio.run(self._update_all_locations(locations, result))
            
            # Success if at least one location updated
            result['success'] = result['details']['locations_succeeded'] > 0
            result['message'] = (
                f"Updated {result['details']['locations_succeeded']}/{len(locations)} locations "
                f"({result['details']['total_days_processed']} days processed)"
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
        - Counts total days processed across all locations
        """
        # Update each location
        for location in locations:
            try:
                days_processed = await self._update_location(location)
                result['details']['locations_succeeded'] += 1
                result['details']['total_days_processed'] += days_processed
            
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
                    'name': 'Madrid Solar Farm',
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
    
    async def _update_location(self, location: Dict[str, Any]) -> int:
        """
        Update satellite radiation data for a single location
        
        Args:
            location: Location dictionary with name, lat, lon, etc.
        
        Returns:
            Number of days processed
        
        Explanation:
        - Calls satellite_service.fetch_and_save_satellite_data()
        - Fetches hourly data for date range
        - Service processes hourly → daily aggregates
        - Logs success/failure
        - Raises exception on failure (caught by _update_all_locations)
        
        Example Flow:
        1. Fetch hourly satellite data (API call)
        2. Process hourly → daily means (skip NULLs)
        3. Save to satellite_radiation_daily (ON DUPLICATE KEY UPDATE)
        """
        self.logger.info(
            f"Updating {location['name']} "
            f"({self.start_date} to {self.end_date})..."
        )
        
        result = await self.service.fetch_and_save_satellite_data(
            location_name=location['name'],
            latitude=location['latitude'],
            longitude=location['longitude'],
            start_date=self.start_date,
            end_date=self.end_date,
            timezone=location['timezone']
        )
        
        if result['success']:
            days_processed = result['processed_records']
            
            self.logger.info(
                f"✓ {location['name']}: "
                f"{days_processed} days processed, "
                f"data_saved={result['data_saved']}"
            )
            
            return days_processed
        else:
            raise Exception(result.get('error', 'Unknown error'))


def main():
    """
    Main entry point for satellite update task
    
    Command-line arguments:
    --days: Number of days back to fetch (default: 1 = yesterday)
    --start-date: Manual start date (YYYY-MM-DD)
    --end-date: Manual end date (YYYY-MM-DD)
    
    Examples:
        # Fetch yesterday's data (default)
        python -m src.tasks.updates.satellite_update_task
        
        # Backfill last 7 days
        python -m src.tasks.updates.satellite_update_task --days 7
        
        # Fetch specific date range
        python -m src.tasks.updates.satellite_update_task \
            --start-date 2024-01-01 --end-date 2024-01-31
        
        # Backfill last 30 days
        python -m src.tasks.updates.satellite_update_task --days 30
    
    Note:
    - Satellite data has 1-2 day lag (fetches historical data)
    - Default: Fetch yesterday's data
    - Use --days for recent backfill
    - Use --start-date/--end-date for historical backfill
    """
    
    parser = argparse.ArgumentParser(
        description='Update satellite radiation data for all locations'
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=1,
        help='Number of days back to fetch (default: 1 = yesterday)'
    )
    
    parser.add_argument(
        '--start-date',
        type=str,
        help='Manual start date (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--end-date',
        type=str,
        help='Manual end date (YYYY-MM-DD)'
    )
    
    args = parser.parse_args()
    
    # Validate date format if provided
    if args.start_date or args.end_date:
        if not (args.start_date and args.end_date):
            parser.error("Both --start-date and --end-date must be provided together")
        
        try:
            datetime.strptime(args.start_date, '%Y-%m-%d')
            datetime.strptime(args.end_date, '%Y-%m-%d')
        except ValueError:
            parser.error("Dates must be in YYYY-MM-DD format")
    
    task = SatelliteUpdateTask(
        days_back=args.days,
        start_date=args.start_date,
        end_date=args.end_date
    )
    
    result = task.run()
    
    sys.exit(0 if result['success'] else 1)


if __name__ == "__main__":
    main()