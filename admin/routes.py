from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify, send_file
from database import get_db_connection
from utils import calculate_expiry_date, generate_qr_code, hash_password, verify_password, check_membership_status, generate_next_admission_number, check_and_send_birthday_emails
from email_utils import send_qr_code_email, send_admin_alert_email, send_birthday_email
from datetime import datetime, timedelta
import csv
import io
from functools import wraps

admin_bp = Blueprint('admin', __name__)

def login_required(f):
    """Decorator to require login for admin routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('Please enter both username and password', 'error')
            return render_template('admin/login.html')
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT id, username, password_hash
                FROM admins
                WHERE username = %s
            """, (username,))
            
            admin = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if admin and verify_password(password, admin['password_hash']):
                session['admin_id'] = admin['id']
                session['admin_username'] = admin['username']
                session.permanent = True
                flash('Login successful!', 'success')
                return redirect(url_for('admin.dashboard'))
            else:
                flash('Invalid username or password', 'error')
                
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
            print(f"Error in login: {e}")
    
    return render_template('admin/login.html')

@admin_bp.route('/logout')
def logout():
    """Admin logout"""
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('admin.login'))

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    """Admin dashboard"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get statistics
        cursor.execute("SELECT COUNT(*) as total FROM members")
        total_members = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM members WHERE status = 'Active'")
        active_members = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM attendance WHERE date = %s", (datetime.now().date(),))
        today_attendance = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM notifications WHERE created_at >= %s", 
                      (datetime.now() - timedelta(days=7),))
        recent_notifications = cursor.fetchone()['total']
        
        # Check for today's birthdays
        today = datetime.now().date()
        cursor.execute("""
            SELECT COUNT(*) as total FROM members
            WHERE date_of_birth IS NOT NULL
            AND MONTH(date_of_birth) = %s
            AND DAY(date_of_birth) = %s
            AND status = 'Active'
        """, (today.month, today.day))
        today_birthdays = cursor.fetchone()['total']
        
        cursor.close()
        conn.close()
        
        # Check and send birthday emails
        if today_birthdays > 0:
            check_and_send_birthday_emails()
        
        stats = {
            'total_members': total_members,
            'active_members': active_members,
            'today_attendance': today_attendance,
            'recent_notifications': recent_notifications,
            'today_birthdays': today_birthdays
        }
        
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        stats = {
            'total_members': 0,
            'active_members': 0,
            'today_attendance': 0,
            'recent_notifications': 0,
            'today_birthdays': 0
        }
    
    return render_template('admin/dashboard.html', stats=stats)

@admin_bp.route('/members')
@login_required
def members():
    """List all members"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        search = request.args.get('search', '').strip()
        status_filter = request.args.get('status', '')
        
        query = "SELECT * FROM members WHERE 1=1"
        params = []
        
        if search:
            query += " AND (name LIKE %s OR admission_number LIKE %s OR email LIKE %s)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])
        
        if status_filter:
            query += " AND status = %s"
            params.append(status_filter)
        
        query += " ORDER BY join_date DESC"
        
        cursor.execute(query, params)
        members_list = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        flash(f'Error loading members: {str(e)}', 'error')
        members_list = []
    
    return render_template('admin/members.html', members=members_list, search=search, status_filter=status_filter)

