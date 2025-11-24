"""
Database migration script to add password_hash column to sessions table.
Run this before starting the server with the new authentication system.
"""

import sqlite3
import os
from pathlib import Path

def migrate_database():
    """Add password_hash column to sessions table if it doesn't exist."""
    
    # Find the database file
    db_path = "raisemyhand.db"
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found. Creating new database.")
        return
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if password_hash column exists
        cursor.execute("PRAGMA table_info(sessions)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'password_hash' not in columns:
            print("Adding password_hash column to sessions table...")
            cursor.execute("""
                ALTER TABLE sessions 
                ADD COLUMN password_hash TEXT NULL
            """)
            conn.commit()
            print("✅ Database migration completed successfully!")
        else:
            print("✅ Database is already up to date (password_hash column exists)")
            
    except sqlite3.Error as e:
        print(f"❌ Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()