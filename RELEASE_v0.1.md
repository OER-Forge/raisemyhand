# RaiseMyHand v0.1 Release Checklist

## Release Goals

This release focuses on:
- Simplified setup for demo and development environments
- Clean, beginner-friendly documentation
- Easy deployment for classroom use
- Auto-reset capability for public demos

---

## Pre-Release Checklist

### 1. Code & Configuration
- [x] Create `docker-compose.demo.yml` - Demo environment on port 8000
- [x] Create `docker-compose.dev.yml` - Dev environment on port 8001
- [x] Archive old docker-compose files to `/archive`
- [x] Remove obsolete `version` field from compose files
- [x] Create demo reset script (`scripts/reset-demo.sh`)
- [x] Create cron setup documentation (`scripts/setup-demo-cron.md`)
- [ ] Update `.gitignore` if needed
- [ ] Verify all demo contexts are working (physics_101, biology_200, etc.)

### 2. Documentation
- [x] Create simplified main README.md
- [x] Create `docs/GETTING_STARTED.md`
- [x] Update `docs/README.md` with new structure
- [ ] Review and update all docs for accuracy
  - [ ] INSTRUCTOR_GUIDE.md
  - [ ] STUDENT_GUIDE.md
  - [ ] ADMIN_GUIDE.md
  - [ ] DEPLOYMENT.md
  - [ ] API.md
  - [ ] FAQ.md
  - [ ] TROUBLESHOOTING.md
- [ ] Add screenshots to docs (if not already present)
- [ ] Update repo URLs in README (replace `<your-repo-url>`)

### 3. Testing
- [x] Test demo environment startup
- [x] Test dev environment startup
- [x] Test demo reset script
- [ ] Test both environments running simultaneously
- [ ] Verify demo loads physics_101 context correctly
- [ ] Verify different demo contexts (biology, chemistry, etc.)
- [ ] Test student workflow in demo
- [ ] Test instructor workflow in demo
- [ ] Test admin panel access
- [ ] Test API key creation and usage
- [ ] Verify QR codes work correctly
- [ ] Test WebSocket connections
- [ ] Test markdown answer formatting
- [ ] Test data export (JSON/CSV)

### 4. Security & Production Readiness
- [ ] Review security settings in demo mode
- [ ] Ensure secrets are not committed
- [ ] Verify `.gitignore` excludes sensitive files
- [ ] Test production deployment guide
- [ ] Review environment variable documentation
- [ ] Verify CORS settings
- [ ] Check rate limiting configuration

### 5. Cleanup
- [x] Archive old docker-compose files
- [ ] Remove any unused demo data
- [ ] Clean up any test databases
- [ ] Remove debug code or comments
- [ ] Run code formatter/linter
- [ ] Check for TODO comments that should be addressed

### 6. Release Artifacts
- [ ] Create CHANGELOG.md for v0.1
- [ ] Tag the release: `git tag -a v0.1 -m "Release v0.1"`
- [ ] Create GitHub release with notes
- [ ] Build and test Docker images
- [ ] Consider creating Docker Hub images (optional)

### 7. Post-Release
- [ ] Update any external documentation links
- [ ] Announce release (if applicable)
- [ ] Monitor for issues
- [ ] Respond to user feedback

---

## Quick Test Commands

```bash
# Clean slate
docker compose -f docker-compose.demo.yml down -v
docker compose -f docker-compose.dev.yml down -v

# Test demo
docker compose -f docker-compose.demo.yml up -d
# Visit http://localhost:8000
# Login: admin / demo123

# Test dev
docker compose -f docker-compose.dev.yml up -d
# Visit http://localhost:8001
# Login: admin / (password from secrets/admin_password.txt)

# Test both simultaneously
docker ps | grep raisemyhand
# Should see demo on :8000 and dev on :8001

# Test reset
./scripts/reset-demo.sh
docker compose -f docker-compose.demo.yml logs
```

---

## What's New in v0.1

### New Features
- **Dual Environment Setup**: Separate demo and dev configurations
  - Demo: Port 8000, auto-loads physics demo data, resets on restart
  - Dev: Port 8001, persistent data for classroom use
- **Auto-Reset Script**: `scripts/reset-demo.sh` for automatic demo cleanup
- **Cron Setup Guide**: Easy daily reset configuration
- **Simplified README**: Quick start focused, detailed docs in `/docs`
- **Getting Started Guide**: Step-by-step walkthrough for new users

### Improvements
- Clearer documentation structure
- Simplified deployment process
- Better separation of demo vs production use
- Archive of old configurations for backwards compatibility

### Configuration Changes
- Demo uses `demo_raisemyhand.db` (auto-resets)
- Dev uses `raisemyhand.db` (persistent)
- Both use named Docker volumes
- Environment-specific settings clearly documented

---

## Breaking Changes

### Docker Compose Files
- Old `docker-compose.yml` moved to `archive/docker-compose.old.yml`
- Old `docker-compose.demo-all.yml` moved to `archive/docker-compose.demo-all.old.yml`
- Users should migrate to new compose files:
  - Use `docker-compose.demo.yml` for demos
  - Use `docker-compose.dev.yml` for development

### Migration Guide

**From old docker-compose.yml:**
```bash
# Stop old setup
docker compose down

# Backup data if needed
cp -r data data.backup

# Use new dev setup
docker compose -f docker-compose.dev.yml up -d
```

**From old demo setup:**
```bash
# Stop old demo
docker compose -f docker-compose.demo.yml down

# Use new demo (will auto-load fresh data)
docker compose -f docker-compose.demo.yml up -d
```

---

## Known Issues

- None yet (track issues on GitHub)

---

## Future Roadmap (v0.2+)

Potential features for future releases:
- [ ] PostgreSQL support out of the box
- [ ] Multi-language support
- [ ] Enhanced analytics dashboard
- [ ] Mobile app for students
- [ ] LTI integration for LMS platforms
- [ ] Automated testing suite
- [ ] Performance optimizations
- [ ] Advanced moderation tools
- [ ] Custom branding options
- [ ] Email notifications

---

## Release Notes Template

```markdown
# RaiseMyHand v0.1

## Overview
First official release of RaiseMyHand with simplified setup for demo and classroom use.

## What's New
- Dual environment setup (demo + dev)
- Auto-reset capability for demos
- Simplified documentation
- Getting started guide
- Improved Docker configuration

## Installation

**Demo Mode:**
```bash
docker compose -f docker-compose.demo.yml up -d
```
Access at http://localhost:8000 (admin/demo123)

**Development Mode:**
```bash
cp .env.example .env
mkdir -p secrets && echo "YourPassword" > secrets/admin_password.txt
docker compose -f docker-compose.dev.yml up -d
```
Access at http://localhost:8001

## Documentation
- [Getting Started](docs/GETTING_STARTED.md)
- [Full Documentation](docs/)
- [Main README](README.md)

## System Requirements
- Docker 20.10+
- Docker Compose 2.0+
- 1GB RAM minimum

## Feedback
Report issues on GitHub: [Issues](../../issues)
```

---

## Sign-off

**Release Manager:** _________________
**Date:** _________________
**Git Tag:** v0.1
**Status:** ☐ Ready for Release ☐ Needs Work

**Notes:**
_______________________________________________________
_______________________________________________________
_______________________________________________________
