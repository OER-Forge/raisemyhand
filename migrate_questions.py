#!/usr/bin/env python3
"""
Migration script to add missing columns to questions table.
"""
import sqlite3

def migrate():
    conn = sqlite3.connect('raisemyhand.db')
    cursor = conn.cursor()
    
    # Check if columns exist
    cursor.execute("PRAGMA table_info(questions)")
    columns = {row[1] for row in cursor.fetchall()}
    
    print(f"Existing columns: {columns}")
    
    # Add missing columns if they don't exist
    if 'session_id' not in columns:
        print("Adding session_id column...")
        cursor.execute("ALTER TABLE questions ADD COLUMN session_id INTEGER")
    
    if 'is_answered' not in columns:
        print("Adding is_answered column...")
        cursor.execute("ALTER TABLE questions ADD COLUMN is_answered INTEGER DEFAULT 0")
    
    if 'answered_at' not in columns:
        print("Adding answered_at column...")
        cursor.execute("ALTER TABLE questions ADD COLUMN answered_at DATETIME")
    
    conn.commit()
    conn.close()
    print("Migration completed successfully!")

if __name__ == "__main__":
    migrate()
