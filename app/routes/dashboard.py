from flask import Blueprint, render_template, flash, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
import requests
import os
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
    headers = {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
        'Content-Type': 'application/json',
    }
    # Fetch flagged messages from Supabase
    resp = requests.get(f"{SUPABASE_URL}/rest/v1/flagged_messages?order=msg_date.desc", headers=headers)
    flagged_messages = resp.json() if resp.status_code == 200 else []
    return render_template('dashboard.html', flagged_messages=flagged_messages)

@dashboard_bp.route('/conversation/<case_id>')
@login_required
def conversation(case_id):
    headers = {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
        'Content-Type': 'application/json',
    }
    # Fetch messages for this case from Supabase
    resp = requests.get(f"{SUPABASE_URL}/rest/v1/flagged_messages?case_id=eq.{case_id}&order=msg_date.asc", headers=headers)
    messages = resp.json() if resp.status_code == 200 else []
    return render_template('conversation.html', messages=messages, case_id=case_id)

@dashboard_bp.route('/followup/<case_id>', methods=['GET', 'POST'])
@login_required
def followup(case_id):
    headers = {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
        'Content-Type': 'application/json',
    }
    # Fetch flagged message for this case and user
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