"""
Question management routes for v2 API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header, BackgroundTasks, Request
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func
from datetime import datetime
from typing import Optional
import uuid
from better_profanity import profanity
import asyncio

from database import get_db
from models_v2 import Question, ClassMeeting, QuestionVote
from schemas_v2 import QuestionCreate, QuestionResponse, QuestionUpdate
from logging_config import get_logger, log_database_operation
from rate_limiter import limiter

router = APIRouter(tags=["questions"])
logger = get_logger(__name__)

# Initialize profanity filter
profanity.load_censor_words()


@router.post("/api/meetings/{meeting_code}/questions", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("500/minute")
async def create_question(
    request: Request,
    meeting_code: str,
    question: QuestionCreate,
    background_tasks: BackgroundTasks,
    student_id: str = None,  # Should come from cookie/session
    db: DBSession = Depends(get_db),
    authorization: str = Header(None)
):
    """Submit a new question to a meeting. Rate limited to 10 questions per minute per IP."""
    # Check maintenance mode
    from security import check_maintenance_mode, verify_jwt_token
    from models_v2 import Instructor
    
    user_role = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        payload = verify_jwt_token(token)
        if payload:
            sub = payload.get("sub")
            if sub == "admin":
                user_role = "SUPER_ADMIN"
            else:
                try:
                    instructor_id = int(sub)
                    instructor = db.query(Instructor).filter(Instructor.id == instructor_id).first()
                    if instructor:
                        user_role = instructor.role
                except (ValueError, TypeError):
                    pass
    
    if check_maintenance_mode(db, user_role):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System is currently in maintenance mode. Questions cannot be submitted at this time."
        )
    
    meeting = db.query(ClassMeeting).filter(
        ClassMeeting.meeting_code == meeting_code,
        ClassMeeting.is_active == True
    ).first()

    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found or inactive")

    # Generate student_id if not provided (anonymous UUID)
    if not student_id:
        student_id = str(uuid.uuid4())

    # Get next question number with retry logic for race conditions
    max_retries = 3
    for attempt in range(max_retries):
        try:
            max_number = db.query(func.max(Question.question_number))\
                .filter(Question.meeting_id == meeting.id)\
                .scalar()
            next_number = (max_number or 0) + 1

            # Check for profanity (strip markdown syntax first to avoid false negatives)
            import re
            from models_config import SystemConfig
            
            # Check if profanity filter is enabled
            profanity_filter_enabled = SystemConfig.get_value(db, "profanity_filter_enabled", default=True)
            
            # Remove markdown formatting characters for profanity check
            text_without_markdown = re.sub(r'[*_`~\[\]()#]', ' ', question.text)
            # Convert to lowercase for case-insensitive matching
            contains_profanity = profanity.contains_profanity(text_without_markdown.lower())
            
            # If filter is enabled, censor and approve; if disabled, flag but don't censor
            if profanity_filter_enabled:
                question_status = "flagged" if contains_profanity else "approved"
                flagged_reason = "profanity" if contains_profanity else None
                sanitized = profanity.censor(question.text) if contains_profanity else question.text
            else:
                # Filter disabled: flag for review but don't censor
                question_status = "flagged" if contains_profanity else "approved"
                flagged_reason = "profanity" if contains_profanity else None
                sanitized = question.text  # Keep uncensored

            db_question = Question(
                meeting_id=meeting.id,
                student_id=student_id,
                question_number=next_number,
                text=question.text,
                sanitized_text=sanitized,
                status=question_status,
                flagged_reason=flagged_reason,
                created_at=datetime.utcnow()
            )
            db.add(db_question)
            db.commit()
            db.refresh(db_question)
            log_database_operation(logger, "CREATE", "questions", db_question.id, success=True)
            
            # Broadcast new question to all connected clients for this meeting
            try:
                from main import manager
                broadcast_message = {
                    "type": "new_question",
                    "question": {
                        "id": db_question.id,
                        "meeting_id": db_question.meeting_id,
                        "student_id": db_question.student_id,
                        "question_number": db_question.question_number,
                        "text": db_question.text,
                        "sanitized_text": db_question.sanitized_text,
                        "status": db_question.status,
                        "flagged_reason": db_question.flagged_reason,
                        "upvotes": db_question.upvotes,
                        "is_answered_in_class": db_question.is_answered_in_class,
                        "has_written_answer": db_question.has_written_answer,
                        "answer": None,
                        "created_at": db_question.created_at.isoformat()
                    }
                }
                # Use await since we made the function async
                await manager.broadcast(broadcast_message, meeting_code)
                logger.debug(f"Broadcasted new question {db_question.id} to meeting {meeting_code}")
            except Exception as e:
                logger.warning(f"Broadcast error (non-critical): {e}")
            
            break
        except Exception as e:
            db.rollback()
            if "unique constraint" in str(e).lower() or "duplicate" in str(e).lower():
                if attempt < max_retries - 1:
                    continue
                else:
                    logger.error(f"Failed to create question after {max_retries} attempts: {e}")
                    raise HTTPException(status_code=500, detail="Failed to create question due to concurrent submissions")
            else:
                logger.error(f"Error creating question: {e}")
                raise HTTPException(status_code=500, detail="Failed to create question")

    return db_question


@router.put("/api/questions/{question_id}/edit")
@limiter.limit("20/minute")
def edit_question(
    request: Request,
    question_id: int,
    question_update: QuestionCreate,
    student_id: str,
    db: DBSession = Depends(get_db)
):
    """Edit a question. Only allowed within 10 minutes by the original submitter."""
    question = db.query(Question).filter(Question.id == question_id).first()
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Verify ownership
    if question.student_id != student_id:
        raise HTTPException(status_code=403, detail="You can only edit your own questions")
    
    # Check time limit (10 minutes)
    from datetime import datetime, timedelta
    time_since_creation = datetime.utcnow() - question.created_at
    if time_since_creation > timedelta(minutes=10):
        raise HTTPException(status_code=403, detail="Questions can only be edited within 10 minutes of submission")
    
    # Check for profanity in updated text
    import re
    from models_config import SystemConfig
    
    profanity_filter_enabled = SystemConfig.get_value(db, "profanity_filter_enabled", default=True)
    text_without_markdown = re.sub(r'[*_`~\[\]()#]', ' ', question_update.text)
    contains_profanity = profanity.contains_profanity(text_without_markdown.lower())
    
    if profanity_filter_enabled:
        question_status = "flagged" if contains_profanity else "approved"
        flagged_reason = "profanity" if contains_profanity else None
        sanitized = profanity.censor(question_update.text) if contains_profanity else question_update.text
    else:
        question_status = "flagged" if contains_profanity else "approved"
        flagged_reason = "profanity" if contains_profanity else None
        sanitized = question_update.text
    
    try:
        # Update question text
        question.text = question_update.text
        question.sanitized_text = sanitized
        question.status = question_status
        question.flagged_reason = flagged_reason
        
        db.commit()
        db.refresh(question)
        log_database_operation(logger, "UPDATE", "questions", question.id, success=True)
        
        # Broadcast update to all connected clients
        try:
            from main import manager
            meeting = db.query(ClassMeeting).filter(ClassMeeting.id == question.meeting_id).first()
            if meeting:
                broadcast_message = {
                    "type": "question_updated",
                    "question_id": question.id,
                    "text": question.text,
                    "sanitized_text": question.sanitized_text,
                    "status": question.status,
                    "flagged_reason": question.flagged_reason
                }
                try:
                    asyncio.create_task(manager.broadcast(broadcast_message, meeting.meeting_code))
                except RuntimeError:
                    logger.debug("Could not create async task for broadcast")
        except Exception as e:
            logger.warning(f"Broadcast error (non-critical): {e}")
        
        return question
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating question: {e}")
        raise HTTPException(status_code=500, detail="Failed to update question")


@router.post("/api/questions/{question_id}/vote")
@limiter.limit("500/minute")
def toggle_vote(
    request: Request,
    question_id: int,
    student_id: str,  # Should come from cookie/session
    db: DBSession = Depends(get_db)
):
    """Toggle vote on a question. Rate limited to 30 votes per minute per IP."""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # Check if vote already exists
    existing_vote = db.query(QuestionVote).filter(
        QuestionVote.question_id == question_id,
        QuestionVote.student_id == student_id
    ).first()

    try:
        if existing_vote:
            # Remove vote
            db.delete(existing_vote)
            question.upvotes = max(0, question.upvotes - 1)
            action = "removed"
        else:
            # Add vote
            vote = QuestionVote(
                question_id=question_id,
                student_id=student_id,
                created_at=datetime.utcnow()
            )
            db.add(vote)
            question.upvotes += 1
            action = "added"

        db.commit()
        db.refresh(question)
        log_database_operation(logger, "UPDATE", "questions", question.id, success=True)
        
        # Broadcast vote update to all connected clients for this meeting
        try:
            from main import manager
            meeting = db.query(ClassMeeting).filter(ClassMeeting.id == question.meeting_id).first()
            if meeting:
                broadcast_message = {
                    "type": "upvote",
                    "question_id": question.id,
                    "upvotes": question.upvotes
                }
                try:
                    asyncio.create_task(manager.broadcast(broadcast_message, meeting.meeting_code))
                except RuntimeError:
                    logger.debug("Could not create async task for broadcast")
        except Exception as e:
            logger.warning(f"Broadcast error (non-critical): {e}")
        
        return {"upvotes": question.upvotes, "action": action}
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating vote count: {e}")
        raise HTTPException(status_code=500, detail="Failed to update vote")


@router.post("/api/questions/{question_id}/mark-answered-in-class")
@limiter.limit("20/minute")
def mark_answered_in_class(
    request: Request,
    question_id: int,
    api_key: Optional[str] = None,
    authorization: Optional[str] = Header(None),
    db: DBSession = Depends(get_db)
):
    """Mark question as answered in class (verbal answer) - supports JWT and API key auth. Rate limited to 20 per minute."""
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
        from models_v2 import APIKey as APIKeyV2
        key_record = db.query(APIKeyV2).filter(
            APIKeyV2.key == api_key,
            APIKeyV2.is_active == True
        ).first()
        if not key_record:
            raise HTTPException(status_code=401, detail="Invalid API key")
    elif instructor_id is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    try:
        question.is_answered_in_class = not question.is_answered_in_class
        db.commit()
        db.refresh(question)
        log_database_operation(logger, "UPDATE", "questions", question.id, success=True)
        
        # Broadcast answer status update to all connected clients for this meeting
        try:
            from main import manager
            meeting = db.query(ClassMeeting).filter(ClassMeeting.id == question.meeting_id).first()
            if meeting:
                broadcast_message = {
                    "type": "answer_status",
                    "question_id": question.id,
                    "is_answered_in_class": question.is_answered_in_class
                }
                try:
                    asyncio.create_task(manager.broadcast(broadcast_message, meeting.meeting_code))
                except RuntimeError:
                    logger.debug("Could not create async task for broadcast")
        except Exception as e:
            logger.warning(f"Broadcast error (non-critical): {e}")
        
        return {"is_answered_in_class": question.is_answered_in_class}
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to mark question as answered: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update question")


@router.put("/api/questions/{question_id}", response_model=QuestionResponse)
@limiter.limit("20/minute")
def update_question_status(
    request: Request,
    question_id: int,
    data: QuestionUpdate,
    api_key: Optional[str] = None,
    authorization: Optional[str] = Header(None),
    db: DBSession = Depends(get_db)
):
    """Update question status (for moderation) - supports JWT and API key auth."""
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
        from models_v2 import APIKey as APIKeyV2
        key_record = db.query(APIKeyV2).filter(
            APIKeyV2.key == api_key,
            APIKeyV2.is_active == True
        ).first()
        if not key_record:
            raise HTTPException(status_code=401, detail="Invalid API key")
    elif instructor_id is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    try:
        if data.status is not None:
            question.status = data.status
            question.reviewed_at = datetime.utcnow()

        if data.is_answered_in_class is not None:
            question.is_answered_in_class = data.is_answered_in_class

        db.commit()
        db.refresh(question)
        log_database_operation(logger, "UPDATE", "questions", question.id, success=True)
        return question
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update question: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update question")


@router.get("/api/meetings/{instructor_code}/flagged-questions")
def get_flagged_questions(
    instructor_code: str,
    api_key: Optional[str] = None,
    authorization: Optional[str] = Header(None),
    db: DBSession = Depends(get_db)
):
    """
    Get all flagged questions for a meeting.
    Authentication: instructor_code in URL is sufficient (proves access to instructor link).
    """

    # Get the meeting by instructor_code
    meeting = db.query(ClassMeeting).filter(
        ClassMeeting.instructor_code == instructor_code
    ).first()

    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # instructor_code itself is authentication - no additional auth required

    # Get flagged questions
    flagged_questions = db.query(Question).filter(
        Question.meeting_id == meeting.id,
        Question.status == "flagged"
    ).order_by(Question.created_at.desc()).all()

    return {"questions": flagged_questions}


@router.post("/api/questions/{question_id}/approve")
@limiter.limit("20/minute")
def approve_question(
    request: Request,
    question_id: int,
    db: DBSession = Depends(get_db)
):
    """
    Approve a flagged question. Rate limited to 20 per minute.
    Note: This endpoint relies on the instructor being authenticated via the instructor page.
    No additional auth required since this is called from an authenticated context.
    """

    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    try:
        question.status = "approved"
        question.reviewed_at = datetime.utcnow()
        db.commit()
        db.refresh(question)
        log_database_operation(logger, "UPDATE", "questions", question.id, success=True)
        return {"message": "Question approved", "question": question}
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to approve question: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to approve question")


@router.post("/api/questions/{question_id}/reject")
@limiter.limit("20/minute")
def reject_question(
    request: Request,
    question_id: int,
    db: DBSession = Depends(get_db)
):
    """
    Reject a flagged question (hides it from view). Rate limited to 20 per minute.
    Note: This endpoint relies on the instructor being authenticated via the instructor page.
    No additional auth required since this is called from an authenticated context.
    """

    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    try:
        question.status = "rejected"
        question.reviewed_at = datetime.utcnow()
        db.commit()
        db.refresh(question)
        log_database_operation(logger, "UPDATE", "questions", question.id, success=True)
        return {"message": "Question rejected", "question": question}
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to reject question: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to reject question")


@router.delete("/api/questions/{question_id}")
@limiter.limit("20/minute")
def delete_question(
    request: Request,
    question_id: int,
    db: DBSession = Depends(get_db)
):
    """
    Delete a question permanently. Rate limited to 20 per minute.
    Note: This endpoint relies on the instructor being authenticated via the instructor page.
    No additional auth required since this is called from an authenticated context.
    """

    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    try:
        db.delete(question)
        db.commit()
        log_database_operation(logger, "DELETE", "questions", question_id, success=True)
        return {"message": "Question deleted successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete question: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete question")
