"""
Cleanup Task

Daily scheduled job to clean up old forecast data.

Performs:
1. Delete forecast batches older than X days
2. Delete individual forecast data points older than Y hours
3. Vacuum/optimize database tables

Schedule:
    Run daily at 2:00 AM via cron:
    0 2 * * * cd /home/ronald/data-viento/apps/server && python -m src.tasks.cleanup_task

Usage:
    python -m src.tasks.cleanup_task
    python -m src.tasks.cleanup_task --days-to-keep 7 --hours-to-keep 168
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import argparse
from typing import Dict, Any
from src.tasks.base_task import BaseTask
from src.services.weather_service import WeatherService


class CleanupTask(BaseTask):
    """
    Daily cleanup task for old forecast data
    
    Cleans up:
    - Old forecast batches (weather_forecasts table)
    - Old forecast data points (forecast_data table)
    - Orphaned records
    """
    
    def __init__(
        self,
        days_to_keep: int = 7,
        hours_to_keep: int = 168
    ):
        """
        Initialize cleanup task
        
        Args:
            days_to_keep: Delete forecast batches older than this (default: 7 days)
            hours_to_keep: Delete data points older than this (default: 168 hours = 7 days)
        """
        super().__init__(task_name="cleanup_task")
        
        self.days_to_keep = days_to_keep
        self.hours_to_keep = hours_to_keep
        self.service = WeatherService()
    
    def execute(self) -> Dict[str, Any]:
        """
        Execute cleanup operations
        
        Returns:
            Dictionary with cleanup results
        """
        result = {
            'success': False,
            'message': '',
            'details': {
                'forecast_batches_deleted': 0,
                'data_points_deleted': 0,
                'errors': []
            }
        }
        
        try:
            # Step 1: Cleanup old forecast batches
            self.logger.info(f"Step 1: Cleaning up forecast batches older than {self.days_to_keep} days...")
            
            deleted_batches = self.service.cleanup_old_forecasts(
                days_to_keep=self.days_to_keep
            )
            
            result['details']['forecast_batches_deleted'] = deleted_batches
            self.logger.info(f"✓ Deleted {deleted_batches} old forecast batches")
            
            # Step 2: Cleanup old data points
            self.logger.info(f"\nStep 2: Cleaning up data points older than {self.hours_to_keep} hours...")
            
            deleted_points = self.service.cleanup_old_forecast_data_points(
                hours_to_keep=self.hours_to_keep
            )
            
            result['details']['data_points_deleted'] = deleted_points
            self.logger.info(f"✓ Deleted {deleted_points} old forecast data points")
            
            # Step 3: Database statistics
            self.logger.info("\nStep 3: Gathering database statistics...")
            stats = self._get_database_stats()
            result['details']['database_stats'] = stats
            
            # Success!
            result['success'] = True
            result['message'] = (
                f"Cleanup completed: {deleted_batches} batches, "
                f"{deleted_points} data points deleted"
            )
        
        except Exception as e:
            result['success'] = False
            result['message'] = f"Cleanup failed: {e}"
            result['details']['errors'].append(str(e))
            self.logger.error(f"Cleanup error: {e}", exc_info=True)
        
        finally:
            # Close service connections
            self.service.db.disconnect()
        
        return result
    
    def _get_database_stats(self) -> Dict[str, int]:
        """
        Get current database statistics
        
        Returns:
            Dictionary with table row counts
        """
        stats = {}
        
        tables = [
            'weather_forecasts',
            'forecast_data',
            'weather_forecasts_daily',
            'current_weather',
            'locations'
        ]
        
        for table in tables:
            query = f"SELECT COUNT(*) FROM {table}"
            result = self.service.db.execute_query(query)
            count = result[0][0] if result else 0
            stats[table] = count
            self.logger.info(f"  {table}: {count:,} rows")
        
        return stats


def main():
    """
    Main entry point for cleanup task
    
    Can be run directly or via cron job
    """
    parser = argparse.ArgumentParser(
        description='Cleanup old weather forecast data'
    )
    
    parser.add_argument(
        '--days-to-keep',
        type=int,
        default=7,
        help='Number of days to keep forecast batches (default: 7)'
    )
    
    parser.add_argument(
        '--hours-to-keep',
        type=int,
        default=168,
        help='Number of hours to keep data points (default: 168 = 7 days)'
    )
    
    args = parser.parse_args()
    
    # Create and run task
    task = CleanupTask(
        days_to_keep=args.days_to_keep,
        hours_to_keep=args.hours_to_keep
    )
    
    result = task.run()
    
    # Exit with proper code
    sys.exit(0 if result['success'] else 1)


if __name__ == "__main__":
    main()