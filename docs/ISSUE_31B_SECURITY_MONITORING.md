# Issue #31b: Security Monitoring & Audit

**Priority: MEDIUM** | **Labels: security, monitoring, observability**  
**Milestone: Production Operations**  
**Estimated Effort: 4-6 days**

## Description

Implement comprehensive security event tracking, audit logging, and monitoring dashboard to detect and respond to security incidents in real-time.

---

## Motivation

Current system has limited visibility into security events:
- No centralized logging of authentication events
- Failed login attempts are not tracked
- No audit trail for admin actions on instructor accounts
- No alerting for suspicious activities
- Difficult to investigate security incidents retroactively

**Risk**: Security breaches may go undetected, and forensic investigation is impossible without audit trails.

---

## Features

### 1. Security Event Logging

**User Story**: As a security administrator, I want all security-relevant events logged so I can investigate incidents and detect patterns.

**Requirements**:
- [ ] Centralized `SecurityLog` table for all security events
- [ ] Event types: login, logout, failed_login, password_change, role_change, api_key_created, api_key_revoked, account_locked, account_unlocked, 2fa_enabled, 2fa_disabled, session_revoked
- [ ] Capture: timestamp, actor (instructor_id), IP address, user agent, success/failure, metadata
- [ ] Structured JSON metadata for event-specific data
- [ ] Retention policy: 1 year for security logs (configurable)
- [ ] Automatic log rotation and archival

**Implementation**:
```python
# Database model
class SecurityLog(Base):
    """Immutable security event log"""
    __tablename__ = "security_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    event_type = Column(String, nullable=False, index=True)
    instructor_id = Column(Integer, ForeignKey("instructors.id", ondelete="SET NULL"), nullable=True, index=True)
    target_instructor_id = Column(Integer, ForeignKey("instructors.id", ondelete="SET NULL"), nullable=True)  # For admin actions
    ip_address = Column(String, nullable=True, index=True)
    user_agent = Column(String, nullable=True)
    success = Column(Boolean, nullable=False, index=True)
    failure_reason = Column(String, nullable=True)
    metadata = Column(JSON, nullable=True)
    
    instructor = relationship("Instructor", foreign_keys=[instructor_id])
    target_instructor = relationship("Instructor", foreign_keys=[target_instructor_id])
    
    # Make logs immutable
    __table_args__ = (
        Index('ix_security_logs_event_type_timestamp', 'event_type', 'timestamp'),
        Index('ix_security_logs_instructor_timestamp', 'instructor_id', 'timestamp'),
    )

# Logging service
class SecurityLogger:
    @staticmethod
    async def log_event(
        event_type: str,
        instructor_id: Optional[int] = None,
        target_instructor_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        failure_reason: Optional[str] = None,
        metadata: Optional[dict] = None,
        db: DBSession = None
    ):
        """Log a security event"""
        log_entry = SecurityLog(
            event_type=event_type,
            instructor_id=instructor_id,
            target_instructor_id=target_instructor_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            failure_reason=failure_reason,
            metadata=metadata
        )
        db.add(log_entry)
        db.commit()
        
        # Real-time alert check
        await check_alert_rules(log_entry)

# Usage throughout codebase
async def handle_login(username: str, password: str, request: Request, db: DBSession):
    instructor = get_instructor_by_username(username, db)
    
    if not instructor or not verify_password(password, instructor.password_hash):
        await SecurityLogger.log_event(
            event_type="failed_login",
            instructor_id=instructor.id if instructor else None,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            success=False,
            failure_reason="Invalid credentials",
            metadata={"username": username},
            db=db
        )
        raise HTTPException(401, "Invalid credentials")
    
    await SecurityLogger.log_event(
        event_type="login",
        instructor_id=instructor.id,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent"),
        success=True,
        db=db
    )
    
    return create_access_token({"sub": instructor.id})
```

**API Endpoints**:
```
GET /api/admin/security/events
  Query params: event_type, instructor_id, start_date, end_date, success, page, per_page
  Returns: Paginated list of security events

GET /api/admin/security/events/{event_id}
  Returns: Detailed event information

GET /api/instructors/my-security-events
  Returns: Security events for current instructor (transparency)
```

---

### 2. Audit Trail System

**User Story**: As a compliance officer, I want a complete audit trail of all administrative actions so I can verify who changed what and when.

