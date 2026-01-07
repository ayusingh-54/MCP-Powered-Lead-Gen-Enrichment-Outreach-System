"""
Logging Configuration
=====================
Centralized logging setup for the lead generation system.
Provides structured logging with consistent formatting across all modules.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import json


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs.
    Ideal for production environments and log aggregation.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_data["data"] = record.extra_data
        
        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """
    Colored formatter for console output.
    Makes logs easier to read during development.
    """
    
    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        color = self.COLORS.get(record.levelname, self.RESET)
        
        # Format timestamp
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        
        # Build formatted message
        formatted = (
            f"{color}[{timestamp}] "
            f"{record.levelname:8s}{self.RESET} "
            f"[{record.name}] "
            f"{record.getMessage()}"
        )
        
        # Add exception info if present
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"
        
        return formatted


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    structured: bool = False
) -> logging.Logger:
    """
    Set up logging configuration for the application.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        structured: Use structured JSON logging
        
    Returns:
        Configured root logger
    """
    # Get root logger
    logger = logging.getLogger("leadgen")
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    
    if structured:
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(ColoredFormatter())
    
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        # Ensure log directory exists
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(StructuredFormatter())  # Always structured for files
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f"leadgen.{name}")


# =============================================================================
# LOG HELPERS
# =============================================================================

def log_tool_call(logger: logging.Logger, tool_name: str, params: dict):
    """Log an MCP tool call with parameters."""
    logger.info(f"MCP Tool Call: {tool_name}", extra={"extra_data": params})


def log_tool_result(logger: logging.Logger, tool_name: str, success: bool, result: dict):
    """Log an MCP tool result."""
    level = logging.INFO if success else logging.ERROR
    logger.log(level, f"MCP Tool Result: {tool_name} - {'SUCCESS' if success else 'FAILED'}", 
               extra={"extra_data": result})


def log_pipeline_step(logger: logging.Logger, step: str, leads_processed: int, errors: int = 0):
    """Log a pipeline step completion."""
    logger.info(f"Pipeline Step: {step} - Processed: {leads_processed}, Errors: {errors}")
