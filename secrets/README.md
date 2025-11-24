# Docker Secrets Directory

This directory contains sensitive configuration files used by Docker secrets.

## Files

- `admin_password.txt` - Admin password (CHANGE THIS BEFORE DEPLOYING!)

## Security

**⚠️ IMPORTANT:** 
- Never commit actual secrets to version control
- Change default passwords before production deployment
- Restrict file permissions: `chmod 600 secrets/*.txt`
- The `.gitignore` file prevents secrets from being committed

## Usage

Docker Compose automatically mounts these files to `/run/secrets/` inside containers.
The application reads secrets from these mounted files.
