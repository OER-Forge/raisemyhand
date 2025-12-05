"""
Class and ClassMeeting management routes for v2 API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session as DBSession, selectinload
from sqlalchemy import func
from datetime import datetime
from typing import List, Optional
from io import BytesIO, StringIO
import csv
import qrcode

from database import get_db
from models_v2 import Class, ClassMeeting, APIKey as APIKeyV2, Instructor, Question
from schemas_v2 import (
    ClassCreate, ClassUpdate, ClassResponse, ClassWithMeetings,
    ClassMeetingCreate, ClassMeetingResponse, ClassMeetingWithQuestions,
    SessionPasswordVerify
)
from config import settings
from logging_config import get_logger, log_database_operation
from passlib.context import CryptContext
from routes_instructor import get_current_instructor

router = APIRouter(tags=["classes"])
logger = get_logger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_api_key_v2(api_key: str, db: DBSession) -> APIKeyV2:
    """Verify API key and return the key object."""
    key_record = db.query(APIKeyV2).filter(
        APIKeyV2.key == api_key,
        APIKeyV2.is_active == True
    ).first()

    if not key_record:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")

    # Update last_used
    key_record.last_used = datetime.utcnow()
    db.commit()

    return key_record


def get_instructor_from_token_optional(
    authorization: Optional[str] = Header(None),
    db: DBSession = Depends(get_db)
) -> Optional[Instructor]:
    """Get instructor from JWT token (optional, returns None if no valid token)."""
    if not authorization or not authorization.startswith("Bearer "):
        return None

    try:
        from routes_instructor import verify_instructor_token
        token = authorization.split(" ")[1]
        payload = verify_instructor_token(token)
        instructor_id = int(payload.get("sub"))

        instructor = db.query(Instructor).filter(Instructor.id == instructor_id).first()
        if not instructor or not instructor.is_active:
            return None
        
        return instructor
    except Exception:
        return None


@router.post("/api/classes", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
def create_class(
    data: ClassCreate,
    api_key: Optional[str] = None,
    instructor: Optional[Instructor] = Depends(get_instructor_from_token_optional),
    db: DBSession = Depends(get_db)
):
    """Create a new class (supports both JWT token and API key auth)."""
    # Try JWT token authentication first
    if instructor:
        instructor_id = instructor.id
    elif api_key:
        # Fallback to API key authentication
        key_record = verify_api_key_v2(api_key, db)
        instructor_id = key_record.instructor_id
    else:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        new_class = Class(
            instructor_id=instructor_id,
            name=data.name,
            description=data.description,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(new_class)
        db.commit()
        db.refresh(new_class)
        log_database_operation(logger, "CREATE", "classes", new_class.id, success=True)
        return new_class
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create class: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create class")


@router.get("/api/classes", response_model=List[ClassResponse])
def list_classes(
    include_archived: bool = False,
    api_key: Optional[str] = None,
    instructor: Optional[Instructor] = Depends(get_instructor_from_token_optional),
    db: DBSession = Depends(get_db)
):
    """List instructor's classes (supports both JWT token and API key auth)."""
    # Try JWT token authentication first
    if instructor:
        instructor_id = instructor.id
    elif api_key:
        # Fallback to API key authentication
        key_record = verify_api_key_v2(api_key, db)
        instructor_id = key_record.instructor_id
    else:
        raise HTTPException(status_code=401, detail="Authentication required")

    query = db.query(Class).filter(Class.instructor_id == instructor_id)

    if not include_archived:
        query = query.filter(Class.is_archived == False)

    classes = query.order_by(Class.created_at.desc()).all()

    # Add meeting count
    for cls in classes:
        cls.meeting_count = db.query(func.count(ClassMeeting.id)).filter(
            ClassMeeting.class_id == cls.id
        ).scalar()

    return classes


