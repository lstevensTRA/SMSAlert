from flask import Blueprint, redirect, url_for, flash
import pyodbc
from sqlalchemy import create_engine, text
from datetime import datetime
import os
from config import Config
from app.models import SupabaseFlaggedMessage
from app import db
import requests

sync_bp = Blueprint('sync', __name__)

SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://zkoqpjlbxbfamidjftsk.supabase.co')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inprb3FwamxieGJmYW1pZGpmdHNrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDgwMzI2MDgsImV4cCI6MjA2MzYwODYwOH0.1HZHnRhI3XTV6WX-td2KprLS712NeQ8A7yiEXInWps0')

@sync_bp.route('/sync')
def sync_flagged():
    # Connect to SQL Server
    sql_conn = pyodbc.connect(
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={os.getenv('DB_SERVER')};"
        f"DATABASE={os.getenv('DB_NAME')};"
        f"UID={os.getenv('DB_USER')};"
        f"PWD={os.getenv('DB_PASSWORD')}"
    )
    cursor = sql_conn.cursor()
    cursor.execute("SELECT CaseID, MsgBody, MsgDirection, MsgDateSent, MsgFrom FROM SMSLog WHERE MsgDirection='inbound'")
    messages = cursor.fetchall()

    keywords = ['refund', 'cancel', 'lawyer']
    headers = {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
        'Content-Type': 'application/json',
    }
    for msg in messages:
        for kw in keywords:
            if kw in (msg.MsgBody or '').lower():
                data = {
                    'case_id': msg.CaseID,
                    'msg_body': msg.MsgBody,
                    'msg_date': msg.MsgDateSent.isoformat() if hasattr(msg.MsgDateSent, 'isoformat') else str(msg.MsgDateSent),
                    'direction': msg.MsgDirection,
                    'from_identity': msg.MsgFrom,
                    'keyword_hit': kw,
                    'score': 100,
                    'status': 'flagged'
                }
                try:
                    requests.post(f"{SUPABASE_URL}/rest/v1/flagged_messages", headers=headers, json=data)
                except Exception as e:
                    flash(f"Could not sync to Supabase: {str(e)}", "warning")
    flash('Sync complete!')
    return redirect(url_for('dashboard.dashboard')) 