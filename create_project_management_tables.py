import sqlite3
import os
from datetime import datetime

def create_project_management_tables():
    """Create project management tables for freelance service tracking"""
    
    # Connect to the database
    db_path = "jarvistrade.db"
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create project_responses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_responses (
                id TEXT PRIMARY KEY,
                project_request_id TEXT NOT NULL,
                admin_id TEXT NOT NULL,
                response_type TEXT DEFAULT 'quote',
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                proposed_price REAL,
                estimated_duration TEXT,
                terms_conditions TEXT,
                is_approved_by_client BOOLEAN DEFAULT 0,
                is_approved_by_admin BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_request_id) REFERENCES project_requests (id),
                FOREIGN KEY (admin_id) REFERENCES users (id)
            )
        """)
        print("Created project_responses table")
        
        # Create project_invoices table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_invoices (
                id TEXT PRIMARY KEY,
                project_request_id TEXT NOT NULL,
                invoice_number TEXT UNIQUE,
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                description TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                due_date TIMESTAMP,
                paid_at TIMESTAMP,
                payment_method TEXT,
                transaction_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_request_id) REFERENCES project_requests (id),
                FOREIGN KEY (transaction_id) REFERENCES transactions (id)
            )
        """)
        print("Created project_invoices table")
        
        # Create project_progress table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_progress (
                id TEXT PRIMARY KEY,
                project_request_id TEXT NOT NULL,
                admin_id TEXT NOT NULL,
                stage TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                percentage_complete INTEGER DEFAULT 0,
                attachments TEXT,
                is_milestone BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_request_id) REFERENCES project_requests (id),
                FOREIGN KEY (admin_id) REFERENCES users (id)
            )
        """)
        print("Created project_progress table")
        
        # Add indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_project_responses_request_id ON project_responses (project_request_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_project_invoices_request_id ON project_invoices (project_request_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_project_progress_request_id ON project_progress (project_request_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_project_invoices_number ON project_invoices (invoice_number)")
        
        # Commit the changes
        conn.commit()
        print("Successfully created project management tables with indexes")
        
    except Exception as e:
        print(f"Error creating project management tables: {e}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    create_project_management_tables() 