@router.get("/api/classes/{class_id}", response_model=ClassWithMeetings)
def get_class(
    class_id: int,
    api_key: Optional[str] = None,
    instructor: Optional[Instructor] = Depends(get_instructor_from_token_optional),
    db: DBSession = Depends(get_db)
):
    """Get class details with meetings. Supports both JWT token and API key auth."""
    # Try JWT token authentication first
    if instructor:
        instructor_id = instructor.id
    elif api_key:
        # Fallback to API key authentication
        key_record = verify_api_key_v2(api_key, db)
        instructor_id = key_record.instructor_id
    else:
        raise HTTPException(status_code=401, detail="Authentication required")

    cls = db.query(Class).filter(
        Class.id == class_id,
        Class.instructor_id == instructor_id
    ).first()

    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")

    # Load meetings
    cls.meetings = db.query(ClassMeeting).filter(
        ClassMeeting.class_id == class_id
    ).order_by(ClassMeeting.created_at.desc()).all()

    return cls


@router.put("/api/classes/{class_id}", response_model=ClassResponse)
def update_class(
    class_id: int,
    data: ClassUpdate,
    api_key: Optional[str] = None,
    instructor: Optional[Instructor] = Depends(get_instructor_from_token_optional),
    db: DBSession = Depends(get_db)
):
    """Update class information (supports both JWT token and API key auth)."""
    # Try JWT token authentication first
    if instructor:
        instructor_id = instructor.id
    elif api_key:
        # Fallback to API key authentication
        key_record = verify_api_key_v2(api_key, db)
        instructor_id = key_record.instructor_id
    else:
        raise HTTPException(status_code=401, detail="Authentication required")

    cls = db.query(Class).filter(
        Class.id == class_id,
        Class.instructor_id == instructor_id
    ).first()

    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")

    try:
        if data.name is not None:
            cls.name = data.name
        if data.description is not None:
            cls.description = data.description

        cls.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(cls)
        log_database_operation(logger, "UPDATE", "classes", cls.id, success=True)
        return cls
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update class: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update class")


@router.delete("/api/classes/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_class(
    class_id: int,
    api_key: Optional[str] = None,
    instructor: Optional[Instructor] = Depends(get_instructor_from_token_optional),
    db: DBSession = Depends(get_db)
):
    """Archive a class (soft delete) - supports both JWT token and API key auth."""
    # Try JWT token authentication first
    if instructor:
        instructor_id = instructor.id
    elif api_key:
        # Fallback to API key authentication
        key_record = verify_api_key_v2(api_key, db)
        instructor_id = key_record.instructor_id
    else:
        raise HTTPException(status_code=401, detail="Authentication required")

    cls = db.query(Class).filter(
        Class.id == class_id,
        Class.instructor_id == instructor_id
    ).first()

    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")

    try:
        cls.is_archived = True
        cls.updated_at = datetime.utcnow()
        db.commit()
        log_database_operation(logger, "UPDATE", "classes", cls.id, success=True)
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to archive class: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to archive class")


@router.post("/api/classes/{class_id}/unarchive", response_model=ClassResponse)
def unarchive_class(
    class_id: int,
    api_key: Optional[str] = None,
    instructor: Optional[Instructor] = Depends(get_instructor_from_token_optional),
    db: DBSession = Depends(get_db)
):
    """Unarchive a class (restore from archive) - supports both JWT token and API key auth."""
    # Try JWT token authentication first
    if instructor:
        instructor_id = instructor.id
    elif api_key:
        # Fallback to API key authentication
        key_record = verify_api_key_v2(api_key, db)
        instructor_id = key_record.instructor_id
    else:
        raise HTTPException(status_code=401, detail="Authentication required")

    cls = db.query(Class).filter(
        Class.id == class_id,
        Class.instructor_id == instructor_id
    ).first()

    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")

    if not cls.is_archived:
        raise HTTPException(status_code=400, detail="Class is not archived")

    try:
        cls.is_archived = False
        cls.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(cls)
        log_database_operation(logger, "UPDATE", "classes", cls.id, success=True)
        return cls
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to unarchive class: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to unarchive class")


