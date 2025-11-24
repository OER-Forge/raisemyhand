from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session as DBSession
from datetime import datetime
from typing import List
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

# Load environment variables from .env file
load_dotenv()

from database import get_db, init_db
from models import Session, Question
from schemas import SessionCreate, SessionResponse, QuestionCreate, QuestionResponse, SessionWithQuestions

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="RaiseMyHand - Student Question Aggregator")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security
security = HTTPBasic()

# Configuration
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
TIMEZONE = os.getenv("TIMEZONE", "UTC")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme")

# Initialize timezone
try:
    LOCAL_TZ = pytz.timezone(TIMEZONE)
except pytz.exceptions.UnknownTimeZoneError:
    print(f"Warning: Unknown timezone '{TIMEZONE}', falling back to UTC")
    LOCAL_TZ = pytz.UTC


# Security helper functions
def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify admin credentials using HTTP Basic Auth."""
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


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


# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    init_db()


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
def create_session(session: SessionCreate, db: DBSession = Depends(get_db)):
    """Create a new Q&A session."""
    db_session = Session(
        session_code=Session.generate_code(),
        instructor_code=Session.generate_code(),
        title=session.title
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


@app.get("/api/sessions/{session_code}", response_model=SessionWithQuestions)
def get_session(session_code: str, db: DBSession = Depends(get_db)):
    """Get a session with all its questions."""
    session = db.query(Session).filter(Session.session_code == session_code).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.get("/api/instructor/sessions/{instructor_code}", response_model=SessionWithQuestions)
@limiter.limit("30/minute")
def get_instructor_session(request: Request, instructor_code: str, db: DBSession = Depends(get_db)):
    """Get a session by instructor code with all its questions."""
    session = db.query(Session).filter(Session.instructor_code == instructor_code).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.post("/api/sessions/{instructor_code}/end")
@limiter.limit("10/minute")
def end_session(request: Request, instructor_code: str, db: DBSession = Depends(get_db)):
    """End a session (instructor only)."""
    session = db.query(Session).filter(Session.instructor_code == instructor_code).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.is_active = False
    session.ended_at = datetime.utcnow()
    db.commit()
    return {"message": "Session ended successfully"}


@app.post("/api/sessions/{instructor_code}/restart")
@limiter.limit("10/minute")
def restart_session(request: Request, instructor_code: str, db: DBSession = Depends(get_db)):
    """Restart an ended session (instructor only)."""
    session = db.query(Session).filter(Session.instructor_code == instructor_code).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.is_active = True
    session.ended_at = None
    db.commit()
    return {"message": "Session restarted successfully"}


@app.get("/api/sessions/{instructor_code}/report")
@limiter.limit("20/minute")
async def get_session_report(request: Request, instructor_code: str, format: str = "json", db: DBSession = Depends(get_db)):
    """Generate a report for a session (instructor only)."""
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

    db_question = Question(
        session_id=session.id,
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
            "text": db_question.text,
            "upvotes": db_question.upvotes,
            "is_answered": db_question.is_answered,
            "created_at": db_question.created_at.isoformat()
        }
    }, session_code)

    return db_question


@app.post("/api/questions/{question_id}/upvote")
async def upvote_question(question_id: int, db: DBSession = Depends(get_db)):
    """Upvote a question."""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    session = db.query(Session).filter(Session.id == question.session_id).first()
    if not session.is_active:
        raise HTTPException(status_code=400, detail="Session is inactive")

    question.upvotes += 1
    db.commit()

    # Broadcast upvote to all connected clients
    await manager.broadcast({
        "type": "upvote",
        "question_id": question.id,
        "upvotes": question.upvotes
    }, session.session_code)

    return {"upvotes": question.upvotes}


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
    """Home page for creating sessions."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/instructor", response_class=HTMLResponse)
async def instructor_view(request: Request):
    """Instructor dashboard."""
    return templates.TemplateResponse("instructor.html", {"request": request})


@app.get("/student", response_class=HTMLResponse)
async def student_view(request: Request):
    """Student question submission page."""
    return templates.TemplateResponse("student.html", {"request": request})


@app.get("/admin", response_class=HTMLResponse)
async def admin_view(request: Request, username: str = Depends(verify_admin)):
    """Admin dashboard (requires authentication)."""
    return templates.TemplateResponse("admin.html", {"request": request})


# Health check
@app.get("/api/health")
def health_check():
    return {"status": "healthy"}


# Configuration endpoint
@app.get("/api/config")
def get_config():
    """Get client configuration including base URL and timezone."""
    return {
        "base_url": BASE_URL,
        "timezone": TIMEZONE
    }


# Admin API endpoints
@app.get("/api/admin/stats")
def get_admin_stats(db: DBSession = Depends(get_db), username: str = Depends(verify_admin)):
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
    username: str = Depends(verify_admin)
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
def delete_session_admin(session_id: int, db: DBSession = Depends(get_db), username: str = Depends(verify_admin)):
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
def bulk_end_sessions(session_ids: List[int], db: DBSession = Depends(get_db), username: str = Depends(verify_admin)):
    """End multiple sessions at once (admin only)."""
    sessions = db.query(Session).filter(Session.id.in_(session_ids)).all()

    for session in sessions:
        session.is_active = False
        session.ended_at = datetime.utcnow()

    db.commit()
    return {"message": f"Ended {len(sessions)} session(s) successfully"}


@app.post("/api/admin/sessions/bulk/restart")
def bulk_restart_sessions(session_ids: List[int], db: DBSession = Depends(get_db), username: str = Depends(verify_admin)):
    """Restart multiple sessions at once (admin only)."""
    sessions = db.query(Session).filter(Session.id.in_(session_ids)).all()

    for session in sessions:
        session.is_active = True
        session.ended_at = None

    db.commit()
    return {"message": f"Restarted {len(sessions)} session(s) successfully"}


@app.post("/api/admin/sessions/bulk/delete")
def bulk_delete_sessions(session_ids: List[int], db: DBSession = Depends(get_db), username: str = Depends(verify_admin)):
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