**Requirements**:
- [ ] Separate `AuditLog` table for administrative actions
- [ ] Track all CRUD operations on: instructors, classes, meetings, api_keys, system_config
- [ ] Capture before/after state snapshots for UPDATE operations
- [ ] Track actor, timestamp, action type, resource type/id, IP address
- [ ] Immutable records (append-only, no deletes)
- [ ] Retention policy: 7 years (regulatory compliance)
- [ ] Efficient querying by resource, actor, and time range

**Implementation**:
```python
# Database model
class AuditLog(Base):
    """Immutable audit trail for administrative actions"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    actor_id = Column(Integer, ForeignKey("instructors.id", ondelete="SET NULL"), nullable=False, index=True)
    action = Column(String, nullable=False, index=True)  # CREATE, UPDATE, DELETE, REVOKE, RESTORE
    resource_type = Column(String, nullable=False, index=True)  # instructor, class, meeting, api_key, system_config
    resource_id = Column(Integer, nullable=True, index=True)
    resource_identifier = Column(String, nullable=True)  # Human-readable ID (username, class name)
    before_state = Column(JSON, nullable=True)
    after_state = Column(JSON, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    reason = Column(Text, nullable=True)  # Optional justification
    
    actor = relationship("Instructor", foreign_keys=[actor_id])
    
    __table_args__ = (
        Index('ix_audit_logs_resource', 'resource_type', 'resource_id', 'timestamp'),
        Index('ix_audit_logs_actor_timestamp', 'actor_id', 'timestamp'),
    )

# Audit middleware decorator
def audit_action(action: str, resource_type: str):
    """Decorator to automatically audit actions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get actor from current request context
            actor = get_current_instructor()
            request = get_request_context()
            
            # Capture before state if UPDATE or DELETE
            if action in ["UPDATE", "DELETE"]:
                resource_id = kwargs.get("id") or kwargs.get(f"{resource_type}_id")
                before_state = await get_resource_state(resource_type, resource_id)
            else:
                before_state = None
            
            # Execute the actual operation
            result = await func(*args, **kwargs)
            
            # Capture after state if CREATE or UPDATE
            if action in ["CREATE", "UPDATE"]:
                after_state = result if isinstance(result, dict) else result.__dict__
                resource_id = result.id if hasattr(result, "id") else None
            else:
                after_state = None
                resource_id = kwargs.get("id")
            
            # Create audit log entry
            audit_entry = AuditLog(
                actor_id=actor.id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                resource_identifier=get_resource_identifier(result),
                before_state=sanitize_state(before_state),
                after_state=sanitize_state(after_state),
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent"),
                reason=kwargs.get("reason")
            )
            db.add(audit_entry)
            db.commit()
            
            return result
        
        return wrapper
    return decorator

# Usage example
@audit_action("UPDATE", "instructor")
async def update_instructor_role(
    instructor_id: int,
    new_role: str,
    reason: str,
    current_user: Instructor = Depends(get_current_admin),
    db: DBSession = Depends(get_db)
):
    instructor = db.query(Instructor).filter_by(id=instructor_id).first()
    if not instructor:
        raise HTTPException(404, "Instructor not found")
    
    instructor.role = new_role
    instructor.role_granted_by = current_user.id
    instructor.role_granted_at = datetime.utcnow()
    db.commit()
    
    return instructor
```

**API Endpoints**:
```
GET /api/admin/audit/logs
  Query params: actor_id, resource_type, resource_id, action, start_date, end_date, page
  Returns: Paginated audit trail

GET /api/admin/audit/logs/{log_id}
  Returns: Detailed audit entry with before/after diff

GET /api/admin/audit/resource/{resource_type}/{resource_id}
  Returns: Complete history of changes for a resource

GET /api/admin/audit/actor/{instructor_id}
  Returns: All actions performed by an actor

POST /api/admin/audit/export
  Body: {filters...}
  Returns: CSV export of audit logs (for compliance reporting)
```

---

### 3. Security Dashboard

**User Story**: As an admin, I want a real-time dashboard showing security events so I can quickly identify and respond to threats.

**Requirements**:
- [ ] Real-time event stream (WebSocket)
- [ ] Failed login visualization (chart over time)
- [ ] Active sessions map (geographic distribution)
- [ ] Recent security events feed
- [ ] Suspicious activity alerts (highlighted)
- [ ] Quick actions: unlock account, revoke sessions
- [ ] Filterable by event type, instructor, time range

