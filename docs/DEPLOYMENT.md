# Deployment Guide

## Overview

RaiseMyHand can be deployed in several ways. This guide covers the recommended production setup.

## Prerequisites

- Docker and Docker Compose (recommended)
- A domain name
- SSL certificate or access to Let's Encrypt
- 2GB+ RAM and 20GB disk space
- Linux server (Ubuntu 20.04+ recommended)

## Quick Start with Docker (Recommended)

### 1. Clone Repository

```bash
git clone https://github.com/your-org/raisemyhand.git
cd raisemyhand
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:

```bash
# Production settings
ENV=production
HOST=0.0.0.0
PORT=8000
BASE_URL=https://questions.yourschool.edu
TIMEZONE=America/New_York
DEBUG=false
```

### 3. Set Admin Password

```bash
mkdir -p secrets
echo "YourSecurePassword123!" > secrets/admin_password.txt
chmod 600 secrets/admin_password.txt
```

### 4. Start Application

```bash
docker compose up -d

# Check logs
docker compose logs -f
```

Application will be available at `http://localhost:8000`

## Production Setup with Nginx + SSL

For production with HTTPS and proper SSL/TLS configuration:

### 1. Install Dependencies

```bash
sudo apt-get update
sudo apt-get install -y nginx certbot python3-certbot-nginx
```

### 2. Create Nginx Configuration

Create `/etc/nginx/sites-available/raisemyhand`:

```nginx
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
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    client_max_body_size 10M;

    location / {
        proxy_pass http://raisemyhand;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws/ {
        proxy_pass http://raisemyhand;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 86400;
    }

    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg)$ {
        expires 7d;
        add_header Cache-Control "public, immutable";
    }
}
```

### 3. Enable Nginx Site

```bash
sudo ln -s /etc/nginx/sites-available/raisemyhand /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 4. Get SSL Certificate

```bash
sudo certbot certonly --nginx -d questions.yourschool.edu
```

### 5. Auto-renew Certificate

```bash
# Enable auto-renewal
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

### 6. Update .env

```bash
BASE_URL=https://questions.yourschool.edu
```

### 7. Restart Docker

```bash
docker compose down
docker compose up -d
```

## Environment Configuration

### Required Variables

```bash
# Server
HOST=0.0.0.0
PORT=8000
BASE_URL=https://questions.yourschool.edu

# Database
DATABASE_URL=sqlite:///./data/raisemyhand.db
# Or for PostgreSQL:
# DATABASE_URL=postgresql://user:password@host:5432/database

# Admin Password (choose one method)
ADMIN_PASSWORD=YourSecurePassword123!
# OR use Docker secrets (recommended for production):
# secrets/admin_password.txt
```

### Optional Variables

```bash
# Settings
TIMEZONE=America/New_York
ENV=production
DEBUG=false

# Features (default: true)
PROFANITY_FILTER_ENABLED=true

# Rate Limiting
RATE_LIMIT_ENABLED=true
```

## Database Configuration

### SQLite (Development/Small Deployments)

Default setup - works out of the box:

```bash
DATABASE_URL=sqlite:///./data/raisemyhand.db
```

**Pros:**
- No additional software needed
- Simple backup (copy database file)

**Cons:**
- Slower with many concurrent users
- Not ideal for 100+ users

### PostgreSQL (Production)

For larger deployments:

1. Install PostgreSQL on your server or use managed service (AWS RDS, DigitalOcean, etc.)

2. Create database:
```bash
createdb raisemyhand
```

3. Set connection string in `.env`:
```bash
DATABASE_URL=postgresql://user:password@hostname:5432/raisemyhand
```

4. Install driver:
```bash
pip install psycopg2-binary
```

5. Application will create tables automatically on startup

## Backup Strategy

### Daily Backups

#### SQLite
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/raisemyhand"
mkdir -p $BACKUP_DIR

DATE=$(date +%Y-%m-%d_%H-%M-%S)
cp /path/to/data/raisemyhand.db $BACKUP_DIR/raisemyhand_$DATE.db