@router.post("/api/classes/{class_id}/meetings", response_model=ClassMeetingResponse, status_code=status.HTTP_201_CREATED)
def create_meeting(
    class_id: int,
    data: ClassMeetingCreate,
    api_key: Optional[str] = None,
    instructor: Optional[Instructor] = Depends(get_instructor_from_token_optional),
    db: DBSession = Depends(get_db)
):
    """Create a new class meeting (supports both JWT token and API key auth)."""
    # Try JWT token authentication first
    if instructor:
        instructor_id = instructor.id
        key_record = None
    elif api_key:
        # Fallback to API key authentication
        key_record = verify_api_key_v2(api_key, db)
        instructor_id = key_record.instructor_id
    else:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Verify class belongs to instructor
    cls = db.query(Class).filter(
        Class.id == class_id,
        Class.instructor_id == instructor_id
    ).first()

    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")

    try:
        meeting = ClassMeeting(
            class_id=class_id,
            api_key_id=key_record.id if key_record else None,
            meeting_code=ClassMeeting.generate_code(),
            instructor_code=ClassMeeting.generate_code(),
            title=data.title,
            password_hash=pwd_context.hash(data.password) if data.password else None,
            created_at=datetime.utcnow(),
            started_at=datetime.utcnow()
        )
        db.add(meeting)
        db.commit()
        db.refresh(meeting)
        log_database_operation(logger, "CREATE", "class_meetings", meeting.id, success=True)

        # Add computed fields
        meeting.student_url = f"{settings.base_url}/student?code={meeting.meeting_code}"
        meeting.instructor_url = f"{settings.base_url}/instructor?code={meeting.instructor_code}"
        meeting.has_password = bool(data.password)

        return meeting
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create meeting: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create meeting")


@router.get("/api/meetings/{meeting_code}", response_model=ClassMeetingWithQuestions)
def get_meeting_by_code(
    meeting_code: str,
    db: DBSession = Depends(get_db)
):
    """Get meeting details by code (for students or instructors)."""
    # Check both meeting_code and instructor_code
    meeting = db.query(ClassMeeting).filter(
        (ClassMeeting.meeting_code == meeting_code) |
        (ClassMeeting.instructor_code == meeting_code)
    ).first()

    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Add computed fields
    meeting.has_password = bool(meeting.password_hash)
    meeting.student_url = f"{settings.base_url}/student?code={meeting.meeting_code}"
    meeting.instructor_url = f"{settings.base_url}/instructor?code={meeting.instructor_code}"
    meeting.question_count = db.query(func.count(Question.id)).filter(
        Question.meeting_id == meeting.id
    ).scalar()

    # Load questions with their answers (eager loading)
    meeting.questions = db.query(Question).options(
        selectinload(Question.answer)
    ).filter(
        Question.meeting_id == meeting.id
    ).order_by(Question.created_at.desc()).all()

    return meeting


@router.post("/api/meetings/{instructor_code}/end")
def end_meeting(
    instructor_code: str,
    api_key: Optional[str] = None,
    authorization: Optional[str] = Header(None),
    db: DBSession = Depends(get_db)
):
    """
    End a class meeting.
    Authentication: instructor_code in URL is sufficient (proves access to instructor link).
    Also supports JWT token and API key auth for backwards compatibility.
    """
    # First, verify the meeting exists and get it by instructor_code
    meeting = db.query(ClassMeeting).filter(
        ClassMeeting.instructor_code == instructor_code
    ).first()

    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # The instructor_code itself is authentication - if you have it, you can control the meeting
    # This is the same security model as accessing the instructor page
    # Optional: Also verify JWT/API key if provided for additional security
    if authorization or api_key:
        instructor_id = None

        # Try JWT authentication
        if authorization and authorization.startswith("Bearer "):
            try:
                from routes_instructor import verify_instructor_token
                token = authorization.split(" ")[1]
                payload = verify_instructor_token(token)
                instructor_id = int(payload.get("sub"))
            except Exception:
                pass

        # Try API key
        if instructor_id is None and api_key:
            key_record = verify_api_key_v2(api_key, db)
            instructor_id = key_record.instructor_id

        # If auth was provided, verify ownership
        if instructor_id is not None:
            cls = db.query(Class).filter(Class.id == meeting.class_id).first()
            if not cls or cls.instructor_id != instructor_id:
                raise HTTPException(status_code=403, detail="Not authorized to end this meeting")

    try:
        meeting.ended_at = datetime.utcnow()
        meeting.is_active = False
        db.commit()
        log_database_operation(logger, "UPDATE", "class_meetings", meeting.id, success=True)
        return {"message": "Meeting ended successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to end meeting: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to end meeting")


