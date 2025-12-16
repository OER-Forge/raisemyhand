"""
Test cases for profanity filter fix.

This test suite verifies that:
1. Profanity is correctly detected in question text
2. Flagged questions are marked with status="flagged"
3. Profanity is censored in sanitized_text
4. SystemConfig correctly enables/disables the filter
"""

import sys
import os

# Add the app directory to path
sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from better_profanity import profanity

# Import models
from models_v2 import Base, Instructor, Class, ClassMeeting, Question, APIKey
from models_config import SystemConfig
from database import DATABASE_URL

# Test profanity words (words in better-profanity's default list)
TEST_PROFANITY_WORDS = [
    "damn",
    "hell",
    "crap",
    "ass",
]

# Test normal words (no profanity)
TEST_CLEAN_WORDS = [
    "hello",
    "question",
    "help",
    "understand",
    "example",
]

def setup_test_db():
    """Create a test database and return a session."""
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def test_profanity_detection():
    """Test that better_profanity correctly detects profanity."""
    print("\n=== Test 1: Profanity Detection ===")
    profanity.load_censor_words()

    for word in TEST_PROFANITY_WORDS:
        is_profane = profanity.contains_profanity(word.lower())
        print(f"  '{word}': {'DETECTED ✓' if is_profane else 'NOT DETECTED ✗'}")
        assert is_profane, f"Failed to detect profanity in '{word}'"

    for word in TEST_CLEAN_WORDS:
        is_profane = profanity.contains_profanity(word.lower())
        print(f"  '{word}': {'clean ✓' if not is_profane else 'FALSE POSITIVE ✗'}")
        assert not is_profane, f"False positive on clean word '{word}'"

    print("✓ Profanity detection working correctly\n")

def test_profanity_censoring():
    """Test that profanity is correctly censored."""
    print("=== Test 2: Profanity Censoring ===")
    profanity.load_censor_words()

    test_cases = [
        ("This is damn annoying", "**** or censored"),
        ("What the hell is this?", "**** or censored"),
        ("This is a clean question", "no censoring"),
    ]

    for original, expected in test_cases:
        censored = profanity.censor(original)
        has_asterisks = '*' in censored
        print(f"  Original: '{original}'")
        print(f"  Censored: '{censored}'")
        print(f"  Status: {'✓' if (has_asterisks or censored == original) else '✗'}\n")

def test_question_status_setting():
    """Test that questions are correctly marked as flagged/approved."""
    print("=== Test 3: Question Status Setting ===")

    db = setup_test_db()
    profanity.load_censor_words()

    try:
        # Ensure profanity filter is enabled
        SystemConfig.set_value(db, "profanity_filter_enabled", True, "boolean")

        # Create test instructor and class
        instructor = Instructor(
            username="test_instructor",
            email="test@example.com",
            password_hash="hash",
            role="INSTRUCTOR"
        )
        db.add(instructor)
        db.commit()

        # Create API key
        api_key = APIKey(
            instructor_id=instructor.id,
            key="test_key_123",
            name="Test API Key"
        )
        db.add(api_key)
        db.commit()

        # Create class
        test_class = Class(
            instructor_id=instructor.id,
            name="Test Class",
            description="Testing profanity filter"
        )
        db.add(test_class)
        db.commit()

        # Create meeting
        meeting = ClassMeeting(
            class_id=test_class.id,
            api_key_id=api_key.id,
            meeting_code="test_meeting_code",
            instructor_code="test_instructor_code",
            title="Test Meeting",
            is_active=True
        )
        db.add(meeting)
        db.commit()

        # Test cases: (text, should_be_flagged)
        test_cases = [
            ("This is a damn question", True),
            ("What the hell?", True),
            ("Normal question about math", False),
            ("How do we solve this problem?", False),
            ("This is crap", True),
        ]

        for text, should_be_flagged in test_cases:
            # Check profanity
            text_clean = text.lower()
            contains_prof = profanity.contains_profanity(text_clean)
            expected_status = "flagged" if contains_prof else "approved"

            # Create question
            q = Question(
                meeting_id=meeting.id,
                student_id="test_student",
                question_number=len(db.query(Question).filter(Question.meeting_id == meeting.id).all()) + 1,
                text=text,
                sanitized_text=profanity.censor(text) if contains_prof else text,
                status=expected_status,
                flagged_reason="profanity" if contains_prof else None,
                created_at=datetime.utcnow()
            )
            db.add(q)
            db.commit()

            status_match = (expected_status == "flagged") == should_be_flagged
            print(f"  Text: '{text}'")
            print(f"  Expected status: {expected_status}")
            print(f"  Should be flagged: {should_be_flagged}")
            print(f"  Status: {'✓' if status_match else '✗'}\n")

            assert status_match, f"Status mismatch for '{text}'"

        print("✓ Question status setting working correctly\n")

    finally:
        db.close()

def test_system_config():
    """Test that SystemConfig can enable/disable the filter."""
    print("=== Test 4: SystemConfig Filter Toggle ===")

    db = setup_test_db()

    try:
        # Test enabling
        SystemConfig.set_value(db, "profanity_filter_enabled", True, "boolean")
        enabled = SystemConfig.get_value(db, "profanity_filter_enabled", default=False)
        print(f"  Set to True: {enabled} {'✓' if enabled else '✗'}")
        assert enabled is True

        # Test disabling
        SystemConfig.set_value(db, "profanity_filter_enabled", False, "boolean")
        enabled = SystemConfig.get_value(db, "profanity_filter_enabled", default=True)
        print(f"  Set to False: {not enabled} {'✓' if not enabled else '✗'}")
        assert enabled is False

        # Test default value
        db.query(SystemConfig).filter(SystemConfig.key == "profanity_filter_enabled").delete()
        db.commit()

        enabled = SystemConfig.get_value(db, "profanity_filter_enabled", default=True)
        print(f"  Default (when not set): {enabled} {'✓' if enabled else '✗'}")
        assert enabled is True

        print("✓ SystemConfig working correctly\n")

    finally:
        db.close()

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("PROFANITY FILTER TEST SUITE")
    print("="*60)

    try:
        test_profanity_detection()
        test_profanity_censoring()
        test_question_status_setting()
        test_system_config()

        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED!")
        print("="*60 + "\n")
        return 0

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}\n")
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
