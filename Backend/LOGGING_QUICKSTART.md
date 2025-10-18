# Quick Start: Structured Logging

## For Developers

### Setup (One-time)

1. **Update your `.env` file** (Backend/.env):
```bash
# Add these lines
DJANGO_LOG_LEVEL=DEBUG
LOG_FORMAT=text
DJANGO_FRAMEWORK_LOG_LEVEL=WARNING
```

2. **Test logging works**:
```bash
cd Backend/netops_backend
python test_logging.py
```

3. **Check log output**:
```bash
# View logs
cat ../logs/netops.log

# Watch logs in real-time
tail -f ../logs/netops.log
```

### Daily Usage

**Instead of this**:
```python
print(f"[NetworkCommandAPIView] connecting to {host}")
```

**Do this**:
```python
import logging
logger = logging.getLogger(__name__)

logger.info("Connecting to device", extra={
    'alias': alias,
    'host': host,
    'strategy': 'direct'
})
```

### Common Patterns

```python
import logging
logger = logging.getLogger(__name__)

# Success
logger.info("Device connected", extra={'alias': alias, 'host': host})

# Warning (recoverable)
logger.warning("Using fallback connection", extra={'alias': alias, 'reason': 'primary failed'})

# Error (with exception)
try:
    connect()
except Exception as e:
    logger.error("Connection failed", extra={'alias': alias, 'error': str(e)}, exc_info=True)

# Performance tracking
import time
start = time.time()
result = do_something()
duration_ms = (time.time() - start) * 1000
logger.info("Operation completed", extra={'duration_ms': duration_ms})
```

### Contextual Fields (Standard Names)

Always use these field names for consistency:

- `alias` - Device alias (INVIJB1SW1, UKLONB1SW2, etc.)
- `host` - IP address or hostname
- `query` - Natural language query
- `session_id` - Conversation session UUID
- `strategy` - Connection strategy (direct, jump_first, jump_only)
- `vendor` - Device vendor (cisco, aruba)
- `duration_ms` - Execution time in milliseconds
- `success` - Boolean success indicator
- `error` - Error message string
- `command` - CLI command executed

### Helper Functions

Use these for common operations:

```python
from chatbot.logging_utils import (
    log_device_connection,
    log_command_execution,
    log_nlp_prediction,
    log_health_alert
)

# Log connection
log_device_connection(logger, alias='INVIJB1SW1', host='192.168.10.1', 
                     strategy='direct', success=True)

# Log command
log_command_execution(logger, alias='INVIJB1SW1', command='show version',
                     duration_ms=123.4, success=True)
```

## For Operators

### View Logs

```bash
# All logs
cat Backend/logs/netops.log

# Watch real-time
tail -f Backend/logs/netops.log

# Last 100 lines
tail -n 100 Backend/logs/netops.log

# Errors only (JSON format)
cat Backend/logs/netops.log | jq 'select(.level == "ERROR")'

# Specific device
cat Backend/logs/netops.log | jq 'select(.alias == "INVIJB1SW1")'

# Slow operations (>1 second)
cat Backend/logs/netops.log | jq 'select(.duration_ms > 1000)'
```

### Troubleshooting

**No logs appearing?**
```bash
# Check log level
grep DJANGO_LOG_LEVEL Backend/.env

# Should be INFO or DEBUG, not WARNING/ERROR
# Change it:
echo "DJANGO_LOG_LEVEL=INFO" >> Backend/.env
```

**Too many logs?**
```bash
# Reduce verbosity
echo "DJANGO_LOG_LEVEL=WARNING" >> Backend/.env
```

**Need JSON for tools?**
```bash
# Switch to JSON format
echo "LOG_FORMAT=json" >> Backend/.env

# Then restart server
```

### Production Setup

```bash
# In Backend/.env
DJANGO_LOG_LEVEL=INFO
LOG_FORMAT=json
DJANGO_FRAMEWORK_LOG_LEVEL=WARNING
```

Then restart the application.

## For DevOps

### Log Rotation

Default: 10MB per file, 5 backups = 50MB total

Adjust in `settings.py` LOGGING config:
```python
'file': {
    'maxBytes': 10485760,  # 10MB
    'backupCount': 5,
}
```

### Integration with Log Aggregation

**Example: Ship to ELK**

Install Filebeat:
```bash
# filebeat.yml
filebeat.inputs:
  - type: log
    paths: ["/path/to/Backend/logs/netops.log"]
    json.keys_under_root: true

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
```

**Example: Datadog**
```bash
# /etc/datadog-agent/conf.d/netops.yaml
logs:
  - type: file
    path: /path/to/Backend/logs/netops.log
    service: netops-chatbot
    source: python
```

### Monitoring Alerts

**High error rate**:
```
Query: level:ERROR
Threshold: > 50 errors in 5 minutes
Alert: Email ops team
```

**Slow API responses**:
```
Query: duration_ms > 5000
Threshold: > 10 slow requests in 5 minutes
Alert: Slack #performance channel
```

**Device unreachable**:
```
Query: message:"Connection failed" AND alias:CRITICAL_DEVICE
Threshold: > 3 failures in 1 minute
Alert: PagerDuty
```

## Migration Checklist

- [ ] Update `.env` with logging config
- [ ] Run `test_logging.py` to verify
- [ ] Check `logs/netops.log` exists
- [ ] Start server and verify logs appear
- [ ] Test JSON format: `LOG_FORMAT=json`
- [ ] Review LOGGING.md for full documentation
- [ ] Set up log aggregation (production)
- [ ] Configure monitoring alerts

## Support

- 📖 Full docs: `Backend/LOGGING.md`
- 🧪 Test script: `Backend/netops_backend/test_logging.py`
- 📝 Summary: `Backend/LOGGING_SUMMARY.md`
- ❓ Questions: Ask the team!
