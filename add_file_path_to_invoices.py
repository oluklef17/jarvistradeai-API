import sqlite3
import os

def add_file_path_to_invoices():
    """Add file_path column to project_invoices table"""
    
    # Connect to the database
    db_path = "jarvistrade.db"
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if file_path column already exists
        cursor.execute("PRAGMA table_info(project_invoices)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if "file_path" not in columns:
            # Add file_path column
            cursor.execute("""
                ALTER TABLE project_invoices 
                ADD COLUMN file_path TEXT
            """)
            print("Added file_path column to project_invoices table")
        else:
            print("file_path column already exists in project_invoices table")
        
        # Commit the changes
        conn.commit()
        print("Successfully updated project_invoices table")
        
    except Exception as e:
        print(f"Error updating project_invoices table: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    add_file_path_to_invoices() 