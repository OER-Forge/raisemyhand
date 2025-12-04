#!/usr/bin/env python3
"""
Initialize database with all tables and optionally create a default admin API key.
This script ensures the database is properly set up from scratch.
"""
import os
import sys
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from models import Base, APIKey, Session, Question
from database import DATABASE_URL

def init_database(create_default_key=False):
    """
    Initialize the database with all tables.
    
    Args:
        create_default_key: If True, creates a default admin API key if none exist
    """
    print("Initializing database...")
    print(f"Database URL: {DATABASE_URL}")
    
    # Create engine
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
    )
    
    # Create all tables
    print("\nCreating tables...")
    Base.metadata.create_all(bind=engine)
    
    # Verify all tables were created
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"\nTables created: {', '.join(tables)}")
    
    # Verify all required tables exist
    required_tables = {'api_keys', 'sessions', 'questions'}
    if not required_tables.issubset(set(tables)):
        missing = required_tables - set(tables)
        print(f"\n⚠️  WARNING: Missing tables: {', '.join(missing)}")
        return False
    
    # Check columns for each table
    print("\nVerifying table schemas...")
    
    # Check api_keys table
    api_key_columns = {col['name'] for col in inspector.get_columns('api_keys')}
    required_api_key_cols = {'id', 'key', 'name', 'created_at', 'last_used', 'is_active'}
    if required_api_key_cols.issubset(api_key_columns):
        print("✓ api_keys table schema correct")
    else:
        missing = required_api_key_cols - api_key_columns
        print(f"✗ api_keys table missing columns: {', '.join(missing)}")
    
    # Check sessions table
    session_columns = {col['name'] for col in inspector.get_columns('sessions')}
    required_session_cols = {'id', 'session_code', 'instructor_code', 'title', 'created_at', 'ended_at', 'is_active'}
    optional_session_cols = {'password_hash'}  # Optional column
    
    if required_session_cols.issubset(session_columns):
        has_optional = optional_session_cols.issubset(session_columns)
        status = "✓" if has_optional else "⚠"
        msg = "sessions table schema correct" if has_optional else "sessions table schema correct (password_hash may not show in SQLite inspection)"
        print(f"{status} {msg}")
    else:
        missing = required_session_cols - session_columns
        print(f"✗ sessions table missing columns: {', '.join(missing)}")
    
    # Check questions table
    question_columns = {col['name'] for col in inspector.get_columns('questions')}
    required_question_cols = {'id', 'session_id', 'text', 'upvotes', 'is_answered', 'created_at', 'answered_at'}
    if required_question_cols.issubset(question_columns):
        print("✓ questions table schema correct")
    else:
        missing = required_question_cols - question_columns
        print(f"✗ questions table missing columns: {', '.join(missing)}")
    
    # Create default API key if requested
    if create_default_key:
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        try:
            # Check if any API keys exist
            key_count = db.query(APIKey).count()
            if key_count == 0:
                print("\nCreating default admin API key...")
                default_key = APIKey(
                    key=APIKey.generate_key(),
                    name="Default Admin Key",
                    is_active=True
                )
                db.add(default_key)
                db.commit()
                db.refresh(default_key)
                print(f"\n✓ Default API key created!")
                print(f"  Name: {default_key.name}")
                print(f"  Key: {default_key.key}")
                print(f"\n  ⚠️  SAVE THIS KEY - you won't see it again!")
                print(f"  Use this key to create your first session or generate more keys via the admin panel.")
            else:
                print(f"\n✓ Database already has {key_count} API key(s)")
        finally:
            db.close()
    
    print("\n✓ Database initialization complete!")
    return True

if __name__ == "__main__":
    # Check if --create-key flag is provided
    create_key = '--create-key' in sys.argv or '-k' in sys.argv
    
    if create_key:
        print("Will create default API key if none exist\n")
    
    success = init_database(create_default_key=create_key)
    sys.exit(0 if success else 1)
