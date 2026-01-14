# Testing Guide

This guide covers all testing methodologies for RaiseMyHand, including unit tests, integration tests, and performance/load tests.

## Table of Contents

1. [Overview](#overview)
2. [Unit & Integration Tests](#unit--integration-tests)
3. [Load Testing](#load-testing)
4. [Running Tests](#running-tests)
5. [Test Organization](#test-organization)
6. [Test Coverage](#test-coverage)
7. [Continuous Integration](#continuous-integration)

## Overview

RaiseMyHand uses a multi-layered testing approach:

| Type | Framework | Location | Purpose |
|------|-----------|----------|---------|
| **Unit & Integration** | pytest | `/tests/*.py` | Functionality, API endpoints, database operations |
| **Load Testing** | Locust | `/tests/load/` | Performance at scale (200+ concurrent users) |

## Unit & Integration Tests

### Test Files

- `test_integration.py` - Core API endpoint tests
- `test_api_key_auth.py` - API key authentication and authorization
- `test_websocket_simple.py` - WebSocket basic functionality
- `test_websocket_security.py` - WebSocket security validations
- `test_race_conditions.py` - Concurrency and race condition handling
- `test_security_fixes.py` - Security vulnerability fixes
- `test_profanity_fix.py` - Profanity filtering functionality

### Running Unit/Integration Tests

**Install dependencies:**
```bash
pip install pytest pytest-asyncio httpx
```

**Run all tests:**
```bash
pytest tests/ -v
```

**Run specific test file:**
```bash
pytest tests/test_integration.py -v
```

**Run with coverage:**
```bash
pytest tests/ --cov=app --cov-report=html
```

**Run tests matching pattern:**
```bash
pytest tests/ -k "auth" -v  # Runs all tests with "auth" in the name
```

### Test Examples

**Example: API endpoint test**
```python
def test_create_question(client):
    response = client.post(
        "/api/meetings/abc123/questions",
        json={"text": "What is an API?"}
    )
    assert response.status_code == 200
    assert "question_id" in response.json()
```

**Example: Concurrency test**
```python
def test_concurrent_votes(client):
    # Test that multiple concurrent votes are handled correctly
    # See test_race_conditions.py for implementation
    pass
```

### Test Organization

Tests follow AAA pattern (Arrange, Act, Assert):

```python
def test_question_creation():
    # Arrange - setup test data
    meeting = create_test_meeting()

    # Act - perform operation
    response = post_question(meeting.id, "Test question?")

    # Assert - verify results
    assert response.status_code == 200
    assert response.json()["text"] == "Test question?"
```

## Load Testing

For testing RaiseMyHand at scale with 75-200+ concurrent students.

### Quick Start

```bash
# 1. Install load testing dependencies
pip install -r tests/load/requirements.txt

# 2. Setup test data
python tests/load/setup_load_test.py

# 3. Run load test
locust -f tests/load/locustfile.py

# 4. Open http://localhost:8089 and configure users/spawn rate
```

### Load Test Performance Targets

Verified with 200 concurrent students (5-minute sustained load):

| Metric | Target | Achieved |
|--------|--------|----------|
| **Success Rate** | > 95% | 99.92% ✅ |
| **Avg Response** | < 1000ms | 932ms ✅ |
| **95th Percentile** | < 2000ms | 1840ms ✅ |
| **Max Response** | < 15000ms | 7418ms ✅ |
| **Throughput** | > 20 req/s | 45 req/s ✅ |
| **Error Rate** | < 2% | 0.08% ✅ |

### Interpreting Load Test Results

**Green indicator** = Success rate > 95%
**Yellow indicator** = 5-10% failures (rate limited)
**Red indicator** = > 10% failures (investigation needed)

Common failure types:
- **429 errors** - Rate limit hit (expected at high load)
- **500 errors** - Application error (investigate logs)
- **Connection errors** - Server overload (increase resources)

### Headless Load Testing

For CI/CD integration:
```bash
locust -f tests/load/locustfile.py \
  --users=200 \
  --spawn-rate=10 \
  --run-time=5m \
  --headless \
  --headless-json \
  -u http://localhost:8000
```

Output: `results_in_csv/` directory with detailed metrics

### Advanced Load Testing

**Custom meeting code:**
```python
# Edit tests/load/locustfile.py
MEETING_CODE = "your_meeting_code"
MEETING_PASSWORD = "your_password"
```

**Adjust task weights:**
```python
@task(5)  # Increase from 3 to 5 (more questions)
def ask_question(self):
    ...
```

**Change load profile:**
```bash
# Ramp test (progressive load increase)
locust --users=500 --spawn-rate=5 --run-time=10m

# Spike test (sudden load increase)
locust --users=500 --spawn-rate=100 --run-time=2m
```

See `/docs/LOAD_TESTING.md` for detailed performance analysis and troubleshooting.

## Running Tests

### Local Development

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=term-missing

# Run with output
pytest tests/ -v -s  # Shows print statements

# Run failing tests only
pytest tests/ --lf

# Run tests in parallel
pytest tests/ -n auto  # Requires pytest-xdist
```

### Before Committing

```bash
# Run full test suite
pytest tests/

# Run load test with small sample
locust -f tests/load/locustfile.py \
  --users=50 \
  --spawn-rate=5 \
  --run-time=1m \
  --headless

# Check code style
black tests/ --check
flake8 tests/
```

## Test Coverage

Current test coverage includes:

- ✅ API key authentication and authorization
- ✅ WebSocket connections and messaging
- ✅ Race conditions in question numbering
- ✅ Security fixes (SQL injection, XSS, CSRF)
- ✅ Profanity filtering
- ✅ Question creation and voting
- ✅ Session management
- ✅ Performance at 200+ concurrent users

## Continuous Integration

### GitHub Actions Example

Add to `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: raisemyhand
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-asyncio

      - name: Run tests
        run: pytest tests/ -v
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost/raisemyhand

      - name: Run load test (small sample)
        run: |
          pip install -r tests/load/requirements.txt
          python tests/load/setup_load_test.py
          locust -f tests/load/locustfile.py \
            --users=50 \
            --spawn-rate=10 \
            --run-time=1m \
            --headless
```

### Pre-Deployment Testing

Before deploying to production:

```bash
# 1. Run all tests
pytest tests/ -v

# 2. Run load test at 150% expected peak load
locust -f tests/load/locustfile.py \
  --users=300 \
  --spawn-rate=10 \
  --run-time=5m \
  --headless

# 3. Verify all requirements
# - Success rate > 95%
# - Avg response < 1500ms
# - Database CPU < 80%
# - Memory usage stable

# 4. Review error logs
docker logs raisemyhand-app | grep ERROR
```

## Troubleshooting Tests

### Tests fail with "Connection refused"

Ensure the application is running:
```bash
# Development
python main.py

# Or with Docker
docker compose -f docker-compose.prod.yml up
```

### Tests fail with "Database error"

Check PostgreSQL is running:
```bash
docker compose -f docker-compose.prod.yml ps
docker logs raisemyhand-postgres
```

### Load test has high failure rate

Check application logs:
```bash
docker logs -f raisemyhand-app | grep ERROR
```

Common causes:
- Rate limits (429 errors) - increase limits in `main.py`
- Database connections full - check `docker-compose.prod.yml` settings
- Application overloaded - increase Uvicorn workers

### WebSocket tests fail

Ensure WebSocket support is enabled in FastAPI:
```python
# In main.py, should have:
from fastapi import WebSocket
@app.websocket("/ws/...")
async def websocket_endpoint(websocket: WebSocket):
    ...
```

## Further Reading

- See `/docs/LOAD_TESTING.md` for detailed load testing methodology
- See `/docs/PRODUCTION_DEPLOYMENT.md` for deployment checklist
- See `/docs/API.md` for API endpoint documentation
- See `tests/` directory for test source code
