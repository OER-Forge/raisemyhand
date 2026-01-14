# RaiseMyHand Environment Guide

This guide explains the three distinct environments available for RaiseMyHand and how to use each one effectively.

## Quick Reference

| Environment | Docker Compose File | Config File | Database | Use Case |
|-------------|---------------------|-------------|----------|----------|
| **Demo** | `docker-compose.demo.yml` | Built-in defaults | SQLite (ephemeral) | Presentations, demos |
| **Development** | `docker-compose.dev.yml` | `.env` | SQLite (persistent) | Local development |
| **Production** | `docker-compose.prod.yml` | `.env.production` | PostgreSQL | Live classroom use |

---

## Demo Environment

### Purpose
Quick demonstrations, presentations, and training sessions with pre-loaded sample data.

### Characteristics
- ✅ **Fast setup** (< 1 minute)
- ✅ **Pre-loaded demo data** (Physics 101 course with sample questions)
- ✅ **Simple credentials** (admin / demo123)
- ✅ **Auto-generated context** (different scenarios available)
- ❌ **Data resets** on container restart
- ❌ **Not for real use** (demo only)

### Quick Start

```bash
# Start demo environment
docker compose -f docker-compose.demo.yml up -d

# Access the application
open http://localhost:8000

# Login credentials
# Username: admin
# Password: demo123

# Stop demo environment
docker compose -f docker-compose.demo.yml down
```

### Available Demo Contexts

Choose different demo scenarios by setting `DEMO_CONTEXT`:

```bash
# Physics 101 (default)
docker compose -f docker-compose.demo.yml up -d

# Custom context
DEMO_CONTEXT=biology_200 docker compose -f docker-compose.demo.yml up -d
```

### When to Use Demo Mode

- **Presentations:** Show features to stakeholders or potential users
- **Training:** Teach instructors how to use the system
- **Testing UI:** Quickly verify UI changes without affecting real data
- **Recording videos:** Create product demonstration videos
- **Sales demos:** Showcase the product to prospective customers

### Limitations

- Data is **ephemeral** - all changes lost on restart
- Maximum **10-20 concurrent users** (SQLite limitation)
- **No production features** (backups, monitoring, SSL)
- **Demo credentials** are publicly known (insecure)

---

## Development Environment

### Purpose
Local development and testing with persistent data and hot reload.

### Characteristics
- ✅ **Persistent data** (survives container restart)
- ✅ **Hot reload** (code changes auto-restart server)
- ✅ **Debug mode enabled** (detailed error messages)
- ✅ **SQLite** (simple setup, no external database)
- ✅ **Custom configuration** via `.env` file
- ⚠️ **Limited to 30 concurrent users** (SQLite write serialization)

### Quick Start

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env and set ADMIN_PASSWORD
nano .env

# 3. Build and start development environment
docker compose -f docker-compose.dev.yml build
docker compose -f docker-compose.dev.yml up -d

# 4. View logs
docker compose -f docker-compose.dev.yml logs -f

# 5. Access the application
open http://localhost:8000
```

### Configuration

Edit `.env` file:

```bash
# Environment
ENV=development

# Database (SQLite)
DATABASE_URL=sqlite:///./data/raisemyhand.db

# Admin credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password_here

# External URL (for QR codes)
BASE_URL=http://localhost:8000

# Timezone
TIMEZONE=America/New_York

# Debug mode
DEBUG=true
```

### Development Workflow

```bash
# Start with hot reload
docker compose -f docker-compose.dev.yml up

# Code changes automatically restart the server
# Edit Python files, save, and see changes immediately

# Stop development environment
docker compose -f docker-compose.dev.yml down

# Reset database (if needed)
docker compose -f docker-compose.dev.yml down -v
```

### When to Use Development Mode

- **Feature development:** Building new features
- **Bug fixes:** Testing fixes locally
- **Experimentation:** Trying out ideas
- **Integration testing:** Testing API integrations
- **Database migrations:** Testing schema changes

### Performance Characteristics

With the recent performance fixes:

| Metric | Performance |
|--------|-------------|
| Concurrent users (optimal) | 10-20 students |
| Concurrent users (maximum) | 30 students |
| Session join time | < 200ms |
| Vote response time | 50-100ms |
| Broadcast latency | 10-20ms (with parallel fix) |

---

## Production Environment

### Purpose
Live classroom deployment with 75+ concurrent students using PostgreSQL.

### Characteristics
- ✅ **PostgreSQL** (scalable, row-level locking)
- ✅ **Supports 150+ concurrent users**
- ✅ **Connection pooling** (20 persistent + 10 overflow)
- ✅ **4 worker processes** for parallelism
- ✅ **Automated health checks**
- ✅ **Backup-ready** (volume mounted for backups)
- ✅ **Production security** (validates strong secrets)
- ⚠️ **More complex setup** (requires PostgreSQL configuration)

### Prerequisites

Before deploying to production:

- ✅ Server with 2GB+ RAM and 20GB disk space
- ✅ Domain name (e.g., questions.yourschool.edu)
- ✅ SSL/TLS certificate (Let's Encrypt recommended)
- ✅ Strong passwords generated
- ✅ Backup strategy planned

### Quick Start

```bash
# 1. Copy production template
cp .env.production.example .env.production

