"""
Question management routes for v2 API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func
from datetime import datetime
import uuid

from database import get_db
from models_v2 import Question, ClassMeeting, QuestionVote
from schemas_v2 import QuestionCreate, QuestionResponse, QuestionUpdate
from logging_config import get_logger, log_database_operation

router = APIRouter(tags=["questions"])
logger = get_logger(__name__)


@router.post("/api/meetings/{meeting_code}/questions", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
def create_question(
    meeting_code: str,
    question: QuestionCreate,
    student_id: str = None,  # Should come from cookie/session
    db: DBSession = Depends(get_db)
):
    """Submit a new question to a meeting."""
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
                .with_for_update()\
                .scalar()
            next_number = (max_number or 0) + 1

            db_question = Question(
                meeting_id=meeting.id,
                student_id=student_id,
                question_number=next_number,
                text=question.text,
                sanitized_text=question.text,  # TODO: Add profanity filter
                status="approved",  # Default to approved (add moderation later)
                created_at=datetime.utcnow()
            )
            db.add(db_question)
            db.commit()
            db.refresh(db_question)
            log_database_operation(logger, "CREATE", "questions", db_question.id, success=True)
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


@router.post("/api/questions/{question_id}/vote")
def toggle_vote(
    question_id: int,
    student_id: str,  # Should come from cookie/session
    db: DBSession = Depends(get_db)
):
    """Toggle vote on a question."""
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
            question.upvotes = func.greatest(0, question.upvotes - 1)
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
        return {"upvotes": question.upvotes, "action": action}
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating vote count: {e}")
        raise HTTPException(status_code=500, detail="Failed to update vote")


@router.post("/api/questions/{question_id}/mark-answered-in-class")
def mark_answered_in_class(
    question_id: int,
    api_key: str,
    db: DBSession = Depends(get_db)
):
    """Mark question as answered in class (verbal answer)."""
    # Verify API key exists (simplified - full auth in routes_classes)
    from models_v2 import APIKey as APIKeyV2
    key_record = db.query(APIKeyV2).filter(
        APIKeyV2.key == api_key,
        APIKeyV2.is_active == True
    ).first()

    if not key_record:
        raise HTTPException(status_code=401, detail="Invalid API key")

    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    try:
        question.is_answered_in_class = not question.is_answered_in_class
        db.commit()
        db.refresh(question)
        log_database_operation(logger, "UPDATE", "questions", question.id, success=True)
        return {"is_answered_in_class": question.is_answered_in_class}
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to mark question as answered: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update question")


@router.put("/api/questions/{question_id}", response_model=QuestionResponse)
def update_question_status(
    question_id: int,
    data: QuestionUpdate,
    api_key: str,
    db: DBSession = Depends(get_db)
):
    """Update question status (for moderation)."""
    # Verify API key
    from models_v2 import APIKey as APIKeyV2
    key_record = db.query(APIKeyV2).filter(
        APIKeyV2.key == api_key,
        APIKeyV2.is_active == True
    ).first()

    if not key_record:
        raise HTTPException(status_code=401, detail="Invalid API key")

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