@router.post("/api/meetings/{instructor_code}/restart")
def restart_meeting(
    instructor_code: str,
    api_key: Optional[str] = None,
    authorization: Optional[str] = Header(None),
    db: DBSession = Depends(get_db)
):
    """
    Restart an ended meeting.
    Authentication: instructor_code in URL is sufficient (proves access to instructor link).
    Also supports JWT token and API key auth for backwards compatibility.
    """
    # First, verify the meeting exists and get it by instructor_code
    meeting = db.query(ClassMeeting).filter(
        ClassMeeting.instructor_code == instructor_code
    ).first()

    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # The instructor_code itself is authentication - if you have it, you can control the meeting
    # This is the same security model as accessing the instructor page
    # Optional: Also verify JWT/API key if provided for additional security
    if authorization or api_key:
        instructor_id = None

        # Try JWT authentication
        if authorization and authorization.startswith("Bearer "):
            try:
                from routes_instructor import verify_instructor_token
                token = authorization.split(" ")[1]
                payload = verify_instructor_token(token)
                instructor_id = int(payload.get("sub"))
            except Exception:
                pass

        # Try API key
        if instructor_id is None and api_key:
            key_record = verify_api_key_v2(api_key, db)
            instructor_id = key_record.instructor_id

        # If auth was provided, verify ownership
        if instructor_id is not None:
            cls = db.query(Class).filter(Class.id == meeting.class_id).first()
            if not cls or cls.instructor_id != instructor_id:
                raise HTTPException(status_code=403, detail="Not authorized to restart this meeting")

    try:
        meeting.ended_at = None
        meeting.is_active = True
        db.commit()
        log_database_operation(logger, "UPDATE", "class_meetings", meeting.id, success=True)
        return {"message": "Meeting restarted successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to restart meeting: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to restart meeting")


@router.get("/api/meetings", response_model=List[ClassMeetingResponse])
def list_all_meetings(
    api_key: Optional[str] = None,
    include_ended: bool = True,
    authorization: Optional[str] = Header(None),
    db: DBSession = Depends(get_db)
):
    """List all meetings for the authenticated instructor (supports both JWT and API key auth)."""
    instructor_id = None

    # Try JWT authentication first (from Authorization header)
    if authorization and authorization.startswith("Bearer "):
        try:
            # Use instructor JWT authentication
            from routes_instructor import verify_instructor_token
            token = authorization.split(" ")[1]
            payload = verify_instructor_token(token)
            instructor_id = int(payload.get("sub"))
            logger.info(f"Authenticated via JWT, instructor_id: {instructor_id}")
        except Exception as e:
            logger.warning(f"JWT auth failed: {e}")
            # Fall through to API key auth

    # Fall back to API key authentication
    if instructor_id is None and api_key:
        key_record = verify_api_key_v2(api_key, db)
        instructor_id = key_record.instructor_id
        logger.info(f"Authenticated via API key, instructor_id: {instructor_id}")

    # If neither auth method succeeded
    if instructor_id is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required: provide either Authorization header (JWT) or api_key parameter"
        )

    # Get all classes for this instructor
    class_ids = db.query(Class.id).filter(
        Class.instructor_id == instructor_id
    ).all()
    class_ids = [c[0] for c in class_ids]

    # Get all meetings for these classes
    query = db.query(ClassMeeting).filter(ClassMeeting.class_id.in_(class_ids))

    if not include_ended:
        query = query.filter(ClassMeeting.is_active == True)

    meetings = query.order_by(ClassMeeting.created_at.desc()).all()

    # Build response with computed fields using dictionaries for Pydantic
    responses = []
    for meeting in meetings:
        question_count = db.query(func.count(Question.id)).filter(
            Question.meeting_id == meeting.id
        ).scalar()
        
        # Get class name
        class_obj = db.query(Class).filter(Class.id == meeting.class_id).first()
        class_name = class_obj.name if class_obj else f"Class {meeting.class_id}"
        
        # Create response dict with all fields explicitly
        response_dict = {
            'id': meeting.id,
            'class_id': meeting.class_id,
            'api_key_id': meeting.api_key_id,
            'meeting_code': meeting.meeting_code,
            'instructor_code': meeting.instructor_code,
            'title': meeting.title,
            'has_password': bool(meeting.password_hash),
            'created_at': meeting.created_at,
            'started_at': meeting.started_at,
            'ended_at': meeting.ended_at,
            'is_active': meeting.is_active,
            'question_count': question_count,
            'student_url': f"{settings.base_url}/student?code={meeting.meeting_code}",
            'instructor_url': f"{settings.base_url}/instructor?code={meeting.instructor_code}",
            'class_name': class_name
        }
        response_data = ClassMeetingResponse(**response_dict)
        responses.append(response_data)

    return responses


