# 📝 Logging System

RaiseMyHand includes a centralized logging system for monitoring application health, debugging issues, and tracking security events.

---

## 🎯 Features

✅ **Environment-Aware Logging**
- Development: Console output with DEBUG/INFO level
- Production: Console + rotating file logs with WARNING level

✅ **Structured Logging Utilities**
- HTTP request logging
- Database operation logging
- WebSocket event logging
- Security event logging

✅ **Log Rotation** (Production)
- Automatic log rotation at 10MB
- Keeps last 5 log files
- Prevents disk space exhaustion

✅ **Third-Party Logger Control**
- Suppresses noisy uvicorn/SQLAlchemy logs
- Focuses on application-specific events

---

## 📂 Log Files

### Development
- **Location:** Console only (stdout)
- **Level:** DEBUG (if `DEBUG=true`) or INFO
- **Format:** `HH:MM:SS - module - LEVEL - message`

### Production
- **Location:**
  - Console (stdout) - for Docker logs
  - File: `logs/app.log`
- **Level:** WARNING (configurable via `LOG_LEVEL` env var)
- **Format:** `YYYY-MM-DD HH:MM:SS - module - LEVEL - [file:line] - message`
- **Rotation:** 10MB max, 5 backup files

---

## ⚙️ Configuration

### Environment Variables

```bash
# Set log level (overrides environment-based defaults)
LOG_LEVEL=INFO  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL

# Environment (affects default log level)
ENV=production  # Options: development, production, testing

# Debug mode (enables DEBUG level in development)
DEBUG=true  # Default: true in development
```

### Log Levels

| Level    | Development | Production | Use Case                          |
|----------|-------------|------------|-----------------------------------|
| DEBUG    | ✅ (if DEBUG=true) | ❌         | Detailed debugging info           |
| INFO     | ✅          | ❌         | General information               |
| WARNING  | ✅          | ✅         | Warnings (still functional)       |
| ERROR    | ✅          | ✅         | Errors (functionality impaired)   |
| CRITICAL | ✅          | ✅         | Critical failures                 |

---

## 🔧 Usage in Code

### Basic Logging

```python
from logging_config import get_logger

logger = get_logger(__name__)

# Standard logging
logger.debug("Detailed debugging information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred")
logger.critical("Critical failure")
```

### Structured Logging

#### HTTP Request Logging

```python
from logging_config import log_request

log_request(
    logger=logger,
    method="POST",
    endpoint="/api/sessions",
    status_code=201,
    duration_ms=45.2,
    user_id="user123"  # Optional
)
```

**Output:**
```
POST /api/sessions - 201 - 45.20ms [user=user123]
```

#### Database Operation Logging

```python
from logging_config import log_database_operation

# Success
log_database_operation(
    logger=logger,
    operation="CREATE",
    table="sessions",
    record_id=42,
    success=True
)

# Failure
log_database_operation(
    logger=logger,
    operation="UPDATE",
    table="questions",
    record_id=15,
    success=False,
    error=exception
)
```

**Output:**
```
DB CREATE: sessions [id=42]
DB UPDATE FAILED: questions [id=15]: Duplicate entry
```

#### WebSocket Event Logging

```python
from logging_config import log_websocket_event

log_websocket_event(
    logger=logger,
    event="CONNECT",
    session_code="abc123",
    details="Active connections: 5"
)
```

**Output:**
```
WS CONNECT [session=abc123]: Active connections: 5
```

#### Security Event Logging

```python
from logging_config import log_security_event

# Authentication failure
log_security_event(
    logger=logger,
    event="AUTH_FAILED",
    details="Failed login attempt for user: admin from 192.168.1.100",
    severity="warning"
)

# Rate limit exceeded
log_security_event(
    logger=logger,
    event="RATE_LIMIT",
    details="Client 10.0.0.5 exceeded rate limit on /api/sessions",
    severity="warning"
)
```

**Output:**
```
SECURITY AUTH_FAILED: Failed login attempt for user: admin from 192.168.1.100
SECURITY RATE_LIMIT: Client 10.0.0.5 exceeded rate limit on /api/sessions
```

---

## 🔍 Viewing Logs

### Local Development

Logs appear in your console:

```bash
python main.py

# Output:
17:23:45 - main - INFO - Logging initialized - Environment: development, Level: DEBUG
17:23:45 - main - INFO - Server starting on http://localhost:8000
17:23:50 - main - INFO - WS CONNECT [session=abc123]: Active connections: 1
```

### Docker Production

**View live logs:**
```bash
docker compose logs -f
```

**View specific service:**
```bash
docker compose logs -f app
```

**View last 100 lines:**
```bash
docker compose logs --tail=100 app
```

**Access log files inside container:**
```bash
docker compose exec app ls -lh logs/
docker compose exec app tail -f logs/app.log
```

