"""
Cleanup Satellite Radiation Task

Removes old satellite radiation data to keep database size manageable.

Performs:
1. Delete satellite_radiation_daily records older than X days
2. Log cleanup statistics

Schedule:
    Run weekly on Sunday at 4 AM:
    0 4 * * 0 cd /home/ronald/data-viento/apps/server && python -m src.tasks.cleanup.cleanup_satellite_task

Usage:
    python -m src.tasks.cleanup.cleanup_satellite_task
    python -m src.tasks.cleanup.cleanup_satellite_task --days 365
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import argparse
from typing import Dict, Any
from src.tasks.base_task import BaseTask
from src.services.satellite_service import SatelliteService


class CleanupSatelliteTask(BaseTask):
    """
    Cleanup old satellite radiation data
    
    Workflow:
    1. Delete satellite_radiation_daily records older than X days
    2. Log cleanup statistics
    
    Database Impact:
    - satellite_radiation_daily: Daily aggregated radiation data
    
    Retention Policy:
    - Default: Keep 180 days (6 months) of satellite data
    - Configurable via --days argument
    - Satellite data is historical (not forecast), so longer retention recommended
    
    Note:
    - Satellite data is smaller than hourly forecast data
    - Daily aggregates (not hourly) → lighter storage
    - Consider keeping 1-2 years for trend analysis
    """
    
    def __init__(self, days_to_keep: int = 180):
        """
        Initialize cleanup task
        
        Args:
            days_to_keep: Number of days to keep (default: 180 = 6 months)
        
        Explanation:
        - 180 days (6 months): Good for seasonal analysis
        - 365 days (1 year): Good for year-over-year comparison
        - 730 days (2 years): Good for long-term trends
        """
        super().__init__(task_name="cleanup_satellite_task")
        self.days_to_keep = days_to_keep
        self.service = SatelliteService()
    
    def execute(self) -> Dict[str, Any]:
        """
        Execute cleanup
        
        Returns:
            Dictionary with cleanup results
        
        Example Result:
            {
                'success': True,
                'message': 'Deleted 150 satellite radiation records',
                'details': {
                    'records_deleted': 150,
                    'days_kept': 180,
                    'oldest_remaining_date': '2024-05-07'
                }
            }
        """
        result = {
            'success': False,
            'message': '',
            'details': {
                'records_deleted': 0,
                'days_kept': self.days_to_keep,
                'oldest_remaining_date': None
            }
        }
        
        try:
            self.logger.info(
                f"Starting satellite radiation data cleanup "
                f"(keeping last {self.days_to_keep} days)..."
            )
            
            # Delete old records
            deleted_count = self._cleanup_old_radiation_data()
            result['details']['records_deleted'] = deleted_count
            
            # Get oldest remaining date
            oldest_date = self._get_oldest_remaining_date()
            result['details']['oldest_remaining_date'] = oldest_date
            
            # Success message
            result['success'] = True
            result['message'] = (
                f"Deleted {deleted_count} satellite radiation records "
                f"(keeping {self.days_to_keep} days)"
            )
            
            self.logger.info(f"✓ Cleanup completed successfully")
            self.logger.info(f"  Records deleted: {deleted_count}")
            self.logger.info(f"  Oldest remaining: {oldest_date}")
        
        except Exception as e:
            result['success'] = False
            result['message'] = f"Cleanup failed: {e}"
            self.logger.error(f"Cleanup error: {e}", exc_info=True)
        
        finally:
            self.service.db.disconnect()
        
        return result
    
    def _cleanup_old_radiation_data(self) -> int:
        """
        Delete old satellite radiation records
        
        Returns:
            Number of records deleted
        
        Explanation:
        - Deletes satellite_radiation_daily rows older than X days
        - Uses valid_date column for date comparison
        - No cascade deletes (standalone table)
        
        SQL Flow:
        1. COUNT records to be deleted
        2. DELETE FROM satellite_radiation_daily WHERE old
        3. Return rowcount
        """
        
        try:
            # Step 1: Count records to delete
            count_query = """
            SELECT COUNT(*) FROM satellite_radiation_daily
            WHERE valid_date < DATE_SUB(CURDATE(), INTERVAL %s DAY)
            """
            
            count_result = self.service.db.execute_query(
                count_query,
                (self.days_to_keep,)
            )
            count = count_result[0][0] if count_result else 0
            
            if count == 0:
                self.logger.info(
                    f"No satellite radiation records older than {self.days_to_keep} days to delete"
                )
                return 0
            
            self.logger.info(f"Found {count} records to delete...")
            
            # Step 2: Delete old records
            delete_query = """
            DELETE FROM satellite_radiation_daily
            WHERE valid_date < DATE_SUB(CURDATE(), INTERVAL %s DAY)
            """
            
            cursor = self.service.db.connection.cursor()
            cursor.execute(delete_query, (self.days_to_keep,))
            deleted_count = cursor.rowcount
            self.service.db.connection.commit()
            cursor.close()
            
            self.logger.info(
                f"✓ Deleted {deleted_count} satellite radiation records "
                f"older than {self.days_to_keep} days"
            )
            
            return deleted_count
        
        except Exception as e:
            self.logger.error(f"Error cleaning satellite data: {e}", exc_info=True)
            return 0
    
    def _get_oldest_remaining_date(self) -> str:
        """
        Get the oldest remaining date in satellite_radiation_daily
        
        Returns:
            Oldest date (YYYY-MM-DD) or None
        
        Explanation:
        - Used for verification after cleanup
        - Helps confirm correct retention period
        """
        
        try:
            query = """
            SELECT MIN(valid_date) as oldest_date
            FROM satellite_radiation_daily
            """
            
            result = self.service.db.execute_query(query)
            
            if result and result[0][0]:
                return str(result[0][0])
            
            return None
        
        except Exception as e:
            self.logger.error(f"Error getting oldest date: {e}", exc_info=True)
            return None
    
    def _get_cleanup_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about current satellite data
        
        Returns:
            Dictionary with statistics
        
        Example Output:
            {
                'total_records': 500,
                'total_locations': 5,
                'oldest_date': '2024-01-01',
                'newest_date': '2024-11-04',
                'days_covered': 308,
                'avg_records_per_location': 100
            }
        """
        
        try:
            query = """
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT location_id) as total_locations,
                MIN(valid_date) as oldest_date,
                MAX(valid_date) as newest_date,
                DATEDIFF(MAX(valid_date), MIN(valid_date)) as days_covered
            FROM satellite_radiation_daily
            """
            
            result = self.service.db.execute_query(query)
            
            if not result:
                return {}
            
            row = result[0]
            total_records = row[0]
            total_locations = row[1]
            
            return {
                'total_records': total_records,
                'total_locations': total_locations,
                'oldest_date': str(row[2]) if row[2] else None,
                'newest_date': str(row[3]) if row[3] else None,
                'days_covered': row[4] if row[4] else 0,
                'avg_records_per_location': round(total_records / total_locations, 1) if total_locations > 0 else 0
            }
        
        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}", exc_info=True)
            return {}


