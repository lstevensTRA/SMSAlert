from flask import Blueprint, render_template, redirect, url_for, request, session
from flask_login import login_required, current_user
import pyodbc
import os
from config import Config

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
    # For demo: store in session, in real app use DB
    if 'emails' not in session:
        session['emails'] = []
    if 'schedule' not in session:
        session['schedule'] = 'hourly'
    if request.method == 'POST':
        email = request.form.get('email')
        schedule = request.form.get('schedule')
        if email and email not in session['emails']:
            session['emails'].append(email)
        if schedule:
            session['schedule'] = schedule
    emails = session.get('emails', [])
    schedule = session.get('schedule', 'hourly')
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