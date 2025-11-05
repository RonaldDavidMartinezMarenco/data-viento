"""
Cleanup Air Quality Task

Removes old air quality forecast data to keep database size manageable.

Schedule:
    Run daily at 2 AM:
    0 2 * * * cd /home/ronald/data-viento/apps/server && python -m src.tasks.cleanup_air_quality_task

Usage:
    python -m src.tasks.cleanup_air_quality_task
    python -m src.tasks.cleanup_air_quality_task --days 14
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import argparse
from typing import Dict, Any
from src.tasks.base_task import BaseTask
from src.services.air_quality_service import AirQualityService


class CleanupAirQualityTask(BaseTask):
    """Cleanup old air quality forecasts"""
    
    def __init__(self, days_to_keep: int = 7):
        """
        Initialize cleanup task
        
        Args:
            days_to_keep: Number of days to keep (default: 7)
        """
        super().__init__(task_name="cleanup_air_quality_task")
        self.days_to_keep = days_to_keep
        self.service = AirQualityService()
    
    def execute(self) -> Dict[str, Any]:
        """Execute cleanup"""
        
        result = {
            'success': False,
            'message': '',
            'details': {
                'forecasts_deleted': 0,
                'data_points_deleted': 0
            }
        }
        
        try:
            self.logger.info(f"Cleaning up air quality data older than {self.days_to_keep} days")
            
            # Delete old forecasts (cascade deletes air_quality_data)
            forecasts_deleted = self.service.cleanup_old_forecasts(self.days_to_keep)
            result['details']['forecasts_deleted'] = forecasts_deleted
            
            result['success'] = True
            result['message'] = f"Deleted {forecasts_deleted} old forecast batches"
            
            self.logger.info(f"✓ Cleanup completed: {forecasts_deleted} batches deleted")
        
        except Exception as e:
            result['success'] = False
            result['message'] = f"Cleanup failed: {e}"
            self.logger.error(f"Cleanup error: {e}", exc_info=True)
        
        finally:
            self.service.db.disconnect()
        
        return result


def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(
        description='Cleanup old air quality forecast data'
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Number of days to keep (default: 7)'
    )
    
    args = parser.parse_args()
    
    task = CleanupAirQualityTask(days_to_keep=args.days)
    result = task.run()
    
    sys.exit(0 if result['success'] else 1)


if __name__ == "__main__":
    main()