from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, Request, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session as DBSession, joinedload, selectinload
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List, Optional
import json
import qrcode
from io import BytesIO
import csv
from io import StringIO
import os
from dotenv import load_dotenv
import pytz
import secrets
import hmac
import hashlib
import logging
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from jose import JWTError, jwt
from passlib.context import CryptContext

# Load environment variables from .env file
load_dotenv()

from database import get_db, init_db
from config import settings
from security import (
    pwd_context,
    verify_password,
    get_password_hash,
    create_access_token,
    verify_jwt_token,
    generate_csrf_token,
    verify_csrf_token
)
# V2 Models
from models_v2 import (
    ClassMeeting as Session,  # Alias for backward compat with old endpoints
    Question,
    APIKey,
    Instructor,
    Class,
    Answer,
    QuestionVote
)
# V2 Schemas
from schemas_v2 import (
    ClassMeetingCreate as SessionCreate,
    ClassMeetingResponse as SessionResponse,
    QuestionCreate,
    QuestionResponse,
    ClassMeetingWithQuestions as SessionWithQuestions,
    AdminLogin,
    Token,
    SessionPasswordVerify,
    APIKeyCreate,
    APIKeyResponse,
    APIKeyMaskedResponse,
    APIKeyRevocationRequest,
    InstructorAuth
)

# Import v2 route modules
from routes_instructor import router as instructor_router
from routes_classes import router as classes_router
from routes_questions import router as questions_router
from routes_answers import router as answers_router
from routes_admin import router as admin_router
from routes_admin_users import router as admin_users_router
from routes_config import router as config_router, set_manager
from logging_config import setup_logging, get_logger, log_request, log_database_operation, log_websocket_event, log_security_event

# Configure centralized logging
setup_logging()
logger = get_logger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="RaiseMyHand - Student Question Aggregator")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Include v2 routers
app.include_router(instructor_router)
app.include_router(classes_router)
app.include_router(questions_router)
app.include_router(answers_router)
app.include_router(admin_router)
app.include_router(admin_users_router)
app.include_router(config_router)


@app.get("/api/system/status")
async def system_status(db: DBSession = Depends(get_db)):
    """Get system status including maintenance mode."""
    from models_config import SystemConfig
    
    maintenance_mode = SystemConfig.get_value(db, "system_maintenance_mode", default=False)
    profanity_filter = SystemConfig.get_value(db, "profanity_filter_enabled", default=True)
    registration_enabled = SystemConfig.get_value(db, "instructor_registration_enabled", default=True)
    
    return {
        "maintenance_mode": maintenance_mode,
        "profanity_filter_enabled": profanity_filter,
        "registration_enabled": registration_enabled
    }


# Security Configuration
security = HTTPBearer(auto_error=False)

# Validate production configuration
if settings.is_production:
    errors, warnings = settings.validate_production_config()
    if errors:
        for error in errors:
            logger.error(f"Production config error: {error}")
        raise ValueError(f"Production configuration errors: {'; '.join(errors)}")
    if warnings:
        for warning in warnings:
            logger.warning(f"Production config warning: {warning}")

# Initialize timezone
try:
    LOCAL_TZ = pytz.timezone(settings.timezone)
except pytz.exceptions.UnknownTimeZoneError:
    logger.warning(f"Unknown timezone '{settings.timezone}', falling back to UTC")
    LOCAL_TZ = pytz.UTC


# API Key verification (specific to this app, not in security.py)
def verify_api_key(api_key: Optional[str], db) -> bool:
    """Verify API key and update last_used timestamp."""
    if not api_key:
        log_security_event(logger, "INVALID_API_KEY", "API key missing", severity="warning")
        return False

    key_record = db.query(APIKey).filter(
        APIKey.key == api_key,
        APIKey.is_active == True
    ).first()

    if key_record:
        # Update last_used timestamp
        key_record.last_used = datetime.utcnow()
        db.commit()
        log_database_operation(logger, "UPDATE", "api_keys", key_record.id, success=True)
        return True

    log_security_event(logger, "INVALID_API_KEY", f"API key not found or inactive: {api_key[:10]}...", severity="warning")
    return False


