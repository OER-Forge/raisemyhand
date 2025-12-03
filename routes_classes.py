"""
Class and ClassMeeting management routes for v2 API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func
from datetime import datetime
from typing import List

from database import get_db
from models_v2 import Class, ClassMeeting, APIKey as APIKeyV2, Instructor
from schemas_v2 import (
    ClassCreate, ClassUpdate, ClassResponse, ClassWithMeetings,
    ClassMeetingCreate, ClassMeetingResponse, ClassMeetingWithQuestions
)
from config import settings
from logging_config import get_logger, log_database_operation
from passlib.context import CryptContext

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


@router.post("/api/classes", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
def create_class(
    data: ClassCreate,
    api_key: str,
    db: DBSession = Depends(get_db)
):
    """Create a new class."""
    key_record = verify_api_key_v2(api_key, db)

    try:
        new_class = Class(
            instructor_id=key_record.instructor_id,
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
    api_key: str,
    include_archived: bool = False,
    db: DBSession = Depends(get_db)
):
    """List instructor's classes."""
    key_record = verify_api_key_v2(api_key, db)

    query = db.query(Class).filter(Class.instructor_id == key_record.instructor_id)

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
    api_key: str,
    db: DBSession = Depends(get_db)
):
    """Get class details with meetings."""
    key_record = verify_api_key_v2(api_key, db)

    cls = db.query(Class).filter(
        Class.id == class_id,
        Class.instructor_id == key_record.instructor_id
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
    api_key: str,
    db: DBSession = Depends(get_db)
):
    """Update class information."""
    key_record = verify_api_key_v2(api_key, db)

    cls = db.query(Class).filter(
        Class.id == class_id,
        Class.instructor_id == key_record.instructor_id
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
    api_key: str,
    db: DBSession = Depends(get_db)
):
    """Archive a class (soft delete)."""
    key_record = verify_api_key_v2(api_key, db)

    cls = db.query(Class).filter(
        Class.id == class_id,
        Class.instructor_id == key_record.instructor_id
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


@router.post("/api/classes/{class_id}/meetings", response_model=ClassMeetingResponse, status_code=status.HTTP_201_CREATED)
def create_meeting(
    class_id: int,
    data: ClassMeetingCreate,
    api_key: str,
    db: DBSession = Depends(get_db)
):
    """Create a new class meeting."""
    key_record = verify_api_key_v2(api_key, db)

    # Verify class belongs to instructor
    cls = db.query(Class).filter(
        Class.id == class_id,
        Class.instructor_id == key_record.instructor_id
    ).first()

    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")

    try:
        meeting = ClassMeeting(
            class_id=class_id,
            api_key_id=key_record.id,
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
    """Get meeting details by code (for students)."""
    meeting = db.query(ClassMeeting).filter(
        ClassMeeting.meeting_code == meeting_code
    ).first()

    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    return meeting


@router.post("/api/meetings/{instructor_code}/end")
def end_meeting(
    instructor_code: str,
    api_key: str,
    db: DBSession = Depends(get_db)
):
    """End a class meeting."""
    key_record = verify_api_key_v2(api_key, db)

    meeting = db.query(ClassMeeting).filter(
        ClassMeeting.instructor_code == instructor_code
    ).first()

    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Verify ownership
    if meeting.api_key_id != key_record.id:
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
    api_key: str,
    db: DBSession = Depends(get_db)
):
    """Restart an ended meeting."""
    key_record = verify_api_key_v2(api_key, db)

    meeting = db.query(ClassMeeting).filter(
        ClassMeeting.instructor_code == instructor_code
    ).first()

    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Verify ownership
    if meeting.api_key_id != key_record.id:
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
