"""
Database migration script to add new columns
Run this script to add the new columns to existing databases
"""

from database import get_db_connection
import logging

logger = logging.getLogger(__name__)

def migrate_database():
    """Add new columns to existing database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("Starting database migration...")
        
        # Add new columns to members table if they don't exist
        columns_to_add = [
            ("mobile_number", "VARCHAR(20)"),
            ("date_of_birth", "DATE"),
            ("sex", "ENUM('Male', 'Female', 'Other')"),
            ("email_notifications_enabled", "BOOLEAN DEFAULT TRUE")
        ]
        
        for column_name, column_def in columns_to_add:
            try:
                cursor.execute(f"ALTER TABLE members ADD COLUMN {column_name} {column_def}")
                print(f"[OK] Added column: {column_name}")
            except Exception as e:
                if "Duplicate column name" in str(e) or "1060" in str(e):
                    print(f"[SKIP] Column {column_name} already exists, skipping...")
                else:
                    print(f"[ERROR] Error adding column {column_name}: {e}")
        
        # Add index on date_of_birth if it doesn't exist
        try:
            cursor.execute("ALTER TABLE members ADD INDEX idx_birthday (date_of_birth)")
            print("[OK] Added index on date_of_birth")
        except Exception as e:
            if "Duplicate key name" in str(e) or "1061" in str(e):
                print("[SKIP] Index idx_birthday already exists, skipping...")
            else:
                print(f"[ERROR] Error adding index: {e}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n[SUCCESS] Database migration completed successfully!")
        
    except Exception as e:
        print(f"[ERROR] Error during migration: {e}")
        raise

if __name__ == '__main__':
    migrate_database()

