# Docker Setup Guide for RaiseMyHand

Complete guide for running RaiseMyHand with Docker.

## Quick Start

1. **Configure environment:**
   ```bash
   cp .env.example .env
   nano .env  # Edit BASE_URL, TIMEZONE, etc.
   ```

2. **Set admin password:**
   ```bash
   echo "YourSecurePassword123" > secrets/admin_password.txt
   chmod 600 secrets/admin_password.txt
   ```

3. **Start:**
   ```bash
   docker compose up -d
   ```

4. **Get API key:**
   ```bash
   docker compose logs app | grep "Key:"
   ```

5. **Access:** Open `http://your-server:8000`

---

## Table of Contents

- [Architecture](#architecture)
- [First Time Setup](#first-time-setup)
- [Configuration](#configuration)
- [Daily Operations](#daily-operations)
- [Data Management](#data-management)
- [Troubleshooting](#troubleshooting)
- [Production Deployment](#production-deployment)

---

## Architecture

### File Structure

```
raisemyhand/
├── .env                      # Your environment config (not in git)
├── .env.example              # Template with all options
├── docker-compose.yml        # Simplified, uses env_file and secrets
├── Dockerfile                # Clean, no hardcoded values
├── secrets/
│   ├── admin_password.txt    # Admin password (not in git)
│   └── README.md             # Secrets documentation
└── data/                     # Docker volume (database, uploads)
```

### Key Benefits

- **Clean separation:** Config (.env) vs Secrets (secrets/)
- **Easy deployment:** Just copy .env and set secrets
- **Secure by default:** Secrets in separate files with proper permissions
- **No duplication:** Settings defined once in .env
- **Docker Compose native:** Uses standard env_file and secrets features

---

## First Time Setup

### Step 1: Configure Environment

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` with your settings:
```bash
nano .env
```

**Key settings to change:**
- `BASE_URL`: Your server's actual URL (e.g., `http://192.168.1.100:8000` or `https://yourdomain.com`)
- `TIMEZONE`: Your local timezone (e.g., `America/New_York`, `Europe/London`)
- `CREATE_DEFAULT_API_KEY`: Set to `true` for first run only

### Step 2: Set Admin Password

**IMPORTANT:** Change the default password!

```bash
echo "YourSecurePassword123" > secrets/admin_password.txt
chmod 600 secrets/admin_password.txt
```

**Security notes:**
- Never use the default password in production
- Use a strong password (16+ characters, mixed case, numbers, symbols)
- Never commit this file to git (already in .gitignore)

### Step 3: Start the Container

```bash
docker compose up -d
```

This will:
- Build the Docker image
- Start the application
- Create the database
- Auto-generate an API key (if `CREATE_DEFAULT_API_KEY=true`)

### Step 4: Get Your API Key

If you set `CREATE_DEFAULT_API_KEY=true`, find your API key in the logs:

```bash
docker compose logs app | grep "Key:"
```

Example output:
```
Key: rmh_gwAYIFSQdwc1NKeWzlkmjKeqVISIYk4uUu1MuaiYb1M
```

**⚠️ SAVE THIS KEY!** You'll need it to create sessions.

### Step 5: Access the Application

- **Main page:** `http://your-server:8000`
- **Admin panel:** `http://your-server:8000/admin-login`
  - Username: `admin` (or whatever you set in .env)
  - Password: from `secrets/admin_password.txt`

---

## Configuration

### Environment Variables (.env file)

All settings are configured via `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server binding address (don't change) |
| `PORT` | `8000` | Server port |
| `DATABASE_URL` | `sqlite:///./data/raisemyhand.db` | Database location |
| `BASE_URL` | `http://localhost:8000` | External URL for QR codes |
| `TIMEZONE` | `UTC` | Timezone for timestamps |
| `ADMIN_USERNAME` | `admin` | Admin login username |
| `CREATE_DEFAULT_API_KEY` | `false` | Auto-create API key on first run |
| `SECRET_KEY` | (auto-generated) | JWT secret key |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` | Admin session duration (8 hours) |

### Secrets (secrets/ directory)

Sensitive data is stored in files and loaded via Docker secrets:

- `admin_password.txt` - Admin password (**change before production!**)

**Setting secrets:**
```bash
# Set admin password
echo "YourSecurePassword123" > secrets/admin_password.txt

# Secure permissions
chmod 600 secrets/*.txt
```

---

## Daily Operations

### View Logs

```bash
# View all logs
docker compose logs -f app

# View only recent logs
docker compose logs --tail=100 app

# Search logs
docker compose logs app | grep "error"
```

### Stop the Server

```bash
docker compose down
```

### Start/Restart the Server

```bash
# Start
docker compose up -d

# Restart
docker compose restart

# Restart and rebuild
docker compose up -d --build
```

### Update to Latest Version

```bash
git pull
docker compose build --no-cache
docker compose up -d
```

### Check Status

```bash
# Container status
docker compose ps

# Resource usage
docker compose stats

# Test if server is responding
curl http://localhost:8000
```

---

## Managing API Keys

### Option 1: Via Admin Panel (Recommended)

1. Go to `http://your-server:8000/admin-login`
2. Login with admin credentials
3. Navigate to "API Keys" section
4. Click "Create New API Key"
5. Key is automatically copied to clipboard

### Option 2: Check Logs for Default Key

```bash
docker compose logs app | grep -A 5 "Default API key created"
```

### Option 3: Enable Auto-Creation

Edit `.env` and set:
```
CREATE_DEFAULT_API_KEY=true
```

Then restart:
```bash
docker compose down
docker compose up -d
docker compose logs app | grep "Key:"
```

**Note:** Set back to `false` after getting the key.

---

## Data Management

### Data Persistence

All data (database, sessions, questions) is stored in a Docker volume named `raisemyhand_app-data`.

### Backup Database

```bash
# Create backup
docker run --rm \
  -v raisemyhand_app-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/backup-$(date +%Y%m%d).tar.gz /data
```

### Restore from Backup

```bash
# Stop the application
docker compose down

# Restore backup
docker run --rm \
  -v raisemyhand_app-data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/backup-20250101.tar.gz -C /

# Restart
docker compose up -d
```

### View Volume Location

```bash
docker volume inspect raisemyhand_app-data
```

### Export Database (SQLite)

```bash
# Copy database out of container
docker cp $(docker compose ps -q app):/app/data/raisemyhand.db ./backup.db
```

---

## Troubleshooting

### No API Keys Exist

If you see warnings about missing API keys:

**Solution 1: Auto-create**
```bash
# Edit .env, set CREATE_DEFAULT_API_KEY=true
nano .env

# Restart
docker compose down
docker compose up -d

# Get key
docker compose logs app | grep "Key:"
```

**Solution 2: Create via admin panel**
- Login at `/admin-login`
- Create new API key in dashboard

### Server Not Starting

```bash
# Check logs for errors
docker compose logs app

# Common issues:
# - Port 8000 already in use (change PORT in .env)
# - Admin password not set (check secrets/admin_password.txt)
# - Permission issues (chmod 600 secrets/*.txt)
```

### Can't Access Admin Panel

```bash
# Verify admin password is set
cat secrets/admin_password.txt

# Check if file is being read
docker compose exec app cat /run/secrets/admin_password

# Reset admin password
echo "NewPassword123" > secrets/admin_password.txt
docker compose restart
```

### Database Errors

```bash
# Check database file permissions
docker compose exec app ls -la /app/data/

# Reset database (⚠️ deletes all data!)
docker compose down -v
docker compose up -d
```

### Container Won't Start

```bash
# View detailed logs
docker compose logs -f

# Rebuild from scratch
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Reset Everything (⚠️ Deletes All Data!)

```bash
docker compose down -v
docker compose up -d
```

---

## Production Deployment

### Pre-Deployment Checklist

Before deploying to production:

- [ ] **Change admin password** in `secrets/admin_password.txt`
- [ ] **Set correct BASE_URL** in `.env` (your actual domain/IP)
- [ ] **Set appropriate TIMEZONE** in `.env`
- [ ] **Set CREATE_DEFAULT_API_KEY=true** for first run only
- [ ] **Secure secrets directory**: `chmod 600 secrets/*.txt`
- [ ] **Configure reverse proxy** (nginx/Apache) for HTTPS
- [ ] **Set up SSL certificate** (Let's Encrypt)
- [ ] **Configure firewall** (allow port 8000 or your custom port)
- [ ] **Set up regular backups** of Docker volume
- [ ] **Never commit** `.env` or `secrets/` to version control
- [ ] **Configure monitoring** (optional but recommended)

### Reverse Proxy Setup (nginx)

Example nginx configuration:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Production Best Practices

1. **Use HTTPS** - Always use SSL/TLS in production
2. **Strong passwords** - 16+ character admin password
3. **Regular backups** - Automated daily backups
4. **Monitor logs** - Set up log aggregation
5. **Resource limits** - Set Docker resource limits in docker-compose.yml
6. **Health checks** - Monitor application health
7. **Update regularly** - Keep dependencies updated

### Scaling Considerations

For high-traffic deployments:

1. **Switch to PostgreSQL** - Better performance than SQLite
2. **Use Redis** - For WebSocket pub/sub across multiple instances
3. **Load balancer** - Distribute traffic across multiple containers
4. **CDN** - Serve static assets from CDN
5. **Separate workers** - Background job processing

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed production deployment guide.

---

## Support and Additional Resources

- **Database Configuration**: [DATABASE_SETUP.md](DATABASE_SETUP.md)
- **Full Deployment Guide**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **Security Guide**: [SECURITY.md](SECURITY.md)
- **General Documentation**: [README.md](README.md)

---

## Changelog

### Recent Improvements

✅ **Simplified Configuration** (2025-11)
- All settings in `.env` file
- No hardcoded values in docker-compose.yml
- Clean separation of config and secrets

✅ **Security Enhancements** (2025-11)
- Admin password in Docker secrets
- Proper file permissions
- CSRF protection
- Rate limiting

✅ **Developer Experience** (2025-11)
- Single command setup
- Better error messages
- Comprehensive documentation
