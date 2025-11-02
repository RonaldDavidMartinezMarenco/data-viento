"""
Base Task Class

Provides common functionality for all scheduled tasks:
- Logging setup
- Error handling
- Execution time tracking
- Success/failure reporting

All scheduled tasks inherit from this class.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class BaseTask(ABC):
    """
    Base class for all scheduled tasks
    
    Features:
    - Automatic logging setup
    - Execution time tracking
    - Error handling and reporting
    - Consistent output format
    
    Usage:
        class MyTask(BaseTask):
            def execute(self) -> Dict[str, Any]:
                # Your task logic here
                return {'success': True}
    """
    
    def __init__(self, task_name: str, log_dir: Optional[Path] = None):
        """
        Initialize base task
        
        Args:
            task_name: Name of the task (used in logs)
            log_dir: Directory for log files (default: logs/{task_name}/)
        """
        self.task_name = task_name
        self.start_time = None
        self.end_time = None
        
        # Setup logging
        if log_dir is None:
            log_dir = Path(__file__).parent.parent.parent / "logs" / task_name
        
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create logger
        self.logger = self._setup_logger(log_dir)
    
    def _setup_logger(self, log_dir: Path) -> logging.Logger:
        """
        Setup logger with file and console handlers
        
        Args:
            log_dir: Directory for log files
        
        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(self.task_name)
        logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        logger.handlers = []
        
        # File handler (daily rotation)
        log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _print_header(self):
        """Print task execution header"""
        print("\n" + "="*70)
        print(f"  {self.task_name.upper()}")
        print(f"  Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70 + "\n")
    
    def _print_footer(self, result: Dict[str, Any]):
        """Print task execution footer"""
        duration = (self.end_time - self.start_time).total_seconds()
        
        print("\n" + "="*70)
        print(f"  TASK COMPLETED")
        print(f"  Duration: {duration:.2f} seconds")
        print(f"  Status: {'SUCCESS' if result.get('success') else 'FAILED'}")
        print("="*70 + "\n")
    
    @abstractmethod
    def execute(self) -> Dict[str, Any]:
        """
        Execute the task
        
        Must be implemented by subclasses.
        
        Returns:
            Dictionary with execution results:
            {
                'success': bool,
                'message': str,
                'details': dict,  # Optional
                'errors': list    # Optional
            }
        """
        pass
    
    def run(self) -> Dict[str, Any]:
        """
        Run the task with error handling and logging
        
        Returns:
            Dictionary with execution results
        """
        self.start_time = datetime.now()
        result = {
            'success': False,
            'message': '',
            'task_name': self.task_name,
            'start_time': self.start_time,
            'end_time': None,
            'duration_seconds': None,
        }
        
        try:
            self._print_header()
            self.logger.info(f"Starting {self.task_name}...")
            
            # Execute the task
            task_result = self.execute()
            
            # Merge results
            result.update(task_result)
            
            if result.get('success'):
                self.logger.info(f"✓ {self.task_name} completed successfully")
            else:
                self.logger.error(f"✗ {self.task_name} failed: {result.get('message')}")
        
        except Exception as e:
            self.logger.error(f"✗ {self.task_name} crashed: {e}", exc_info=True)
            result['success'] = False
            result['message'] = str(e)
            result['error'] = str(e)
        
        finally:
            self.end_time = datetime.now()
            result['end_time'] = self.end_time
            result['duration_seconds'] = (self.end_time - self.start_time).total_seconds()
            
            self._print_footer(result)
        
        return result


def run_task(task_class, *args, **kwargs):
    """
    Utility function to run a task
    
    Args:
        task_class: Task class to instantiate and run
        *args, **kwargs: Arguments to pass to task constructor
    
    Returns:
        Task execution result
    
    Example:
        >>> from src.tasks import CleanupTask, run_task
        >>> result = run_task(CleanupTask, days_to_keep=7)
    """
    task = task_class(*args, **kwargs)
    return task.run()