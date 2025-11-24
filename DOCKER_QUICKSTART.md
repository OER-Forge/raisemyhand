# Docker Quick Start Guide

## First Time Setup

1. **Configure the environment** (optional but recommended):
   ```bash
   # Edit docker-compose.yml
   nano docker-compose.yml
   ```
   
   Change these settings:
   - `BASE_URL`: Your server's actual URL (e.g., `http://192.168.1.100:8000`)
   - `ADMIN_USERNAME` and `ADMIN_PASSWORD`: Change from defaults!
   - `CREATE_DEFAULT_API_KEY`: Keep as `true` for first run

2. **Start the container**:
   ```bash
   docker-compose up -d
   ```

3. **Get your API key** (shown in logs on first run):
   ```bash
   docker-compose logs raisemyhand | grep "Key:"
   ```
   
   Example output:
   ```
   Key: rmh_gwAYIFSQdwc1NKeWzlkmjKeqVISIYk4uUu1MuaiYb1M
   ```
   
   **⚠️ SAVE THIS KEY!** You'll need it to create sessions.

4. **Access the application**:
   - Main page: `http://your-server:8000`
   - Admin panel: `http://your-server:8000/admin-login`
   - Login with your configured credentials (default: admin/changeme123)

## Daily Usage

### View logs
```bash
docker-compose logs -f raisemyhand
```

### Stop the server
```bash
docker-compose down
```

### Restart the server
```bash
docker-compose restart
```

### Update to latest version
```bash
docker-compose pull
docker-compose up -d
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
docker-compose logs raisemyhand | grep -A 5 "Default API key created"
```

## Data Persistence

All data (database, sessions, questions) is stored in a Docker volume:
```bash
# View volume location
docker volume inspect vibes_raisemyhand-data

# Backup the database
docker run --rm -v vibes_raisemyhand-data:/data -v $(pwd):/backup alpine tar czf /backup/backup.tar.gz /data

# Restore from backup
docker run --rm -v vibes_raisemyhand-data:/data -v $(pwd):/backup alpine tar xzf /backup/backup.tar.gz -C /
```

## Environment Variables

All configurable via `docker-compose.yml`:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server binding address (don't change) |
| `PORT` | `8000` | Server port |
| `DATABASE_URL` | `sqlite:///./data/raisemyhand.db` | Database location |
| `BASE_URL` | `http://localhost:8000` | External URL for QR codes |
| `TIMEZONE` | `UTC` | Timezone for timestamps |
| `ADMIN_USERNAME` | `admin` | Admin login username |
| `ADMIN_PASSWORD` | `changeme123` | Admin login password |
| `CREATE_DEFAULT_API_KEY` | `false` | Auto-create API key on first run |

## Troubleshooting

### No API keys exist
If you see warnings about missing API keys:

1. **Set environment variable and restart**:
   ```bash
   # Edit docker-compose.yml, set CREATE_DEFAULT_API_KEY=true
   docker-compose down
   docker-compose up -d
   docker-compose logs raisemyhand | grep "Key:"
   ```

2. **Or create manually via admin panel**:
   - Login at `/admin-login`
   - Create new API key in dashboard

### Check if server is running
```bash
docker-compose ps
curl http://localhost:8000
```

### View real-time logs
```bash
docker-compose logs -f
```

### Reset everything (⚠️ deletes all data!)
```bash
docker-compose down -v
docker-compose up -d
```

## Production Checklist

Before deploying to production:

- [ ] Change `ADMIN_PASSWORD` from default
- [ ] Set correct `BASE_URL` (your actual domain/IP)
- [ ] Set appropriate `TIMEZONE`
- [ ] Set `CREATE_DEFAULT_API_KEY=true` for first run only
- [ ] Configure reverse proxy (nginx) for HTTPS
- [ ] Set up regular backups of Docker volume
- [ ] Consider using `docker-compose.prod.yml` with production settings

## Support

- **Database Setup**: See [DATABASE_SETUP.md](DATABASE_SETUP.md)
- **Full Deployment Guide**: See [DEPLOYMENT.md](DEPLOYMENT.md)
- **General Info**: See [README.md](README.md)
