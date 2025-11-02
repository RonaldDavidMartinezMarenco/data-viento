"""
Scheduled Tasks Module

Contains all periodic/scheduled jobs:
- Cleanup tasks (delete old data)
- Update tasks (fetch new data)
- Maintenance tasks (optimize database)

All tasks inherit from BaseTask for consistent logging and error handling.
"""