def get_api_key(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: DBSession = Depends(get_db)
) -> str:
    """
    Extract and verify API key from Authorization header or query parameter (deprecated).
    Preferred: Authorization: Bearer <api_key>
    Fallback: ?api_key=<api_key> (for backward compatibility, will be removed in future versions)
    """
    api_key = None

    # Try to get from Authorization header (preferred)
    if credentials:
        api_key = credentials.credentials

    # Fallback to query parameter (deprecated but supported for backward compatibility)
    if not api_key:
        api_key = request.query_params.get('api_key')
        if api_key:
            print("Warning: API key in query parameter is deprecated. Use Authorization header instead.")

    # Verify the API key
    if not api_key or not verify_api_key(api_key, db):
        raise HTTPException(
            status_code=401,
            detail="Invalid or inactive API key",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return api_key


# CSRF token dependency helper
def get_csrf_token(x_csrf_token: Optional[str] = Header(None)) -> str:
    """
    Dependency to extract and verify CSRF token from X-CSRF-Token header.
    """
    if not x_csrf_token or not verify_csrf_token(x_csrf_token):
        raise HTTPException(
            status_code=403,
            detail="Invalid or missing CSRF token"
        )
    return x_csrf_token


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[str]:
    """Verify JWT token and return username if valid."""
    if not settings.enable_auth:
        return "admin"  # Skip auth if disabled

    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Timezone utility function
def to_local_time(utc_dt: datetime) -> str:
    """Convert UTC datetime to local timezone and return ISO format string."""
    if utc_dt is None:
        return None
    # Ensure the datetime is timezone-aware (UTC)
    if utc_dt.tzinfo is None:
        utc_dt = pytz.UTC.localize(utc_dt)
    # Convert to local timezone
    local_dt = utc_dt.astimezone(LOCAL_TZ)
    return local_dt.isoformat()


def format_session_response(session: Session) -> dict:
    """Format a session object for API response."""
    return {
        "id": session.id,
        "session_code": session.meeting_code,
        "instructor_code": session.instructor_code,
        "title": session.title,
        "has_password": session.password_hash is not None,
        "created_at": session.created_at,
        "ended_at": session.ended_at,
        "is_active": session.is_active,
        "questions": [
            {
                "id": q.id,
                "meeting_id": q.meeting_id,
                "text": q.text,
                "upvotes": q.upvotes,
                "is_answered": q.is_answered,
                "created_at": q.created_at,
                "answered_at": q.answered_at,
                "question_number": q.question_number
            }
            for q in session.questions
        ]
    }


# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    """Initialize application on startup"""

    # Validate configuration
    from config import settings

    print("\n" + "="*70)
    print(f"🚀 RaiseMyHand Starting - Environment: {settings.env.upper()}")
    print("="*70)

    # Check production configuration
    if settings.is_production:
        errors, warnings = settings.validate_production_config()

        if errors:
            print("\n❌ CRITICAL CONFIGURATION ERRORS:")
            for error in errors:
                print(f"   • {error}")
            print("\n⚠️  Application may not be secure in production!")
            print("="*70 + "\n")

        if warnings:
            print("\n⚠️  CONFIGURATION WARNINGS:")
            for warning in warnings:
                print(f"   • {warning}")
            print()
    else:
        print(f"✓ Running in {settings.env} mode")
        print(f"✓ Debug mode: {settings.debug}")
        print(f"✓ Base URL: {settings.base_url}")

    print("="*70)

    # Initialize database
    init_db()

    # Check if any API keys exist
    db = next(get_db())
    try:
        key_count = db.query(APIKey).count()
        if key_count == 0:
            print("\n" + "="*70)
            print("⚠️  WARNING: No API keys found in database!")
            print("="*70)
            print("Instructors need an API key to create sessions.")
            print("\nTo create a default API key, run:")
            print("  python init_database.py --create-key")
            print("\nOr create one via the admin panel:")
            print("  1. Go to http://localhost:8000/admin-login")
            print("  2. Login with your admin credentials")
            print("  3. Create an API key in the 'API Keys' section")
            print("="*70 + "\n")
        else:
            print(f"\n✓ Database initialized with {key_count} API key(s)\n")
    finally:
        db.close()


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}
        # Rate limiting: track message counts per connection
        self.message_counts: dict[WebSocket, list[float]] = {}
        # Connection timestamps for timeout tracking
        self.connection_times: dict[WebSocket, float] = {}

    async def connect(self, websocket: WebSocket, session_code: str):
        await websocket.accept()
        if session_code not in self.active_connections:
            self.active_connections[session_code] = []
        self.active_connections[session_code].append(websocket)
        # Initialize rate limiting and timeout tracking
        self.message_counts[websocket] = []
        self.connection_times[websocket] = datetime.utcnow().timestamp()
        log_websocket_event(logger, "CONNECT", session_code, f"Active connections: {len(self.active_connections[session_code])}")

    def disconnect(self, websocket: WebSocket, session_code: str):
        if session_code in self.active_connections:
            if websocket in self.active_connections[session_code]:
                self.active_connections[session_code].remove(websocket)
            remaining = len(self.active_connections[session_code])
            if not self.active_connections[session_code]:
                del self.active_connections[session_code]
            log_websocket_event(logger, "DISCONNECT", session_code, f"Remaining connections: {remaining}")
        # Clean up rate limiting data
        if websocket in self.message_counts:
            del self.message_counts[websocket]
        if websocket in self.connection_times:
            del self.connection_times[websocket]

    def check_rate_limit(self, websocket: WebSocket, max_messages: int = 10, window_seconds: int = 1) -> bool:
        """
        Check if a WebSocket connection is within rate limits.
        Returns True if within limits, False if rate limit exceeded.
        """
        current_time = datetime.utcnow().timestamp()

        # Clean old timestamps outside the window
        if websocket in self.message_counts:
            self.message_counts[websocket] = [
                ts for ts in self.message_counts[websocket]
                if current_time - ts < window_seconds
            ]

            # Check if limit exceeded
            if len(self.message_counts[websocket]) >= max_messages:
                return False

            # Add current timestamp
            self.message_counts[websocket].append(current_time)

        return True

    def check_connection_timeout(self, websocket: WebSocket, timeout_seconds: int = 3600) -> bool:
        """
        Check if a WebSocket connection has been idle too long.
        Returns True if connection should be closed, False if still valid.
        """
        if websocket in self.connection_times:
            current_time = datetime.utcnow().timestamp()
            elapsed = current_time - self.connection_times[websocket]
            return elapsed > timeout_seconds
        return False

    def update_activity(self, websocket: WebSocket):
        """Update the last activity timestamp for a connection."""
        self.connection_times[websocket] = datetime.utcnow().timestamp()

    async def broadcast(self, message: dict, session_code: str):
        if session_code in self.active_connections:
            disconnected = []
            for connection in self.active_connections[session_code]:
                try:
                    await connection.send_json(message)
                except (WebSocketDisconnect, RuntimeError, ConnectionError) as e:
                    logger.warning(f"WebSocket connection error for session {session_code}: {e}")
                    disconnected.append(connection)

            # Clean up disconnected clients
            for conn in disconnected:
                self.disconnect(conn, session_code)

    async def broadcast_to_all(self, message: dict):
        """Broadcast message to all active connections across all sessions."""
        logger.info(f"[BROADCAST_TO_ALL] Starting broadcast. Active sessions: {list(self.active_connections.keys())}")
        disconnected = []
        sent_count = 0
        for session_code, connections in self.active_connections.items():
            logger.info(f"[BROADCAST_TO_ALL] Session '{session_code}' has {len(connections)} connections")
            for connection in connections:
                try:
                    await connection.send_json(message)
                    sent_count += 1
                except (WebSocketDisconnect, RuntimeError, ConnectionError) as e:
                    logger.warning(f"WebSocket connection error for session {session_code}: {e}")
                    disconnected.append((connection, session_code))

        # Clean up disconnected clients
        for conn, session_code in disconnected:
            self.disconnect(conn, session_code)
        
        logger.info(f"[BROADCAST_TO_ALL] Broadcast complete. Sent to {sent_count} connections, {len(disconnected)} failed")