# Keep only last 30 days
find $BACKUP_DIR -mtime +30 -delete
```

Schedule with cron:
```bash
0 2 * * * /scripts/backup.sh
```

#### PostgreSQL
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/raisemyhand"
mkdir -p $BACKUP_DIR

DATE=$(date +%Y-%m-%d_%H-%M-%S)
pg_dump raisemyhand | gzip > $BACKUP_DIR/raisemyhand_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -mtime +30 -delete
```

Schedule with cron:
```bash
0 2 * * * /scripts/backup.sh
```

## Monitoring & Logs

### View Logs

```bash
# Real-time logs
docker compose logs -f

# Last 100 lines
docker compose logs --tail=100

# Logs from specific time
docker compose logs --since 2025-12-16 -f
```

### Log Files

Logs include:
- API requests and responses
- WebSocket connections
- Database operations
- Security events
- Errors and exceptions

### Health Check

Monitor application health:

```bash
curl -s https://questions.yourschool.edu/health || echo "Application down!"
```

Use with monitoring tools (Uptime Robot, Datadog, etc.)

## Performance Tuning

### Docker Limits

Set memory limits in `docker-compose.yml`:

```yaml
services:
  raisemyhand:
    mem_limit: 2g
    memswap_limit: 2g
```

### Connection Pooling

For PostgreSQL with many users, add to `.env`:

```bash
# Connection pool size
DATABASE_POOL_SIZE=20
```

### Nginx Caching

Static assets are cached for 7 days. Adjust in nginx config if needed.

## Scaling

### Single Server

For up to 500 concurrent students, single server is adequate:
- 2GB RAM
- 2 CPU cores
- Docker + Nginx setup

### Multiple Servers

For 500+ users, add load balancing:

1. Set up multiple application servers
2. Add Redis for session sharing (if needed)
3. Configure load balancer (HAProxy, AWS ALB, nginx)
4. Use shared database (PostgreSQL recommended)

## Troubleshooting

### "Port 8000 already in use"

Solution:
```bash
# Find process using port
lsof -i :8000

# Kill process or use different port
docker compose down
```

### "Database connection failed"

Check connection string:
```bash
# For PostgreSQL
pg_isready -h your-host -U your-user

# For SQLite
ls -la ./data/raisemyhand.db
```

### "SSL certificate errors"

```bash
# Test SSL configuration
sudo certbot certificates

# Renew certificate manually
sudo certbot renew --dry-run

# Check nginx config
sudo nginx -t
```

### "WebSocket connection failed"

Check nginx configuration has WebSocket upgrade headers and location /ws/ is properly configured.

### "High memory usage"

```bash
# Check container memory
docker stats

# Restart container to free memory
docker compose restart
```

## Maintenance

### Weekly
- Check disk space: `df -h`
- Monitor logs for errors
- Verify backups completed

### Monthly
- Review and update packages
- Check for security patches
- Test backup restoration
- Review performance metrics

### Quarterly
- Full security audit
- Performance optimization
- Update documentation
- Plan capacity upgrades

## Disaster Recovery

### Database Loss

**SQLite:**
```bash
# Restore from backup
cp /backups/raisemyhand/raisemyhand_2025-12-15.db ./data/raisemyhand.db
docker compose restart
```

**PostgreSQL:**
```bash
# Restore from backup
gunzip < /backups/raisemyhand/raisemyhand_2025-12-15.sql.gz | psql
docker compose restart
```

### Application Not Starting

1. Check logs: `docker compose logs`
2. Verify .env configuration
3. Check database connectivity
4. Restart: `docker compose down && docker compose up -d`

## Deactivation/Shutdown

To safely shut down:

```bash
# Stop accepting new connections
docker pause raisemyhand

# Wait for active sessions to end (students see "Session ending")
sleep 300

# Stop application
docker compose down

# Backup database
cp ./data/raisemyhand.db ./data/raisemyhand.db.final-backup
```
