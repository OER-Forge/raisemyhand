# Changelog

All notable changes to RaiseMyHand are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Load Testing Infrastructure** - Comprehensive Locust-based load testing suite
  - Load test files organized in `/tests/load/` with setup and configuration scripts
  - Support for testing 75-200+ concurrent students
  - Verified 99.92% success rate with 200 concurrent users
  - Load testing documentation in `/docs/LOAD_TESTING.md`

- **Testing Documentation** - Complete testing guide
  - `/docs/TESTING.md` - Comprehensive guide for unit, integration, and load tests
  - Test organization and best practices
  - CI/CD integration examples
  - Troubleshooting guide for test failures

- **Performance Documentation** - Detailed performance metrics
  - Updated `/docs/LOAD_TESTING.md` with methodology and benchmarks
  - Added scalability section to `/docs/FEATURES.md`
  - Updated `/docs/PRODUCTION_DEPLOYMENT.md` with pre-deployment load testing guide
  - Performance tuning guidance for 200+ concurrent users

- **Rate Limit Updates** - Optimized rate limits for classroom scale
  - `/api/meetings/{code}/questions`: Increased from 10/min to 500/min
  - `/api/questions/{id}/vote`: Increased from 30/min to 500/min
  - `/api/sessions/{code}/stats`: Increased from 30/min to 500/min
  - Updated `/docs/API.md` with current rate limit configuration

### Fixed
- **PostgreSQL Compatibility** - Fixed critical database issue
  - Removed incompatible `FOR UPDATE` lock on aggregate functions
  - Bug: `(psycopg2.errors.FeatureNotSupported) FOR UPDATE is not allowed with aggregate functions`
  - Location: `routes_questions.py` line 81-84
  - Behavior: Concurrent question numbering now relies on existing retry logic

- **Question Numbering** - Race condition handling
  - Existing retry logic properly handles concurrent question numbering attempts
  - No data loss or corruption during high-load scenarios

### Changed
- **Database Configuration** - Optimized for classroom scale
  - PostgreSQL 16 with performance tuning enabled
  - Connection pool: 20 persistent + 10 overflow connections
  - Tuned parameters for 200+ concurrent students
  - `max_connections: 100`, `shared_buffers: 256MB`, `effective_cache_size: 1GB`

- **Documentation Updates** - Comprehensive documentation overhaul
  - Updated `/README.md` with performance metrics and testing links
  - Added performance & scalability section to main README
  - Updated `/docs/README.md` documentation hub with testing links
  - Consistent documentation of 200+ concurrent user capability across all docs

### Performance
- **Verified Performance at Scale**
  - **200 Concurrent Students**: 99.92% success rate (13,469/13,480 requests)
  - **Average Response Time**: 932ms
  - **95th Percentile**: 1840ms
  - **Throughput**: 45 requests/second
  - **Error Rate**: 0.08% (gracefully handled race conditions)
  - **Sustained Load**: 5-minute test with realistic classroom workload

---

## [v0.1] - 2025-12-16

Initial production release with core features and PostgreSQL support.

### Added
- Real-time question submission and voting system
- WebSocket support for instant updates
- Content moderation with profanity filtering
- Admin dashboard for system management
- API key authentication for instructors
- Session statistics and reporting
- CSV and JSON data export
- QR code generation for easy student access
- Presentation mode for classroom projection
- Docker deployment with PostgreSQL backend

### Security
- CSRF protection on all state-changing requests
- XSS prevention with HTML sanitization
- Rate limiting to prevent abuse
- Password hashing with bcrypt
- Session isolation and access control

---

## Git Log

For a complete list of commits, see the repository's git history:
```bash
git log --oneline
```

Recent commits:
- `b34033f` - some updates for production
- `0fc43ae` - fix: Critical performance improvements for 75+ concurrent users
- `40ba492` - Add Jekyll config for GitHub Pages
- `3dc1b14` - added demo mode information on all pages and routes
- `4e0c4b7` - chore: Clean up debug logging and reset rate limits for v0.1 release

---

## Versioning

RaiseMyHand uses semantic versioning:
- **Major (X.0.0)** - Breaking changes, major features
- **Minor (0.X.0)** - New features, backwards compatible
- **Patch (0.0.X)** - Bug fixes, documentation updates

Current version: See `VERSION` file or check git tags.

---

## Contributing

Please follow these guidelines when contributing:
1. Create a branch from `main` or `dev`
2. Make your changes with clear commit messages
3. Test your changes locally
4. Submit a pull request with a description
5. Ensure load tests pass for performance-sensitive changes

See [TESTING.md](docs/TESTING.md) for testing procedures.

---

## Support

For issues or questions:
- Check [FAQ.md](docs/FAQ.md) for common questions
- See [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for solutions
- Open an issue on GitHub for bugs
- See [TESTING.md](docs/TESTING.md) for test failures
