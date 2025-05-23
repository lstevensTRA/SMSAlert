from flask import Blueprint, redirect, url_for, flash
import pyodbc
from sqlalchemy import create_engine, text
from datetime import datetime
import os
from config import Config

sync_bp = Blueprint('sync', __name__)

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

    # Define your keywords
    keywords = ['refund', 'cancel', 'lawyer']

    # Connect to Supabase
    try:
        supabase_engine = create_engine(Config.SUPABASE_DB_URL)
    except Exception as e:
        supabase_engine = None
        flash(f"Warning: Could not connect to Supabase. {str(e)}", "warning")

    # Flag and insert
    for msg in messages:
        for kw in keywords:
            if kw in (msg.MsgBody or '').lower():
                if supabase_engine:
                    try:
                        with supabase_engine.connect() as conn:
                            conn.execute(
                                text("""
                                INSERT INTO flagged_messages (case_id, msg_body, msg_date, direction, from_identity, keyword_hit, score, status, created_at)
                                VALUES (:case_id, :msg_body, :msg_date, :direction, :from_identity, :keyword_hit, :score, :status, :created_at)
                                ON CONFLICT (case_id, msg_date) DO NOTHING
                                """),
                                {
                                    'case_id': msg.CaseID,
                                    'msg_body': msg.MsgBody,
                                    'msg_date': msg.MsgDateSent,
                                    'direction': msg.MsgDirection,
                                    'from_identity': msg.MsgFrom,
                                    'keyword_hit': kw,
                                    'score': 100,  # or your scoring logic
                                    'status': 'flagged',
                                    'created_at': datetime.utcnow()
                                }
                            )
                    except Exception as e:
                        flash(f"Warning: Could not insert into Supabase. {str(e)}", "warning")
                # else: skip insert if supabase_engine is None
    flash('Sync complete!')
    return redirect(url_for('dashboard.dashboard')) 