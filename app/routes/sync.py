from flask import Blueprint, redirect, url_for, flash
import pyodbc
from sqlalchemy import create_engine, text
from datetime import datetime
import os
from config import Config
from app.models import SupabaseFlaggedMessage
from app import db

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

    # Flag and insert into local DB
    for msg in messages:
        for kw in keywords:
            if kw in (msg.MsgBody or '').lower():
                exists = SupabaseFlaggedMessage.query.filter_by(case_id=msg.CaseID, msg_date=msg.MsgDateSent).first()
                if not exists:
                    flagged = SupabaseFlaggedMessage(
                        case_id=msg.CaseID,
                        msg_body=msg.MsgBody,
                        msg_date=msg.MsgDateSent,
                        direction=msg.MsgDirection,
                        from_identity=msg.MsgFrom,
                        keyword_hit=kw,
                        score=100,
                        status='flagged'
                    )
                    db.session.add(flagged)
    db.session.commit()
    flash('Sync complete!')
    return redirect(url_for('dashboard.dashboard')) 