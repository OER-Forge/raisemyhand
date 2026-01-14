# 🚀 RaiseMyHand Production Deployment Guide

This guide walks you through deploying RaiseMyHand to production with PostgreSQL on Docker.

## Quick Start (5 minutes)

### Step 1: Generate Production Configuration

```bash
python scripts/setup_production.py
```

This interactive script will:
- Generate secure random secrets
- Prompt for critical passwords and configuration
- Create `.env.production` with proper permissions (600)

You'll need to provide:
- **PostgreSQL Password**: Strong password (16+ characters)
- **Base URL**: Your actual domain (e.g., `https://questions.yourschool.edu`)
- **Admin Password**: Strong password (12+ characters)

### Step 2: Start Production Environment

```bash
docker compose -f docker-compose.prod.yml up -d
```

Wait for the app to initialize (20-30 seconds):
```bash
docker logs -f raisemyhand-app
```

You should see:
```
✨ Ready for production deployment!
🌐 Starting server with 4 workers...
```

### Step 3: Verify Deployment

```bash
# Check application health
curl http://localhost:8000/api/system/status

# Check PostgreSQL connection
docker compose -f docker-compose.prod.yml exec postgres psql -U raisemyhand -d raisemyhand -c "\dt"
```

Done! Your application is now running on PostgreSQL.

---

## Full Deployment Checklist

### Pre-Deployment (Server Setup)

- [ ] Server has Docker and Docker Compose installed
- [ ] Sufficient disk space (20GB+ recommended)
- [ ] Firewall configured:
  - [ ] Port 80/443 open (HTTP/HTTPS for users)
  - [ ] Port 8000 blocked from external access (Docker only)
  - [ ] Port 5432 blocked from external access (internal only)
- [ ] SSL/TLS certificates ready (for nginx reverse proxy)
- [ ] Automated backup solution configured

### Configuration Setup

- [ ] Run `python scripts/setup_production.py`
- [ ] Verify `.env.production` created with:
  - [ ] `ENV=production`
  - [ ] `POSTGRES_PASSWORD` set to strong value
  - [ ] `SECRET_KEY` is 32+ random characters
  - [ ] `CSRF_SECRET` is 32+ random characters
  - [ ] `ADMIN_PASSWORD` set to strong value
  - [ ] `BASE_URL` points to your actual domain
  - [ ] `DEBUG=false`
  - [ ] `DEMO_MODE=false`
- [ ] Verify `.env.production` permissions are 600: `ls -l .env.production`
- [ ] Verify `.env.production` is in `.gitignore`

### Deployment

- [ ] Start production environment: `docker compose -f docker-compose.prod.yml up -d`
- [ ] Monitor startup: `docker logs -f raisemyhand-app`
- [ ] Wait for all services to be healthy (~30 seconds)
- [ ] Verify API is responding: `curl http://localhost:8000/api/system/status`
- [ ] Verify PostgreSQL connection: `docker compose exec postgres psql -U raisemyhand -d raisemyhand -c "\dt"`

### Post-Deployment

- [ ] Test login with admin credentials
- [ ] Create test class and meeting
- [ ] Test question submission and voting
- [ ] Configure nginx reverse proxy with SSL
- [ ] Set up database backups
- [ ] Configure monitoring/alerting
- [ ] Set up log aggregation
- [ ] Document server setup in team wiki

---

## Pre-Deployment Load Testing

Before deploying to production, verify the system can handle your expected load.

### Quick Load Test

1. **Setup test data:**
   ```bash
   python tests/load/setup_load_test.py
   ```

2. **Run load test (100 users for 2 minutes):**
   ```bash
   pip install -r tests/load/requirements.txt
   locust -f tests/load/locustfile.py \
     --users=100 \
     --spawn-rate=5 \
     --run-time=2m \
     --headless
   ```

3. **Verify performance targets:**
   - Success rate > 95%
   - Avg response time < 1500ms
   - Database CPU < 80%

### Production-Scale Load Test

Before going live with 200+ concurrent students:

```bash
# 1. Setup test data
python tests/load/setup_load_test.py

# 2. Run 5-minute load test at expected peak load
locust -f tests/load/locustfile.py \
  --users=200 \
  --spawn-rate=10 \
  --run-time=5m \
  --headless

# 3. Monitor during test
# In another terminal:
docker stats raisemyhand-app raisemyhand-postgres
```

### Expected Performance (200 concurrent users)

RaiseMyHand is verified to support:

| Metric | Result |
|--------|--------|
| **Success Rate** | 99.92% ✅ |
| **Avg Response Time** | 932ms ✅ |
| **Throughput** | 45 req/sec ✅ |
| **95th Percentile** | 1840ms ✅ |
| **Error Rate** | 0.08% ✅ |

**Database Configuration:**
- PostgreSQL 16 with tuning (see docker-compose.prod.yml)
- Connection pool: 20 persistent + 10 overflow
- Max connections: 100

