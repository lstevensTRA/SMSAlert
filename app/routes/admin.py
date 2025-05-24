from flask import Blueprint, render_template, redirect, url_for, request, session, flash
from flask_login import login_required, current_user
import pyodbc
import os
from config import Config
from app.models import Settings, User, Keyword
from app import db
import json
import requests

admin_bp = Blueprint('admin', __name__)

SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://zkoqpjlbxbfamidjftsk.supabase.co')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inprb3FwamxieGJmYW1pZGpmdHNrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgwMzI2MDgsImV4cCI6MjA2MzYwODYwOH0.1HZHnRhI3XTV6WX-td2KprLS712NeQ8A7yiEXInWps0')

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
    headers = {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
        'Content-Type': 'application/json',
    }
    # Fetch users from Supabase
    resp = requests.get(f"{SUPABASE_URL}/rest/v1/profiles?order=created_at", headers=headers)
    users = resp.json() if resp.status_code == 200 else []
    logs = []  # TODO: fetch audit logs if needed
    return render_template('admin_panel.html', users=users, logs=logs)

@admin_bp.route('/admin/notifications', methods=['GET', 'POST'])
@login_required
def notifications():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    headers = {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
        'Content-Type': 'application/json',
    }
    # Fetch settings from Supabase
    resp = requests.get(f"{SUPABASE_URL}/rest/v1/settings?select=alert_recipients,id", headers=headers)
    settings = resp.json()[0] if resp.status_code == 200 and resp.json() else None
    emails = []
    schedule = 'hourly'
    if settings and settings.get('alert_recipients'):
        data = settings['alert_recipients']
        if isinstance(data, dict):
            emails = data.get('emails', [])
            schedule = data.get('schedule', 'hourly')
        else:
            emails = data
    if request.method == 'POST':
        email = request.form.get('email')
        schedule_form = request.form.get('schedule')
        if email and email not in emails:
            emails.append(email)
        if schedule_form:
            schedule = schedule_form
        payload = {'alert_recipients': {'emails': emails, 'schedule': schedule}}
        if settings:
            # PATCH existing
            requests.patch(f"{SUPABASE_URL}/rest/v1/settings?id=eq.{settings['id']}", headers=headers, json=payload)
        else:
            # POST new
            requests.post(f"{SUPABASE_URL}/rest/v1/settings", headers=headers, json=payload)
        flash('Notification settings updated!', 'success')
    return render_template('notifications.html', emails=emails, schedule=schedule)

@admin_bp.route('/admin/toggle/<string:user_id>')
@login_required
def toggle_user(user_id):
    headers = {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
        'Content-Type': 'application/json',
    }
    # Fetch user
    resp = requests.get(f"{SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}", headers=headers)
    user = resp.json()[0] if resp.status_code == 200 and resp.json() else None
    if user:
        new_status = not user.get('is_active', True)
        payload = {'is_active': new_status}
        requests.patch(f"{SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}", headers=headers, json=payload)
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