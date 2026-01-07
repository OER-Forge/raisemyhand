# Archive Directory

This directory contains old configuration files that were replaced during the v0.1 release cleanup.

## Archived Files

### docker-compose.old.yml
- **Original:** docker-compose.yml
- **Replaced by:** docker-compose.dev.yml (on port 8001)
- **Reason:** Simplified setup with clear naming for demo vs dev environments

### docker-compose.demo-all.old.yml
- **Original:** docker-compose.demo-all.yml
- **Replaced by:** docker-compose.demo.yml with DEMO_CONTEXT environment variable
- **Reason:** Unified demo configuration with selectable contexts

## Current Setup (v0.1+)

For v0.1 and later releases, use:

- **Demo Environment:** `docker compose -f docker-compose.demo.yml up -d` (port 8000)
- **Dev Environment:** `docker compose -f docker-compose.dev.yml up -d` (port 8001)

## Restoring Old Configurations

If you need to use the old configurations:

```bash
# Restore old docker-compose.yml
cp archive/docker-compose.old.yml docker-compose.yml
docker compose up -d

# Restore old demo-all configuration
cp archive/docker-compose.demo-all.old.yml docker-compose.demo-all.yml
docker compose -f docker-compose.demo-all.yml up -d
```

## Migration Notes

**Changes in v0.1:**
1. Split environments into explicit demo and dev configs
2. Demo runs on port 8000, Dev on port 8001
3. Both can run simultaneously
4. Added auto-reset script for demo environment
5. Simplified README and documentation structure