**Application Configuration:**
- 4 Uvicorn workers
- Rate limits: 500/min for questions/votes/stats

See [Load Testing Guide](LOAD_TESTING.md) for detailed methodology, performance analysis, and troubleshooting.

---

## Architecture

```
┌─────────────────┐
│   HTTPS User    │
└────────┬────────┘
         │
    ┌────▼─────────────────┐
    │  nginx Reverse Proxy  │  Port 443 (SSL/TLS)
    │  (Recommended)        │
    └────┬─────────────────┘
         │
    ┌────▼──────────────────┐
    │  RaiseMyHand App      │  Port 8000
    │  4 uvicorn workers    │  Container: raisemyhand-app
    │  (FastAPI)            │
    └────┬──────────────────┘
         │
    ┌────▼──────────────────┐
    │  PostgreSQL 16        │  Port 5432 (internal only)
    │  150+ concurrent      │  Container: raisemyhand-postgres
    │  users supported      │  Volume: postgres-data
    └───────────────────────┘
```

---

## Environment Variables

### Required (will block startup if missing/invalid)

| Variable | Purpose | Example |
|----------|---------|---------|
| `ENV` | Environment type | `production` |
| `POSTGRES_USER` | Database user | `raisemyhand` |
| `POSTGRES_PASSWORD` | Database password | Generated by setup script |
| `POSTGRES_DB` | Database name | `raisemyhand` |
| `BASE_URL` | Public URL for app | `https://questions.yourschool.edu` |
| `SECRET_KEY` | JWT signing key (32+ chars) | Generated by setup script |
| `CSRF_SECRET` | CSRF token key (32+ chars) | Generated by setup script |
| `ADMIN_PASSWORD` | Admin panel password | Generated by setup script |

### Important Settings

| Variable | Purpose | Default | Production Value |
|----------|---------|---------|---|
| `DEBUG` | Debug mode | `true` | **`false`** |
| `DEMO_MODE` | Demo mode | `false` | **`false`** |
| `ENABLE_AUTH` | Authentication required | `true` | `true` |
| `RATE_LIMIT_ENABLED` | Rate limiting | `true` | `true` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Session timeout | `480` (8h) | `480` |

### Optional

| Variable | Purpose | Default |
|----------|---------|---------|
| `TIMEZONE` | App timezone | `UTC` |
| `PGADMIN_EMAIL` | PgAdmin user | `admin@example.com` |
| `PGADMIN_PASSWORD` | PgAdmin password | `admin` |

---

## Production Deployment with Nginx

### 1. Install Nginx

```bash
sudo apt update
sudo apt install nginx
```

### 2. Create SSL Certificates

For Let's Encrypt (recommended):
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d questions.yourschool.edu
```

### 3. Configure Nginx Reverse Proxy

Create `/etc/nginx/sites-available/raisemyhand`:

```nginx
upstream raisemyhand {
    server localhost:8000;
}

server {
    listen 80;
    server_name questions.yourschool.edu;
    return 301 https://$server_name$request_uri;  # Redirect to HTTPS
}

