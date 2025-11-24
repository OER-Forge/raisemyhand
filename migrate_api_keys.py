#!/usr/bin/env python3
"""
Migration script to add API keys table to the database.
"""

import sqlite3
import os

def migrate_api_keys():
    """Add API keys table to the database."""
    db_path = "raisemyhand.db"
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found. Please run the main application first.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if api_keys table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='api_keys'
        """)
        
        if cursor.fetchone():
            print("✅ API keys table already exists!")
            return
        
        print("Adding api_keys table...")
        
        # Create api_keys table
        cursor.execute("""
            CREATE TABLE api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key VARCHAR UNIQUE NOT NULL,
                name VARCHAR NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_used DATETIME,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE UNIQUE INDEX ix_api_keys_key ON api_keys (key)")
        cursor.execute("CREATE INDEX ix_api_keys_id ON api_keys (id)")
        
        conn.commit()
        print("✅ API keys table created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating API keys table: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_api_keys()