import qrcode
from PIL import Image
import os
from config import Config
from datetime import datetime, timedelta

def calculate_expiry_date(start_date, plan_type):
    """Calculate expiry date based on plan type"""
    start = datetime.strptime(start_date, '%Y-%m-%d').date()
    
    plan_durations = {
        '1 Day Pass': timedelta(days=1),
        'Monthly': timedelta(days=30),
        '3 Months': timedelta(days=90),
        '6 Months': timedelta(days=180),
        '12 Months': timedelta(days=365)
    }
    
    duration = plan_durations.get(plan_type, timedelta(days=30))
    expiry = start + duration
    
    return expiry.strftime('%Y-%m-%d')

def generate_qr_code(admission_number, member_name):
    """Generate QR code for a member"""
    try:
        # Create QR code instance
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        # QR code data (JSON format for easier parsing)
        qr_data = {
            'admission_number': admission_number,
            'timestamp': datetime.now().isoformat()
        }
        import json
        qr.add_data(json.dumps(qr_data))
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR code
        filename = f"qr_{admission_number}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        img.save(filepath)
        
        return filepath
    except Exception as e:
        print(f"Error generating QR code: {e}")
        return None

def check_membership_status(expiry_date):
    """Check if membership is active"""
    # Handle both string and date objects from database
    if isinstance(expiry_date, str):
        expiry = datetime.strptime(expiry_date, '%Y-%m-%d').date()
    elif hasattr(expiry_date, 'date'):  # datetime object
        expiry = expiry_date.date()
    else:  # date object
        expiry = expiry_date
    today = datetime.now().date()
    return today <= expiry

def hash_password(password):
    """Hash password using SHA-256"""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    """Verify password against hash"""
    return hash_password(password) == password_hash

def generate_next_admission_number():
    """Generate the next admission number"""
    from database import get_db_connection
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get the highest numeric admission number
        cursor.execute("""
            SELECT admission_number FROM members 
            WHERE admission_number REGEXP '^[0-9]+$'
            ORDER BY CAST(admission_number AS UNSIGNED) DESC 
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            # Increment the number
            next_num = int(result[0]) + 1
            return str(next_num).zfill(6)  # Format as 6-digit number (e.g., 000001)
        else:
            # Start from 1
            return "000001"
            
    except Exception as e:
        print(f"Error generating admission number: {e}")
        # Fallback: use timestamp-based number
        return datetime.now().strftime('%Y%m%d%H%M%S')[:10]

def check_and_send_birthday_emails():
    """Check for today's birthdays and send emails"""
    from database import get_db_connection
    from email_utils import send_birthday_email
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        today = datetime.now().date()
        
        # Get members with birthdays today
        cursor.execute("""
            SELECT id, name, email, date_of_birth, email_notifications_enabled
            FROM members
            WHERE date_of_birth IS NOT NULL
            AND MONTH(date_of_birth) = %s
            AND DAY(date_of_birth) = %s
            AND status = 'Active'
        """, (today.month, today.day))
        
        birthday_members = cursor.fetchall()
        
        sent_count = 0
        for member in birthday_members:
            if member.get('email_notifications_enabled', True):
                if send_birthday_email(member['email'], member['name']):
                    sent_count += 1
        
        cursor.close()
        conn.close()
        
        return sent_count
        
    except Exception as e:
        print(f"Error checking birthdays: {e}")
        return 0