manager = ConnectionManager()

# Pass manager to routes_config for broadcasting
set_manager(manager)


# Session endpoints






@app.post("/api/sessions/{instructor_code}/restart")
@limiter.limit("10/minute")
def restart_session(
    request: Request,
    instructor_code: str,
    api_key: str = Depends(get_api_key),
    csrf_token: str = Depends(get_csrf_token),
    db: DBSession = Depends(get_db)
):
    """Restart an ended session (requires valid API key and CSRF token)."""
    from security import check_maintenance_mode
    
    # Check maintenance mode (admins exempt)
    if check_maintenance_mode(db):
        raise HTTPException(
            status_code=503,
            detail="System is currently in maintenance mode. Sessions cannot be restarted at this time."
        )
    
    try:
        # API key and CSRF token are already verified by the dependencies
        session = db.query(Session).filter(Session.instructor_code == instructor_code).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        session.is_active = True
        session.ended_at = None
        db.commit()
        return {"message": "Session restarted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to restart session: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to restart session. Please try again.")


# Question endpoints
async def create_question(session_code: str, question: QuestionCreate, db: DBSession = Depends(get_db)):
    """Submit a new question to a session."""
    session = db.query(Session).filter(Session.meeting_code == session_code, Session.is_active == True).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or inactive")

    # Retry logic to handle race conditions with unique constraint
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Get the next question number for this session with a lock
            # Use SELECT FOR UPDATE to prevent concurrent reads
            max_number = db.query(func.max(Question.question_number))\
                .filter(Question.meeting_id == session.id)\
                .with_for_update()\
                .scalar()
            next_number = (max_number or 0) + 1

            db_question = Question(
                meeting_id=session.id,
                question_number=next_number,
                text=question.text
            )
            db.add(db_question)
            db.commit()
            db.refresh(db_question)
            break  # Success, exit retry loop
        except Exception as e:
            db.rollback()
            # Check if it's a unique constraint violation
            if "unique constraint" in str(e).lower() or "duplicate" in str(e).lower():
                if attempt < max_retries - 1:
                    # Retry with a new number
                    continue
                else:
                    # Max retries exceeded
                    logger.error(f"Failed to create question after {max_retries} attempts: {e}")
                    raise HTTPException(status_code=500, detail="Failed to create question due to concurrent submissions")
            else:
                # Different error, don't retry
                logger.error(f"Error creating question: {e}")
                raise HTTPException(status_code=500, detail="Failed to create question")

    # Broadcast new question to all connected clients
    await manager.broadcast({
        "type": "new_question",
        "question": {
            "id": db_question.id,
            "question_number": db_question.question_number,
            "text": db_question.text,
            "upvotes": db_question.upvotes,
            "is_answered": db_question.is_answered,
            "created_at": db_question.created_at.isoformat()
        }
    }, session_code)

    return db_question


