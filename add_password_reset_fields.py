#!/usr/bin/env python3
"""
Database Migration Script: Add Password Reset and Email Verification Fields

This script adds the following fields to the User table:
- password_reset_token: For storing password reset tokens
- password_reset_expires: For storing password reset token expiration
- email_verified: Boolean flag for email verification status
- email_verification_token: For storing email verification tokens
- email_verification_expires: For storing email verification token expiration

Usage:
    python add_password_reset_fields.py
"""

import sqlite3
import os
from datetime import datetime

def add_password_reset_fields():
    """Add password reset and email verification fields to User table"""
    
    # Database file path
    db_path = "jarvistrade.db"
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Connected to database successfully")
        
        # Check if fields already exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        fields_to_add = [
            ("password_reset_token", "TEXT"),
            ("password_reset_expires", "DATETIME"),
            ("email_verified", "BOOLEAN DEFAULT 0"),
            ("email_verification_token", "TEXT"),
            ("email_verification_expires", "DATETIME")
        ]
        
        added_fields = []
        
        for field_name, field_type in fields_to_add:
            if field_name not in columns:
                try:
                    if field_name == "email_verified":
                        # Add boolean field with default value
                        cursor.execute(f"ALTER TABLE users ADD COLUMN {field_name} {field_type}")
                        # Update existing users to have verified emails (for backward compatibility)
                        cursor.execute("UPDATE users SET email_verified = 1 WHERE email_verified IS NULL")
                    else:
                        cursor.execute(f"ALTER TABLE users ADD COLUMN {field_name} {field_type}")
                    
                    added_fields.append(field_name)
                    print(f"✓ Added field: {field_name}")
                    
                except sqlite3.OperationalError as e:
                    print(f"✗ Error adding field {field_name}: {e}")
            else:
                print(f"✓ Field {field_name} already exists")
        
        # Commit changes
        conn.commit()
        
        if added_fields:
            print(f"\nSuccessfully added {len(added_fields)} new fields:")
            for field in added_fields:
                print(f"  - {field}")
        else:
            print("\nNo new fields were added - all fields already exist")
        
        # Verify the changes
        print("\nVerifying table structure...")
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        print("Current User table structure:")
        for column in columns:
            print(f"  {column[1]} ({column[2]}) - Default: {column[4]}")
        
        # Close connection
        conn.close()
        print("\nDatabase connection closed")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        if 'conn' in locals():
            conn.close()
        return False

def main():
    """Main function"""
    print("=" * 60)
    print("Database Migration: Add Password Reset Fields")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = add_password_reset_fields()
    
    print()
    if success:
        print("✅ Migration completed successfully!")
        print("\nNext steps:")
        print("1. Restart your FastAPI application")
        print("2. Test the new password reset and email verification endpoints")
        print("3. Update your frontend to use the new authentication features")
    else:
        print("❌ Migration failed!")
        print("Please check the error messages above and try again")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
