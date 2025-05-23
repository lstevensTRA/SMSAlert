from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user, UserMixin
import pyodbc
import os
import bcrypt
import hashlib
from flask_mail import Message
import requests

from .. import login_manager, mail

auth_bp = Blueprint('auth', __name__)

class UserObj(UserMixin):
    def __init__(self, row):
        self.id = row.UserID
        self.Email = row.Email
        self.FirstName = row.FirstName
        self.LastName = row.LastName
    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    conn = pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={os.getenv('DB_SERVER')};"
        f"DATABASE={os.getenv('DB_NAME')};"
        f"UID={os.getenv('DB_USER')};"
        f"PWD={os.getenv('DB_PASSWORD')}"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT UserID, Email, Password, IsActive, FirstName, LastName FROM Users WHERE UserID = ?", user_id)
    row = cursor.fetchone()
    if row and row.IsActive:
        return UserObj(row)
    return None

SUPABASE_URL = 'https://zkoqpjlbxbfamidjftsk.supabase.co'
SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inprb3FwamxieGJmYW1pZGpmdHNrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgwMzI2MDgsImV4cCI6MjA2MzYwODYwOH0.1HZHnRhI3XTV6WX-td2KprLS712NeQ8A7yiEXInWps0'

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={os.getenv('DB_SERVER')};"
            f"DATABASE={os.getenv('DB_NAME')};"
            f"UID={os.getenv('DB_USER')};"
            f"PWD={os.getenv('DB_PASSWORD')}"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT UserID, Email, Password, IsActive, FirstName, LastName FROM Users WHERE Email = ?", email)
        row = cursor.fetchone()
        valid = False
        if row and row.IsActive:
            stored_hash = row.Password
            # Try bcrypt first
            try:
                if stored_hash.startswith('$2b$') or stored_hash.startswith('$2a$'):
                    valid = bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
            except Exception:
                valid = False
            # Fallback to SHA1 (legacy)
            if not valid:
                sha1_hash = hashlib.sha1(password.encode()).hexdigest().upper()
                if sha1_hash == stored_hash:
                    valid = True
        if valid:
            user = UserObj(row)
            login_user(user)
            # Create user in Supabase if not exists
            try:
                headers = {
                    'apikey': SUPABASE_ANON_KEY,
                    'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
                    'Content-Type': 'application/json',
                }
                # Check if user exists
                resp = requests.get(
                    f"{SUPABASE_URL}/rest/v1/profiles?email=eq.{email}",
                    headers=headers
                )
                if resp.status_code == 200 and not resp.json():
                    # Create user profile
                    data = {
                        'email': email,
                        'first_name': row.FirstName,
                        'last_name': row.LastName
                    }
                    requests.post(
                        f"{SUPABASE_URL}/rest/v1/profiles",
                        headers=headers,
                        json=data
                    )
            except Exception as e:
                flash(f"Could not sync user to Supabase: {str(e)}", "warning")
            # Notify super admin if not the super admin
            if email != 'lindsey.stevens@tra.com':
                try:
                    msg = Message(
                        subject='New User Login Request',
                        recipients=['lindsey.stevens@tra.com'],
                        body=f'User {email} has logged in and may need approval.'
                    )
                    mail.send(msg)
                except Exception as e:
                    flash(f'Could not send notification email: {str(e)}', 'warning')
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash('Invalid credentials or inactive user.')
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login')) 