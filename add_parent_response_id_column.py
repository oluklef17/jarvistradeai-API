#!/usr/bin/env python3
"""
Database migration script to add parent_response_id column to project_responses table.
This script adds the missing column that was added to the model but not yet migrated to the database.
"""

import sqlite3
import os
from pathlib import Path

def add_parent_response_id_column():
    """Add parent_response_id column to project_responses table"""
    
    # Get the database file path
    db_path = Path(__file__).parent / "jarvistrade.db"
    
    if not db_path.exists():
        print(f"Database file not found at {db_path}")
        return
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(project_responses)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if "parent_response_id" in columns:
            print("parent_response_id column already exists in project_responses table")
            return
        
        # Add the parent_response_id column
        cursor.execute("""
            ALTER TABLE project_responses 
            ADD COLUMN parent_response_id TEXT 
            REFERENCES project_responses(id)
        """)
        
        # Commit the changes
        conn.commit()
        print("Successfully added parent_response_id column to project_responses table")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Adding parent_response_id column to project_responses table...")
    add_parent_response_id_column()
    print("Migration completed!") 