# Keep old endpoint for backwards compatibility
@app.post("/api/questions/{question_id}/upvote")
async def upvote_question(question_id: int, db: DBSession = Depends(get_db)):
    """Upvote a question (deprecated - use /vote instead)."""
    return await toggle_vote(question_id, "add", db)


# QR Code generation
# Public stats endpoint - no authentication required
@app.get("/api/sessions/{session_code}/stats")
@limiter.limit("30/minute")
async def get_session_stats(request: Request, session_code: str, db: DBSession = Depends(get_db)):
    """Get public stats for a session - question count, answered count, votes per question (no text)."""
    session = db.query(Session).filter(Session.meeting_code == session_code).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    questions = db.query(Question).filter(Question.meeting_id == session.id).all()

    stats = {
        "session_title": session.title,
        "session_code": session.meeting_code,
        "is_active": session.is_active,
        "created_at": session.created_at.isoformat(),
        "ended_at": session.ended_at.isoformat() if session.ended_at else None,
        "total_questions": len(questions),
        "answered_questions": sum(1 for q in questions if q.is_answered_in_class),
        "unanswered_questions": sum(1 for q in questions if not q.is_answered_in_class),
        "total_votes": sum(q.upvotes for q in questions),
        "questions_by_votes": [
            {
                "question_id": q.id,
                "question_number": q.question_number,
                "votes": q.upvotes,
                "answered": q.is_answered_in_class,
                "created_at": q.created_at.isoformat(),
                "answered_at": None  # v2 model doesn't have answered_at, only reviewed_at
            }
            for q in sorted(questions, key=lambda x: x.upvotes, reverse=True)
        ]
    }
    
    return stats


@app.get("/stats", response_class=HTMLResponse)
async def stats_page(request: Request):
    """Public stats page."""
    return templates.TemplateResponse("stats.html", {"request": request, "base_url": settings.base_url})


