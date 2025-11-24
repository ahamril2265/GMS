# Quick Setup Guide

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Configure Environment

Edit `config.py` or set environment variables:

### Database Configuration
```python
MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'your_password'
MYSQL_DATABASE = 'gymtrack'
```

### Email Configuration (for Gmail)
```python
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = 'your_email@gmail.com'
MAIL_PASSWORD = 'your_app_password'  # Use App Password, not regular password
MAIL_DEFAULT_SENDER = 'your_email@gmail.com'
```

**Note for Gmail**: You need to:
1. Enable 2-Step Verification
2. Generate an App Password at: https://myaccount.google.com/apppasswords
3. Use that App Password in `MAIL_PASSWORD`

## Step 3: Initialize Database

```bash
python init_db.py
```

This creates:
- All database tables
- Default admin account (username: `admin`, password: `admin123`)

## Step 4: Run the Application

```bash
python app.py
```

## Step 5: Access the Application

- **Home Page**: http://localhost:5000
- **Admin Portal**: http://localhost:5000/admin/login
  - Username: `admin`
  - Password: `admin123`

## Important Security Steps

1. **Change the default admin password** immediately after first login
2. **Set a strong SECRET_KEY** in `config.py`:
   ```python
   SECRET_KEY = 'your-very-long-random-secret-key-here'
   ```
3. For production, use environment variables for all sensitive data

## Troubleshooting

### Database Connection Error
- Ensure MySQL server is running
- Verify database credentials in `config.py`
- Make sure the database exists (or let init_db.py create it)

### Email Not Sending
- Check email credentials
- For Gmail, ensure you're using an App Password
- Check firewall/network settings
- Verify SMTP server and port settings

### QR Code Generation Error
- Ensure `static/qr_codes` directory exists
- Check file permissions

## Next Steps

1. Add your first member through the admin portal
2. Test check-in/out functionality
3. Verify email notifications are working
4. Customize the system as needed



