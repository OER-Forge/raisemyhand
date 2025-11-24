# Quick Setup Instructions

This Docker setup has been simplified to use environment variables and Docker secrets.

## What Changed

✅ **Simplified Configuration:**
- All settings in `.env` file (copy from `.env.example`)
- No hardcoded values in `docker-compose.yml` or `Dockerfile`
- Sensitive data uses Docker secrets

✅ **Security Improvements:**
- Admin password stored in `secrets/admin_password.txt` (not in .env)
- Secrets never committed to git
- Clean separation of config and secrets

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

## File Structure

```
├── .env                      # Your environment config (not in git)
├── .env.example              # Template with all options
├── docker-compose.yml        # Simplified, no hardcoded values
├── Dockerfile                # No ENV variables
├── secrets/
│   ├── admin_password.txt    # Admin password (not in git)
│   └── README.md             # Secrets documentation
```

## Key Benefits

- **Clean separation:** Config (.env) vs Secrets (secrets/)
- **Easy deployment:** Just copy .env and set secrets
- **Secure by default:** Secrets in separate files with proper permissions
- **No duplication:** Port, names, and URLs defined once in .env
- **Docker Compose native:** Uses standard env_file and secrets features

## Configuration Options

All options are in `.env`:
- `BASE_URL` - External URL for QR codes
- `PORT` - Server port (default: 8000)
- `TIMEZONE` - Display timezone
- `ADMIN_USERNAME` - Admin login (default: admin)
- `CREATE_DEFAULT_API_KEY` - Auto-create key on first run

Admin password is always loaded from `secrets/admin_password.txt`.

See [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md) for detailed instructions.
