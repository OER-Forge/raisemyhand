#!/usr/bin/env python3
"""
Migrate data from SQLite to PostgreSQL for RaiseMyHand

Usage:
    # Export SQLite to JSON
    python scripts/migrate_sqlite_to_postgres.py export --sqlite-url sqlite:///./data/raisemyhand.db

    # Import JSON to PostgreSQL
    python scripts/migrate_sqlite_to_postgres.py import --postgres-url postgresql://user:pass@host:5432/db

    # One-step migration
    python scripts/migrate_sqlite_to_postgres.py migrate \\
        --sqlite-url sqlite:///./data/raisemyhand.db \\
        --postgres-url postgresql://user:pass@host:5432/db
"""
import sys
import os
import argparse
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models_v2 import Base, Instructor, APIKey, Class, ClassMeeting, Question, Answer, QuestionVote


def export_sqlite_to_json(sqlite_url: str, output_file: str = "migration_data.json"):
    """Export all data from SQLite to JSON"""
    print(f"\n📤 Exporting from SQLite: {sqlite_url}")
    print(f"   Output file: {output_file}\n")

    engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})
    Session = sessionmaker(bind=engine)
    session = Session()

    data = {
        "exported_at": datetime.utcnow().isoformat(),
        "source": sqlite_url,
        "instructors": [],
        "api_keys": [],
        "classes": [],
        "class_meetings": [],
        "questions": [],
        "answers": [],
        "question_votes": []
    }

    try:
        # Export instructors
        print("Exporting instructors...", end=" ")
        for instructor in session.query(Instructor).all():
            data["instructors"].append({
                "id": instructor.id,
                "username": instructor.username,
                "email": instructor.email,
                "display_name": instructor.display_name,
                "password_hash": instructor.password_hash,
                "created_at": instructor.created_at.isoformat() if instructor.created_at else None,
                "last_login": instructor.last_login.isoformat() if instructor.last_login else None,
                "is_active": instructor.is_active,
                "role": instructor.role,
                "role_granted_by": instructor.role_granted_by,
                "role_granted_at": instructor.role_granted_at.isoformat() if instructor.role_granted_at else None,
                "deactivated_by": instructor.deactivated_by,
                "deactivated_at": instructor.deactivated_at.isoformat() if instructor.deactivated_at else None,
                "deactivation_reason": instructor.deactivation_reason,
            })
        print(f"✓ {len(data['instructors'])} records")

        # Export API keys
        print("Exporting API keys...", end=" ")
        for api_key in session.query(APIKey).all():
            data["api_keys"].append({
                "id": api_key.id,
                "instructor_id": api_key.instructor_id,
                "key": api_key.key,
                "name": api_key.name,
                "created_at": api_key.created_at.isoformat() if api_key.created_at else None,
                "last_used": api_key.last_used.isoformat() if api_key.last_used else None,
                "is_active": api_key.is_active,
                "revoked_by": api_key.revoked_by,
                "revoked_at": api_key.revoked_at.isoformat() if api_key.revoked_at else None,
                "revocation_reason": api_key.revocation_reason,
            })
        print(f"✓ {len(data['api_keys'])} records")

        # Export classes
        print("Exporting classes...", end=" ")
        for cls in session.query(Class).all():
            data["classes"].append({
                "id": cls.id,
                "instructor_id": cls.instructor_id,
                "name": cls.name,
                "description": cls.description,
                "created_at": cls.created_at.isoformat() if cls.created_at else None,
                "updated_at": cls.updated_at.isoformat() if cls.updated_at else None,
                "is_archived": cls.is_archived,
            })
        print(f"✓ {len(data['classes'])} records")

        # Export class meetings
        print("Exporting class meetings...", end=" ")
        for meeting in session.query(ClassMeeting).all():
            data["class_meetings"].append({
                "id": meeting.id,
                "class_id": meeting.class_id,
                "api_key_id": meeting.api_key_id,
                "meeting_code": meeting.meeting_code,
                "instructor_code": meeting.instructor_code,
                "meeting_name": meeting.meeting_name,
                "is_active": meeting.is_active,
                "created_at": meeting.created_at.isoformat() if meeting.created_at else None,
                "ended_at": meeting.ended_at.isoformat() if meeting.ended_at else None,
            })
        print(f"✓ {len(data['class_meetings'])} records")

        # Export questions
        print("Exporting questions...", end=" ")
        for question in session.query(Question).all():
            data["questions"].append({
                "id": question.id,
                "meeting_id": question.meeting_id,
                "student_id": question.student_id,
                "question_number": question.question_number,
                "text": question.text,
                "sanitized_text": question.sanitized_text,
                "upvotes": question.upvotes,
                "status": question.status,
                "flagged_reason": question.flagged_reason,
                "is_answered_in_class": question.is_answered_in_class,
                "has_written_answer": question.has_written_answer,
                "created_at": question.created_at.isoformat() if question.created_at else None,
                "reviewed_at": question.reviewed_at.isoformat() if question.reviewed_at else None,
            })
        print(f"✓ {len(data['questions'])} records")

        # Export answers
        print("Exporting answers...", end=" ")
        for answer in session.query(Answer).all():
            data["answers"].append({
                "id": answer.id,
                "question_id": answer.question_id,
                "instructor_id": answer.instructor_id,
                "answer_text": answer.answer_text,
                "is_approved": answer.is_approved,
                "created_at": answer.created_at.isoformat() if answer.created_at else None,
                "updated_at": answer.updated_at.isoformat() if answer.updated_at else None,
            })
        print(f"✓ {len(data['answers'])} records")

        # Export question votes
        print("Exporting question votes...", end=" ")
        for vote in session.query(QuestionVote).all():
            data["question_votes"].append({
                "id": vote.id,
                "question_id": vote.question_id,
                "student_id": vote.student_id,
                "created_at": vote.created_at.isoformat() if vote.created_at else None,
            })
        print(f"✓ {len(data['question_votes'])} records")

    finally:
        session.close()

    # Write to JSON file
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"\n✅ Export complete! Saved to: {output_file}")
    print(f"   File size: {os.path.getsize(output_file) / 1024:.1f} KB")

    return output_file


