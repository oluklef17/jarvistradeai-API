#!/usr/bin/env python3
"""
MySQL Migration Script for JarvisTrade

This script helps migrate from SQLite to MySQL with proper data handling
and table creation for production use.

Usage:
    python migrate_to_mysql.py --create-tables
    python migrate_to_mysql.py --migrate-data
    python migrate_to_mysql.py --full-migration
"""

import argparse
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_database_engines():
    """Get both source (SQLite) and target (MySQL) database engines"""
    # Source database (SQLite)
    sqlite_url = "sqlite:///./jarvistrade.db"
    sqlite_engine = create_engine(sqlite_url, echo=False)
    
    # Target database (MySQL)
    mysql_url = os.getenv("DATABASE_URL")
    if not mysql_url:
        print("❌ DATABASE_URL not found in environment variables")
        print("Please set DATABASE_URL=mysql+pymysql://username:password@localhost:3306/jarvistrade_prod")
        sys.exit(1)
    
    try:
        mysql_engine = create_engine(mysql_url, echo=False)
        # Test connection
        with mysql_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ MySQL connection successful")
    except Exception as e:
        print(f"❌ MySQL connection failed: {e}")
        sys.exit(1)
    
    return sqlite_engine, mysql_engine

def create_mysql_tables(mysql_engine):
    """Create all tables in MySQL using the MySQL-optimized models"""
    try:
        print("📋 Creating MySQL tables...")
        
        # Import MySQL-optimized models
        from models_mysql import Base
        
        # Create all tables
        Base.metadata.create_all(bind=mysql_engine)
        print("✅ MySQL tables created successfully")
        
        # Verify table creation
        with mysql_engine.connect() as conn:
            result = conn.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result]
            print(f"📊 Created {len(tables)} tables: {', '.join(tables)}")
            
    except Exception as e:
        print(f"❌ Failed to create MySQL tables: {e}")
        sys.exit(1)

def migrate_data(sqlite_engine, mysql_engine):
    """Migrate data from SQLite to MySQL"""
    try:
        print("🔄 Starting data migration...")
        
        # Get table names from SQLite
        with sqlite_engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            sqlite_tables = [row[0] for row in result if row[0] != 'sqlite_sequence']
        
        print(f"📋 Found {len(sqlite_tables)} tables in SQLite: {', '.join(sqlite_tables)}")
        
        # Migrate each table
        for table_name in sqlite_tables:
            try:
                print(f"🔄 Migrating table: {table_name}")
                
                # Get data from SQLite
                with sqlite_engine.connect() as conn:
                    result = conn.execute(text(f"SELECT * FROM {table_name}"))
                    columns = result.keys()
                    rows = result.fetchall()
                
                if not rows:
                    print(f"   ⚠️  Table {table_name} is empty, skipping")
                    continue
                
                print(f"   📊 Found {len(rows)} rows to migrate")
                
                # Insert data into MySQL
                with mysql_engine.connect() as conn:
                    # Build INSERT statement
                    placeholders = ', '.join(['%s'] * len(columns))
                    insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                    
                    # Execute batch insert
                    conn.execute(text(insert_sql), rows)
                    conn.commit()
                
                print(f"   ✅ Successfully migrated {len(rows)} rows")
                
            except Exception as e:
                print(f"   ❌ Failed to migrate table {table_name}: {e}")
                continue
        
        print("✅ Data migration completed")
        
    except Exception as e:
        print(f"❌ Data migration failed: {e}")
        sys.exit(1)

def verify_migration(sqlite_engine, mysql_engine):
    """Verify that migration was successful by comparing row counts"""
    try:
        print("🔍 Verifying migration...")
        
        # Get table names from MySQL
        with mysql_engine.connect() as conn:
            result = conn.execute(text("SHOW TABLES"))
            mysql_tables = [row[0] for row in result]
        
        for table_name in mysql_tables:
            try:
                # Get SQLite count
                with sqlite_engine.connect() as conn:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    sqlite_count = result.scalar()
                
                # Get MySQL count
                with mysql_engine.connect() as conn:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    mysql_count = result.scalar()
                
                if sqlite_count == mysql_count:
                    print(f"   ✅ {table_name}: {mysql_count} rows (matched)")
                else:
                    print(f"   ⚠️  {table_name}: SQLite={sqlite_count}, MySQL={mysql_count} (mismatch)")
                    
            except Exception as e:
                print(f"   ❌ Error verifying {table_name}: {e}")
        
        print("✅ Migration verification completed")
        
    except Exception as e:
        print(f"❌ Migration verification failed: {e}")

def create_mysql_database():
    """Create MySQL database if it doesn't exist"""
    try:
        # Parse DATABASE_URL to get connection details
        mysql_url = os.getenv("DATABASE_URL")
        if not mysql_url:
            print("❌ DATABASE_URL not found")
            return False
        
        # Extract database name from URL
        if "mysql+pymysql://" in mysql_url:
            db_name = mysql_url.split("/")[-1]
            # Create connection without database name
            base_url = mysql_url.rsplit("/", 1)[0]
            engine = create_engine(base_url, echo=False)
            
            with engine.connect() as conn:
                conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
                conn.commit()
            
            print(f"✅ Database '{db_name}' created/verified successfully")
            return True
            
    except Exception as e:
        print(f"❌ Failed to create database: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="MySQL Migration Script for JarvisTrade")
    parser.add_argument("--create-tables", action="store_true", help="Create MySQL tables")
    parser.add_argument("--migrate-data", action="store_true", help="Migrate data from SQLite to MySQL")
    parser.add_argument("--full-migration", action="store_true", help="Perform full migration (create tables + migrate data)")
    parser.add_argument("--verify", action="store_true", help="Verify migration results")
    
    args = parser.parse_args()
    
    if not any([args.create_tables, args.migrate_data, args.full_migration, args.verify]):
        parser.print_help()
        return
    
    print("🚀 JarvisTrade MySQL Migration Script")
    print("=" * 50)
    
    # Create database if needed
    if not create_mysql_database():
        print("❌ Cannot proceed without database")
        return
    
    # Get database engines
    sqlite_engine, mysql_engine = get_database_engines()
    
    try:
        if args.create_tables or args.full_migration:
            create_mysql_tables(mysql_engine)
        
        if args.migrate_data or args.full_migration:
            migrate_data(sqlite_engine, mysql_engine)
        
        if args.verify or args.full_migration:
            verify_migration(sqlite_engine, mysql_engine)
        
        print("\n🎉 Migration completed successfully!")
        print("\n📝 Next steps:")
        print("1. Update your .env file to use the new MySQL DATABASE_URL")
        print("2. Test your application with the new database")
        print("3. Consider backing up your old SQLite database")
        print("4. Update your deployment scripts to use MySQL")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)
    finally:
        # Close connections
        sqlite_engine.dispose()
        mysql_engine.dispose()

if __name__ == "__main__":
    main()
