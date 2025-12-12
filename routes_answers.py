"""
Written answer management routes for v2 API (Phase 5 - Issue #21)
Instructors can write, edit, publish, and delete answers to questions.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session as DBSession
from datetime import datetime
from typing import Optional

from database import get_db
from models_v2 import Answer, Question, ClassMeeting, APIKey as APIKeyV2, Instructor
from schemas_v2 import AnswerCreate, AnswerUpdate, AnswerResponse
from logging_config import get_logger, log_database_operation

router = APIRouter(tags=["answers"])
logger = get_logger(__name__)


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


def get_instructor_id_from_auth(authorization: Optional[str], api_key: Optional[str], db: DBSession) -> int:
    """Extract instructor_id from JWT token or API key."""
    instructor_id = None
    
    # Try JWT authentication first
    if authorization and authorization.startswith("Bearer "):
        try:
            from routes_instructor import verify_instructor_token
            token = authorization.split(" ")[1]
            payload = verify_instructor_token(token)
            instructor_id = int(payload.get("sub"))
            return instructor_id
        except Exception:
            pass
    
    # Fall back to API key
    if api_key:
        key_record = verify_api_key_v2(api_key, db)
        return key_record.instructor_id
    
    raise HTTPException(status_code=401, detail="Authentication required")


def verify_question_ownership(question_id: int, key_record: APIKeyV2, db: DBSession) -> Question:
    """Verify that the question belongs to a meeting owned by the instructor."""
    question = db.query(Question).filter(Question.id == question_id).first()

    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Get the meeting
    meeting = db.query(ClassMeeting).filter(ClassMeeting.id == question.meeting_id).first()

    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # Verify the meeting belongs to the instructor
    if meeting.api_key_id != key_record.id:
        raise HTTPException(status_code=403, detail="Not authorized to answer this question")

    return question


@router.post("/api/questions/{question_id}/answer", response_model=AnswerResponse)
def create_or_update_answer(
    question_id: int,
    data: AnswerCreate,
    api_key: Optional[str] = None,
    authorization: Optional[str] = Header(None),
    db: DBSession = Depends(get_db)
):
    """
    Create or update a written answer to a question.
    Instructors can save answers as drafts (is_approved=false) or publish immediately.
    Supports both JWT token and API key authentication.
    """
    # Check maintenance mode
    from security import check_maintenance_mode
    user_role = None
    instructor_id = get_instructor_id_from_auth(authorization, api_key, db)
    
    # Get user role
    instructor = db.query(Instructor).filter(Instructor.id == instructor_id).first()
    if instructor:
        user_role = instructor.role
    
    maintenance_blocked = check_maintenance_mode(db, user_role)
    if maintenance_blocked:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System is currently in maintenance mode. Answers cannot be created or updated at this time."
        )
    
    # Get the question
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Verify the meeting belongs to this instructor
    meeting = db.query(ClassMeeting).filter(ClassMeeting.id == question.meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Check if instructor owns this class
    from models_v2 import Class
    cls = db.query(Class).filter(Class.id == meeting.class_id).first()
    if not cls or cls.instructor_id != instructor_id:
        raise HTTPException(status_code=403, detail="Not authorized to answer this question")

    try:
        # Check if answer already exists
        existing_answer = db.query(Answer).filter(Answer.question_id == question_id).first()

        if existing_answer:
            # Update existing answer
            existing_answer.answer_text = data.answer_text
            existing_answer.is_approved = data.is_approved
            existing_answer.updated_at = datetime.utcnow()
            
            # Ensure question's has_written_answer flag is set
            question.has_written_answer = True
            
            db.commit()
            db.refresh(existing_answer)
            log_database_operation(logger, "UPDATE", "answers", existing_answer.id, success=True)
            return existing_answer
        else:
            # Create new answer
            new_answer = Answer(
                question_id=question_id,
                instructor_id=instructor_id,
                answer_text=data.answer_text,
                is_approved=data.is_approved,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(new_answer)
            
            # Update question's has_written_answer flag
            question.has_written_answer = True
            
            db.commit()
            db.refresh(new_answer)
            log_database_operation(logger, "CREATE", "answers", new_answer.id, success=True)
            return new_answer

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save answer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save answer")


@router.get("/api/questions/{question_id}/answer", response_model=AnswerResponse)
def get_answer(
    question_id: int,
    api_key: Optional[str] = None,
    authorization: Optional[str] = Header(None),
    db: DBSession = Depends(get_db)
):
    """
    Get the answer for a question.
    Instructors can see their own answers (approved or not).
    Supports both JWT token and API key authentication.
    """
    instructor_id = get_instructor_id_from_auth(authorization, api_key, db)
    
    # Get the question
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Verify the meeting belongs to this instructor
    meeting = db.query(ClassMeeting).filter(ClassMeeting.id == question.meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    from models_v2 import Class
    cls = db.query(Class).filter(Class.id == meeting.class_id).first()
    if not cls or cls.instructor_id != instructor_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this answer")

    answer = db.query(Answer).filter(Answer.question_id == question_id).first()

    if not answer:
        raise HTTPException(status_code=404, detail="No answer found for this question")

    return answer


@router.put("/api/questions/{question_id}/answer", response_model=AnswerResponse)
def update_answer(
    question_id: int,
    data: AnswerUpdate,
    api_key: Optional[str] = None,
    authorization: Optional[str] = Header(None),
    db: DBSession = Depends(get_db)
):
    """Update an existing answer. Supports both JWT token and API key authentication."""
    instructor_id = get_instructor_id_from_auth(authorization, api_key, db)
    
    # Get the question
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Verify the meeting belongs to this instructor
    meeting = db.query(ClassMeeting).filter(ClassMeeting.id == question.meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    from models_v2 import Class
    cls = db.query(Class).filter(Class.id == meeting.class_id).first()
    if not cls or cls.instructor_id != instructor_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this answer")

    answer = db.query(Answer).filter(Answer.question_id == question_id).first()

    if not answer:
        raise HTTPException(status_code=404, detail="No answer found for this question")

    try:
        if data.answer_text is not None:
            answer.answer_text = data.answer_text

        if data.is_approved is not None:
            answer.is_approved = data.is_approved

        answer.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(answer)
        log_database_operation(logger, "UPDATE", "answers", answer.id, success=True)
        return answer

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update answer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update answer")


@router.delete("/api/questions/{question_id}/answer")
def delete_answer(
    question_id: int,
    api_key: Optional[str] = None,
    authorization: Optional[str] = Header(None),
    db: DBSession = Depends(get_db)
):
    """Delete an answer. Supports both JWT token and API key authentication."""
    instructor_id = get_instructor_id_from_auth(authorization, api_key, db)
    
    # Get the question
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Verify the meeting belongs to this instructor
    meeting = db.query(ClassMeeting).filter(ClassMeeting.id == question.meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    from models_v2 import Class
    cls = db.query(Class).filter(Class.id == meeting.class_id).first()
    if not cls or cls.instructor_id != instructor_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this answer")

    answer = db.query(Answer).filter(Answer.question_id == question_id).first()

    if not answer:
        raise HTTPException(status_code=404, detail="No answer found for this question")

    try:
        db.delete(answer)
        
        # Update question's has_written_answer flag
        question.has_written_answer = False
        
        db.commit()
        log_database_operation(logger, "DELETE", "answers", answer.id, success=True)
        return {"message": "Answer deleted successfully"}

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete answer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete answer")


@router.post("/api/questions/{question_id}/answer/publish")
def publish_answer(
    question_id: int,
    api_key: Optional[str] = None,
    authorization: Optional[str] = Header(None),
    db: DBSession = Depends(get_db)
):
    """
    Publish an answer (set is_approved=true).
    Once published, students can see the answer.
    Supports both JWT token and API key authentication.
    """
    instructor_id = get_instructor_id_from_auth(authorization, api_key, db)
    
    # Get the question
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Verify the meeting belongs to this instructor
    meeting = db.query(ClassMeeting).filter(ClassMeeting.id == question.meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    from models_v2 import Class
    cls = db.query(Class).filter(Class.id == meeting.class_id).first()
    if not cls or cls.instructor_id != instructor_id:
        raise HTTPException(status_code=403, detail="Not authorized to publish this answer")

    answer = db.query(Answer).filter(Answer.question_id == question_id).first()

    if not answer:
        raise HTTPException(status_code=404, detail="No answer found for this question")

    try:
        answer.is_approved = True
        answer.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(answer)
        log_database_operation(logger, "UPDATE", "answers", answer.id, success=True)

        return {
            "message": "Answer published successfully",
            "answer": {
                "id": answer.id,
                "question_id": answer.question_id,
                "is_approved": answer.is_approved
            }
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to publish answer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to publish answer")
