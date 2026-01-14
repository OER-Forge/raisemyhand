# Load Testing for RaiseMyHand

This directory contains load testing scripts for validating RaiseMyHand's performance under concurrent student load.

## Overview

Load tests simulate real-world classroom scenarios with multiple students:
- Asking questions
- Voting on questions
- Fetching question lists
- Checking session statistics

**Verified Performance**: 200+ concurrent students, 99.92% success rate

## Quick Start

### 1. Install Dependencies

```bash
pip install -r tests/load/requirements.txt
```

### 2. Start RaiseMyHand (if not running)

```bash
# Development
python main.py

# Or with Docker
docker compose -f docker-compose.prod.yml up
```

### 3. Setup Test Data

```bash
python tests/load/setup_load_test.py
```

This script creates:
- Test instructor account
- Test class
- Test meeting with password protection

The output will show the meeting code and password to use.

### 4. Update Locustfile

Edit `tests/load/locustfile.py` and update:
```python
MEETING_CODE = "your_meeting_code_from_setup"
MEETING_PASSWORD = "loadtest123"
```

### 5. Run Load Test

**Web UI (interactive):**
```bash
locust -f tests/load/locustfile.py
```

Then open http://localhost:8089 and configure:
- **Number of users**: 75-200
- **Spawn rate**: 5-10 users/second
- Click "Start swarming"

**Headless (automated):**
```bash
locust -f tests/load/locustfile.py \
  --users=200 \
  --spawn-rate=10 \
  --run-time=5m \
  --headless
```

## Interpreting Results

### Key Metrics

| Metric | Target | Status |
|--------|--------|--------|
| **Success Rate** | > 95% | ✅ 99.92% |
| **Avg Response** | < 1s | ✅ 932ms |
| **Max Response** | < 10s | ✅ 7.4s |
| **Throughput** | > 20 req/s | ✅ 45 req/s |

### Performance by Endpoint

| Endpoint | Rate Limit | Success Rate | Avg Time |
|----------|-----------|--------------|----------|
| POST `/questions` | 500/min | 99.99% | 53ms |
| POST `/vote` | 500/min | 100% | 11ms |
| GET `/meetings` | Unlimited | 100% | 18ms |
| GET `/stats` | 500/min | 100% | 13ms |

### Expected Results (200 concurrent users, 5 min)

- **Total Requests**: ~13,500
- **Failures**: < 150 (< 2%)
- **Avg Response**: 900-1000ms
- **Min Response**: < 5ms
- **Max Response**: < 10s

## Troubleshooting

### Connection Refused
- Ensure RaiseMyHand is running: `curl http://localhost:8000`
- Check Docker containers: `docker ps`

### 429 Rate Limit Errors
- Indicates rate limit hit - normal at very high loads
- Verify rate limits in `/docs/API.md`
- Current limits: 500/minute for questions, votes, stats

### Slow Response Times
- Check database performance: `docker logs raisemyhand-postgres`
- Monitor Docker resource usage: `docker stats`
- Consider reducing user count or spawn rate

### Meeting Not Found
- Run `setup_load_test.py` again to create new test data
- Verify `MEETING_CODE` in `locustfile.py`

## Performance Tuning

### Database Performance
For optimal results with 200+ users:
- PostgreSQL 16+ with tuned settings (see `docker-compose.prod.yml`)
- Connection pooling: 20 persistent + 10 overflow
- Minimum shared_buffers: 256MB

### Application Performance
- Run with 4+ Uvicorn workers
- Use FastAPI's default async settings
- Enable connection keep-alive

### Load Test Tuning
- **Spawn Rate**: 5-10 users/second (avoid thundering herd)
- **Run Time**: 5+ minutes (allow stabilization)
- **Wait Time**: 2-5 seconds between user actions (realistic)

## Advanced Configuration

### Custom Meeting Code
To test against existing meeting:
1. Find meeting code from instructor dashboard
2. Update `MEETING_CODE` in `locustfile.py`
3. Set meeting password in script
4. Run load test

### Custom Question Distribution
Modify task weights in `locustfile.py`:
```python
@task(3)  # Ask question 3x per cycle
def ask_question(self):
    ...

@task(5)  # Vote 5x per cycle
def vote_on_question(self):
    ...
```

Higher numbers = more frequent actions

## Integration with CI/CD

Add to GitHub Actions or similar:

```yaml
- name: Load Test
  run: |
    pip install -r tests/load/requirements.txt
    locust -f tests/load/locustfile.py \
      --users=100 \
      --spawn-rate=5 \
      --run-time=2m \
      --headless \
      --headless-json \
      -u http://${{ env.APP_URL }}
```

## Documentation

For more information:
- See `/docs/LOAD_TESTING.md` for detailed performance analysis
- See `/docs/TESTING.md` for all test types
- See `/docs/PRODUCTION_DEPLOYMENT.md` for deployment with load testing

## License

These tests are part of RaiseMyHand and follow the same MIT license.
