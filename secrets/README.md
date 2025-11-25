# Secrets Directory

This directory stores sensitive data that should never be committed to version control.

## Files

### `admin_password.txt`
Contains the admin panel password.

**Current password:** `TestSecure123!`

## Password Configuration - Choose ONE Method

### Method 1: For Local Development (Recommended)
Use **`.env`** file only:

```bash
# Set password in .env file
ADMIN_PASSWORD=TestSecure123!

# That's it! No need to touch secrets/admin_password.txt
```

### Method 2: For Docker/Production (Recommended)
Use **`secrets/admin_password.txt`** only:

```bash
# Set password in secrets file
echo "YourSecurePassword" > secrets/admin_password.txt
chmod 600 admin_password.txt

# Remove or comment out ADMIN_PASSWORD from .env
# ADMIN_PASSWORD=  # Commented out, using secrets file instead
```

## How It Works

The application checks in this order:
1. **`ADMIN_PASSWORD` environment variable** (from `.env` or shell) - highest priority
2. **Docker secrets** at `/run/secrets/admin_password` (Docker only)
3. **Local secrets file** at `secrets/admin_password.txt` (fallback)

**Choose one method to avoid confusion!**

## Security Notes

1. ⚠️ **NEVER commit this directory to git** - it's already in `.gitignore`
2. ⚠️ **Change passwords before production deployment**
3. ✅ **Set restrictive permissions**: `chmod 600 *.txt`
4. ✅ **Use strong passwords**: 16+ characters, mixed case, numbers, symbols
5. ✅ **Keep `.env` and `secrets/admin_password.txt` in sync**

## Docker Usage

Docker Compose automatically mounts these files to `/run/secrets/` inside containers.
The application reads secrets from these mounted files.