**Implementation**:
```python
# WebSocket endpoint for real-time events
@app.websocket("/ws/admin/security-feed")
async def security_event_feed(
    websocket: WebSocket,
    token: str = Query(...),
    db: DBSession = Depends(get_db)
):
    # Verify admin token
    admin = await verify_admin_websocket(token, db)
    if not admin:
        await websocket.close(code=1008)
        return
    
    await websocket.accept()
    
    try:
        # Subscribe to security events
        async for event in security_event_stream():
            await websocket.send_json({
                "id": event.id,
                "type": event.event_type,
                "timestamp": event.timestamp.isoformat(),
                "instructor": event.instructor.username if event.instructor else None,
                "ip_address": event.ip_address,
                "success": event.success,
                "metadata": event.metadata
            })
    except WebSocketDisconnect:
        pass

# API endpoints for dashboard data
GET /api/admin/security/dashboard/summary
  Returns: {
    "failed_logins_24h": 12,
    "active_sessions": 45,
    "locked_accounts": 2,
    "suspicious_activities": 1,
    "recent_events": [...]
  }

GET /api/admin/security/dashboard/failed-logins-chart
  Query params: start_date, end_date, granularity (hour/day)
  Returns: Time series data for charting

GET /api/admin/security/dashboard/geo-map
  Returns: [{"country": "US", "count": 34, "lat": 37.7749, "lng": -122.4194}, ...]

GET /api/admin/security/dashboard/suspicious-activities
  Returns: List of flagged activities with severity scores
```

**Frontend Components**:
- `SecurityDashboard.js` - Main dashboard page
- `SecurityEventFeed.js` - Real-time event stream component
- `FailedLoginsChart.js` - Time series chart
- `ActiveSessionsMap.js` - Geographic map with IP locations
- `SuspiciousActivityList.js` - Alerts list with actions

---

### 4. Alerting System

**User Story**: As a security administrator, I want to receive alerts for critical security events so I can respond immediately to potential threats.

