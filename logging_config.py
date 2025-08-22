import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path



# Create logs directory if it doesn't exist
logs_dir = Path("./logs")
logs_dir.mkdir(exist_ok=True)

# Configure logging format
log_format = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Configure console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(log_format)

# Configure file handler for all logs
file_handler = logging.handlers.RotatingFileHandler(
    logs_dir / "app.log",
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(log_format)

# Configure error file handler
error_handler = logging.handlers.RotatingFileHandler(
    logs_dir / "error.log",
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(log_format)

# Configure access log handler
access_handler = logging.handlers.RotatingFileHandler(
    logs_dir / "access.log",
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
access_handler.setLevel(logging.INFO)
access_handler.setFormatter(log_format)

# Configure security log handler
security_handler = logging.handlers.RotatingFileHandler(
    logs_dir / "security.log",
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
security_handler.setLevel(logging.INFO)
security_handler.setFormatter(log_format)

# Configure payment log handler
payment_handler = logging.handlers.RotatingFileHandler(
    logs_dir / "payment.log",
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
payment_handler.setLevel(logging.INFO)
payment_handler.setFormatter(log_format)

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Setup and return a logger with the specified name and level"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers multiple times
    if not logger.handlers:
        try:
            logger.addHandler(console_handler)
            logger.addHandler(file_handler)
            logger.addHandler(error_handler)
            
            # Add specific handlers based on logger name
            if 'access' in name.lower():
                logger.addHandler(access_handler)
            if 'security' in name.lower() or 'auth' in name.lower():
                logger.addHandler(security_handler)
            if 'payment' in name.lower():
                logger.addHandler(payment_handler)
        except Exception as e:
            # Fallback to basic logging if handler setup fails
            print(f"Warning: Failed to setup logger handlers for {name}: {e}")
            basic_handler = logging.StreamHandler()
            basic_handler.setFormatter(log_format)
            logger.addHandler(basic_handler)
    
    return logger

# Create main application logger
app_logger = setup_logger("jarvistrade.app")
auth_logger = setup_logger("jarvistrade.auth")
payment_logger = setup_logger("jarvistrade.payment")
access_logger = setup_logger("jarvistrade.access")
security_logger = setup_logger("jarvistrade.security")
file_logger = setup_logger("jarvistrade.file")
user_logger = setup_logger("jarvistrade.user")
product_logger = setup_logger("jarvistrade.product")
download_logger = setup_logger("jarvistrade.download")
notification_logger = setup_logger("jarvistrade.notification")
blog_logger = setup_logger("jarvistrade.blog")
project_logger = setup_logger("jarvistrade.project")
review_logger = setup_logger("jarvistrade.review")
exchange_rate_logger = setup_logger("jarvistrade.exchange_rate")

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name"""
    return setup_logger(name)

def safe_log(logger_name: str, level: str, message: str, *args, **kwargs):
    """
    Bulletproof logging function that NEVER fails.
    This function makes it impossible to get 'name logger is not defined' errors.
    
    Args:
        logger_name: The name of the logger to use
        level: The log level ('debug', 'info', 'warning', 'error', 'critical')
        message: The message to log
        *args, **kwargs: Additional arguments for the message formatting
    """
    try:
        # Create a logger directly using the name - this NEVER fails
        logger = logging.getLogger(f"jarvistrade.{logger_name}")
        
        # Ensure the logger has at least one handler
        if not logger.handlers:
            # Add console handler if none exists
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(log_format)
            logger.addHandler(console_handler)
            logger.setLevel(logging.INFO)
        
        # Log the message at the specified level
        if level.lower() == "debug":
            logger.debug(message, *args, **kwargs)
        elif level.lower() == "info":
            logger.info(message, *args, **kwargs)
        elif level.lower() == "warning":
            logger.warning(message, *args, **kwargs)
        elif level.lower() == "error":
            logger.error(message, *args, **kwargs)
        elif level.lower() == "critical":
            logger.critical(message, *args, **kwargs)
        else:
            logger.info(message, *args, **kwargs)
            
    except Exception as e:
        # If anything goes wrong, fall back to basic logging
        try:
            basic_logger = logging.getLogger("fallback")
            if not basic_logger.handlers:
                handler = logging.StreamHandler(sys.stderr)
                handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
                basic_logger.addHandler(handler)
                basic_logger.setLevel(logging.INFO)
            
            basic_logger.error(f"Logging system error in {logger_name}.{level}: {e}")
            basic_logger.error(f"Original message: {message}")
        except:
            # Last resort - print to stderr
            print(f"CRITICAL LOGGING FAILURE: {logger_name}.{level}: {message}", file=sys.stderr)
            print(f"Error: {e}", file=sys.stderr)



# Set environment-specific log levels
if os.getenv("ENVIRONMENT") == "development":
    app_logger.setLevel(logging.DEBUG)
    console_handler.setLevel(logging.DEBUG)
elif os.getenv("ENVIRONMENT") == "production":
    app_logger.setLevel(logging.INFO)
    console_handler.setLevel(logging.WARNING)
