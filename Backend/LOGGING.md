# Structured Logging Guide

## Overview

The backend now uses structured JSON logging for better observability, debugging, and integration with log aggregation systems (ELK, Datadog, Splunk, etc.).

## Configuration

### Environment Variables

```bash
# Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
DJANGO_LOG_LEVEL=INFO

# Log format (json or text)
LOG_FORMAT=json

# Django framework logging level (separate from app logging)
DJANGO_FRAMEWORK_LOG_LEVEL=WARNING
```

### Log Output

**Development (text format)**:
```bash
LOG_FORMAT=text
```
Output:
```
2025-10-18 10:30:45 [INFO] chatbot.views NetworkCommandAPIView.post:330 - Network command request
```

**Production (JSON format)**:
```bash
LOG_FORMAT=json
```
Output:
```json
{
  "timestamp": "2025-10-18T10:30:45.123456Z",
  "level": "INFO",
  "logger": "chatbot.views",
  "message": "Network command request",
  "module": "views",
  "function": "post",
  "line": 330,
  "query": "show interfaces",
  "session_id": "abc-123",
  "alias": "INVIJB1SW1",
  "host": "192.168.10.1",
  "resolution_method": "direct_alias"
}
```

## Log Locations

- **Console**: stdout (all logs)
- **File**: `Backend/logs/netops.log` (rotating, max 10MB, 5 backups)

## Contextual Fields

Logs automatically include relevant context:

### Device Operations
- `alias`: Device alias (e.g., INVIJB1SW1)
- `host`: IP address or hostname
- `strategy`: Connection strategy (direct, jump_first, jump_only)
- `vendor`: Device vendor (cisco, aruba)

### Command Execution
- `query`: Natural language query
- `predicted_cli`: Generated CLI command
- `duration_ms`: Execution time in milliseconds
- `success`: Boolean success indicator
- `error`: Error message (if failed)

### Health Monitoring
- `cpu_pct`: CPU percentage
- `threshold`: Alert threshold
- `consecutive_breaches`: Number of consecutive threshold breaches
- `loop_path`: Network loop path (if detected)

### Session Tracking
- `session_id`: Conversation session UUID
- `resolution_method`: How device was resolved (direct_alias, phrase, fuzzy, etc.)

## Using Structured Logging in Code

### Basic Logging

```python
import logging

logger = logging.getLogger(__name__)

# Simple message
logger.info("Device connected")

# With context
logger.info("Device connected", extra={
    'alias': 'INVIJB1SW1',
    'host': '192.168.10.1',
    'duration_ms': 234.5
})
```

### Helper Functions

Use the logging utilities in `chatbot/logging_utils.py`:

```python
from chatbot.logging_utils import log_device_connection, log_command_execution

# Log connection attempt
log_device_connection(
    logger, 
    alias='INVIJB1SW1', 
    host='192.168.10.1',
    strategy='direct',
    success=True
)

# Log command execution
log_command_execution(
    logger,
    alias='INVIJB1SW1',
    command='show interfaces',
    duration_ms=123.4,
    success=True
)
```

## Log Levels

- **DEBUG**: Detailed diagnostic information (connection attempts, retries)
- **INFO**: General operational messages (successful connections, commands)
- **WARNING**: Non-critical issues (retries, fallbacks, alerts raised)
- **ERROR**: Errors that don't stop execution (connection failures, parse errors)
- **CRITICAL**: System-level failures

## Production Integration

### ELK Stack

```python
# Filebeat config (filebeat.yml)
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /path/to/Backend/logs/netops.log
    json.keys_under_root: true
    json.add_error_key: true

output.elasticsearch:
  hosts: ["localhost:9200"]
  index: "netops-logs-%{+yyyy.MM.dd}"
```

### Datadog

```bash
# Install Datadog agent and configure
DD_API_KEY=<your-key> DD_SITE="datadoghq.com" \
  bash -c "$(curl -L https://s3.amazonaws.com/dd-agent/scripts/install_script.sh)"

# Configure log collection (datadog.yaml)
logs_enabled: true

# Create log config (/etc/datadog-agent/conf.d/netops.d/conf.yaml)
logs:
  - type: file
    path: /path/to/Backend/logs/netops.log
    service: netops-chatbot
    source: python
    sourcecategory: django
```

### Splunk

```bash
# Install Splunk Universal Forwarder
# Configure inputs.conf
[monitor:///path/to/Backend/logs/netops.log]
sourcetype = json
index = netops
```

## Querying Logs

### Find all failed commands
```bash
# grep
grep '"success": false' logs/netops.log

# jq
cat logs/netops.log | jq 'select(.success == false)'
```

### Find CPU alerts
```bash
cat logs/netops.log | jq 'select(.category == "cpu" and .level == "WARNING")'
```

### Find slow operations (>1s)
```bash
cat logs/netops.log | jq 'select(.duration_ms > 1000)'
```

### Group errors by alias
```bash
cat logs/netops.log | jq -r 'select(.level == "ERROR") | .alias' | sort | uniq -c
```

## Monitoring Alerts

### Example: High Error Rate

**Datadog Monitor**:
```
sum(last_5m):sum:netops.logs{level:error}.as_count() > 50
```

**ELK Watcher**:
```json
{
  "trigger": {
    "schedule": { "interval": "5m" }
  },
  "input": {
    "search": {
      "request": {
        "indices": ["netops-logs-*"],
        "body": {
          "query": {
            "bool": {
              "filter": [
                { "term": { "level": "ERROR" } },
                { "range": { "timestamp": { "gte": "now-5m" } } }
              ]
            }
          }
        }
      }
    }
  },
  "condition": {
    "compare": { "ctx.payload.hits.total": { "gt": 50 } }
  },
  "actions": {
    "email_admin": {
      "email": {
        "to": "ops@example.com",
        "subject": "High Error Rate Detected"
      }
    }
  }
}
```

## Performance Considerations

- **Production**: Use `LOG_FORMAT=json` and `DJANGO_LOG_LEVEL=INFO`
- **Development**: Use `LOG_FORMAT=text` and `DJANGO_LOG_LEVEL=DEBUG`
- **High volume**: Set `DJANGO_LOG_LEVEL=WARNING` to reduce I/O
- **File rotation**: Default 10MB × 5 files = 50MB max disk usage

## Best Practices

1. **Always include context**: Use `extra={}` parameter with relevant fields
2. **Use appropriate levels**: INFO for success, WARNING for recoverable issues, ERROR for failures
3. **Don't log sensitive data**: Passwords, tokens, full command outputs
4. **Use consistent field names**: `alias`, `host`, `duration_ms`, etc.
5. **Log at decision points**: Connection strategy, fallback attempts, alert raises/clears
6. **Include timing**: Add `duration_ms` for performance tracking

## Troubleshooting

### No logs appearing
- Check `logs/` directory exists (created automatically)
- Verify `DJANGO_LOG_LEVEL` is not too high
- Ensure logger name matches module (`logger = logging.getLogger(__name__)`)

### JSON parsing errors
- Validate with `cat logs/netops.log | jq .`
- Check for newlines in message strings
- Verify formatter is set correctly in settings.py

### Too many logs
- Increase `DJANGO_LOG_LEVEL` to WARNING or ERROR
- Filter Django framework logs separately (`DJANGO_FRAMEWORK_LOG_LEVEL=ERROR`)
- Adjust file rotation settings (maxBytes, backupCount)

## Examples

See `chatbot/logging_utils.py` for reusable logging helpers and `chatbot/views.py` for real-world usage examples.
