# Gym Management System 🏋️

A full-stack gym membership and attendance management platform built with Flask and MySQL.

The system helps gym administrators manage memberships, automate attendance tracking, generate QR codes, send notifications, and monitor operational metrics through an administrative dashboard.

---

## Overview

Managing gym memberships manually is time-consuming and error-prone.

This project provides:

- Member registration
- QR-based attendance
- Membership tracking
- Automated email notifications
- Expiry management
- Admin dashboard and reporting

---

## Features

### Member Management

- Register new members
- Edit member profiles
- Membership plans
- Membership renewal
- Expiry tracking

### Attendance Tracking

- QR-based check-in
- QR-based check-out
- Daily attendance records
- Attendance history

### Email Notifications

- Check-in confirmation
- Check-out confirmation
- Membership alerts
- Birthday wishes

### Admin Dashboard

- Total members
- Active memberships
- Daily attendance
- Notifications
- Birthday reminders

### Reporting

- Attendance exports
- Member records
- Operational summaries

---

## Architecture

```text
Gym Member
      │
      ▼
 QR Code Scan
      │
      ▼
 Flask Application
      │
      ├────────► Attendance Module
      │
      ├────────► Membership Module
      │
      ├────────► Notification Module
      │
      └────────► Admin Dashboard
                     │
                     ▼
                  MySQL
```

---

## Database Schema

### Members

Stores:

- Admission Number
- Name
- Email
- Mobile Number
- Membership Details
- Expiry Date

### Attendance

Stores:

- Check-in Time
- Check-out Time
- Attendance Date

### Notifications

Stores:

- Alerts
- Membership Events
- Birthday Messages

### Admins

Stores:

- Login Credentials
- Administrator Information

---

## Tech Stack

| Layer | Technology |
|---------|-----------|
| Backend | Flask |
| Database | MySQL |
| Frontend | HTML, CSS, JavaScript |
| Email Service | SMTP |
| QR Generation | Python QR Libraries |

---

## Project Structure

```text
GMS/
│
├── admin/
├── templates/
├── static/
├── app.py
├── routes.py
├── database.py
├── email_utils.py
├── utils.py
├── config.py
└── requirements.txt
```

---

## Future Improvements

- Docker Deployment
- REST API Layer
- Mobile Application
- SMS Notifications
- Payment Integration
- Membership Analytics Dashboard
- Cloud Hosting

---

## Author

Ahamed Rilwan

GitHub: https://github.com/ahamril2265

LinkedIn: https://www.linkedin.com/in/ahamedrilwan