def main():
    """
    Main entry point for cleanup task
    
    Command-line arguments:
    --days: Number of days to keep (default: 180 = 6 months)
    --stats: Show statistics without deleting
    
    Examples:
        # Default cleanup (keep 180 days)
        python -m src.tasks.cleanup.cleanup_satellite_task
        
        # Keep 1 year of data
        python -m src.tasks.cleanup.cleanup_satellite_task --days 365
        
        # Keep 2 years of data
        python -m src.tasks.cleanup.cleanup_satellite_task --days 730
        
        # Aggressive cleanup (keep 90 days)
        python -m src.tasks.cleanup.cleanup_satellite_task --days 90
        
        # Show statistics only
        python -m src.tasks.cleanup.cleanup_satellite_task --stats
    """
    
    parser = argparse.ArgumentParser(
        description='Cleanup old satellite radiation data'
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=180,
        help='Number of days to keep (default: 180 = 6 months)'
    )
    
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show statistics without deleting'
    )
    
    args = parser.parse_args()
    
    task = CleanupSatelliteTask(days_to_keep=args.days)
    
    # If --stats, show statistics and exit
    if args.stats:
        stats = task._get_cleanup_statistics()
        
        print("\n" + "="*70)
        print("  SATELLITE RADIATION DATA STATISTICS")
        print("="*70)
        print(f"Total records:           {stats.get('total_records', 0):,}")
        print(f"Total locations:         {stats.get('total_locations', 0)}")
        print(f"Oldest date:             {stats.get('oldest_date', 'N/A')}")
        print(f"Newest date:             {stats.get('newest_date', 'N/A')}")
        print(f"Days covered:            {stats.get('days_covered', 0)}")
        print(f"Avg records/location:    {stats.get('avg_records_per_location', 0)}")
        print("="*70 + "\n")
        
        sys.exit(0)
    
    result = task.run()
    
    sys.exit(0 if result['success'] else 1)


if __name__ == "__main__":
    main()