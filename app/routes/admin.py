from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from flask_login import login_required, current_user
import pyodbc
import os
from config import Config
from app.models import Settings, User, Keyword
from app import db
import json

admin_bp = Blueprint('admin', __name__)

@admin_bp.before_request
def restrict_to_superadmin():
    # Only restrict /admin and /admin/toggle to superadmin
    if request.endpoint in ['admin.admin_panel', 'admin.toggle_user']:
        if not current_user.is_authenticated or current_user.Email != 'lindsey.stevens@tra.com':
            return redirect(url_for('dashboard.dashboard'))
    # Do not redirect for notifications; let @login_required handle it

@admin_bp.route('/admin')
@login_required
def admin_panel():
    # Connect to SQL Server
    sql_conn = pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={os.getenv('DB_SERVER')};"
        f"DATABASE={os.getenv('DB_NAME')};"
        f"UID={os.getenv('DB_USER')};"
        f"PWD={os.getenv('DB_PASSWORD')}"
    )
    cursor = sql_conn.cursor()
    cursor.execute("SELECT UserID, Email, FirstName, LastName, IsActive FROM Users")
    users = cursor.fetchall()
    logs = []  # TODO: fetch audit logs if needed
    return render_template('admin_panel.html', users=users, logs=logs)

@admin_bp.route('/admin/notifications', methods=['GET', 'POST'])
@login_required
def notifications():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    # Use DB for persistent settings
    settings = Settings.query.first()
    if not settings:
        settings = Settings(alert_recipients=json.dumps([]))
        db.session.add(settings)
        db.session.commit()
    # Parse emails and schedule from DB
    try:
        data = json.loads(settings.alert_recipients)
        if isinstance(data, dict):
            emails = data.get('emails', [])
            schedule = data.get('schedule', 'hourly')
        else:
            emails = data
            schedule = 'hourly'
    except Exception:
        emails = []
        schedule = 'hourly'
    if request.method == 'POST':
        email = request.form.get('email')
        schedule_form = request.form.get('schedule')
        if email and email not in emails:
            emails.append(email)
        if schedule_form:
            schedule = schedule_form
        # Save as JSON
        settings.alert_recipients = json.dumps({'emails': emails, 'schedule': schedule})
        db.session.commit()
        flash('Notification settings updated!', 'success')
    return render_template('notifications.html', emails=emails, schedule=schedule)

@admin_bp.route('/admin/toggle/<int:user_id>')
@login_required
def toggle_user(user_id):
    sql_conn = pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={os.getenv('DB_SERVER')};"
        f"DATABASE={os.getenv('DB_NAME')};"
        f"UID={os.getenv('DB_USER')};"
        f"PWD={os.getenv('DB_PASSWORD')}"
    )
    cursor = sql_conn.cursor()
    cursor.execute("UPDATE Users SET IsActive = 1 - IsActive WHERE UserID = ?", user_id)
    sql_conn.commit()
    return redirect(url_for('admin.admin_panel'))

@admin_bp.route('/health')
def health():
    try:
        # Test User CRUD
        user_count = User.query.count()
        # Test Keyword CRUD
        keyword_count = Keyword.query.count()
        # Test Settings CRUD
        settings = Settings.query.first()
        settings_ok = bool(settings)
        return {
            'status': 'ok',
            'user_count': user_count,
            'keyword_count': keyword_count,
            'settings_ok': settings_ok
        }, 200
    except Exception as e:
        return {'status': 'error', 'error': str(e)}, 500 