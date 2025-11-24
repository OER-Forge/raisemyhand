# Docker Quick Start Guide

## First Time Setup

1. **Configure your environment**:
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env with your settings
   nano .env
   ```
   
   Key settings to change in `.env`:
   - `BASE_URL`: Your server's actual URL (e.g., `http://192.168.1.100:8000`)
   - `TIMEZONE`: Your local timezone
   - `CREATE_DEFAULT_API_KEY`: Keep as `true` for first run

2. **Set admin password** (IMPORTANT!):
   ```bash
   # Change the default password in secrets/admin_password.txt
   echo "YourSecurePassword123" > secrets/admin_password.txt
   chmod 600 secrets/admin_password.txt
   ```

3. **Start the container**:
   ```bash
   docker compose up -d
   ```

4. **Get your API key** (shown in logs on first run):
   ```bash
   docker compose logs app | grep "Key:"
   ```
   
   Example output:
   ```
   Key: rmh_gwAYIFSQdwc1NKeWzlkmjKeqVISIYk4uUu1MuaiYb1M
   ```
   
   **⚠️ SAVE THIS KEY!** You'll need it to create sessions.

5. **Access the application**:
   - Main page: `http://your-server:8000`
   - Admin panel: `http://your-server:8000/admin-login`
   - Login with username `admin` and your password from `secrets/admin_password.txt`

## Daily Usage

### View logs
```bash
docker compose logs -f app
```

### Stop the server
```bash
docker compose down
```

### Restart the server
```bash
docker compose restart
```

### Update to latest version
```bash
docker compose build --no-cache
docker compose up -d
```

## Managing API Keys

### Option 1: Via Admin Panel (Recommended)
1. Go to `http://your-server:8000/admin-login`
2. Login with admin credentials
3. Navigate to "API Keys" section
4. Click "Create New API Key"
5. Key is automatically copied to clipboard

### Option 2: Check logs for default key
```bash
docker compose logs app | grep -A 5 "Default API key created"
```

## Data Persistence

All data (database, sessions, questions) is stored in a Docker volume:
```bash
# View volume location
docker volume inspect raisemyhand_app-data

# Backup the database
docker run --rm -v raisemyhand_app-data:/data -v $(pwd):/backup alpine tar czf /backup/backup.tar.gz /data

# Restore from backup
docker run --rm -v raisemyhand_app-data:/data -v $(pwd):/backup alpine tar xzf /backup/backup.tar.gz -C /
```

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

### Secrets (secrets/ directory)

Sensitive data is stored in files and loaded via Docker secrets:

- `admin_password.txt` - Admin password (change before production!)

## Troubleshooting

### No API keys exist
If you see warnings about missing API keys:

1. **Set environment variable and restart**:
   ```bash
   # Edit .env, set CREATE_DEFAULT_API_KEY=true
   docker compose down
   docker compose up -d
   docker compose logs app | grep "Key:"
   ```

2. **Or create manually via admin panel**:
   - Login at `/admin-login`
   - Create new API key in dashboard

### Check if server is running
```bash
docker compose ps
curl http://localhost:8000
```

### View real-time logs
```bash
docker compose logs -f
```

### Reset everything (⚠️ deletes all data!)
```bash
docker compose down -v
docker compose up -d
```

## Production Checklist

Before deploying to production:

- [ ] Change admin password in `secrets/admin_password.txt`
- [ ] Set correct `BASE_URL` in `.env` (your actual domain/IP)
- [ ] Set appropriate `TIMEZONE` in `.env`
- [ ] Set `CREATE_DEFAULT_API_KEY=true` in `.env` for first run only
- [ ] Secure secrets directory permissions: `chmod 600 secrets/*.txt`
- [ ] Configure reverse proxy (nginx) for HTTPS
- [ ] Set up regular backups of Docker volume
- [ ] Never commit `.env` or `secrets/` files to version control

## Support

- **Database Setup**: See [DATABASE_SETUP.md](DATABASE_SETUP.md)
- **Full Deployment Guide**: See [DEPLOYMENT.md](DEPLOYMENT.md)
- **General Info**: See [README.md](README.md)