# WebSocket endpoint
@app.websocket("/ws/{session_code}")
async def websocket_endpoint(websocket: WebSocket, session_code: str, db: DBSession = Depends(get_db)):
    """
    WebSocket endpoint for real-time updates.
    Validates session existence and enforces rate limiting.
    Special code 'system' is for system-wide broadcasts (maintenance mode, etc.).
    """
    # Special handling for system-wide connection
    if session_code == "system":
        logger.info("WebSocket connection for system-wide updates")
        await manager.connect(websocket, session_code)
        try:
            while True:
                message = await websocket.receive_text()
                if message.strip().lower() in ["ping", "keepalive"]:
                    await websocket.send_json({"type": "pong"})
        except WebSocketDisconnect:
            manager.disconnect(websocket, session_code)
            logger.info("System WebSocket disconnected")
        return
    
    try:
        # Validate that the session exists and is active BEFORE accepting connection
        logger.info(f"WebSocket validation: checking session code {session_code}")
        session = db.query(Session).filter(Session.meeting_code == session_code).first()
        logger.info(f"WebSocket validation: query returned session={session}")
    except Exception as e:
        logger.error(f"WebSocket validation error: {e}", exc_info=True)
        await websocket.accept()
        await websocket.send_json({"type": "error", "message": "Internal server error"})
        await websocket.close(code=1011, reason="Internal error")
        return

    if not session:
        logger.warning(f"WebSocket connection rejected: invalid session code {session_code}")
        await websocket.accept()
        await websocket.send_json({"type": "error", "message": "Session not found"})
        await websocket.close(code=4004, reason="Session not found")
        return

    if not session.is_active:
        logger.warning(f"WebSocket connection rejected: inactive session {session_code}")
        await websocket.accept()
        await websocket.send_json({"type": "error", "message": "Session is not active"})
        await websocket.close(code=4003, reason="Session is not active")
        return

    # Accept connection and register with manager
    await manager.connect(websocket, session_code)
    logger.info(f"WebSocket connected to session {session_code}")

    try:
        while True:
            # Receive messages (mostly ping/keepalive)
            message = await websocket.receive_text()

            # Update activity timestamp
            manager.update_activity(websocket)

            # Check rate limiting (10 messages per second)
            if not manager.check_rate_limit(websocket, max_messages=10, window_seconds=1):
                logger.warning(f"WebSocket rate limit exceeded for session {session_code}")
                await websocket.send_json({
                    "type": "error",
                    "message": "Rate limit exceeded. Please slow down."
                })
                continue

            # Check for connection timeout (1 hour of inactivity)
            if manager.check_connection_timeout(websocket, timeout_seconds=3600):
                logger.info(f"WebSocket timeout for session {session_code}")
                await websocket.close(code=1000, reason="Connection timeout due to inactivity")
                break

            # Echo ping/pong for keepalive
            if message.strip().lower() in ["ping", "keepalive"]:
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected from session {session_code}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_code}: {e}")
    finally:
        manager.disconnect(websocket, session_code)


# HTML page routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with marketing content."""
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/student-login", response_class=HTMLResponse)
async def student_login_view(request: Request):
    """Student login page - enter session code or scan QR."""
    return templates.TemplateResponse("student-login.html", {"request": request})