def import_json_to_postgres(postgres_url: str, input_file: str = "migration_data.json"):
    """Import JSON data into PostgreSQL"""
    print(f"\n📥 Importing to PostgreSQL: {postgres_url}")
    print(f"   Input file: {input_file}\n")

    # Load JSON data
    with open(input_file, 'r') as f:
        data = json.load(f)

    print(f"Data exported at: {data.get('exported_at', 'unknown')}")
    print(f"Source: {data.get('source', 'unknown')}\n")

    engine = create_engine(postgres_url)

    # Create all tables
    print("Creating database schema...")
    Base.metadata.create_all(engine)
    print("✓ Schema created\n")

    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Import instructors
        print("Importing instructors...", end=" ")
        for item in data["instructors"]:
            instructor = Instructor(
                id=item["id"],
                username=item["username"],
                email=item["email"],
                display_name=item["display_name"],
                password_hash=item["password_hash"],
                created_at=datetime.fromisoformat(item["created_at"]) if item["created_at"] else None,
                last_login=datetime.fromisoformat(item["last_login"]) if item["last_login"] else None,
                is_active=item["is_active"],
                role=item["role"],
                role_granted_by=item["role_granted_by"],
                role_granted_at=datetime.fromisoformat(item["role_granted_at"]) if item["role_granted_at"] else None,
                deactivated_by=item["deactivated_by"],
                deactivated_at=datetime.fromisoformat(item["deactivated_at"]) if item["deactivated_at"] else None,
                deactivation_reason=item["deactivation_reason"],
            )
            session.add(instructor)
        session.flush()
        print(f"✓ {len(data['instructors'])} records")

        # Import API keys
        print("Importing API keys...", end=" ")
        for item in data["api_keys"]:
            api_key = APIKey(
                id=item["id"],
                instructor_id=item["instructor_id"],
                key=item["key"],
                name=item["name"],
                created_at=datetime.fromisoformat(item["created_at"]) if item["created_at"] else None,
                last_used=datetime.fromisoformat(item["last_used"]) if item["last_used"] else None,
                is_active=item["is_active"],
                revoked_by=item["revoked_by"],
                revoked_at=datetime.fromisoformat(item["revoked_at"]) if item["revoked_at"] else None,
                revocation_reason=item["revocation_reason"],
            )
            session.add(api_key)
        session.flush()
        print(f"✓ {len(data['api_keys'])} records")

        # Import classes
        print("Importing classes...", end=" ")
        for item in data["classes"]:
            cls = Class(
                id=item["id"],
                instructor_id=item["instructor_id"],
                name=item["name"],
                description=item["description"],
                created_at=datetime.fromisoformat(item["created_at"]) if item["created_at"] else None,
                updated_at=datetime.fromisoformat(item["updated_at"]) if item["updated_at"] else None,
                is_archived=item["is_archived"],
            )
            session.add(cls)
        session.flush()
        print(f"✓ {len(data['classes'])} records")

        # Import class meetings
        print("Importing class meetings...", end=" ")
        for item in data["class_meetings"]:
            meeting = ClassMeeting(
                id=item["id"],
                class_id=item["class_id"],
                api_key_id=item["api_key_id"],
                meeting_code=item["meeting_code"],
                instructor_code=item["instructor_code"],
                meeting_name=item["meeting_name"],
                is_active=item["is_active"],
                created_at=datetime.fromisoformat(item["created_at"]) if item["created_at"] else None,
                ended_at=datetime.fromisoformat(item["ended_at"]) if item["ended_at"] else None,
            )
            session.add(meeting)
        session.flush()
        print(f"✓ {len(data['class_meetings'])} records")

        # Import questions
        print("Importing questions...", end=" ")
        for item in data["questions"]:
            question = Question(
                id=item["id"],
                meeting_id=item["meeting_id"],
                student_id=item["student_id"],
                question_number=item["question_number"],
                text=item["text"],
                sanitized_text=item["sanitized_text"],
                upvotes=item["upvotes"],
                status=item["status"],
                flagged_reason=item["flagged_reason"],
                is_answered_in_class=item["is_answered_in_class"],
                has_written_answer=item["has_written_answer"],
                created_at=datetime.fromisoformat(item["created_at"]) if item["created_at"] else None,
                reviewed_at=datetime.fromisoformat(item["reviewed_at"]) if item["reviewed_at"] else None,
            )
            session.add(question)
        session.flush()
        print(f"✓ {len(data['questions'])} records")

        # Import answers
        print("Importing answers...", end=" ")
        for item in data["answers"]:
            answer = Answer(
                id=item["id"],
                question_id=item["question_id"],
                instructor_id=item["instructor_id"],
                answer_text=item["answer_text"],
                is_approved=item["is_approved"],
                created_at=datetime.fromisoformat(item["created_at"]) if item["created_at"] else None,
                updated_at=datetime.fromisoformat(item["updated_at"]) if item["updated_at"] else None,
            )
            session.add(answer)
        session.flush()
        print(f"✓ {len(data['answers'])} records")

        # Import question votes
        print("Importing question votes...", end=" ")
        for item in data["question_votes"]:
            vote = QuestionVote(
                id=item["id"],
                question_id=item["question_id"],
                student_id=item["student_id"],
                created_at=datetime.fromisoformat(item["created_at"]) if item["created_at"] else None,
            )
            session.add(vote)
        session.flush()
        print(f"✓ {len(data['question_votes'])} records")

        # Commit all changes
        print("\nCommitting transaction...", end=" ")
        session.commit()
        print("✓ Done")

        print("\n✅ Import complete!")

    except Exception as e:
        session.rollback()
        print(f"\n❌ Import failed: {e}")
        raise
    finally:
        session.close()