server {
    listen 443 ssl http2;
    server_name questions.yourschool.edu;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/questions.yourschool.edu/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/questions.yourschool.edu/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy Configuration
    location / {
        proxy_pass http://raisemyhand;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/raisemyhand /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Database Backups

### Automated Daily Backups

Create `/home/ubuntu/backup_raisemyhand.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/backups/raisemyhand"
BACKUP_DATE=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_FILE="$BACKUP_DIR/raisemyhand_$BACKUP_DATE.sql"

mkdir -p "$BACKUP_DIR"

# Create backup
docker compose -f /path/to/docker-compose.prod.yml exec -T postgres \
    pg_dump -U raisemyhand -d raisemyhand > "$BACKUP_FILE"

# Compress backup
gzip "$BACKUP_FILE"

# Keep only last 30 days
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +30 -delete

echo "✅ Backup created: $BACKUP_FILE.gz"
```

Add to crontab:
```bash
crontab -e
# Add: 0 2 * * * /home/ubuntu/backup_raisemyhand.sh
```

### Manual Backup

```bash
docker compose -f docker-compose.prod.yml exec postgres \
    pg_dump -U raisemyhand -d raisemyhand > backup.sql
```

### Restore Backup

```bash
docker compose -f docker-compose.prod.yml exec -T postgres \
    psql -U raisemyhand -d raisemyhand < backup.sql
```

---

## Monitoring & Logs

### Check Application Status

```bash
# View real-time logs
docker logs -f raisemyhand-app

# View last 100 lines
docker logs --tail 100 raisemyhand-app

# View logs with timestamps
docker logs -t raisemyhand-app
```

### Database Status

```bash
# Connect to database
docker compose -f docker-compose.prod.yml exec postgres \
    psql -U raisemyhand -d raisemyhand

# Show database size
\l+

# Show connections
SELECT pid, usename, application_name, query_start, state FROM pg_stat_activity;

# Exit
\q
```

### Health Check

```bash
# Application health
curl http://localhost:8000/api/system/status

# Database connectivity
docker compose -f docker-compose.prod.yml exec postgres \
    pg_isready -U raisemyhand
```

### Container Status

```bash
# All containers
docker compose -f docker-compose.prod.yml ps

# Container resource usage
docker stats raisemyhand-app raisemyhand-postgres

# Container logs with follow
docker compose -f docker-compose.prod.yml logs -f
```

---

## Troubleshooting

### "FATAL: Ident authentication failed"
**Cause**: PostgreSQL ident authentication issue
**Fix**: Ensure `POSTGRES_PASSWORD` is set correctly in `.env.production`

### "connection refused"
**Cause**: PostgreSQL not started or network issue
**Fix**:
```bash
docker compose -f docker-compose.prod.yml ps
# Should show postgres and app both "Up"
# If not: docker compose -f docker-compose.prod.yml up -d
```

### "SECRET_KEY must be set to a random 32+ character value"
**Cause**: `SECRET_KEY` is still the default value
**Fix**:
```bash
python scripts/setup_production.py
# Or manually set SECRET_KEY in .env.production
```

### App crashes on startup
**Check logs**:
```bash
docker logs raisemyhand-app
```

**Common issues**:
- `.env.production` missing
- PostgreSQL credentials wrong
- Database not ready (wait 10-20s)
- Secrets not properly set

### High Database Connections
**Current**: `max_connections=100` in PostgreSQL
**If reaching limit**: Reduce uvicorn workers or tune PostgreSQL

```sql
-- Check current connections
SELECT COUNT(*) as total_connections FROM pg_stat_activity;

-- Kill idle connections
SELECT pg_terminate_backend(pid) FROM pg_stat_activity
WHERE state = 'idle' AND query_start < now() - interval '10 minutes';
```

---

## Performance Tuning

### PostgreSQL Configuration

Current settings support **200+ concurrent students** (verified with load tests):
- `max_connections: 100`
- `shared_buffers: 256MB`
- `effective_cache_size: 1GB`
- Connection pooling: 20 persistent + 10 overflow

**Performance Results (200 concurrent students, 5 min test):**
- 99.92% success rate (13,469/13,480 requests)
- 932ms average response time
- 45 requests/second throughput

### Application Scaling

Current: **4 uvicorn workers** (handles 200+ concurrent users)

For higher loads, increase workers (modify docker-compose.prod.yml):
```bash
uvicorn main:app --workers 8  # For 300+ concurrent users
uvicorn main:app --workers 16 # For 500+ concurrent users
```

Monitor database CPU during increases - it becomes the bottleneck above 250-300 users.

### Database Optimization

```sql
-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM questions WHERE meeting_id = 1;

-- Create missing indexes
CREATE INDEX idx_questions_meeting_id ON questions(meeting_id);
CREATE INDEX idx_answers_question_id ON answers(question_id);
CREATE INDEX idx_api_keys_instructor_id ON api_keys(instructor_id);

-- Vacuum to recover space
VACUUM ANALYZE;
```

---

## Security Hardening

### Network Security

- Restrict database port 5432 to Docker network only
- Use firewall rules to block direct database access
- Run application behind reverse proxy (nginx/Apache)
- Use SSL/TLS for all external connections

### Secrets Management

- Never commit `.env.production` to git
- Ensure `.gitignore` includes `.env.production`
- Back up `.env.production` in secure location
- Rotate passwords periodically
- Use Docker secrets for sensitive data (advanced)

### Regular Maintenance

- Update Docker images monthly
- Monitor for security advisories
- Review access logs regularly
- Test backup/restore procedures
- Review database permissions

---

## Migration from Development

### If Migrating Existing SQLite Data

```bash
# On development machine, export data
python scripts/migrate_sqlite_to_postgres.py export \
    --sqlite-url sqlite:///./data/raisemyhand.db

# Copy migration_data.json to production server, then import
python scripts/migrate_sqlite_to_postgres.py import \
    --postgres-url postgresql://user:pass@host:5432/raisemyhand
```

### Or One-Step Migration

```bash
python scripts/migrate_sqlite_to_postgres.py migrate \
    --sqlite-url sqlite:///./data/raisemyhand.db \
    --postgres-url postgresql://user:pass@host:5432/raisemyhand
```

---

## Support & Troubleshooting

For issues, check:
1. Application logs: `docker logs raisemyhand-app`
2. Database status: `docker compose ps`
3. This guide's Troubleshooting section
4. `.env.production` configuration
5. PostgreSQL health: `docker compose exec postgres pg_isready`

---

**Last Updated**: January 2026
**Version**: RaiseMyHand v0.1+ with PostgreSQL
