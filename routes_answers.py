"""
Written answer management routes for v2 API (Phase 5 - Issue #21)
Instructors can write, edit, publish, and delete answers to questions.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DBSession
from datetime import datetime
from typing import Optional

from database import get_db
from models_v2 import Answer, Question, ClassMeeting, APIKey as APIKeyV2
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
    api_key: str,
    db: DBSession = Depends(get_db)
):
    """
    Create or update a written answer to a question.
    Instructors can save answers as drafts (is_approved=false) or publish immediately.
    """
    key_record = verify_api_key_v2(api_key, db)
    question = verify_question_ownership(question_id, key_record, db)

    try:
        # Check if answer already exists
        existing_answer = db.query(Answer).filter(Answer.question_id == question_id).first()

        if existing_answer:
            # Update existing answer
            existing_answer.answer_text = data.answer_text
            existing_answer.is_approved = data.is_approved
            existing_answer.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing_answer)
            log_database_operation(logger, "UPDATE", "answers", existing_answer.id, success=True)
            return existing_answer
        else:
            # Create new answer
            new_answer = Answer(
                question_id=question_id,
                instructor_id=key_record.instructor_id,
                answer_text=data.answer_text,
                is_approved=data.is_approved,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(new_answer)
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
    api_key: str,
    db: DBSession = Depends(get_db)
):
    """
    Get the answer for a question.
    Instructors can see their own answers (approved or not).
    """
    key_record = verify_api_key_v2(api_key, db)
    question = verify_question_ownership(question_id, key_record, db)

    answer = db.query(Answer).filter(Answer.question_id == question_id).first()

    if not answer:
        raise HTTPException(status_code=404, detail="No answer found for this question")

    return answer


@router.put("/api/questions/{question_id}/answer", response_model=AnswerResponse)
def update_answer(
    question_id: int,
    data: AnswerUpdate,
    api_key: str,
    db: DBSession = Depends(get_db)
):
    """Update an existing answer."""
    key_record = verify_api_key_v2(api_key, db)
    question = verify_question_ownership(question_id, key_record, db)

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
    api_key: str,
    db: DBSession = Depends(get_db)
):
    """Delete an answer."""
    key_record = verify_api_key_v2(api_key, db)
    question = verify_question_ownership(question_id, key_record, db)

    answer = db.query(Answer).filter(Answer.question_id == question_id).first()

    if not answer:
        raise HTTPException(status_code=404, detail="No answer found for this question")

    try:
        db.delete(answer)
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
    api_key: str,
    db: DBSession = Depends(get_db)
):
    """
    Publish an answer (set is_approved=true).
    Once published, students can see the answer.
    """
    key_record = verify_api_key_v2(api_key, db)
    question = verify_question_ownership(question_id, key_record, db)

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