@router.get("/api/meetings/{meeting_code}/qr")
def get_meeting_qr_code(meeting_code: str, url_base: str):
    """Generate QR code for meeting URL (v2 API)."""
    url = f"{url_base}/student?code={meeting_code}"

    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png")


@router.post("/api/meetings/{meeting_code}/verify-password")
def verify_meeting_password(
    meeting_code: str,
    password_data: SessionPasswordVerify,
    db: DBSession = Depends(get_db)
):
    """Verify meeting password (v2 API)."""
    meeting = db.query(ClassMeeting).filter(
        ClassMeeting.meeting_code == meeting_code
    ).first()

    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if not meeting.password_hash:
        return {"verified": True}

    if pwd_context.verify(password_data.password, meeting.password_hash):
        return {"verified": True}
    else:
        raise HTTPException(status_code=401, detail="Incorrect password")


@router.get("/api/meetings/{instructor_code}/report")
def get_meeting_report(
    instructor_code: str,
    format: str = "json",
    api_key: Optional[str] = None,
    authorization: Optional[str] = Header(None),
    db: DBSession = Depends(get_db)
):
    """Generate a report for a meeting. Supports both JWT token and API key auth."""
    instructor_id = None
    
    # Try JWT authentication first
    if authorization and authorization.startswith("Bearer "):
        try:
            from routes_instructor import verify_instructor_token
            token = authorization.split(" ")[1]
            payload = verify_instructor_token(token)
            instructor_id = int(payload.get("sub"))
        except Exception:
            pass
    
    # Fall back to API key
    if instructor_id is None and api_key:
        key_record = verify_api_key_v2(api_key, db)
        instructor_id = key_record.instructor_id
    # Note: report can also be generated without auth for public access (optional)

    meeting = db.query(ClassMeeting).filter(
        ClassMeeting.instructor_code == instructor_code
    ).first()

    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    questions = db.query(Question).filter(
        Question.meeting_id == meeting.id
    ).order_by(Question.upvotes.desc()).all()

    if format == "csv":
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["Question", "Upvotes", "Answered in Class", "Created At"])
        for q in questions:
            writer.writerow([
                q.text,
                q.upvotes,
                "Yes" if q.is_answered_in_class else "No",
                q.created_at.isoformat()
            ])

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=meeting_{meeting.meeting_code}_report.csv"}
        )

    # JSON format (default)
    return {
        "meeting": {
            "title": meeting.title,
            "meeting_code": meeting.meeting_code,
            "created_at": meeting.created_at.isoformat(),
            "ended_at": meeting.ended_at.isoformat() if meeting.ended_at else None,
            "is_active": meeting.is_active
        },
        "questions": [
            {
                "text": q.text,
                "upvotes": q.upvotes,
                "is_answered_in_class": q.is_answered_in_class,
                "created_at": q.created_at.isoformat()
            }
            for q in questions
        ],
        "stats": {
            "total_questions": len(questions),
            "answered_questions": sum(1 for q in questions if q.is_answered_in_class),
            "total_upvotes": sum(q.upvotes for q in questions)
        }
    }