@app.get("/instructor-login", response_class=HTMLResponse)
async def instructor_login_view(request: Request):
    """Instructor login page - enter API key or create session."""
    return templates.TemplateResponse("instructor-login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
async def register_view(request: Request, db: DBSession = Depends(get_db)):
    """Instructor registration page."""
    from models_config import SystemConfig
    
    # Check if registration is enabled
    registration_enabled = SystemConfig.get_value(db, "instructor_registration_enabled", default=True)
    disabled_reason = SystemConfig.get_value(db, "instructor_registration_disabled_reason", default="Registration is currently disabled")
    
    return templates.TemplateResponse("register.html", {
        "request": request,
        "registration_enabled": registration_enabled,
        "disabled_reason": disabled_reason
    })


@app.get("/instructor", response_class=HTMLResponse)
async def instructor_view(request: Request):
    """Instructor dashboard (authentication handled by frontend JavaScript)."""
    return templates.TemplateResponse("instructor.html", {"request": request})


@app.get("/student", response_class=HTMLResponse)
async def student_view(request: Request):
    """Student question submission page."""
    return templates.TemplateResponse("student.html", {"request": request})


@app.get("/sessions", response_class=HTMLResponse)
async def sessions_dashboard(request: Request):
    """Sessions dashboard - view all sessions for an API key."""
    return templates.TemplateResponse("sessions.html", {"request": request})


@app.get("/classes", response_class=HTMLResponse)
async def classes_dashboard(request: Request):
    """Classes dashboard - manage instructor classes."""
    return templates.TemplateResponse("classes.html", {"request": request})


@app.get("/profile", response_class=HTMLResponse)
async def profile_view(request: Request):
    """Instructor profile page - edit personal information (authentication handled by frontend)."""
    return templates.TemplateResponse("profile.html", {"request": request})


# API Key Management endpoints (admin only)
@app.post("/api/admin/api-keys", response_model=APIKeyResponse)
@limiter.limit("10/minute")
def create_api_key(request: Request, key_data: APIKeyCreate, username: str = Depends(verify_token), db: DBSession = Depends(get_db)):
    """Create a new API key for instructor authentication (admin only, rate limited: 10/min)."""
    try:
        # In v2, API keys require an instructor_id
        # Create a placeholder instructor account for admin-created keys
        # The instructor can later register and claim this API key
        instructor_username = f"instructor_{secrets.token_urlsafe(8)}"
        instructor = Instructor(
            username=instructor_username,
            email=None,
            display_name=key_data.name,  # Use API key name as display name
            password_hash=pwd_context.hash(secrets.token_urlsafe(32)),  # Random password
            created_at=datetime.utcnow(),
            is_active=True
        )
        db.add(instructor)
        db.flush()  # Get instructor.id without committing

        # Create a default class for this instructor
        # This is required because meetings need a class_id in v2
        default_class = Class(
            instructor_id=instructor.id,
            name="Default Class",
            description="Auto-created default class for meetings",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            is_archived=False
        )
        db.add(default_class)
        db.flush()  # Get class.id without committing

        api_key = APIKey(
            instructor_id=instructor.id,
            key=APIKey.generate_key(),
            name=key_data.name
        )
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        return api_key
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create API key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create API key. Please try again.")

@app.get("/api/admin/api-keys", response_model=list[APIKeyMaskedResponse])
@limiter.limit("60/minute")
def list_api_keys(request: Request, reveal: bool = False, username: str = Depends(verify_token), db: DBSession = Depends(get_db)):
    """List all API keys (admin only, rate limited: 60/min).

    By default, returns masked keys with instructor information. Set reveal=true to show full keys (not recommended).
    """
    # Join with instructor table to get instructor details
    results = db.query(APIKey, Instructor).join(
        Instructor, APIKey.instructor_id == Instructor.id
    ).order_by(APIKey.created_at.desc()).all()

    if reveal:
        # For reveal=true, return full keys (still wrapped in masked response for consistency)
        # Admin explicitly requested to reveal - this should be logged
        log_security_event(logger, "API_KEYS_REVEALED", f"Admin {username} requested full API keys list", severity="warning")

    return [APIKeyMaskedResponse.from_api_key(key, instructor) for key, instructor in results]

@app.get("/api/admin/api-keys/{key_id}", response_model=APIKeyResponse)
@limiter.limit("30/minute")
def reveal_api_key(request: Request, key_id: int, username: str = Depends(verify_token), db: DBSession = Depends(get_db)):
    """Reveal the full API key (admin only, rate limited: 30/min).

    This endpoint returns the full, unmasked API key. Use with caution!
    """
    try:
        api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
        if not api_key:
            raise HTTPException(status_code=404, detail="API key not found")

        # Log the reveal action
        log_security_event(logger, "API_KEY_REVEALED", f"Admin {username} revealed API key {key_id}", severity="warning")

        return api_key
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reveal API key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to reveal API key. Please try again.")


@app.delete("/api/admin/api-keys/{key_id}")
@limiter.limit("20/minute")
def delete_api_key(request: Request, key_id: int, revocation_data: APIKeyRevocationRequest, username: str = Depends(verify_token), db: DBSession = Depends(get_db)):
    """Revoke an API key (admin only, rate limited: 20/min)."""
    try:
        api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
        if not api_key:
            raise HTTPException(status_code=404, detail="API key not found")

        # Get admin instructor record for tracking who revoked the key
        admin_instructor = db.query(Instructor).filter(Instructor.username == username).first()

        # Mark the API key as revoked with full audit tracking
        api_key.is_active = False
        api_key.revoked_at = datetime.utcnow()
        api_key.revocation_reason = revocation_data.reason
        if admin_instructor:
            api_key.revoked_by = admin_instructor.id

        db.commit()

        # Log the revocation event
        admin_identifier = admin_instructor.username if admin_instructor else username
        log_security_event(logger, "API_KEY_REVOKED", f"Admin {admin_identifier} revoked API key {key_id}: {revocation_data.reason}", severity="warning")

        return {"message": "API key revoked successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to revoke API key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to revoke API key. Please try again.")


@app.post("/api/admin/api-keys/{instructor_id}/regenerate")
@limiter.limit("10/minute")
def regenerate_api_key_admin(
    request: Request,
    instructor_id: int,
    regeneration_data: APIKeyRevocationRequest,
    username: str = Depends(verify_token),
    db: DBSession = Depends(get_db)
):
    """
    Regenerate an API key for an instructor (admin only, rate limited: 10/min).

    This will:
    1. Revoke all existing active API keys for the instructor
    2. Generate a new API key
    3. Return the new key (unmasked, one-time view)
    """
    try:
        # Get the instructor
        instructor = db.query(Instructor).filter(Instructor.id == instructor_id).first()
        if not instructor:
            raise HTTPException(status_code=404, detail="Instructor not found")

        # Get admin instructor record for tracking
        # Note: Admin users (username="admin") may not have an instructor record
        admin_instructor = db.query(Instructor).filter(Instructor.username == username).first()

        # Use admin instructor ID if exists, otherwise use the target instructor's ID
        # (for audit trail when admin doesn't have instructor record)
        admin_id = admin_instructor.id if admin_instructor else instructor_id

        # Import APIKeyService
        from services.api_key_service import APIKeyService

        # Regenerate the API key
        reason = f"Admin regenerated: {regeneration_data.reason}"
        new_key = APIKeyService.regenerate_api_key(
            instructor=instructor,
            reason=reason,
            revoked_by_id=admin_id,
            db=db
        )

        # Log the regeneration event
        admin_identifier = admin_instructor.username if admin_instructor else username
        log_security_event(
            logger,
            "API_KEY_ADMIN_REGENERATED",
            f"Admin {admin_identifier} regenerated API key for instructor {instructor.username}: {regeneration_data.reason}",
            severity="warning"
        )

        return {
            "message": "API key regenerated successfully",
            "api_key": {
                "id": new_key.id,
                "key": new_key.key,  # Return unmasked key (one-time view)
                "name": new_key.name,
                "created_at": new_key.created_at,
                "is_active": new_key.is_active
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to regenerate API key: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to regenerate API key. Please try again.")

@app.post("/api/instructor/auth")
def instructor_auth(auth_data: InstructorAuth, db: DBSession = Depends(get_db)):
    """Authenticate instructor with API key and return session cookie data."""
    if not verify_api_key(auth_data.api_key, db):
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")
    
    # Return success with API key validation
    return {"authenticated": True, "message": "API key is valid"}

# Authentication endpoints
@app.post("/api/admin/login", response_model=Token)
@limiter.limit("5/minute")
def admin_login(request: Request, login_data: AdminLogin):
    """Admin login endpoint."""
    if not settings.enable_auth:
        # If auth is disabled, always return a valid token
        access_token = create_access_token(data={"sub": "admin"})
        log_security_event(logger, "AUTH_DISABLED_LOGIN", "Admin login with auth disabled", severity="warning")
        return {"access_token": access_token, "token_type": "bearer"}

    # Verify admin credentials
    correct_username = secrets.compare_digest(login_data.username, settings.admin_username)
    correct_password = secrets.compare_digest(login_data.password, settings.admin_password or "")

    if not (correct_username and correct_password):
        log_security_event(
            logger,
            "AUTH_FAILED",
            f"Failed admin login attempt for user: {login_data.username} from {request.client.host if request.client else 'unknown'}",
            severity="warning"
        )
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )

    log_security_event(logger, "AUTH_SUCCESS", f"Admin login successful: {login_data.username}", severity="info")
    access_token = create_access_token(data={"sub": login_data.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/admin/verify")
@limiter.limit("60/minute")
def verify_admin_token(request: Request, username: str = Depends(verify_token)):
    """Verify if the current token is valid."""
    return {"username": username, "valid": True}


@app.get("/admin-login", response_class=HTMLResponse)
async def admin_login_view(request: Request):
    """Admin login page."""
    return templates.TemplateResponse("admin-login.html", {"request": request})

@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_view_alt(request: Request):
    """Admin login page (alternative route)."""
    return templates.TemplateResponse("admin-login.html", {"request": request})


@app.get("/admin/instructor-details", response_class=HTMLResponse)
async def admin_instructor_details_page(request: Request):
    """Admin instructor details page"""
    return templates.TemplateResponse("instructor-details.html", {"request": request})


@app.get("/admin", response_class=HTMLResponse)
async def admin_view(request: Request):
    """Admin dashboard (authentication handled by frontend JavaScript)."""
    return templates.TemplateResponse("admin.html", {"request": request})


# Health check
@app.get("/api/health")
def health_check():
    return {"status": "healthy"}


# Configuration endpoint
@app.get("/api/config")
def get_config():
    """Get client configuration including base URL, timezone, auth status, and environment."""
    return {
        "base_url": settings.base_url,
        "timezone": settings.timezone,
        "auth_enabled": settings.enable_auth,
        "environment": settings.env,
        "debug": settings.debug
    }


@app.get("/api/csrf-token")
def get_csrf_token_endpoint():
    """Generate and return a CSRF token for form submissions."""
    token = generate_csrf_token()
    return {"csrf_token": token}


# Admin API endpoints
@app.get("/api/admin/stats")
@limiter.limit("60/minute")
def get_admin_stats(request: Request, db: DBSession = Depends(get_db), username: str = Depends(verify_token)):
    """Get overall system statistics."""
    from sqlalchemy import func
    from datetime import timedelta

    total_sessions = db.query(func.count(Session.id)).scalar()
    active_sessions = db.query(func.count(Session.id)).filter(Session.is_active == True).scalar()
    total_questions = db.query(func.count(Question.id)).scalar()
    total_upvotes = db.query(func.sum(Question.upvotes)).scalar() or 0

    # Recent sessions (last 24 hours)
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_sessions = db.query(func.count(Session.id)).filter(Session.created_at >= yesterday).scalar()

    return {
        "total_sessions": total_sessions,
        "active_sessions": active_sessions,
        "ended_sessions": total_sessions - active_sessions,
        "total_questions": total_questions,
        "total_upvotes": total_upvotes,
        "sessions_last_24h": recent_sessions
    }


@app.get("/api/admin/sessions")
@limiter.limit("60/minute")
def get_all_sessions(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    active_only: bool = False,
    db: DBSession = Depends(get_db),
    username: str = Depends(verify_token)
):
    """Get all sessions with pagination."""
    from sqlalchemy import func

    query = db.query(Session)

    if active_only:
        query = query.filter(Session.is_active == True)

    # Use eager loading to avoid N+1 queries
    sessions = query\
        .options(selectinload(Session.questions))\
        .options(selectinload(Session.class_obj).selectinload(Class.instructor))\
        .order_by(Session.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()

    # Add question counts using loaded questions
    result = []
    for session in sessions:
        question_count = len(session.questions)
        # Get instructor name from the class
        instructor_name = "Unknown"
        if session.class_obj and session.class_obj.instructor:
            instructor_name = session.class_obj.instructor.display_name or session.class_obj.instructor.username
        
        result.append({
            "id": session.id,
            "title": session.title,
            "instructor_code": session.instructor_code,
            "instructor_name": instructor_name,
            "created_at": session.created_at.isoformat(),
            "ended_at": session.ended_at.isoformat() if session.ended_at else None,
            "is_active": session.is_active,
            "question_count": question_count
        })

    return result


@app.delete("/api/admin/sessions/{session_id}")
@limiter.limit("20/minute")
def delete_session_admin(request: Request, session_id: int, db: DBSession = Depends(get_db), username: str = Depends(verify_token)):
    """Delete a session (admin only)."""
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Delete associated questions first
    db.query(Question).filter(Question.meeting_id == session_id).delete()
    db.delete(session)
    db.commit()

    return {"message": "Session deleted successfully"}


@app.post("/api/admin/sessions/bulk/end")
@limiter.limit("10/minute")
def bulk_end_sessions(
    request: Request,
    session_ids: List[int],
    db: DBSession = Depends(get_db),
    username: str = Depends(verify_token)
):
    """End multiple sessions at once (admin only)."""
    sessions = db.query(Session).filter(Session.id.in_(session_ids)).all()

    for session in sessions:
        session.is_active = False
        session.ended_at = datetime.utcnow()

    db.commit()
    return {"message": f"Ended {len(sessions)} session(s) successfully"}


@app.post("/api/admin/sessions/bulk/restart")
@limiter.limit("10/minute")
def bulk_restart_sessions(
    request: Request,
    session_ids: List[int],
    db: DBSession = Depends(get_db),
    username: str = Depends(verify_token)
):
    """Restart multiple sessions at once (admin only)."""
    sessions = db.query(Session).filter(Session.id.in_(session_ids)).all()

    for session in sessions:
        session.is_active = True
        session.ended_at = None

    db.commit()
    return {"message": f"Restarted {len(sessions)} session(s) successfully"}


@app.post("/api/admin/sessions/bulk/delete")
@limiter.limit("10/minute")
def bulk_delete_sessions(
    request: Request,
    session_ids: List[int],
    db: DBSession = Depends(get_db),
    username: str = Depends(verify_token)
):
    """Delete multiple sessions at once (admin only)."""
    # Delete associated questions first
    db.query(Question).filter(Question.meeting_id.in_(session_ids)).delete(synchronize_session=False)

    # Delete sessions
    deleted_count = db.query(Session).filter(Session.id.in_(session_ids)).delete(synchronize_session=False)
    db.commit()

    return {"message": f"Deleted {deleted_count} session(s) successfully"}


if __name__ == "__main__":
    import uvicorn
    import os

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    uvicorn.run(app, host=host, port=port)
