# logging_config.py

import os
import logging
from logging.handlers import RotatingFileHandler
from django.conf import settings

class DatabaseLogHandler(logging.Handler):
    """
    Custom log handler that saves log entries to the database
    """
    def __init__(self, task_id):
        super().__init__()
        self.task_id = task_id
    
    def emit(self, record):
        from automation.models import TaskLog
        
        try:
            message = self.format(record)
            TaskLog.objects.create(
                task_id=self.task_id,
                level=record.levelname,
                message=message,
                timestamp=record.created
            )
        except Exception:
            # Don't let logging errors interrupt the flow
            pass

def configure_logging():
    """
    Configure logging for the application with both file and database handlers
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(settings.BASE_DIR, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid duplicates
    if root_logger.handlers:
        root_logger.handlers = []
    
    # Console handler for development
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    
    # File handler for all logs
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=10
    )
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    
    # Error file handler for error logs only
    error_handler = RotatingFileHandler(
        os.path.join(log_dir, 'error.log'),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=10
    )
    error_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s\n%(pathname)s:%(lineno)d\n%(message)s')
    error_handler.setFormatter(error_formatter)
    error_handler.setLevel(logging.ERROR)
    root_logger.addHandler(error_handler)
    
    # Set specific loggers to appropriate levels
    logging.getLogger('automation.tasks').setLevel(logging.DEBUG)
    logging.getLogger('celery').setLevel(logging.INFO)
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.getLogger('s3transfer').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    # Return the configured root logger
    return root_logger

# Initialize logger - to be called in your Django app's AppConfig.ready() method
logger = configure_logging()
