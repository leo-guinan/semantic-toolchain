"""Logging utilities for the semantic toolchain."""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from rich.logging import RichHandler
from rich.console import Console
from rich.theme import Theme

# Custom theme for rich console
CUSTOM_THEME = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red",
    "success": "green",
    "debug": "dim",
})

def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    use_rich: bool = True,
    format_string: Optional[str] = None
) -> logging.Logger:
    """Setup logging configuration."""
    
    # Create logger
    logger = logging.getLogger("stc")
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    formatter = logging.Formatter(format_string)
    
    # Console handler
    if use_rich:
        console = Console(theme=CUSTOM_THEME)
        console_handler = RichHandler(
            console=console,
            show_time=True,
            show_path=False,
            markup=True,
            rich_tracebacks=True
        )
        console_handler.setLevel(getattr(logging, level.upper()))
        logger.addHandler(console_handler)
    else:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(getattr(logging, level.upper()))
        logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(getattr(logging, level.upper()))
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str = "stc") -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)

class LoggerMixin:
    """Mixin to add logging capabilities to classes."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = get_logger(self.__class__.__name__)
    
    def log_info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message, **kwargs)
    
    def log_warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message, **kwargs)
    
    def log_error(self, message: str, **kwargs):
        """Log error message."""
        self.logger.error(message, **kwargs)
    
    def log_debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, **kwargs)
    
    def log_success(self, message: str, **kwargs):
        """Log success message."""
        self.logger.info(f"[green]✓ {message}[/green]", **kwargs)

class ProgressLogger:
    """Logger for progress tracking."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or get_logger("progress")
        self.step_count = 0
        self.total_steps = 0
    
    def start_progress(self, total_steps: int, description: str = "Processing"):
        """Start a progress sequence."""
        self.total_steps = total_steps
        self.step_count = 0
        self.logger.info(f"Starting {description}: {total_steps} steps")
    
    def step(self, description: str = ""):
        """Increment progress step."""
        self.step_count += 1
        if description:
            self.logger.info(f"Step {self.step_count}/{self.total_steps}: {description}")
        else:
            self.logger.info(f"Step {self.step_count}/{self.total_steps}")
    
    def finish(self, description: str = "Completed"):
        """Finish progress sequence."""
        self.logger.info(f"{description}: {self.step_count}/{self.total_steps} steps completed")

class StructuredLogger:
    """Logger for structured data."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or get_logger("structured")
    
    def log_event(self, event_type: str, data: Dict[str, Any], level: str = "info"):
        """Log a structured event."""
        log_data = {
            "event_type": event_type,
            "data": data,
            "timestamp": None  # Will be added by formatter
        }
        
        log_method = getattr(self.logger, level.lower())
        log_method(f"EVENT: {event_type} - {data}")
    
    def log_metric(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Log a metric."""
        metric_data = {
            "metric": metric_name,
            "value": value,
            "tags": tags or {}
        }
        self.logger.info(f"METRIC: {metric_name}={value} {tags or ''}")
    
    def log_error_with_context(self, error: Exception, context: Dict[str, Any]):
        """Log an error with context."""
        error_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context
        }
        self.logger.error(f"ERROR: {error_data}")

def log_function_call(func):
    """Decorator to log function calls."""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} returned {result}")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} raised {type(e).__name__}: {e}")
            raise
    return wrapper

def log_execution_time(func):
    """Decorator to log function execution time."""
    import time
    
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.2f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.2f}s: {e}")
            raise
    return wrapper

class LogCapture:
    """Context manager to capture log messages."""
    
    def __init__(self, logger_name: str = "stc"):
        self.logger_name = logger_name
        self.logger = get_logger(logger_name)
        self.handler = None
        self.messages = []
    
    def __enter__(self):
        self.handler = CapturingHandler()
        self.logger.addHandler(self.handler)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.handler:
            self.logger.removeHandler(self.handler)
            self.messages = self.handler.messages
    
    def get_messages(self, level: Optional[str] = None) -> list:
        """Get captured messages, optionally filtered by level."""
        if level is None:
            return self.messages
        return [msg for msg in self.messages if msg['level'] == level.upper()]

class CapturingHandler(logging.Handler):
    """Handler that captures log messages."""
    
    def __init__(self):
        super().__init__()
        self.messages = []
    
    def emit(self, record):
        self.messages.append({
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        })

def configure_logging_for_tests():
    """Configure logging for test environments."""
    return setup_logging(
        level="DEBUG",
        use_rich=False,
        format_string="%(levelname)s - %(name)s - %(message)s"
    ) 