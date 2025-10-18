"""
Test script to demonstrate structured logging.
Run from Backend/netops_backend directory:
  python test_logging.py
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'netops_backend.settings')
django.setup()

import logging
from chatbot.logging_utils import log_device_connection, log_command_execution, log_nlp_prediction, log_health_alert

logger = logging.getLogger(__name__)

def test_basic_logging():
    """Test basic logging functionality."""
    print("\n=== Testing Basic Logging ===\n")
    
    logger.debug("Debug message - detailed diagnostics")
    logger.info("Info message - normal operation")
    logger.warning("Warning message - something unexpected")
    logger.error("Error message - operation failed")
    
def test_contextual_logging():
    """Test logging with context fields."""
    print("\n=== Testing Contextual Logging ===\n")
    
    logger.info("Device connection attempt", extra={
        'alias': 'INVIJB1SW1',
        'host': '192.168.10.1',
        'strategy': 'direct',
        'vendor': 'cisco'
    })
    
    logger.warning("CPU threshold exceeded", extra={
        'alias': 'UKLONB1SW2',
        'cpu_pct': 85.3,
        'threshold': 80.0,
        'consecutive_breaches': 3
    })
    
    logger.error("Connection failed", extra={
        'alias': 'INHYDB3SW3',
        'host': '192.168.50.3',
        'error': 'Connection timeout after 8.0s'
    }, exc_info=False)

def test_helper_functions():
    """Test logging helper functions."""
    print("\n=== Testing Helper Functions ===\n")
    
    log_device_connection(
        logger,
        alias='INVIJB1SW1',
        host='192.168.10.1',
        strategy='direct',
        success=True,
        duration_ms=234.5
    )
    
    log_command_execution(
        logger,
        alias='UKLONB1SW2',
        command='show interfaces GigabitEthernet0/0',
        duration_ms=456.7,
        success=True
    )
    
    log_nlp_prediction(
        logger,
        query='show all interfaces in Vijayawada',
        predicted_cli='show interfaces',
        vendor='cisco',
        provider='local',
        duration_ms=123.4
    )
    
    log_health_alert(
        logger,
        alias='INHYDB3SW3',
        category='cpu',
        severity='warn',
        message='CPU utilization 85% exceeds threshold 80%'
    )

def test_performance_logging():
    """Test performance tracking with duration_ms."""
    print("\n=== Testing Performance Logging ===\n")
    
    import time
    start = time.time()
    time.sleep(0.1)  # Simulate operation
    duration_ms = (time.time() - start) * 1000
    
    logger.info("NLP prediction completed", extra={
        'query': 'show version',
        'predicted_cli': 'show version',
        'provider': 'openai',
        'model': 'gpt-4o-mini',
        'duration_ms': duration_ms
    })

def test_error_with_exception():
    """Test logging with exception traceback."""
    print("\n=== Testing Error with Exception ===\n")
    
    try:
        raise ValueError("Simulated error for testing")
    except Exception as e:
        logger.error("Operation failed with exception", extra={
            'alias': 'TEST',
            'operation': 'test_operation',
            'error': str(e)
        }, exc_info=True)

if __name__ == '__main__':
    print("\n" + "="*60)
    print(" Structured Logging Test Suite")
    print("="*60)
    
    # Check log format
    log_format = os.getenv('LOG_FORMAT', 'json')
    print(f"\nLog Format: {log_format}")
    print(f"Log Level: {os.getenv('DJANGO_LOG_LEVEL', 'INFO')}")
    print(f"Log File: Backend/logs/netops.log")
    
    # Run tests
    test_basic_logging()
    test_contextual_logging()
    test_helper_functions()
    test_performance_logging()
    test_error_with_exception()
    
    print("\n" + "="*60)
    print(" Tests Complete!")
    print("="*60)
    print("\nCheck logs at: Backend/logs/netops.log")
    print("View JSON logs: cat Backend/logs/netops.log | jq .")
    print("View text logs: cat Backend/logs/netops.log")
    print("\n")