# 2. Generate strong secrets
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
python3 -c "import secrets; print('CSRF_SECRET=' + secrets.token_urlsafe(32))"
python3 -c "import secrets; print('POSTGRES_PASSWORD=' + secrets.token_urlsafe(16))"

# 3. Edit .env.production with generated secrets
nano .env.production

# Required settings:
# - DATABASE_URL=postgresql://raisemyhand:YOUR_POSTGRES_PASSWORD@postgres:5432/raisemyhand
# - BASE_URL=https://questions.yourschool.edu
# - SECRET_KEY=<generated>
# - CSRF_SECRET=<generated>
# - ADMIN_PASSWORD=<strong password>
# - POSTGRES_PASSWORD=<generated>

# 4. Start production stack
docker compose -f docker-compose.prod.yml up -d

# 5. Verify deployment
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f app

# 6. Check health
curl http://localhost:8000/api/system/status
```

### Configuration

Minimum required settings in `.env.production`:

```bash
# Environment
ENV=production

# Database - PostgreSQL REQUIRED
POSTGRES_USER=raisemyhand
POSTGRES_PASSWORD=STRONG_PASSWORD_HERE
POSTGRES_DB=raisemyhand

# External URL - MUST be your actual domain
BASE_URL=https://questions.yourschool.edu

# Security - Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=YOUR_32_CHAR_SECRET_KEY
CSRF_SECRET=YOUR_32_CHAR_CSRF_SECRET

# Admin credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=STRONG_PASSWORD_HERE

# Production settings
DEBUG=false
DEMO_MODE=false
ENABLE_AUTH=true
RATE_LIMIT_ENABLED=true

# Server config
HOST=0.0.0.0
PORT=8000
TIMEZONE=America/New_York
```

### PostgreSQL Configuration

The production setup includes optimized PostgreSQL settings for classroom workloads:

- **max_connections:** 100
- **shared_buffers:** 256MB
- **effective_cache_size:** 1GB
- **work_mem:** 4MB
- **Connection pool:** 20 persistent + 10 overflow

These settings support 150+ concurrent students with optimal performance.

### SSL/TLS Setup (Nginx)

Production deployments should use nginx as a reverse proxy with SSL/TLS:

```nginx
# /etc/nginx/sites-available/raisemyhand
upstream raisemyhand {
    server localhost:8000;
}

