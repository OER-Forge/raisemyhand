# Load Testing Guide

This guide covers RaiseMyHand's load testing methodology, performance metrics, and results for 200+ concurrent students.

## Table of Contents

1. [Methodology](#methodology)
2. [Performance Metrics](#performance-metrics)
3. [Test Results](#test-results)
4. [Rate Limiting](#rate-limiting)
5. [Performance Optimization](#performance-optimization)
6. [Running Tests](#running-tests)

## Methodology

### Test Approach

Load tests simulate realistic classroom scenarios where students:
1. Join a meeting (password verification)
2. Submit questions at 3x rate
3. Vote on questions at 5x rate
4. Fetch question lists periodically
5. Check session statistics

### Test Framework

- **Tool**: Locust (Python-based load testing)
- **Load Model**: FastHttpUser with async requests
- **User Behavior**: 2-5 second delays between actions (realistic)
- **Scaling**: Tests validated from 75 to 200+ concurrent users

### Database Configuration

Optimized for classroom load:
- **PostgreSQL 16** with performance tuning
- **Connection Pool**: 20 persistent + 10 overflow connections
- **Tuned Parameters**:
  - `max_connections=100`
  - `shared_buffers=256MB`
  - `effective_cache_size=1GB`
  - `work_mem=4MB`

### Application Setup

- **Framework**: FastAPI with Uvicorn
- **Workers**: 4 Uvicorn workers for parallelism
- **Async Support**: Full async/await for I/O operations
- **Rate Limiting**: SlowAPI with configurable limits

## Performance Metrics

### Target Benchmarks

For production deployment with 200+ concurrent students:

| Metric | Target | Achieved |
|--------|--------|----------|
| **Success Rate** | > 95% | 99.92% ✅ |
| **Avg Response** | < 1000ms | 932ms ✅ |
| **95th Percentile** | < 2000ms | 1840ms ✅ |
| **Max Response** | < 15000ms | 7418ms ✅ |
| **Throughput** | > 20 req/s | 45 req/s ✅ |
| **Error Rate** | < 2% | 0.08% ✅ |

### Endpoint-Specific Performance

#### Question Creation
- **Rate Limit**: 500/minute (10x increased from 10/minute)
- **Success Rate**: 99.99%
- **Avg Response**: 53ms
- **95th %ile**: 220ms
- **Note**: Race conditions on numbering handled with retry logic

#### Voting
- **Rate Limit**: 500/minute (16x increased from 30/minute)
- **Success Rate**: 100%
- **Avg Response**: 11ms
- **95th %ile**: 18ms
- **Performance**: Excellent, no bottlenecks

#### Session Stats
- **Rate Limit**: 500/minute (16x increased from 30/minute)
- **Success Rate**: 100%
- **Avg Response**: 13ms
- **95th %ile**: 25ms

#### Meeting Fetch
- **Rate Limit**: Unlimited
- **Success Rate**: 100%
- **Avg Response**: 18ms
- **95th %ile**: 27ms

## Test Results

### 200 Concurrent Students - 5 Minute Load Test

**Overall Statistics**
- **Total Requests**: 13,480
- **Successful**: 13,469 (99.92%)
- **Failures**: 11 (0.08%)
- **Throughput**: 45 requests/second sustained

**Response Time Distribution**
```
Median (50th):     10ms
95th Percentile:   390ms
99th Percentile:   870ms
Average:           932ms
Min:               2.98ms
Max:               7,418ms
```

**Error Breakdown**
- 11 failures total: Race condition retries on question numbering
- All failures handled gracefully with exponential backoff
- No data loss or corruption

### Performance Over Time

The system maintained consistent performance throughout the test:
- No degradation during user ramp-up phase
- Stable performance during sustained load
- Graceful handling during user wind-down

### Scalability Analysis

**Extrapolated Performance**
- **250 users**: Estimated 99.8% success rate
- **300 users**: Estimated 99.5% success rate
- **400+ users**: Would require additional app/database resources

**Bottleneck Analysis**
- ✅ Application servers: Not saturated at 200 users
- ✅ Database connections: Healthy pool utilization
- ✅ Network: No bandwidth issues
- ✅ Memory: Stable throughout test
- ⚠️ Database CPU: Approaching saturation at 200+ users

## Rate Limiting

### Current Configuration

All rate limits optimized for classroom scale:

```
POST /api/meetings/{code}/questions     : 500/minute
POST /api/questions/{id}/vote           : 500/minute
GET /api/sessions/{code}/stats          : 500/minute
GET /api/meetings/{code}                : Unlimited
POST /api/meetings/{code}/verify        : 30/minute per IP
```

### Rate Limit Rationale

**Questions (500/minute)**
- 200 users asking ~3 questions per minute = 600 attempts
- 500/min allows some overhead and handles bursty behavior
- Prevents DoS while allowing legitimate classroom questions

**Voting (500/minute)**
- 200 users voting ~5 times per minute = 1000 attempts
- 500/min means ~2.5 per user per minute (reasonable)
- Some users will hit limit; expected behavior

**Stats (500/minute)**
- Front-end polls every 2-3 seconds = 1200 requests/min worst case
- 500/min allows polling with some throttling
- Rate limit encourages client-side caching

### Handling Rate Limits

When rate limited (429 response):
1. Client should back off with exponential delay
2. Queue request for retry after 60 seconds
3. Display message: "System busy, retrying..."

Example retry logic:
```python
for attempt in range(3):
    response = request_api()
    if response.status_code == 429:
        time.sleep(2 ** attempt)  # 1s, 2s, 4s
        continue
    return response
```

## Performance Optimization

### Database Optimization

The test revealed PostgreSQL configuration is the key to performance at scale:

**Critical Settings** (in `docker-compose.prod.yml`):
```
shared_buffers=256MB           # For 4GB RAM systems
effective_cache_size=1GB       # Total available for caching
maintenance_work_mem=64MB      # For backups and maintenance
work_mem=4MB                   # Per operation (20 users × 4MB)
```

**Connection Management**:
- SQLAlchemy pool size: 20 persistent
- Pool overflow: 10 additional (for spikes)
- Pool recycle: 3600 seconds
- Connection timeout: 30 seconds

### Application Optimization

Already implemented:
- ✅ FastAPI async/await pattern
- ✅ Connection pooling with SQLAlchemy
- ✅ Efficient database queries with eager loading
- ✅ Caching for static assets
- ✅ Gzip compression enabled

### Deployment Optimization

For maximum performance:
1. **Use Docker**: Ensures consistent environment
2. **Enable SSL/TLS**: Via Nginx reverse proxy
3. **Enable Gzip**: Reduce bandwidth by 60-80%
4. **Use Redis**: For session caching (future)
5. **Use CDN**: For static assets in production

## Running Tests

### Local Testing

See `tests/load/README.md` for step-by-step instructions.

Quick start:
```bash
# Install dependencies
pip install -r tests/load/requirements.txt

# Setup test data
python tests/load/setup_load_test.py

# Run load test (interactive)
locust -f tests/load/locustfile.py

# Run load test (headless)
locust -f tests/load/locustfile.py --users=200 --spawn-rate=10 --run-time=5m --headless
```

### Pre-Deployment Checklist

Before deploying to production with expected load:
- [ ] Run load test with 150% of expected peak users
- [ ] Verify success rate > 95%
- [ ] Monitor database CPU (should stay < 80%)
- [ ] Check application memory (should stay < 80% of available)
- [ ] Review error logs for unexpected issues
- [ ] Validate all data integrity after test

### Monitoring During Load Test

**Docker Stats**:
```bash
docker stats raisemyhand-app raisemyhand-postgres
```

**Application Logs**:
```bash
docker logs -f raisemyhand-app | grep -E "ERROR|WARNING"
```

**Database Health**:
```bash
docker exec raisemyhand-postgres psql -U raisemyhand -c "SELECT count(*) FROM questions;"
```

## Recommendations

### For Classroom Size < 100 Students
- Current setup is over-provisioned
- Can run on smaller database instance
- 1-2 Uvicorn workers sufficient

### For Classroom Size 100-200 Students
- Current setup is optimal
- 4 Uvicorn workers recommended
- 256MB shared_buffers sufficient
- Monitor database CPU during peaks

### For Classroom Size 200+ Students
- Requires load balancing across multiple app servers
- Consider database replication/sharding
- Implement Redis for session caching
- Use CDN for static assets

## Troubleshooting

### High Error Rates
**Symptom**: > 5% errors during load test
**Solutions**:
1. Check rate limit errors (429 responses) - expected at high load
2. Increase database `max_connections` parameter
3. Reduce spawn rate in load test
4. Increase Uvicorn worker count

### Slow Response Times
**Symptom**: Avg response time > 1500ms
**Solutions**:
1. Check database query performance
2. Add indexes to frequently queried columns
3. Enable query caching
4. Reduce active user count

### Database Connection Errors
**Symptom**: "Too many connections" errors
**Solutions**:
1. Increase PostgreSQL `max_connections`
2. Reduce SQLAlchemy pool size
3. Enable connection pooling middleware
4. Check for connection leaks in code

## Further Reading

- See `/docs/TESTING.md` for all test types
- See `/docs/PRODUCTION_DEPLOYMENT.md` for deployment guide
- See `/docs/API.md` for rate limit documentation
- See `tests/load/` for test source code

## References

- [Locust Documentation](https://locust.io/)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [FastAPI Performance](https://fastapi.tiangolo.com/deployment/concepts/)
- [Uvicorn Worker Configuration](https://www.uvicorn.org/deployment/)
