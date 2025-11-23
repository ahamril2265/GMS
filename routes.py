from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from database import get_db_connection
from utils import check_membership_status
from email_utils import send_checkin_email, send_checkout_email, send_admin_alert_email
from datetime import datetime
import json

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page with check-in/out form"""
    return render_template('index.html')

@main_bp.route('/check', methods=['POST'])
def check_member():
    """Handle manual check-in/out"""
    admission_number = request.form.get('admission_number', '').strip()
    
    if not admission_number:
        flash('Please enter an admission number', 'error')
        return redirect(url_for('main.index'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get member details
        cursor.execute("""
            SELECT id, name, email, access_type, expiry_date, status
            FROM members
            WHERE admission_number = %s
        """, (admission_number,))
        
        member = cursor.fetchone()
        
        if not member:
            flash('Member not found. Please check your admission number.', 'error')
            cursor.close()
            conn.close()
            return redirect(url_for('main.index'))
        
        # Check membership status
        if not check_membership_status(member['expiry_date']):
            # Update status if expired
            cursor.execute("""
                UPDATE members SET status = 'Expired'
                WHERE id = %s
            """, (member['id'],))
            conn.commit()
            flash('Your membership has expired. Please renew to continue.', 'error')
            cursor.close()
            conn.close()
            return redirect(url_for('main.index'))
        
        # Get today's date
        today = datetime.now().date()
        
        # Check today's attendance
        cursor.execute("""
            SELECT id, check_in, check_out
            FROM attendance
            WHERE member_id = %s AND date = %s
            ORDER BY id DESC
            LIMIT 1
        """, (member['id'], today))
        
        attendance = cursor.fetchone()
        current_time = datetime.now()
        
        if not attendance:
            # No attendance today - create check-in
            cursor.execute("""
                INSERT INTO attendance (member_id, check_in, date)
                VALUES (%s, %s, %s)
            """, (member['id'], current_time, today))
            conn.commit()
            
            # Send check-in email if notifications enabled
            if member.get('email_notifications_enabled', True):
                send_checkin_email(
                    member['email'],
                    member['name'],
                    current_time.strftime('%Y-%m-%d %H:%M:%S')
                )
            
            flash(f'Welcome {member["name"]}! You have been checked in.', 'success')
            
        elif attendance['check_in'] and not attendance['check_out']:
            # Already checked in, now check out
            cursor.execute("""
                UPDATE attendance
                SET check_out = %s
                WHERE id = %s
            """, (current_time, attendance['id']))
            conn.commit()
            
            # Send check-out email if notifications enabled
            if member.get('email_notifications_enabled', True):
                send_checkout_email(
                    member['email'],
                    member['name'],
                    attendance['check_in'].strftime('%Y-%m-%d %H:%M:%S'),
                    current_time.strftime('%Y-%m-%d %H:%M:%S')
                )
            
            flash(f'Thank you {member["name"]}! You have been checked out.', 'success')
            
        elif attendance['check_in'] and attendance['check_out']:
            # Already checked in and out today
            if member['access_type'] == 'Multiple':
                # Create new check-in for multiple access type
                cursor.execute("""
                    INSERT INTO attendance (member_id, check_in, date)
                    VALUES (%s, %s, %s)
                """, (member['id'], current_time, today))
                conn.commit()
                
                # Send check-in email if notifications enabled
                if member.get('email_notifications_enabled', True):
                    send_checkin_email(
                        member['email'],
                        member['name'],
                        current_time.strftime('%Y-%m-%d %H:%M:%S')
                    )
                
                flash(f'Welcome back {member["name"]}! You have been checked in again.', 'success')
            else:
                flash('You have already checked in and out today. One-time access members can only check in once per day.', 'info')
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
        print(f"Error in check_member: {e}")
    
    return redirect(url_for('main.index'))

@main_bp.route('/api/scan', methods=['POST'])
def scan_qr():
    """Handle QR code scan"""
    try:
        data = request.get_json()
        
        # Handle different QR code formats
        if isinstance(data, dict):
            admission_number = data.get('admission_number') or data.get('admissionNumber')
        elif isinstance(data, str):
            # Try to parse as JSON string
            try:
                data = json.loads(data)
                admission_number = data.get('admission_number') or data.get('admissionNumber')
            except:
                admission_number = data
        else:
            admission_number = None
        
        if not admission_number:
            return jsonify({
                'success': False,
                'message': 'Invalid QR code data'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get member details
        cursor.execute("""
            SELECT id, name, email, access_type, expiry_date, status, email_notifications_enabled
            FROM members
            WHERE admission_number = %s
        """, (admission_number,))
        
        member = cursor.fetchone()
        
        if not member:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Member not found'
            }), 404
        
        # Check membership status
        if not check_membership_status(member['expiry_date']):
            # Update status
            cursor.execute("""
                UPDATE members SET status = 'Expired'
                WHERE id = %s
            """, (member['id'],))
            
            # Create notification
            message = f"Expired membership scan attempt by {member['name']} ({admission_number})"
            cursor.execute("""
                INSERT INTO notifications (type, member_id, message)
                VALUES (%s, %s, %s)
            """, ('expired_scan', member['id'], message))
            conn.commit()
            
            # Send admin alert
            cursor.execute("SELECT email FROM admins LIMIT 1")
            admin = cursor.fetchone()
            if admin and admin['email']:
                send_admin_alert_email(
                    admin['email'],
                    member['name'],
                    admission_number,
                    f"Expired membership scan attempt by {member['name']} ({admission_number})"
                )
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': False,
                'message': 'Membership has expired'
            }), 403
        
        # Process check-in/out (same logic as manual entry)
        today = datetime.now().date()
        cursor.execute("""
            SELECT id, check_in, check_out
            FROM attendance
            WHERE member_id = %s AND date = %s
            ORDER BY id DESC
            LIMIT 1
        """, (member['id'], today))
        
        attendance = cursor.fetchone()
        current_time = datetime.now()
        
        if not attendance:
            # Check in
            cursor.execute("""
                INSERT INTO attendance (member_id, check_in, date)
                VALUES (%s, %s, %s)
            """, (member['id'], current_time, today))
            conn.commit()
            
            # Send check-in email if notifications enabled
            if member.get('email_notifications_enabled', True):
                send_checkin_email(
                    member['email'],
                    member['name'],
                    current_time.strftime('%Y-%m-%d %H:%M:%S')
                )
            
            action = 'check-in'
            
        elif attendance['check_in'] and not attendance['check_out']:
            # Check out
            cursor.execute("""
                UPDATE attendance
                SET check_out = %s
                WHERE id = %s
            """, (current_time, attendance['id']))
            conn.commit()
            
            # Send check-out email if notifications enabled
            if member.get('email_notifications_enabled', True):
                send_checkout_email(
                    member['email'],
                    member['name'],
                    attendance['check_in'].strftime('%Y-%m-%d %H:%M:%S'),
                    current_time.strftime('%Y-%m-%d %H:%M:%S')
                )
            
            action = 'check-out'
            
        elif attendance['check_in'] and attendance['check_out']:
            if member['access_type'] == 'Multiple':
                cursor.execute("""
                    INSERT INTO attendance (member_id, check_in, date)
                    VALUES (%s, %s, %s)
                """, (member['id'], current_time, today))
                conn.commit()
                
                # Send check-in email if notifications enabled
                if member.get('email_notifications_enabled', True):
                    send_checkin_email(
                        member['email'],
                        member['name'],
                        current_time.strftime('%Y-%m-%d %H:%M:%S')
                    )
                
                action = 'check-in'
            else:
                cursor.close()
                conn.close()
                return jsonify({
                    'success': False,
                    'message': 'Already checked in and out today (One-time access)'
                }), 400
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Successfully {action}',
            'member_name': member['name'],
            'action': action
        }), 200
        
    except Exception as e:
        print(f"Error in scan_qr: {e}")
        return jsonify({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }), 500

