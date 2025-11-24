"""
Database initialization script
Run this script once to set up the database tables and default admin account
"""

from database import init_database
import sys

if __name__ == '__main__':
    try:
        print("Initializing database...")
        init_database()
        print("✅ Database initialized successfully!")
        print("\nDefault admin credentials:")
        print("  Username: admin")
        print("  Password: admin123")
        print("\n⚠️  Please change the default password after first login!")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        sys.exit(1)



