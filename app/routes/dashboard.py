import pyodbc
import requests
import os
from flask import Blueprint, render_template, flash, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.models import FlaggedMessage
from app import db

dashboard_bp = Blueprint('dashboard', __name__)

SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://zkoqpjlbxbfamidjftsk.supabase.co')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inprb3FwamxieGJmYW1pZGpmdHNrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgwMzI2MDgsImV4cCI6MjA2MzYwODYwOH0.1HZHnRhI3XTV6WX-td2KprLS712NeQ8A7yiEXInWps0')

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    # Read SMS logs from SQL Server
    try:
        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={os.getenv('DB_SERVER')};"
            f"DATABASE={os.getenv('DB_NAME')};"
            f"UID={os.getenv('DB_USER')};"
            f"PWD={os.getenv('DB_PASSWORD')}"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT SMSLogID, CaseID, MsgDateSent, MsgFrom, MsgTo, MsgBody FROM SMSLog WHERE MsgDirection='inbound' AND MsgBody IS NOT NULL AND MsgBody <> '' AND IsDeleted = 0 AND MsgDateSent >= DATEADD(day, -30, GETDATE()) ORDER BY MsgDateSent DESC")
        sms_logs = cursor.fetchall()
        conn.close()
    except Exception as e:
        sms_logs = []
        flash(f"Error connecting to main database: {str(e)}", "danger")
    # Fetch flagged messages from Supabase
    headers = {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
        'Content-Type': 'application/json',
    }
    resp = requests.get(f"{SUPABASE_URL}/rest/v1/flagged_messages", headers=headers)
    flagged_data = resp.json() if resp.status_code == 200 else []
    flagged_lookup = {(f['case_id'], f['msg_date']): f for f in flagged_data}
    # Combine SMS logs with flagged status
    dashboard_rows = []
    for log in sms_logs:
        flagged = flagged_lookup.get((log.CaseID, log.MsgDateSent.isoformat() if hasattr(log.MsgDateSent, 'isoformat') else str(log.MsgDateSent)))
        dashboard_rows.append({
            'SMSLogID': log.SMSLogID,
            'CaseID': log.CaseID,
            'MsgDateSent': log.MsgDateSent,
            'MsgFrom': log.MsgFrom,
            'MsgTo': log.MsgTo,
            'MsgBody': log.MsgBody,
            'flagged': flagged
        })
    return render_template('dashboard.html', flagged_messages=dashboard_rows)

@dashboard_bp.route('/conversation/<case_id>')
@login_required
def conversation(case_id):
    try:
        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={os.getenv('DB_SERVER')};"
            f"DATABASE={os.getenv('DB_NAME')};"
            f"UID={os.getenv('DB_USER')};"
            f"PWD={os.getenv('DB_PASSWORD')}"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM SMSLog WHERE CaseID = ? ORDER BY MsgDateSent ASC", case_id)
        messages = cursor.fetchall()
        conn.close()
    except Exception as e:
        messages = []
        flash(f"Error loading conversation: {str(e)}", "danger")
    # Fetch flagged/follow-up info from Supabase
    headers = {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
        'Content-Type': 'application/json',
    }
    resp = requests.get(f"{SUPABASE_URL}/rest/v1/flagged_messages?case_id=eq.{case_id}", headers=headers)
    flagged = resp.json()[0] if resp.status_code == 200 and resp.json() else None
    return render_template('conversation.html', messages=messages, case_id=case_id, flagged=flagged)

@dashboard_bp.route('/followup/<case_id>', methods=['GET', 'POST'])
@login_required
def followup(case_id):
    headers = {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
        'Content-Type': 'application/json',
    }
    # Fetch flagged message for this case
    resp = requests.get(f"{SUPABASE_URL}/rest/v1/flagged_messages?case_id=eq.{case_id}", headers=headers)
    flagged = resp.json()[0] if resp.status_code == 200 and resp.json() else None
    if request.method == 'POST':
        status = request.form.get('status')
        notes = request.form.get('notes')
        payload = {'follow_up_status': status, 'notes': notes, 'followed_up_by': current_user.Email}
        if flagged:
            # PATCH existing
            requests.patch(f"{SUPABASE_URL}/rest/v1/flagged_messages?id=eq.{flagged['id']}", headers=headers, json=payload)
        flash('Follow-up updated!', 'success')
        return redirect(url_for('dashboard.conversation', case_id=case_id))
    # GET
    if not flagged:
        flagged = {'follow_up_status': 'No', 'notes': '', 'followed_up_by': ''}
    return render_template('followup.html', flagged=flagged, case_id=case_id) 