@admin_bp.route('/members/add', methods=['GET', 'POST'])
@login_required
def add_member():
    """Add new member"""
    if request.method == 'POST':
        try:
            admission_number = request.form.get('admission_number', '').strip()
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            mobile_number = request.form.get('mobile_number', '').strip() or None
            date_of_birth = request.form.get('date_of_birth', '').strip() or None
            sex = request.form.get('sex', '').strip() or None
            plan_type = request.form.get('plan_type', '')
            access_type = request.form.get('access_type', 'One-time')
            start_date = request.form.get('start_date', '')
            email_notifications = request.form.get('email_notifications', 'off') == 'on'
            
            # Auto-generate admission number if not provided
            if not admission_number:
                admission_number = generate_next_admission_number()
            
            # Validation
            if not all([name, email, plan_type, start_date]):
                flash('Please fill in all required fields', 'error')
                return render_template('admin/add_member.html', auto_admission=generate_next_admission_number())
            
            # Calculate expiry date
            expiry_date = calculate_expiry_date(start_date, plan_type)
            
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Check if admission number already exists
            cursor.execute("SELECT id FROM members WHERE admission_number = %s", (admission_number,))
            if cursor.fetchone():
                flash('Admission number already exists', 'error')
                cursor.close()
                conn.close()
                return render_template('admin/add_member.html', auto_admission=generate_next_admission_number())
            
            # Generate QR code
            qr_code_path = generate_qr_code(admission_number, name)
            
            # Insert member
            cursor.execute("""
                INSERT INTO members (admission_number, name, email, mobile_number, date_of_birth, sex, 
                                   plan_type, access_type, start_date, expiry_date, qr_code_path, status, email_notifications_enabled)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (admission_number, name, email, mobile_number, date_of_birth, sex, 
                  plan_type, access_type, start_date, expiry_date, qr_code_path, 'Active', email_notifications))
            
            member_id = cursor.lastrowid
            conn.commit()
            
            # Send QR code email
            if qr_code_path:
                send_qr_code_email(email, name, admission_number, qr_code_path, plan_type, expiry_date)
            
            cursor.close()
            conn.close()
            
            flash(f'Member {name} added successfully! QR code sent to email.', 'success')
            return redirect(url_for('admin.members'))
            
        except Exception as e:
            flash(f'Error adding member: {str(e)}', 'error')
            print(f"Error in add_member: {e}")
    
    # GET request - generate auto admission number
    auto_admission = generate_next_admission_number()
    return render_template('admin/add_member.html', auto_admission=auto_admission)

@admin_bp.route('/members/edit/<int:member_id>', methods=['GET', 'POST'])
@login_required
def edit_member(member_id):
    """Edit member"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            mobile_number = request.form.get('mobile_number', '').strip() or None
            date_of_birth = request.form.get('date_of_birth', '').strip() or None
            sex = request.form.get('sex', '').strip() or None
            plan_type = request.form.get('plan_type', '')
            access_type = request.form.get('access_type', 'One-time')
            start_date = request.form.get('start_date', '')
            email_notifications = request.form.get('email_notifications', 'off') == 'on'
            
            if not all([name, email, plan_type, start_date]):
                flash('Please fill in all required fields', 'error')
                cursor.execute("SELECT * FROM members WHERE id = %s", (member_id,))
                member = cursor.fetchone()
                cursor.close()
                conn.close()
                return render_template('admin/edit_member.html', member=member)
            
            expiry_date = calculate_expiry_date(start_date, plan_type)
            
            # Check membership status
            status = 'Active' if check_membership_status(expiry_date) else 'Expired'
            
            cursor.execute("""
                UPDATE members
                SET name = %s, email = %s, mobile_number = %s, date_of_birth = %s, sex = %s,
                    plan_type = %s, access_type = %s, start_date = %s, expiry_date = %s, 
                    status = %s, email_notifications_enabled = %s
                WHERE id = %s
            """, (name, email, mobile_number, date_of_birth, sex, plan_type, access_type, 
                  start_date, expiry_date, status, email_notifications, member_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Member updated successfully!', 'success')
            return redirect(url_for('admin.members'))
        
        # GET request - load member data
        cursor.execute("SELECT * FROM members WHERE id = %s", (member_id,))
        member = cursor.fetchone()
        
        if not member:
            flash('Member not found', 'error')
            cursor.close()
            conn.close()
            return redirect(url_for('admin.members'))
        
        cursor.close()
        conn.close()
        
        return render_template('admin/edit_member.html', member=member)
        
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        print(f"Error in edit_member: {e}")
        return redirect(url_for('admin.members'))

@admin_bp.route('/members/delete/<int:member_id>', methods=['POST'])
@login_required
def delete_member(member_id):
    """Delete member"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT name FROM members WHERE id = %s", (member_id,))
        member = cursor.fetchone()
        
        if not member:
            flash('Member not found', 'error')
            cursor.close()
            conn.close()
            return redirect(url_for('admin.members'))
        
        cursor.execute("DELETE FROM members WHERE id = %s", (member_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        flash(f'Member {member["name"]} deleted successfully', 'success')
        
    except Exception as e:
        flash(f'Error deleting member: {str(e)}', 'error')
        print(f"Error in delete_member: {e}")
    
    return redirect(url_for('admin.members'))

@admin_bp.route('/attendance')
@login_required
def attendance():
    """View attendance records"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        date_filter = request.args.get('date', '')
        member_search = request.args.get('member', '').strip()
        
        query = """
            SELECT a.*, m.name as member_name, m.admission_number
            FROM attendance a
            JOIN members m ON a.member_id = m.id
            WHERE 1=1
        """
        params = []
        
        if date_filter:
            query += " AND a.date = %s"
            params.append(date_filter)
        
        if member_search:
            query += " AND (m.name LIKE %s OR m.admission_number LIKE %s)"
            search_param = f"%{member_search}%"
            params.extend([search_param, search_param])
        
        query += " ORDER BY a.date DESC, a.check_in DESC LIMIT 100"
        
        cursor.execute(query, params)
        attendance_list = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        flash(f'Error loading attendance: {str(e)}', 'error')
        attendance_list = []
    
    return render_template('admin/attendance.html', attendance=attendance_list, date_filter=date_filter, member_search=member_search)

@admin_bp.route('/attendance/export')
@login_required
def export_attendance():
    """Export attendance to CSV"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        date_filter = request.args.get('date', '')
        member_search = request.args.get('member', '').strip()
        
        query = """
            SELECT a.date, a.check_in, a.check_out, m.name as member_name, m.admission_number, m.email
            FROM attendance a
            JOIN members m ON a.member_id = m.id
            WHERE 1=1
        """
        params = []
        
        if date_filter:
            query += " AND a.date = %s"
            params.append(date_filter)
        
        if member_search:
            query += " AND (m.name LIKE %s OR m.admission_number LIKE %s)"
            search_param = f"%{member_search}%"
            params.extend([search_param, search_param])
        
        query += " ORDER BY a.date DESC, a.check_in DESC"
        
        cursor.execute(query, params)
        records = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Date', 'Member Name', 'Admission Number', 'Email', 'Check-In', 'Check-Out'])
        
        # Write data
        for record in records:
            writer.writerow([
                record['date'].strftime('%Y-%m-%d') if record['date'] else '',
                record['member_name'],
                record['admission_number'],
                record['email'],
                record['check_in'].strftime('%Y-%m-%d %H:%M:%S') if record['check_in'] else '',
                record['check_out'].strftime('%Y-%m-%d %H:%M:%S') if record['check_out'] else ''
            ])
        
        output.seek(0)
        
        filename = f'attendance_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        flash(f'Error exporting attendance: {str(e)}', 'error')
        return redirect(url_for('admin.attendance'))

@admin_bp.route('/notifications')
@login_required
def notifications():
    """View notifications"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get regular notifications
        cursor.execute("""
            SELECT n.*, m.name as member_name, m.admission_number
            FROM notifications n
            LEFT JOIN members m ON n.member_id = m.id
            ORDER BY n.created_at DESC
            LIMIT 100
        """)
        
        notifications_list = cursor.fetchall()
        
        # Check for today's birthdays
        today = datetime.now().date()
        cursor.execute("""
            SELECT id, name, admission_number, date_of_birth, email
            FROM members
            WHERE date_of_birth IS NOT NULL
            AND MONTH(date_of_birth) = %s
            AND DAY(date_of_birth) = %s
            AND status = 'Active'
        """, (today.month, today.day))
        
        birthday_members = cursor.fetchall()
        
        # Add birthday notifications
        for member in birthday_members:
            birthday_notification = {
                'id': None,
                'type': 'birthday',
                'member_id': member['id'],
                'member_name': member['name'],
                'admission_number': member['admission_number'],
                'message': f"🎉 Today is {member['name']}'s birthday!",
                'created_at': datetime.now()
            }
            notifications_list.insert(0, birthday_notification)
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        flash(f'Error loading notifications: {str(e)}', 'error')
        notifications_list = []
        birthday_members = []
    
    return render_template('admin/notifications.html', notifications=notifications_list, birthday_members=birthday_members)

@admin_bp.route('/notifications/delete/<int:notification_id>', methods=['POST'])
@login_required
def delete_notification(notification_id):
    """Delete notification"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM notifications WHERE id = %s", (notification_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        flash('Notification deleted', 'success')
        
    except Exception as e:
        flash(f'Error deleting notification: {str(e)}', 'error')
    
    return redirect(url_for('admin.notifications'))

