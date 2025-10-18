"""
Logging utility helpers for structured context logging across the chatbot module.
"""
import logging
from typing import Any, Dict, Optional

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the module."""
    return logging.getLogger(name)


def log_device_connection(logger: logging.Logger, alias: str, host: str, 
                          strategy: str, success: bool, error: Optional[str] = None,
                          **kwargs: Any) -> None:
    """Log device connection attempt with structured context."""
    extra = {
        'alias': alias,
        'host': host,
        'strategy': strategy,
        'success': success,
        **kwargs
    }
    if error:
        extra['error'] = error
    
    if success:
        logger.info(f"Device connection successful: {alias}", extra=extra)
    else:
        logger.warning(f"Device connection failed: {alias}", extra=extra)


def log_command_execution(logger: logging.Logger, alias: str, command: str,
                          duration_ms: float, success: bool, 
                          error: Optional[str] = None, **kwargs: Any) -> None:
    """Log command execution with timing and context."""
    extra = {
        'alias': alias,
        'command': command,
        'duration_ms': duration_ms,
        'success': success,
        **kwargs
    }
    if error:
        extra['error'] = error
    
    if success:
        logger.info(f"Command executed: {command[:50]}", extra=extra)
    else:
        logger.error(f"Command failed: {command[:50]}", extra=extra)


def log_nlp_prediction(logger: logging.Logger, query: str, predicted_cli: str,
                       vendor: str, provider: str, duration_ms: float,
                       **kwargs: Any) -> None:
    """Log NLP prediction with model info."""
    extra = {
        'query': query,
        'predicted_cli': predicted_cli,
        'vendor': vendor,
        'provider': provider,
        'duration_ms': duration_ms,
        **kwargs
    }
    logger.info(f"NLP prediction: {query[:50]} -> {predicted_cli}", extra=extra)


def log_health_alert(logger: logging.Logger, alias: str, category: str,
                     severity: str, message: str, **kwargs: Any) -> None:
    """Log health monitoring alert."""
    extra = {
        'alias': alias,
        'category': category,
        'severity': severity,
        'message': message,
        **kwargs
    }
    logger.warning(f"Health alert: {category} on {alias}", extra=extra)
