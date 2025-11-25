from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session as DBSession
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
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from jose import JWTError, jwt
from passlib.context import CryptContext

# Load environment variables from .env file
load_dotenv()

from database import get_db, init_db
from models import Session, Question, APIKey
from schemas import (
    SessionCreate, SessionResponse, QuestionCreate, QuestionResponse, 
    SessionWithQuestions, AdminLogin, Token, SessionPasswordVerify,
    APIKeyCreate, APIKeyResponse, InstructorAuth
)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="RaiseMyHand - Student Question Aggregator")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security Configuration
security = HTTPBearer(auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))  # 8 hours default

# App Configuration
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
TIMEZONE = os.getenv("TIMEZONE", "UTC")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme123")
ENABLE_AUTH = os.getenv("ENABLE_AUTH", "true").lower() == "true"

# Initialize timezone
try:
    LOCAL_TZ = pytz.timezone(TIMEZONE)
except pytz.exceptions.UnknownTimeZoneError:
    print(f"Warning: Unknown timezone '{TIMEZONE}', falling back to UTC")
    LOCAL_TZ = pytz.UTC


# Security helper functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_api_key(api_key: Optional[str], db) -> bool:
    """Verify API key and update last_used timestamp."""
    if not api_key:
        return False
    
    key_record = db.query(APIKey).filter(
        APIKey.key == api_key, 
        APIKey.is_active == True
    ).first()
    
    if key_record:
        # Update last_used timestamp
        key_record.last_used = datetime.utcnow()
        db.commit()
        return True
    
    return False

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[str]:
    """Verify JWT token and return username if valid."""
    if not ENABLE_AUTH:
        return "admin"  # Skip auth if disabled
    
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
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
        "session_code": session.session_code,
        "instructor_code": session.instructor_code,
        "title": session.title,
        "has_password": session.password_hash is not None,
        "created_at": session.created_at,
        "ended_at": session.ended_at,
        "is_active": session.is_active,
        "questions": [
            {
                "id": q.id,
                "session_id": q.session_id,
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
            print("  2. Login (default: admin/changeme123)")
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

    async def connect(self, websocket: WebSocket, session_code: str):
        await websocket.accept()
        if session_code not in self.active_connections:
            self.active_connections[session_code] = []
        self.active_connections[session_code].append(websocket)

    def disconnect(self, websocket: WebSocket, session_code: str):
        if session_code in self.active_connections:
            self.active_connections[session_code].remove(websocket)
            if not self.active_connections[session_code]:
                del self.active_connections[session_code]

    async def broadcast(self, message: dict, session_code: str):
        if session_code in self.active_connections:
            disconnected = []
            for connection in self.active_connections[session_code]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.append(connection)

            # Clean up disconnected clients
            for conn in disconnected:
                self.disconnect(conn, session_code)


manager = ConnectionManager()


# Session endpoints
@app.post("/api/sessions", response_model=SessionResponse)
def create_session(
    session: SessionCreate, 
    request: Request,
    api_key: Optional[str] = None,
    db: DBSession = Depends(get_db)
):
    """Create a new Q&A session (requires valid API key)."""
    # Get API key from query parameter if not in body
    if not api_key:
        api_key = request.query_params.get('api_key')
    
    # Verify API key
    if not verify_api_key(api_key, db):
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")
    password_hash = None
    if session.password:
        password_hash = get_password_hash(session.password)
    
    db_session = Session(
        session_code=Session.generate_code(),
        instructor_code=Session.generate_code(),
        title=session.title,
        password_hash=password_hash
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    # Create response with has_password field
    response_data = {
        "id": db_session.id,
        "session_code": db_session.session_code,
        "instructor_code": db_session.instructor_code,
        "title": db_session.title,
        "has_password": password_hash is not None,
        "created_at": db_session.created_at,
        "ended_at": db_session.ended_at,
        "is_active": db_session.is_active
    }
    return response_data


@app.get("/api/sessions/my-sessions")
@limiter.limit("60/minute")
def get_my_sessions(
    request: Request,
    api_key: Optional[str] = None,
    db: DBSession = Depends(get_db)
):
    """Get all sessions created with this API key."""
    # Get API key from query parameter if not provided
    if not api_key:
        api_key = request.query_params.get('api_key')
    
    # Verify API key and get the key record
    key_record = db.query(APIKey).filter(
        APIKey.key == api_key,
        APIKey.is_active == True
    ).first()
    
    if not key_record:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")
    
    # Update last used timestamp
    key_record.last_used = datetime.utcnow()
    db.commit()
    
    # Get all sessions (we don't track which API key created which session currently)
    # For now, return all sessions - you could add an api_key_id field to Session model to track this
    sessions = db.query(Session).order_by(Session.created_at.desc()).all()
    
    # Format sessions with stats
    result = []
    for session in sessions:
        questions = session.questions
        result.append({
            "id": session.id,
            "title": session.title,
            "session_code": session.session_code,
            "instructor_code": session.instructor_code,
            "created_at": session.created_at,
            "ended_at": session.ended_at,
            "is_active": session.is_active,
            "question_count": len(questions),
            "unanswered_count": sum(1 for q in questions if not q.is_answered),
            "total_upvotes": sum(q.upvotes for q in questions)
        })
    
    return result


@app.get("/api/sessions/{session_code}", response_model=SessionWithQuestions)
def get_session(session_code: str, db: DBSession = Depends(get_db)):
    """Get a session with all its questions."""
    session = db.query(Session).filter(Session.session_code == session_code).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return format_session_response(session)


@app.post("/api/sessions/{session_code}/verify-password")
def verify_session_password(session_code: str, password_data: SessionPasswordVerify, db: DBSession = Depends(get_db)):
    """Verify session password for protected sessions."""
    session = db.query(Session).filter(Session.session_code == session_code).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not session.password_hash:
        return {"verified": True, "message": "Session is not password protected"}
    
    if verify_password(password_data.password, session.password_hash):
        return {"verified": True, "message": "Password correct"}
    else:
        raise HTTPException(status_code=401, detail="Invalid password")


@app.get("/api/instructor/sessions/{instructor_code}", response_model=SessionWithQuestions)
@limiter.limit("30/minute")
def get_instructor_session(
    request: Request, 
    instructor_code: str, 
    api_key: Optional[str] = None, 
    db: DBSession = Depends(get_db)
):
    """Get a session by instructor code with all its questions (requires valid API key)."""
    # Get API key from query parameter if not provided
    if not api_key:
        api_key = request.query_params.get('api_key')
    
    # Verify API key
    if not verify_api_key(api_key, db):
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")
    
    session = db.query(Session).filter(Session.instructor_code == instructor_code).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return format_session_response(session)


@app.post("/api/sessions/{instructor_code}/end")
@limiter.limit("10/minute")
def end_session(
    request: Request, 
    instructor_code: str, 
    api_key: Optional[str] = None, 
    db: DBSession = Depends(get_db)
):
    """End a session (requires valid API key)."""
    # Get API key from query parameter if not provided
    if not api_key:
        api_key = request.query_params.get('api_key')
    
    # Verify API key
    if not verify_api_key(api_key, db):
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")
    session = db.query(Session).filter(Session.instructor_code == instructor_code).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.is_active = False
    session.ended_at = datetime.utcnow()
    db.commit()
    return {"message": "Session ended successfully"}


@app.post("/api/sessions/{instructor_code}/restart")
@limiter.limit("10/minute")
def restart_session(
    request: Request, 
    instructor_code: str, 
    api_key: Optional[str] = None, 
    db: DBSession = Depends(get_db)
):
    """Restart an ended session (requires valid API key)."""
    # Get API key from query parameter if not provided
    if not api_key:
        api_key = request.query_params.get('api_key')
    
    # Verify API key
    if not verify_api_key(api_key, db):
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")
    session = db.query(Session).filter(Session.instructor_code == instructor_code).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.is_active = True
    session.ended_at = None
    db.commit()
    return {"message": "Session restarted successfully"}


@app.get("/api/sessions/{instructor_code}/report")
@limiter.limit("20/minute")
async def get_session_report(
    request: Request, 
    instructor_code: str, 
    format: str = "json", 
    api_key: Optional[str] = None, 
    db: DBSession = Depends(get_db)
):
    """Generate a report for a session (requires valid API key)."""
    # Get API key from query parameter if not provided
    if not api_key:
        api_key = request.query_params.get('api_key')
    
    # Verify API key
    if not api_key or not verify_api_key(api_key, db):
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")
    session = db.query(Session).filter(Session.instructor_code == instructor_code).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    questions = db.query(Question).filter(Question.session_id == session.id).order_by(Question.upvotes.desc()).all()

    if format == "csv":
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["Question", "Upvotes", "Answered", "Created At", "Answered At"])
        for q in questions:
            writer.writerow([
                q.text,
                q.upvotes,
                "Yes" if q.is_answered else "No",
                q.created_at.isoformat(),
                q.answered_at.isoformat() if q.answered_at else ""
            ])

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=session_{session.session_code}_report.csv"}
        )

    # JSON format (default)
    return {
        "session": {
            "title": session.title,
            "session_code": session.session_code,
            "created_at": session.created_at.isoformat(),
            "ended_at": session.ended_at.isoformat() if session.ended_at else None,
            "is_active": session.is_active
        },
        "questions": [
            {
                "text": q.text,
                "upvotes": q.upvotes,
                "is_answered": q.is_answered,
                "created_at": q.created_at.isoformat(),
                "answered_at": q.answered_at.isoformat() if q.answered_at else None
            }
            for q in questions
        ],
        "stats": {
            "total_questions": len(questions),
            "answered_questions": sum(1 for q in questions if q.is_answered),
            "total_upvotes": sum(q.upvotes for q in questions)
        }
    }


# Question endpoints
@app.post("/api/sessions/{session_code}/questions", response_model=QuestionResponse)
async def create_question(session_code: str, question: QuestionCreate, db: DBSession = Depends(get_db)):
    """Submit a new question to a session."""
    session = db.query(Session).filter(Session.session_code == session_code, Session.is_active == True).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or inactive")

    # Get the next question number for this session
    max_number = db.query(func.max(Question.question_number)).filter(Question.session_id == session.id).scalar()
    next_number = (max_number or 0) + 1

    db_question = Question(
        session_id=session.id,
        question_number=next_number,
        text=question.text
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)

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


@app.post("/api/questions/{question_id}/vote")
async def toggle_vote(question_id: int, action: str, db: DBSession = Depends(get_db)):
    """Toggle vote on a question (upvote or remove vote)."""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    session = db.query(Session).filter(Session.id == question.session_id).first()
    if not session.is_active:
        raise HTTPException(status_code=400, detail="Session is inactive")

    if action == "add":
        question.upvotes += 1
    elif action == "remove":
        question.upvotes = max(0, question.upvotes - 1)
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    db.commit()

    # Broadcast vote change to all connected clients
    await manager.broadcast({
        "type": "vote_update",
        "question_id": question.id,
        "upvotes": question.upvotes
    }, session.session_code)

    return {"upvotes": question.upvotes}


# Keep old endpoint for backwards compatibility
@app.post("/api/questions/{question_id}/upvote")
async def upvote_question(question_id: int, db: DBSession = Depends(get_db)):
    """Upvote a question (deprecated - use /vote instead)."""
    return await toggle_vote(question_id, "add", db)


@app.post("/api/questions/{question_id}/answer")
async def mark_answered(question_id: int, instructor_code: str, db: DBSession = Depends(get_db)):
    """Mark a question as answered (instructor only)."""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    session = db.query(Session).filter(Session.id == question.session_id).first()
    if session.instructor_code != instructor_code:
        raise HTTPException(status_code=403, detail="Unauthorized")

    question.is_answered = not question.is_answered
    question.answered_at = datetime.utcnow() if question.is_answered else None
    db.commit()

    # Broadcast answer status to all connected clients
    await manager.broadcast({
        "type": "answer_status",
        "question_id": question.id,
        "is_answered": question.is_answered
    }, session.session_code)

    return {"is_answered": question.is_answered}


# QR Code generation
@app.get("/api/sessions/{session_code}/qr")
def get_qr_code(session_code: str, url_base: str):
    """Generate QR code for session URL."""
    url = f"{url_base}/student?code={session_code}"

    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png")


# Public stats endpoint - no authentication required
@app.get("/api/sessions/{session_code}/stats")
@limiter.limit("30/minute")
async def get_session_stats(request: Request, session_code: str, db: DBSession = Depends(get_db)):
    """Get public stats for a session - question count, answered count, votes per question (no text)."""
    session = db.query(Session).filter(Session.session_code == session_code).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    questions = db.query(Question).filter(Question.session_id == session.id).all()
    
    stats = {
        "session_title": session.title,
        "session_code": session.session_code,
        "is_active": session.is_active,
        "created_at": session.created_at.isoformat(),
        "ended_at": session.ended_at.isoformat() if session.ended_at else None,
        "total_questions": len(questions),
        "answered_questions": sum(1 for q in questions if q.is_answered),
        "unanswered_questions": sum(1 for q in questions if not q.is_answered),
        "total_votes": sum(q.upvotes for q in questions),
        "questions_by_votes": [
            {
                "question_id": q.id,
                "question_number": q.question_number,
                "votes": q.upvotes,
                "answered": q.is_answered,
                "created_at": q.created_at.isoformat(),
                "answered_at": q.answered_at.isoformat() if q.answered_at else None
            }
            for q in sorted(questions, key=lambda x: x.upvotes, reverse=True)
        ]
    }
    
    return stats


@app.get("/stats", response_class=HTMLResponse)
async def stats_page(request: Request):
    """Public stats page."""
    return templates.TemplateResponse("stats.html", {"request": request, "base_url": BASE_URL})


# WebSocket endpoint
@app.websocket("/ws/{session_code}")
async def websocket_endpoint(websocket: WebSocket, session_code: str):
    await manager.connect(websocket, session_code)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
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


# API Key Management endpoints (admin only)
@app.post("/api/admin/api-keys", response_model=APIKeyResponse)
def create_api_key(key_data: APIKeyCreate, username: str = Depends(verify_token), db: DBSession = Depends(get_db)):
    """Create a new API key for instructor authentication (admin only)."""
    api_key = APIKey(
        key=APIKey.generate_key(),
        name=key_data.name
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return api_key

@app.get("/api/admin/api-keys", response_model=list[APIKeyResponse])
def list_api_keys(username: str = Depends(verify_token), db: DBSession = Depends(get_db)):
    """List all API keys (admin only)."""
    return db.query(APIKey).order_by(APIKey.created_at.desc()).all()

@app.delete("/api/admin/api-keys/{key_id}")
def delete_api_key(key_id: int, username: str = Depends(verify_token), db: DBSession = Depends(get_db)):
    """Deactivate an API key (admin only)."""
    api_key = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    api_key.is_active = False
    db.commit()
    return {"message": "API key deactivated successfully"}

@app.post("/api/instructor/auth")
def instructor_auth(auth_data: InstructorAuth, db: DBSession = Depends(get_db)):
    """Authenticate instructor with API key and return session cookie data."""
    if not verify_api_key(auth_data.api_key, db):
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")
    
    # Return success with API key validation
    return {"authenticated": True, "message": "API key is valid"}

# Authentication endpoints
@app.post("/api/admin/login", response_model=Token)
def admin_login(login_data: AdminLogin):
    """Admin login endpoint."""
    if not ENABLE_AUTH:
        # If auth is disabled, always return a valid token
        access_token = create_access_token(data={"sub": "admin"})
        return {"access_token": access_token, "token_type": "bearer"}
    
    # Verify admin credentials
    correct_username = secrets.compare_digest(login_data.username, ADMIN_USERNAME)
    correct_password = secrets.compare_digest(login_data.password, ADMIN_PASSWORD)
    
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )
    
    access_token = create_access_token(data={"sub": login_data.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/admin/verify")
def verify_admin_token(username: str = Depends(verify_token)):
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
    """Get client configuration including base URL, timezone, and auth status."""
    return {
        "base_url": BASE_URL,
        "timezone": TIMEZONE,
        "auth_enabled": ENABLE_AUTH
    }


# Admin API endpoints
@app.get("/api/admin/stats")
def get_admin_stats(db: DBSession = Depends(get_db), username: str = Depends(verify_token)):
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
def get_all_sessions(
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

    sessions = query.order_by(Session.created_at.desc()).offset(skip).limit(limit).all()

    # Add question counts
    result = []
    for session in sessions:
        question_count = db.query(func.count(Question.id)).filter(Question.session_id == session.id).scalar()
        result.append({
            "id": session.id,
            "title": session.title,
            "session_code": session.session_code,
            "instructor_code": session.instructor_code,
            "created_at": session.created_at.isoformat(),
            "ended_at": session.ended_at.isoformat() if session.ended_at else None,
            "is_active": session.is_active,
            "question_count": question_count
        })

    return result


@app.delete("/api/admin/sessions/{session_id}")
def delete_session_admin(session_id: int, db: DBSession = Depends(get_db), username: str = Depends(verify_token)):
    """Delete a session (admin only)."""
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Delete associated questions first
    db.query(Question).filter(Question.session_id == session_id).delete()
    db.delete(session)
    db.commit()

    return {"message": "Session deleted successfully"}


@app.post("/api/admin/sessions/bulk/end")
def bulk_end_sessions(session_ids: List[int], db: DBSession = Depends(get_db), username: str = Depends(verify_token)):
    """End multiple sessions at once (admin only)."""
    sessions = db.query(Session).filter(Session.id.in_(session_ids)).all()

    for session in sessions:
        session.is_active = False
        session.ended_at = datetime.utcnow()

    db.commit()
    return {"message": f"Ended {len(sessions)} session(s) successfully"}


@app.post("/api/admin/sessions/bulk/restart")
def bulk_restart_sessions(session_ids: List[int], db: DBSession = Depends(get_db), username: str = Depends(verify_token)):
    """Restart multiple sessions at once (admin only)."""
    sessions = db.query(Session).filter(Session.id.in_(session_ids)).all()

    for session in sessions:
        session.is_active = True
        session.ended_at = None

    db.commit()
    return {"message": f"Restarted {len(sessions)} session(s) successfully"}


@app.post("/api/admin/sessions/bulk/delete")
def bulk_delete_sessions(session_ids: List[int], db: DBSession = Depends(get_db), username: str = Depends(verify_token)):
    """Delete multiple sessions at once (admin only)."""
    # Delete associated questions first
    db.query(Question).filter(Question.session_id.in_(session_ids)).delete(synchronize_session=False)

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