def migrate_direct(sqlite_url: str, postgres_url: str):
    """One-step migration from SQLite to PostgreSQL"""
    temp_file = "migration_data_temp.json"

    try:
        # Export
        export_sqlite_to_json(sqlite_url, temp_file)

        # Import
        import_json_to_postgres(postgres_url, temp_file)

        # Clean up temp file
        os.remove(temp_file)
        print(f"\n🎉 Migration complete!")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        if os.path.exists(temp_file):
            print(f"   Temporary file preserved: {temp_file}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Migrate RaiseMyHand data from SQLite to PostgreSQL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export SQLite to JSON')
    export_parser.add_argument('--sqlite-url', required=True, help='SQLite database URL')
    export_parser.add_argument('--output', default='migration_data.json', help='Output JSON file')

    # Import command
    import_parser = subparsers.add_parser('import', help='Import JSON to PostgreSQL')
    import_parser.add_argument('--postgres-url', required=True, help='PostgreSQL database URL')
    import_parser.add_argument('--input', default='migration_data.json', help='Input JSON file')

    # Migrate command
    migrate_parser = subparsers.add_parser('migrate', help='One-step migration')
    migrate_parser.add_argument('--sqlite-url', required=True, help='SQLite database URL')
    migrate_parser.add_argument('--postgres-url', required=True, help='PostgreSQL database URL')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        if args.command == 'export':
            export_sqlite_to_json(args.sqlite_url, args.output)
        elif args.command == 'import':
            import_json_to_postgres(args.postgres_url, args.input)
        elif args.command == 'migrate':
            migrate_direct(args.sqlite_url, args.postgres_url)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