**Requirements**:
- [ ] Configurable alert rules (admin UI)
- [ ] Alert channels: in-app notifications, email, webhook
- [ ] Built-in rule templates: repeated failures, new device login, role elevation, geo-anomaly
- [ ] Custom rules with SQL-like conditions
- [ ] Alert aggregation (don't spam on repeated events)
- [ ] Alert acknowledgment and resolution workflow

**Implementation**:
```python
# Database models
class AlertRule(Base):
    """Configurable security alert rules"""
    __tablename__ = "alert_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    enabled = Column(Boolean, default=True, index=True)
    event_type = Column(String, nullable=True, index=True)  # Filter by event type
    conditions = Column(JSON, nullable=False)  # Rule conditions
    severity = Column(String, nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    notification_channels = Column(JSON, nullable=False)  # ["email", "webhook"]
    notification_config = Column(JSON, nullable=True)  # Channel-specific config
    aggregation_window_minutes = Column(Integer, default=5)  # Dedup window
    created_by = Column(Integer, ForeignKey("instructors.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    creator = relationship("Instructor")
    alerts = relationship("SecurityAlert", back_populates="rule")

class SecurityAlert(Base):
    """Triggered security alerts"""
    __tablename__ = "security_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey("alert_rules.id", ondelete="CASCADE"), nullable=False, index=True)
    triggered_at = Column(DateTime, default=datetime.utcnow, index=True)
    severity = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    event_ids = Column(JSON, nullable=True)  # Related SecurityLog IDs
    metadata = Column(JSON, nullable=True)
    acknowledged = Column(Boolean, default=False, index=True)
    acknowledged_by = Column(Integer, ForeignKey("instructors.id"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved = Column(Boolean, default=False, index=True)
    resolved_by = Column(Integer, ForeignKey("instructors.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    rule = relationship("AlertRule", back_populates="alerts")
    acknowledger = relationship("Instructor", foreign_keys=[acknowledged_by])
    resolver = relationship("Instructor", foreign_keys=[resolved_by])

# Built-in alert rule templates
DEFAULT_ALERT_RULES = [
    {
        "name": "Repeated Failed Logins",
        "description": "5+ failed login attempts within 5 minutes for same account",
        "event_type": "failed_login",
        "conditions": {
            "count": 5,
            "window_minutes": 5,
            "group_by": "instructor_id"
        },
        "severity": "HIGH",
        "notification_channels": ["email", "in_app"]
    },
    {
        "name": "New Device Login",
        "description": "Login from previously unseen user agent",
        "event_type": "login",
        "conditions": {
            "new_user_agent": True,
            "role": ["ADMIN", "SUPER_ADMIN"]
        },
        "severity": "MEDIUM",
        "notification_channels": ["email", "in_app"]
    },
    {
        "name": "Role Elevation",
        "description": "Instructor role changed to ADMIN or SUPER_ADMIN",
        "event_type": "role_change",
        "conditions": {
            "new_role": ["ADMIN", "SUPER_ADMIN"]
        },
        "severity": "HIGH",
        "notification_channels": ["email", "webhook"]
    },
    {
        "name": "Geographic Anomaly",
        "description": "Login from country different than last 10 logins",
        "event_type": "login",
        "conditions": {
            "geo_anomaly": True,
            "threshold_distance_km": 1000
        },
        "severity": "MEDIUM",
        "notification_channels": ["email"]
    }
]

# Alert evaluation engine
async def check_alert_rules(security_log: SecurityLog):
    """Check if any alert rules are triggered by this event"""
    rules = db.query(AlertRule).filter_by(
        enabled=True,
        event_type=security_log.event_type
    ).all()
    
    for rule in rules:
        if await evaluate_rule(rule, security_log):
            # Check if already alerted recently (aggregation)
            recent_alert = db.query(SecurityAlert).filter(
                SecurityAlert.rule_id == rule.id,
                SecurityAlert.triggered_at > datetime.utcnow() - timedelta(minutes=rule.aggregation_window_minutes)
            ).first()
            
            if not recent_alert:
                await create_alert(rule, security_log)

async def evaluate_rule(rule: AlertRule, event: SecurityLog) -> bool:
    """Evaluate if rule conditions match event"""
    conditions = rule.conditions
    
    # Count-based rule
    if "count" in conditions:
        window = timedelta(minutes=conditions["window_minutes"])
        events = db.query(SecurityLog).filter(
            SecurityLog.event_type == rule.event_type,
            SecurityLog.instructor_id == event.instructor_id,
            SecurityLog.timestamp > datetime.utcnow() - window
        ).count()
        
        if events >= conditions["count"]:
            return True
    
    # New user agent rule
    if conditions.get("new_user_agent"):
        previous = db.query(SecurityLog).filter(
            SecurityLog.instructor_id == event.instructor_id,
            SecurityLog.user_agent == event.user_agent,
            SecurityLog.id < event.id
        ).first()
        
        if not previous:
            return True
    
    # Role change rule
    if "new_role" in conditions and event.metadata:
        new_role = event.metadata.get("new_role")
        if new_role in conditions["new_role"]:
            return True
    
    return False

async def create_alert(rule: AlertRule, event: SecurityLog):
    """Create and send security alert"""
    alert = SecurityAlert(
        rule_id=rule.id,
        severity=rule.severity,
        title=f"Security Alert: {rule.name}",
        message=f"{rule.description}\nEvent ID: {event.id}",
        event_ids=[event.id],
        metadata={
            "instructor_id": event.instructor_id,
            "ip_address": event.ip_address,
            "timestamp": event.timestamp.isoformat()
        }
    )
    db.add(alert)
    db.commit()
    
    # Send notifications
    for channel in rule.notification_channels:
        if channel == "email":
            await send_alert_email(alert, rule)
        elif channel == "webhook":
            await send_alert_webhook(alert, rule)
        elif channel == "in_app":
            await send_in_app_notification(alert)
```

**API Endpoints**:
```
GET /api/admin/security/alerts
  Query params: severity, acknowledged, resolved, page
  Returns: Paginated list of alerts

GET /api/admin/security/alerts/{alert_id}
  Returns: Detailed alert information

POST /api/admin/security/alerts/{alert_id}/acknowledge
  Body: {}
  Returns: Acknowledged alert

POST /api/admin/security/alerts/{alert_id}/resolve
  Body: {"notes": "False positive - training exercise"}
  Returns: Resolved alert

GET /api/admin/security/alert-rules
  Returns: List of alert rules

POST /api/admin/security/alert-rules
  Body: {rule definition}
  Returns: Created rule

PUT /api/admin/security/alert-rules/{rule_id}
  Body: {updated fields}
  Returns: Updated rule
```

---

### 5. API Key Monitoring

**User Story**: As a system, I want to detect compromised API keys so I can automatically revoke them before damage occurs.

**Requirements**:
- [ ] Track API key usage patterns (IP addresses, request frequency, endpoints)
- [ ] Detect anomalies: multiple IPs simultaneously, sudden spike in requests, unusual endpoints
- [ ] Automatic alert on suspected compromise
- [ ] Optional: automatic revocation with email notification
- [ ] API key usage dashboard for instructors

**Implementation**:
```python
# Database model
class APIKeyUsageLog(Base):
    """Track API key usage for anomaly detection"""
    __tablename__ = "api_key_usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    ip_address = Column(String, nullable=False, index=True)
    endpoint = Column(String, nullable=False)
    method = Column(String, nullable=False)
    response_status = Column(Integer, nullable=False)
    request_count = Column(Integer, default=1)  # Aggregated count per minute
    
    api_key = relationship("APIKey")
    
    __table_args__ = (
        Index('ix_api_key_usage_key_timestamp', 'api_key_id', 'timestamp'),
    )

# Usage tracking middleware
@app.middleware("http")
async def track_api_key_usage(request: Request, call_next):
    response = await call_next(request)
    
    # Check if request used API key
    api_key = request.state.get("api_key")
    if api_key:
        # Aggregate by minute to reduce storage
        minute_timestamp = datetime.utcnow().replace(second=0, microsecond=0)
        
        usage_log = db.query(APIKeyUsageLog).filter_by(
            api_key_id=api_key.id,
            timestamp=minute_timestamp,
            ip_address=request.client.host,
            endpoint=request.url.path,
            method=request.method
        ).first()
        
        if usage_log:
            usage_log.request_count += 1
        else:
            usage_log = APIKeyUsageLog(
                api_key_id=api_key.id,
                timestamp=minute_timestamp,
                ip_address=request.client.host,
                endpoint=request.url.path,
                method=request.method,
                response_status=response.status_code,
                request_count=1
            )
            db.add(usage_log)
        
        db.commit()
        
        # Check for anomalies
        await check_api_key_anomalies(api_key, request.client.host)
    
    return response

async def check_api_key_anomalies(api_key: APIKey, current_ip: str):
    """Detect suspicious API key usage"""
    # Check 1: Multiple IPs in last 5 minutes
    recent_ips = db.query(APIKeyUsageLog.ip_address).filter(
        APIKeyUsageLog.api_key_id == api_key.id,
        APIKeyUsageLog.timestamp > datetime.utcnow() - timedelta(minutes=5)
    ).distinct().all()
    
    if len(recent_ips) > 3:
        await create_security_alert(
            "API Key Compromise Suspected",
            f"API key {api_key.name} used from {len(recent_ips)} different IPs in 5 minutes",
            severity="HIGH",
            metadata={"api_key_id": api_key.id, "ips": recent_ips}
        )
    
    # Check 2: Sudden spike in requests
    current_minute_requests = db.query(func.sum(APIKeyUsageLog.request_count)).filter(
        APIKeyUsageLog.api_key_id == api_key.id,
        APIKeyUsageLog.timestamp == datetime.utcnow().replace(second=0, microsecond=0)
    ).scalar() or 0
    
    if current_minute_requests > 100:  # Threshold
        await create_security_alert(
            "API Key Request Spike",
            f"API key {api_key.name} made {current_minute_requests} requests in last minute",
            severity="MEDIUM",
            metadata={"api_key_id": api_key.id, "request_count": current_minute_requests}
        )
```

---

## Database Migration

See separate migration file: `alembic/versions/security_monitoring_v1.py`

---

## Testing Checklist

### Unit Tests
- [ ] SecurityLog creation and querying
- [ ] AuditLog creation with before/after snapshots
- [ ] Alert rule evaluation logic
- [ ] API key anomaly detection

### Integration Tests
- [ ] Security events logged on all authentication actions
- [ ] Audit logs created on admin CRUD operations
- [ ] Alerts triggered and sent via configured channels
- [ ] WebSocket real-time event streaming
- [ ] Dashboard API endpoints return correct data

### Performance Tests
- [ ] Security log ingestion rate (target: 1000 events/sec)
- [ ] Audit log query performance on large datasets
- [ ] Alert rule evaluation latency (<100ms)
- [ ] Dashboard load time with 10k events

---

## Documentation

- [ ] Admin guide: Configuring alert rules
- [ ] API documentation: Security and audit endpoints
- [ ] Monitoring guide: Reading security dashboards
- [ ] Incident response playbook

---

## Dependencies

- `geoip2==4.7.0` - IP geolocation
- `user-agents==2.2.0` - User agent parsing
- No additional frontend dependencies (use existing Chart.js, Leaflet)

---

## Success Metrics

- [ ] 100% of security events logged
- [ ] <1 second latency for alert notifications
- [ ] Zero data loss in audit logs
- [ ] Dashboard loads in <2 seconds with 10k events