server {
    listen 80;
    server_name questions.yourschool.edu;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name questions.yourschool.edu;

    ssl_certificate /etc/letsencrypt/live/questions.yourschool.edu/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/questions.yourschool.edu/privkey.pem;

    location / {
        proxy_pass http://raisemyhand;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://raisemyhand;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

### Database Management (PgAdmin)

Optional: Start PgAdmin for database management:

```bash
# Start with management profile
docker compose -f docker-compose.prod.yml --profile management up -d

# Access PgAdmin
open http://localhost:5050

# Default credentials (set in .env.production):
# Email: admin@example.com
# Password: admin
```

### Backup Strategy

```bash
# Create backup directory
mkdir -p backups

# Backup database
docker compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U raisemyhand raisemyhand > backups/backup_$(date +%Y%m%d_%H%M%S).sql

# Automated daily backups (cron job)
0 2 * * * cd /path/to/raisemyhand && docker compose -f docker-compose.prod.yml exec -T postgres pg_dump -U raisemyhand raisemyhand > backups/backup_$(date +\%Y\%m\%d).sql

# Restore from backup
cat backups/backup_20260113.sql | docker compose -f docker-compose.prod.yml exec -T postgres \
  psql -U raisemyhand -d raisemyhand
```

### Monitoring

Check application health:

```bash
# System status
curl http://localhost:8000/api/system/status

# Container health
docker compose -f docker-compose.prod.yml ps

# Application logs
docker compose -f docker-compose.prod.yml logs -f app

# PostgreSQL logs
docker compose -f docker-compose.prod.yml logs -f postgres

# Connection pool status (if endpoint added)
curl http://localhost:8000/api/debug/pool-status
```

### Performance Characteristics

With PostgreSQL and our performance fixes:

| Metric | Performance |
|--------|-------------|
| Concurrent users (optimal) | 75-100 students |
| Concurrent users (maximum) | 150+ students |
| Session join time (75 students) | 2-5 seconds total |
| Vote response time | 50ms |
| Broadcast latency | 10-20ms |
| Database write concurrency | Row-level (true parallel) |

### When to Use Production Mode

- **Live classroom use** with 50+ students
- **Production deployment** requiring reliability
- **High concurrency** scenarios (75+ simultaneous users)
- **Data persistence** with automated backups
- **Scalability requirements** for future growth

---

## Migrating Between Environments

### From Demo to Development

```bash
# Stop demo (data will be lost)
docker compose -f docker-compose.demo.yml down

# Start development
docker compose -f docker-compose.dev.yml up -d
```

### From Development to Production

**Step 1: Export existing data**

```bash
# Export SQLite to JSON
docker compose -f docker-compose.dev.yml exec app \
  python scripts/migrate_sqlite_to_postgres.py export \
  --sqlite-url sqlite:///./data/raisemyhand.db \
  --output /app/data/migration.json

# Copy migration file from container
docker cp raisemyhand-dev:/app/data/migration.json ./migration.json
```

**Step 2: Setup production environment**

```bash
# Create production config
cp .env.production.example .env.production

# Generate secrets (see Quick Start above)
# Edit .env.production with generated secrets
```

**Step 3: Start production with PostgreSQL**

```bash
# Start production stack
docker compose -f docker-compose.prod.yml up -d

# Wait for PostgreSQL to be ready
docker compose -f docker-compose.prod.yml logs postgres | grep "ready to accept"
```

**Step 4: Import data to PostgreSQL**

```bash
# Copy migration file to production container
docker cp migration.json raisemyhand-app:/app/data/migration.json

# Import to PostgreSQL
docker compose -f docker-compose.prod.yml exec app \
  python scripts/migrate_sqlite_to_postgres.py import \
  --postgres-url "postgresql://raisemyhand:YOUR_POSTGRES_PASSWORD@postgres:5432/raisemyhand" \
  --input /app/data/migration.json
```

**Step 5: Verify migration**

```bash
# Check data was imported
docker compose -f docker-compose.prod.yml exec app python -c "
from database import get_db
from models_v2 import Instructor, Question, ClassMeeting
db = next(get_db())
print(f'Instructors: {db.query(Instructor).count()}')
print(f'Meetings: {db.query(ClassMeeting).count()}')
print(f'Questions: {db.query(Question).count()}')
"

# Test login and verify data appears correctly
open http://localhost:8000
```

### From Production Back to Development (Rollback)

```bash
# Stop production
docker compose -f docker-compose.prod.yml down

# Start development with previous SQLite database
docker compose -f docker-compose.dev.yml up -d
```

---

## Environment Variables Reference

### Common Variables (All Environments)

```bash
ENV=demo|development|production  # Environment type
HOST=0.0.0.0                     # Server host (usually 0.0.0.0)
PORT=8000                        # Server port
BASE_URL=http://localhost:8000   # External URL for QR codes
TIMEZONE=UTC                     # Server timezone (IANA format)
```

### Database Variables

```bash
# Development/Demo (SQLite)
DATABASE_URL=sqlite:///./data/raisemyhand.db

# Production (PostgreSQL)
DATABASE_URL=postgresql://user:password@host:5432/database
POSTGRES_USER=raisemyhand
POSTGRES_PASSWORD=secure_password_here
POSTGRES_DB=raisemyhand
```

### Security Variables

```bash
SECRET_KEY=32_char_random_string      # JWT signing key
CSRF_SECRET=32_char_random_string     # CSRF protection key
ADMIN_USERNAME=admin                  # Admin username
ADMIN_PASSWORD=strong_password        # Admin password
```

### Feature Flags

```bash
DEMO_MODE=true|false                  # Enable demo features
DEBUG=true|false                      # Debug mode (dev only)
ENABLE_AUTH=true|false                # Require authentication
RATE_LIMIT_ENABLED=true|false         # Rate limiting
```

### Optional Variables

```bash
ACCESS_TOKEN_EXPIRE_MINUTES=480       # Session timeout (8 hours)
PGADMIN_EMAIL=admin@example.com       # PgAdmin email
PGADMIN_PASSWORD=admin                # PgAdmin password
```

---

## Troubleshooting

### Demo Environment Issues

**Problem:** Demo data not loading

```bash
# Solution: Recreate container with fresh data
docker compose -f docker-compose.demo.yml down -v
docker compose -f docker-compose.demo.yml up -d
```

**Problem:** Port 8000 already in use

```bash
# Check what's using the port
lsof -i :8000

# Stop conflicting service
docker compose -f docker-compose.dev.yml down
# or
docker compose -f docker-compose.demo.yml down
```

### Development Environment Issues

**Problem:** Hot reload not working

```bash
# Ensure source code is mounted
docker compose -f docker-compose.dev.yml down
docker compose -f docker-compose.dev.yml up -d

# Check volume mount
docker inspect raisemyhand-dev | grep Mounts -A 20
```

**Problem:** Database locked errors

```bash
# SQLite is single-writer - reduce concurrent operations
# Or migrate to PostgreSQL for production
```

### Production Environment Issues

**Problem:** PostgreSQL connection failed

```bash
# Check PostgreSQL is running
docker compose -f docker-compose.prod.yml ps

# Check logs
docker compose -f docker-compose.prod.yml logs postgres

# Verify connection string
echo $DATABASE_URL

# Test connection manually
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U raisemyhand -d raisemyhand -c "SELECT version();"
```

**Problem:** Application won't start

```bash
# Check validation errors
docker compose -f docker-compose.prod.yml logs app | grep ERROR

# Common issues:
# - SQLite in production (not supported)
# - SECRET_KEY not set
# - ADMIN_PASSWORD not set
# - BASE_URL contains localhost
```

**Problem:** Slow performance with 75+ students

```bash
# Verify PostgreSQL is being used (not SQLite)
docker compose -f docker-compose.prod.yml exec app python -c "
from config import settings
print(f'Database: {settings.database_url}')
print(f'Environment: {settings.env}')
"

# Check connection pool
# Should see: "postgresql://..." not "sqlite://..."

# Monitor database queries
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U raisemyhand -d raisemyhand -c "
    SELECT count(*) as active_connections
    FROM pg_stat_activity
    WHERE datname = 'raisemyhand';
  "
```

---

## Performance Comparison

### Load Test Results (75 Students Joining Simultaneously)

| Metric | Demo (SQLite) | Dev (SQLite) | Prod (PostgreSQL) |
|--------|---------------|--------------|-------------------|
| Total join time | 30-60s | 30-60s | 5-10s |
| Individual join time (p95) | 800ms | 800ms | 200ms |
| Vote response time | 800ms | 800ms | 50ms |
| Broadcast latency | 10-20ms* | 10-20ms* | 10-20ms* |
| Concurrent votes (10 students) | 8s sequential | 8s sequential | < 1s parallel |
| Max recommended users | 20 | 30 | 150+ |

*With parallel broadcasting fix applied

### Database Comparison

| Feature | SQLite | PostgreSQL |
|---------|--------|------------|
| Locking | Database-level | Row-level |
| Concurrent writes | 1 at a time | Multiple parallel |
| Connection pooling | Limited | Full support |
| Write throughput (75 students) | 10-15 ops/sec | 100+ ops/sec |
| Best for | Development, demo | Production |

---

## Security Checklist

### Demo Environment
- ✅ Public credentials acceptable (demo only)
- ✅ No sensitive data
- ✅ Not accessible from internet

### Development Environment
- ✅ Custom admin password set
- ✅ .env file in .gitignore
- ✅ Only accessible on localhost

### Production Environment
- ✅ Strong POSTGRES_PASSWORD (16+ characters)
- ✅ SECRET_KEY randomly generated (32+ characters)
- ✅ CSRF_SECRET randomly generated (32+ characters)
- ✅ ADMIN_PASSWORD strong (12+ characters)
- ✅ BASE_URL points to actual domain (not localhost)
- ✅ DEBUG=false
- ✅ SSL/TLS configured (via nginx)
- ✅ Firewall restricts PostgreSQL port 5432
- ✅ .env.production in .gitignore
- ✅ Automated backups configured
- ✅ Health checks enabled
- ✅ Rate limiting enabled

---

## See Also

- [Deployment Guide](DEPLOYMENT.md) - Full production deployment with nginx and SSL
- [Migration Guide](../scripts/migrate_sqlite_to_postgres.py) - Database migration tool
- [README.md](../README.md) - Project overview and quick start
- [Configuration Reference](../config.py) - All available settings

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/OER-Forge/raisemyhand/issues
- Documentation: https://github.com/OER-Forge/raisemyhand/tree/main/docs
