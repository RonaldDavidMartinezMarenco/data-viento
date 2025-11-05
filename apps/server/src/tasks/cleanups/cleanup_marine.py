"""
Cleanup Marine Task

Removes old marine forecast data to keep database size manageable.

Performs:
1. Delete old marine_forecasts batches (cascade deletes marine_data)
2. Delete old marine_forecasts_daily records
3. Optionally clean up orphaned marine_current records

Schedule:
    Run daily at 3 AM:
    0 3 * * * cd /home/ronald/data-viento/apps/server && python -m src.tasks.cleanup.cleanup_marine_task

Usage:
    python -m src.tasks.cleanup.cleanup_marine_task
    python -m src.tasks.cleanup.cleanup_marine_task --days 14
    python -m src.tasks.cleanup.cleanup_marine_task --hourly-hours 72
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import argparse
from typing import Dict, Any
from src.tasks.base_task import BaseTask
from src.services.marine_service import MarineService


class CleanupMarineTask(BaseTask):
    """
    Cleanup old marine forecast data
    
    Workflow:
    1. Delete marine_forecasts batches older than X days
       - This CASCADE deletes marine_data rows (FK constraint)
    2. Delete marine_forecasts_daily older than X days
    3. Log cleanup statistics
    
    Database Impact:
    - marine_forecasts: Metadata table (small)
    - marine_data: Large table (hourly data points)
    - marine_forecasts_daily: Medium table (daily forecasts)
    
    Retention Policy:
    - Hourly data: 3-7 days (configurable)
    - Daily forecasts: 30 days (configurable)
    - Current conditions: Never deleted (always 1 row per location)
    """
    
    def __init__(
        self,
        days_to_keep_daily: int = 30,
        days_to_keep_hourly: int = 7
    ):
        """
        Initialize cleanup task
        
        Args:
            days_to_keep_daily: Number of days to keep daily forecasts (default: 30)
            days_to_keep_hourly: Number of days to keep hourly forecasts (default: 7)
        """
        super().__init__(task_name="cleanup_marine_task")
        
        self.days_to_keep_daily = days_to_keep_daily
        self.days_to_keep_hourly = days_to_keep_hourly
        self.service = MarineService()
    
    def execute(self) -> Dict[str, Any]:
        """
        Execute cleanup
        
        Returns:
            Dictionary with cleanup results
        
        Example Result:
            {
                'success': True,
                'message': 'Deleted 10 hourly batches, 20 daily forecasts',
                'details': {
                    'hourly_batches_deleted': 10,
                    'hourly_data_points_deleted': 1680,
                    'daily_forecasts_deleted': 20
                }
            }
        """
        result = {
            'success': False,
            'message': '',
            'details': {
                'hourly_batches_deleted': 0,
                'hourly_data_points_deleted': 0,
                'daily_forecasts_deleted': 0
            }
        }
        
        try:
            self.logger.info("Starting marine data cleanup...")
            
            # Step 1: Clean up hourly forecast batches (+ cascade delete marine_data)
            if self.days_to_keep_hourly > 0:
                hourly_batches = self._cleanup_hourly_forecasts()
                result['details']['hourly_batches_deleted'] = hourly_batches
                
                self.logger.info(
                    f"✓ Deleted {hourly_batches} hourly forecast batches "
                    f"older than {self.days_to_keep_hourly} days"
                )
            
            # Step 2: Clean up daily forecasts
            if self.days_to_keep_daily > 0:
                daily_deleted = self._cleanup_daily_forecasts()
                result['details']['daily_forecasts_deleted'] = daily_deleted
                
                self.logger.info(
                    f"✓ Deleted {daily_deleted} daily forecast records "
                    f"older than {self.days_to_keep_daily} days"
                )
            
            # Success message
            result['success'] = True
            result['message'] = (
                f"Deleted {result['details']['hourly_batches_deleted']} hourly batches, "
                f"{result['details']['daily_forecasts_deleted']} daily forecasts"
            )
            
            self.logger.info(f"✓ Cleanup completed successfully")
        
        except Exception as e:
            result['success'] = False
            result['message'] = f"Cleanup failed: {e}"
            self.logger.error(f"Cleanup error: {e}", exc_info=True)
        
        finally:
            self.service.db.disconnect()
        
        return result
    
    def _cleanup_hourly_forecasts(self) -> int:
        """
        Delete old hourly forecast batches (cascade deletes marine_data)
        
        Returns:
            Number of forecast batches deleted
        
        Explanation:
        - Deletes marine_forecasts rows older than X days
        - FK constraint CASCADE deletes marine_data rows
        - This is the main cleanup (hourly data is largest)
        
        SQL Flow:
        1. SELECT marine_id FROM marine_forecasts WHERE old
        2. COUNT marine_data rows to be deleted
        3. DELETE FROM marine_forecasts (CASCADE to marine_data)
        """
        
        try:
            # Step 1: Find old forecast IDs
            select_query = """
            SELECT marine_id, location_id, forecast_reference_time,
                   (SELECT COUNT(*) FROM marine_data WHERE marine_id = mf.marine_id) as data_points
            FROM marine_forecasts mf
            WHERE forecast_reference_time < DATE_SUB(NOW(), INTERVAL %s DAY)
            """
            
            old_forecasts = self.service.db.execute_query(
                select_query,
                (self.days_to_keep_hourly,)
            )
            
            if not old_forecasts:
                self.logger.info(
                    f"No hourly forecasts older than {self.days_to_keep_hourly} days to delete"
                )
                return 0
            
            forecast_ids = [row[0] for row in old_forecasts]
            total_data_points = sum(row[3] for row in old_forecasts)
            
            self.logger.info(
                f"Found {len(forecast_ids)} forecast batches with "
                f"{total_data_points:,} data points to delete"
            )
            
            # Step 2: Delete marine_data rows first (explicit delete for logging)
            if forecast_ids:
                placeholders = ','.join(['%s'] * len(forecast_ids))
                
                # Count before delete
                count_query = f"""
                SELECT COUNT(*) FROM marine_data
                WHERE marine_id IN ({placeholders})
                """
                count_result = self.service.db.execute_query(count_query, forecast_ids)
                data_count = count_result[0][0] if count_result else 0
                
                # Delete marine_data
                delete_data_query = f"""
                DELETE FROM marine_data
                WHERE marine_id IN ({placeholders})
                """
                
                self.service.db.execute_query(delete_data_query, forecast_ids)
                self.logger.info(f"  ✓ Deleted {data_count:,} marine_data rows")
            
            # Step 3: Delete forecast batches
            delete_forecast_query = f"""
            DELETE FROM marine_forecasts
            WHERE marine_id IN ({placeholders})
            """
            
            self.service.db.execute_query(delete_forecast_query, forecast_ids)
            
            self.logger.info(
                f"  ✓ Deleted {len(forecast_ids)} marine_forecasts batches"
            )
            
            return len(forecast_ids)
        
        except Exception as e:
            self.logger.error(f"Error cleaning hourly forecasts: {e}", exc_info=True)
            return 0
    
    def _cleanup_daily_forecasts(self) -> int:
        """
        Delete old daily marine forecasts
        
        Returns:
            Number of daily forecast records deleted
        
        Explanation:
        - Deletes marine_forecasts_daily rows older than X days
        - No cascade (standalone table)
        - Lighter than hourly cleanup
        """
        
        try:
            # Count before delete
            count_query = """
            SELECT COUNT(*) FROM marine_forecasts_daily
            WHERE valid_date < DATE_SUB(CURDATE(), INTERVAL %s DAY)
            """
            
            count_result = self.service.db.execute_query(
                count_query,
                (self.days_to_keep_daily,)
            )
            count = count_result[0][0] if count_result else 0
            
            if count == 0:
                self.logger.info(
                    f"No daily forecasts older than {self.days_to_keep_daily} days to delete"
                )
                return 0
            
            # Delete old daily forecasts
            delete_query = """
            DELETE FROM marine_forecasts_daily
            WHERE valid_date < DATE_SUB(CURDATE(), INTERVAL %s DAY)
            """
            
            cursor = self.service.db.connection.cursor()
            cursor.execute(delete_query, (self.days_to_keep_daily,))
            deleted_count = cursor.rowcount
            self.service.db.connection.commit()
            cursor.close()
            
            self.logger.info(
                f"  ✓ Deleted {deleted_count} daily forecast records "
                f"older than {self.days_to_keep_daily} days"
            )
            
            return deleted_count
        
        except Exception as e:
            self.logger.error(f"Error cleaning daily forecasts: {e}", exc_info=True)
            return 0
    
    def _cleanup_orphaned_current(self) -> int:
        """
        Optional: Clean up orphaned marine_current records
        
        Returns:
            Number of orphaned records deleted
        
        Explanation:
        - Deletes marine_current rows for locations that no longer exist
        - Rarely needed (locations are rarely deleted)
        - Run this manually if needed
        """
        
        try:
            # Find orphaned records (location_id not in locations table)
            select_query = """
            SELECT mc.marine_current_id, mc.location_id
            FROM marine_current mc
            LEFT JOIN locations l ON mc.location_id = l.location_id
            WHERE l.location_id IS NULL
            """
            
            orphaned = self.service.db.execute_query(select_query)
            
            if not orphaned:
                self.logger.info("No orphaned marine_current records found")
                return 0
            
            orphaned_ids = [row[0] for row in orphaned]
            
            # Delete orphaned records
            placeholders = ','.join(['%s'] * len(orphaned_ids))
            delete_query = f"""
            DELETE FROM marine_current
            WHERE marine_current_id IN ({placeholders})
            """
            
            self.service.db.execute_query(delete_query, orphaned_ids)
            
            self.logger.info(f"✓ Deleted {len(orphaned_ids)} orphaned marine_current records")
            
            return len(orphaned_ids)
        
        except Exception as e:
            self.logger.error(f"Error cleaning orphaned records: {e}", exc_info=True)
            return 0


def main():
    """
    Main entry point for cleanup task
    
    Command-line arguments:
    --days-daily: Number of days to keep daily forecasts (default: 30)
    --days-hourly: Number of days to keep hourly forecasts (default: 7)
    --cleanup-orphaned: Also clean up orphaned marine_current records
    
    Examples:
        # Default cleanup (7 days hourly, 30 days daily)
        python -m src.tasks.cleanup.cleanup_marine_task
        
        # Keep 14 days of hourly data
        python -m src.tasks.cleanup.cleanup_marine_task --days-hourly 14
        
        # Keep 60 days of daily forecasts
        python -m src.tasks.cleanup.cleanup_marine_task --days-daily 60
        
        # Aggressive cleanup (3 days hourly, 14 days daily)
        python -m src.tasks.cleanup.cleanup_marine_task --days-hourly 3 --days-daily 14
    """
    
    parser = argparse.ArgumentParser(
        description='Cleanup old marine forecast data'
    )
    
    parser.add_argument(
        '--days-daily',
        type=int,
        default=30,
        help='Number of days to keep daily forecasts (default: 30)'
    )
    
    parser.add_argument(
        '--days-hourly',
        type=int,
        default=7,
        help='Number of days to keep hourly forecasts (default: 7)'
    )
    
    parser.add_argument(
        '--cleanup-orphaned',
        action='store_true',
        help='Also clean up orphaned marine_current records'
    )
    
    args = parser.parse_args()
    
    task = CleanupMarineTask(
        days_to_keep_daily=args.days_daily,
        days_to_keep_hourly=args.days_hourly
    )
    
    result = task.run()
    
    # Optional: Clean up orphaned records
    if args.cleanup_orphaned and result['success']:
        task.logger.info("\nCleaning up orphaned records...")
        orphaned_count = task._cleanup_orphaned_current()
        result['details']['orphaned_deleted'] = orphaned_count
    
    sys.exit(0 if result['success'] else 1)


if __name__ == "__main__":
    main()
    
    
    