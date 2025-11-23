import mysql.connector
from mysql.connector import Error
from config import Config
import logging

logger = logging.getLogger(__name__)

def get_db_connection():
    """Create and return a database connection"""
    try:
        connection = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DATABASE,
            autocommit=False
        )
        return connection
    except Error as e:
        logger.error(f"Error connecting to MySQL: {e}")
        raise

def init_database():
    """Initialize database tables if they don't exist"""
    try:
        # First connect without database to create it if needed
        connection = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD
        )
        cursor = connection.cursor()
        
        # Create database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DATABASE}")
        cursor.close()
        connection.close()
        
        # Now connect to the database and create tables
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Create members table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS members (
                id INT AUTO_INCREMENT PRIMARY KEY,
                admission_number VARCHAR(20) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(255) NOT NULL,
                mobile_number VARCHAR(20),
                date_of_birth DATE,
                sex ENUM('Male', 'Female', 'Other'),
                join_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                plan_type ENUM('1 Day Pass', 'Monthly', '3 Months', '6 Months', '12 Months') NOT NULL,
                access_type ENUM('One-time', 'Multiple') NOT NULL DEFAULT 'One-time',
                start_date DATE NOT NULL,
                expiry_date DATE NOT NULL,
                qr_code_path VARCHAR(255),
                status ENUM('Active', 'Expired') DEFAULT 'Active',
                email_notifications_enabled BOOLEAN DEFAULT TRUE,
                INDEX idx_admission (admission_number),
                INDEX idx_status (status),
                INDEX idx_expiry (expiry_date),
                INDEX idx_birthday (date_of_birth)
            )
        """)
        
        # Add new columns to existing table if they don't exist
        try:
            cursor.execute("ALTER TABLE members ADD COLUMN mobile_number VARCHAR(20)")
        except:
            pass  # Column already exists
        
        try:
            cursor.execute("ALTER TABLE members ADD COLUMN date_of_birth DATE")
        except:
            pass
        
        try:
            cursor.execute("ALTER TABLE members ADD COLUMN sex ENUM('Male', 'Female', 'Other')")
        except:
            pass
        
        try:
            cursor.execute("ALTER TABLE members ADD COLUMN email_notifications_enabled BOOLEAN DEFAULT TRUE")
        except:
            pass
        
        try:
            cursor.execute("ALTER TABLE members ADD INDEX idx_birthday (date_of_birth)")
        except:
            pass
        
        # Create attendance table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INT AUTO_INCREMENT PRIMARY KEY,
                member_id INT NOT NULL,
                check_in DATETIME,
                check_out DATETIME,
                date DATE NOT NULL,
                FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE,
                INDEX idx_member_date (member_id, date),
                INDEX idx_date (date)
            )
        """)
        
        # Create notifications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                type VARCHAR(50) NOT NULL,
                member_id INT,
                message TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE SET NULL,
                INDEX idx_type (type),
                INDEX idx_created (created_at)
            )
        """)
        
        # Create admins table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                email VARCHAR(255),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create default admin if it doesn't exist
        cursor.execute("SELECT COUNT(*) FROM admins")
        if cursor.fetchone()[0] == 0:
            import hashlib
            default_password = hashlib.sha256('admin123'.encode()).hexdigest()
            cursor.execute("""
                INSERT INTO admins (username, password_hash, email)
                VALUES (%s, %s, %s)
            """, ('admin', default_password, 'admin@gymtrack.com'))
        
        connection.commit()
        cursor.close()
        connection.close()
        logger.info("Database initialized successfully")
        
    except Error as e:
        logger.error(f"Error initializing database: {e}")
        raise

