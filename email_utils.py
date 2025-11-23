import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from config import Config
from datetime import datetime
import os

def send_email(to_email, subject, body, html_body=None, attachment_path=None):
    """Send email using SMTP"""
    try:
        if not Config.MAIL_USERNAME or not Config.MAIL_PASSWORD:
            print("Email configuration not set. Skipping email send.")
            return False
        
        msg = MIMEMultipart('alternative')
        msg['From'] = Config.MAIL_DEFAULT_SENDER or Config.MAIL_USERNAME
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add text and HTML parts
        if html_body:
            part1 = MIMEText(body, 'plain')
            part2 = MIMEText(html_body, 'html')
            msg.attach(part1)
            msg.attach(part2)
        else:
            msg.attach(MIMEText(body, 'plain'))
        
        # Add attachment if provided
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, 'rb') as f:
                img = MIMEImage(f.read())
                img.add_header('Content-Disposition', 'attachment', filename=os.path.basename(attachment_path))
                msg.attach(img)
        
        # Send email
        server = smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT)
        server.starttls()
        server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_qr_code_email(member_email, member_name, admission_number, qr_code_path, plan_type, expiry_date):
    """Send QR code to member's email"""
    subject = f"Welcome to GymTrack - Your QR Code"
    
    body = f"""
Hello {member_name},

Welcome to GymTrack! Your membership has been activated.

Membership Details:
- Admission Number: {admission_number}
- Plan Type: {plan_type}
- Expiry Date: {expiry_date}

Your QR code is attached to this email. You can use it to check in and check out at the gym.

Thank you for choosing GymTrack!

Best regards,
GymTrack Team
    """
    
    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
          <h2 style="color: #2c3e50;">Welcome to GymTrack!</h2>
          <p>Hello {member_name},</p>
          <p>Welcome to GymTrack! Your membership has been activated.</p>
          
          <div style="background-color: #f4f4f4; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="margin-top: 0;">Membership Details:</h3>
            <ul style="list-style: none; padding: 0;">
              <li><strong>Admission Number:</strong> {admission_number}</li>
              <li><strong>Plan Type:</strong> {plan_type}</li>
              <li><strong>Expiry Date:</strong> {expiry_date}</li>
            </ul>
          </div>
          
          <p>Your QR code is attached to this email. You can use it to check in and check out at the gym.</p>
          
          <p>Thank you for choosing GymTrack!</p>
          
          <p style="margin-top: 30px; color: #7f8c8d; font-size: 12px;">
            Best regards,<br>
            GymTrack Team
          </p>
        </div>
      </body>
    </html>
    """
    
    return send_email(member_email, subject, body, html_body, qr_code_path)

def send_checkin_email(member_email, member_name, check_in_time):
    """Send check-in confirmation email"""
    subject = "GymTrack - Check-In Confirmation"
    
    body = f"""
Hello {member_name},

You have successfully checked in at {check_in_time}.

Thank you for using GymTrack!

Best regards,
GymTrack Team
    """
    
    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
          <h2 style="color: #27ae60;">Check-In Confirmed</h2>
          <p>Hello {member_name},</p>
          <p>You have successfully checked in at <strong>{check_in_time}</strong>.</p>
          <p>Thank you for using GymTrack!</p>
          <p style="margin-top: 30px; color: #7f8c8d; font-size: 12px;">
            Best regards,<br>
            GymTrack Team
          </p>
        </div>
      </body>
    </html>
    """
    
    return send_email(member_email, subject, body, html_body)

def send_checkout_email(member_email, member_name, check_in_time, check_out_time):
    """Send check-out confirmation email"""
    subject = "GymTrack - Check-Out Confirmation"
    
    # Calculate duration if both times are available
    duration_text = ""
    duration_html = ""
    if check_in_time and check_out_time:
        try:
            check_in = datetime.strptime(check_in_time, '%Y-%m-%d %H:%M:%S')
            check_out = datetime.strptime(check_out_time, '%Y-%m-%d %H:%M:%S')
            duration = check_out - check_in
            total_seconds = int(duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            duration_text = f"\n\nDuration: {hours} hours and {minutes} minutes"
            duration_html = f'<p>Duration: <strong>{hours} hours and {minutes} minutes</strong></p>'
        except Exception as e:
            print(f"Error calculating duration: {e}")
    
    body = f"""
Hello {member_name},

You have successfully checked out at {check_out_time}.{duration_text}

Thank you for using GymTrack!

Best regards,
GymTrack Team
    """
    
    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
          <h2 style="color: #e74c3c;">Check-Out Confirmed</h2>
          <p>Hello {member_name},</p>
          <p>You have successfully checked out at <strong>{check_out_time}</strong>.</p>
          {duration_html}
          <p>Thank you for using GymTrack!</p>
          <p style="margin-top: 30px; color: #7f8c8d; font-size: 12px;">
            Best regards,<br>
            GymTrack Team
          </p>
        </div>
      </body>
    </html>
    """
    
    return send_email(member_email, subject, body, html_body)

def send_birthday_email(member_email, member_name):
    """Send birthday email to member"""
    subject = "🎉 Happy Birthday from GymTrack!"
    
    body = f"""
Dear {member_name},

🎉 Happy Birthday! 🎉

We hope your special day is filled with joy, happiness, and lots of celebration!

Thank you for being a valued member of GymTrack. We appreciate your commitment to fitness and health.

Have a wonderful day and keep up the great work!

Best wishes,
GymTrack Team
    """
    
    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; text-align: center;">
          <h1 style="color: #e74c3c; font-size: 3rem; margin: 20px 0;">🎉</h1>
          <h2 style="color: #2c3e50;">Happy Birthday, {member_name}!</h2>
          <p style="font-size: 1.2rem; color: #7f8c8d;">We hope your special day is filled with joy, happiness, and lots of celebration!</p>
          
          <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; margin: 30px 0; color: white;">
            <p style="font-size: 1.1rem; margin: 0;">Thank you for being a valued member of GymTrack.</p>
            <p style="font-size: 1.1rem; margin: 10px 0 0 0;">We appreciate your commitment to fitness and health.</p>
          </div>
          
          <p style="font-size: 1.1rem;">Have a wonderful day and keep up the great work! 💪</p>
          
          <p style="margin-top: 30px; color: #7f8c8d; font-size: 12px;">
            Best wishes,<br>
            GymTrack Team
          </p>
        </div>
      </body>
    </html>
    """
    
    return send_email(member_email, subject, body, html_body)

def send_admin_alert_email(admin_email, member_name, admission_number, message):
    """Send alert email to admin"""
    subject = "GymTrack - Membership Alert"
    
    body = f"""
Admin Alert,

{message}

Member Details:
- Name: {member_name}
- Admission Number: {admission_number}

Please review this in the admin portal.

GymTrack System
    """
    
    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
          <h2 style="color: #e74c3c;">Admin Alert</h2>
          <p>{message}</p>
          <div style="background-color: #f4f4f4; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="margin-top: 0;">Member Details:</h3>
            <ul style="list-style: none; padding: 0;">
              <li><strong>Name:</strong> {member_name}</li>
              <li><strong>Admission Number:</strong> {admission_number}</li>
            </ul>
          </div>
          <p>Please review this in the admin portal.</p>
          <p style="margin-top: 30px; color: #7f8c8d; font-size: 12px;">
            GymTrack System
          </p>
        </div>
      </body>
    </html>
    """
    
    return send_email(admin_email, subject, body, html_body)
