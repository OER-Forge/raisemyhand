"""
Database models for RaiseMyHand v2.0
Implements hierarchical architecture: Instructor → Class → ClassMeeting → Question → Answer
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import secrets

Base = declarative_base()


class Instructor(Base):
    """Instructor with persistent identity."""
    __tablename__ = "instructors"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, nullable=True, index=True)
    display_name = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)  # For instructor login
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, index=True)

    # Relationships
    api_keys = relationship("APIKey", back_populates="instructor", cascade="all, delete-orphan")
    classes = relationship("Class", back_populates="instructor", cascade="all, delete-orphan")
    answers = relationship("Answer", back_populates="instructor", cascade="all, delete-orphan")


class APIKey(Base):
    """API keys for instructor authentication, now tied to instructor identity."""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    instructor_id = Column(Integer, ForeignKey("instructors.id", ondelete="CASCADE"), nullable=False, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)  # Human-readable name for the key
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    last_used = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, index=True)

    # Relationships
    instructor = relationship("Instructor", back_populates="api_keys")
    class_meetings = relationship("ClassMeeting", back_populates="api_key")

    @staticmethod
    def generate_key():
        """Generate a secure API key."""
        return f"rmh_{secrets.token_urlsafe(32)}"


class Class(Base):
    """A class/course (e.g., 'CS 101 - Fall 2024')."""
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    instructor_id = Column(Integer, ForeignKey("instructors.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)  # e.g., "CS 101 - Fall 2024"
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_archived = Column(Boolean, default=False, index=True)

    # Relationships
    instructor = relationship("Instructor", back_populates="classes")
    meetings = relationship("ClassMeeting", back_populates="class_obj", cascade="all, delete-orphan")

    # Composite index for instructor's active classes
    __table_args__ = (
        Index('ix_classes_instructor_archived', 'instructor_id', 'is_archived'),
    )


class ClassMeeting(Base):
    """A class meeting/session (replaces Session model)."""
    __tablename__ = "class_meetings"

    id = Column(Integer, primary_key=True, index=True)
    class_id = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id", ondelete="SET NULL"), nullable=True, index=True)
    meeting_code = Column(String, unique=True, index=True, nullable=False)  # For students
    instructor_code = Column(String, unique=True, index=True, nullable=False)  # For instructor
    title = Column(String, nullable=False)  # e.g., "Lecture 5: Linked Lists"
    password_hash = Column(String, nullable=True)  # Optional session password
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, index=True)

    # Relationships
    class_obj = relationship("Class", back_populates="meetings")
    api_key = relationship("APIKey", back_populates="class_meetings")
    questions = relationship("Question", back_populates="meeting", cascade="all, delete-orphan")

    # Composite indexes
    __table_args__ = (
        Index('ix_meetings_class_active', 'class_id', 'is_active'),
    )

    @staticmethod
    def generate_code(length=32):
        """Generate a random alphanumeric code."""
        return secrets.token_urlsafe(length)[:length]


class Question(Base):
    """A question submitted by a student, with moderation support."""
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("class_meetings.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(String, nullable=False, index=True)  # Anonymous UUID
    question_number = Column(Integer, nullable=False)  # Permanent display number (Q1, Q2, Q3...)
    text = Column(Text, nullable=False)  # Original text
    sanitized_text = Column(Text, nullable=True)  # Profanity redacted version
    upvotes = Column(Integer, default=0, index=True)
    status = Column(String, default="approved", index=True)  # pending/approved/rejected/flagged
    flagged_reason = Column(String, nullable=True)  # profanity/spam/inappropriate
    is_answered_in_class = Column(Boolean, default=False, index=True)  # Answered verbally during session
    has_written_answer = Column(Boolean, default=False, index=True)  # Has written answer (computed)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    reviewed_at = Column(DateTime, nullable=True)

    # Relationships
    meeting = relationship("ClassMeeting", back_populates="questions")
    answer = relationship("Answer", back_populates="question", uselist=False, cascade="all, delete-orphan")
    votes = relationship("QuestionVote", back_populates="question", cascade="all, delete-orphan")

    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('meeting_id', 'question_number', name='uq_meeting_question_number'),
        Index('ix_questions_meeting_question_number', 'meeting_id', 'question_number'),
        Index('ix_questions_meeting_upvotes', 'meeting_id', 'upvotes'),
        Index('ix_questions_meeting_status', 'meeting_id', 'status'),
        Index('ix_questions_student', 'student_id', 'created_at'),  # For rate limiting
    )


class Answer(Base):
    """Written answer from instructor to a question."""
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    instructor_id = Column(Integer, ForeignKey("instructors.id", ondelete="CASCADE"), nullable=False, index=True)
    answer_text = Column(Text, nullable=False)  # Markdown supported
    is_approved = Column(Boolean, default=False, index=True)  # Published to students
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    question = relationship("Question", back_populates="answer")
    instructor = relationship("Instructor", back_populates="answers")

    # Composite index for instructor's answers
    __table_args__ = (
        Index('ix_answers_instructor_approved', 'instructor_id', 'is_approved'),
    )


class QuestionVote(Base):
    """Track individual votes to prevent duplicate voting."""
    __tablename__ = "question_votes"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(String, nullable=False, index=True)  # Anonymous UUID
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    question = relationship("Question", back_populates="votes")

    # Prevent duplicate votes
    __table_args__ = (
        UniqueConstraint('question_id', 'student_id', name='uq_question_student_vote'),
        Index('ix_votes_student', 'student_id', 'created_at'),  # For user vote history
    )