**Copy logs to host:**
```bash
docker compose cp app:/app/logs ./logs_backup/
```

---

## 🎨 Advanced Features

### Temporary Log Level Changes

Use `LogLevelContext` to temporarily increase log verbosity:

```python
from logging_config import LogLevelContext
import logging

# Normal INFO level
logger.info("Regular message")

# Temporarily enable DEBUG
with LogLevelContext(logging.DEBUG):
    logger.debug("Detailed debug info")  # This will be logged
    # ... complex operation ...

# Back to INFO level
logger.debug("This won't be logged")
```

### Custom Logger Names

Create loggers for specific modules:

```python
# In websocket_manager.py
logger = get_logger("websocket_manager")

# Logs will show:
# websocket_manager - INFO - Connection established
```

---

## 🛡️ Security Event Types

The logging system tracks these security events:

| Event Type          | Description                              | Severity |
|---------------------|------------------------------------------|----------|
| AUTH_FAILED         | Failed login attempt                     | WARNING  |
| AUTH_SUCCESS        | Successful login                         | INFO     |
| AUTH_DISABLED_LOGIN | Login with auth disabled                 | WARNING  |
| INVALID_API_KEY     | Invalid or inactive API key used         | WARNING  |
| INVALID_TOKEN       | Invalid JWT token                        | WARNING  |
| RATE_LIMIT          | Rate limit exceeded                      | WARNING  |
| CSRF_FAILED         | CSRF token validation failed             | WARNING  |
| SESSION_NOT_FOUND   | Access to non-existent session           | WARNING  |

---

## 📊 Log Analysis

### Search for errors:
```bash
# Development (console)
python main.py 2>&1 | grep ERROR

# Production (log file)
docker compose exec app grep ERROR logs/app.log
```

### Count events by type:
```bash
# WebSocket connections
docker compose exec app grep "WS CONNECT" logs/app.log | wc -l

# Failed auth attempts
docker compose exec app grep "AUTH_FAILED" logs/app.log | wc -l
```

### Find specific session:
```bash
docker compose exec app grep "session=abc123" logs/app.log
```

### Recent errors:
```bash
docker compose exec app tail -100 logs/app.log | grep ERROR
```

---

## 🔧 Troubleshooting

### "Logs directory not found"

The `logs/` directory is created automatically on startup. If missing:

```bash
mkdir logs
chmod 755 logs
```

### "Permission denied" writing logs

**Local:**
```bash
chmod 755 logs
```

**Docker:**
```bash
docker compose exec app chown -R appuser:appuser logs/
```

### "Log files too large"

Log rotation should handle this automatically. If needed, manually:

```bash
# Keep last 1000 lines
docker compose exec app sh -c "tail -1000 logs/app.log > logs/app.log.tmp && mv logs/app.log.tmp logs/app.log"

# Or delete old backups
docker compose exec app rm logs/app.log.{4,5}
```

### "Too much noise in logs"

Adjust log level in production:

```bash
# In .env
LOG_LEVEL=WARNING  # Only warnings and errors
```

Or suppress specific loggers in `logging_config.py`:

```python
logging.getLogger("noisy_module").setLevel(logging.ERROR)
```

---

## 📈 Production Best Practices

1. **Monitor Disk Usage**
   - Log rotation keeps max ~50MB (5 files × 10MB)
   - Set up disk space alerts

2. **Centralized Logging** (Optional)
   - Forward logs to ELK Stack (Elasticsearch, Logstash, Kibana)
   - Use Datadog, Splunk, or CloudWatch for aggregation

3. **Log Retention**
   - Docker logs: Configure Docker log rotation
   - File logs: Automated cleanup older than 30 days

4. **Alert on Patterns**
   - Multiple AUTH_FAILED from same IP → Possible attack
   - High ERROR rate → System issues
   - RATE_LIMIT events → DDoS attempt or misconfigured client

5. **Regular Review**
   - Weekly: Review WARNING and ERROR logs
   - Monthly: Analyze trends and patterns
   - Quarterly: Audit security events

---

## 🔗 Integration Examples

### With Docker Logging

Update `docker-compose.yml`:

```yaml
services:
  app:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### With External Services

**Sentry (Error Tracking):**
```python
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

sentry_logging = LoggingIntegration(
    level=logging.INFO,
    event_level=logging.ERROR
)

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[sentry_logging]
)
```

**CloudWatch:**
```python
import watchtower

handler = watchtower.CloudWatchLogHandler(log_group="raisemyhand")
logger.addHandler(handler)
```

---

## 📚 Related Documentation

- [SECURITY.md](SECURITY.md) - Security best practices
- [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment
- [DOCKER.md](DOCKER.md) - Docker configuration

---

**Questions?** Check the main [README.md](README.md) or open an issue.
