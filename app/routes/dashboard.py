from flask import Blueprint, render_template, flash, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
import pyodbc
import os
from app.models import FlaggedMessage
from app import db

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    # Get filter values from request.args
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    keyword = request.args.get('keyword')
    severity = request.args.get('severity')

    # Build SQL query to only include aggressive/flagged messages, sorted by most recent
    sql = '''
    SELECT 
        SMSLogID,
        CaseID,
        MsgDateSent,
        MsgFrom,
        MsgTo,
        MsgBody,
        DATEDIFF(day, MsgDateSent, GETDATE()) AS DaysAgo,
        LEN(MsgBody) AS MessageLength,
        (
            (CASE WHEN LOWER(MsgBody) LIKE '%i want%' AND LOWER(MsgBody) LIKE '%refund%' THEN 3 ELSE 0 END) +
            (CASE WHEN LOWER(MsgBody) LIKE '%i need%' AND LOWER(MsgBody) LIKE '%refund%' THEN 2.5 ELSE 0 END) +
            (CASE WHEN LOWER(MsgBody) LIKE '%full refund%' THEN 3 ELSE 0 END) +
            (CASE WHEN LOWER(MsgBody) LIKE '%money back%' THEN 3 ELSE 0 END) +
            (CASE WHEN LOWER(MsgBody) LIKE '%don''t charge%' THEN 2.5 ELSE 0 END) +
            (CASE WHEN LOWER(MsgBody) LIKE '%unauthorized%' AND LOWER(MsgBody) LIKE '%charge%' THEN 2.5 ELSE 0 END) +
            (CASE WHEN LOWER(MsgBody) LIKE '%you charged me%' THEN 3 ELSE 0 END) +
            (CASE WHEN LOWER(MsgBody) LIKE '%was charged%' THEN 2.5 ELSE 0 END) +
            (CASE WHEN LOWER(MsgBody) LIKE '%got charged%' THEN 2.5 ELSE 0 END) +
            (CASE WHEN LOWER(MsgBody) LIKE '%charged my%' AND LOWER(MsgBody) LIKE '%account%' THEN 2.5 ELSE 0 END) +
            (CASE WHEN LOWER(MsgBody) LIKE '%stop%' AND LOWER(MsgBody) LIKE '%charge%' THEN 2.5 ELSE 0 END) +
            (CASE WHEN LOWER(MsgBody) LIKE '%why%' AND LOWER(MsgBody) LIKE '%charge%' THEN 2.5 ELSE 0 END) +
            (CASE WHEN LOWER(MsgBody) LIKE '%unexpected charge%' THEN 2.5 ELSE 0 END) +
            (CASE WHEN LOWER(MsgBody) LIKE '%cancel%' AND (LOWER(MsgBody) LIKE '%service%' OR LOWER(MsgBody) LIKE '%account%' OR LOWER(MsgBody) LIKE '%program%' OR LOWER(MsgBody) LIKE '%subscription%') THEN 3 ELSE 0 END) +
            (CASE WHEN UPPER(TRIM(MsgBody)) = 'CANCEL' THEN 3 ELSE 0 END) +
            (CASE WHEN LOWER(MsgBody) LIKE '%better business%' THEN 2.5 ELSE 0 END) +
            (CASE WHEN LOWER(MsgBody) LIKE '%bbb%' THEN 2.5 ELSE 0 END) +
            (CASE WHEN LOWER(MsgBody) LIKE '%lawyer%' THEN 2.5 ELSE 0 END)
        ) AS Score
    FROM dbo.SMSLog
    WHERE 
        MsgDirection = 'inbound' AND
        MsgBody IS NOT NULL AND
        MsgBody <> '' AND
        IsDeleted = 0 AND
        MsgDateSent >= DATEADD(day, -30, GETDATE())
        AND (
            (
                (LOWER(MsgBody) LIKE '%i want%' AND LOWER(MsgBody) LIKE '%refund%') OR
                (LOWER(MsgBody) LIKE '%i need%' AND LOWER(MsgBody) LIKE '%refund%') OR
                LOWER(MsgBody) LIKE '%full refund%' OR
                LOWER(MsgBody) LIKE '%money back%' OR
                LOWER(MsgBody) LIKE '%don''t charge%' OR
                (LOWER(MsgBody) LIKE '%unauthorized%' AND LOWER(MsgBody) LIKE '%charge%') OR
                LOWER(MsgBody) LIKE '%you charged me%' OR
                LOWER(MsgBody) LIKE '%was charged%' OR
                LOWER(MsgBody) LIKE '%got charged%' OR
                (LOWER(MsgBody) LIKE '%charged my%' AND LOWER(MsgBody) LIKE '%account%') OR
                (LOWER(MsgBody) LIKE '%stop%' AND LOWER(MsgBody) LIKE '%charge%') OR
                (LOWER(MsgBody) LIKE '%why%' AND LOWER(MsgBody) LIKE '%charge%') OR
                LOWER(MsgBody) LIKE '%unexpected charge%' OR
                (LOWER(MsgBody) LIKE '%cancel%' AND (LOWER(MsgBody) LIKE '%service%' OR LOWER(MsgBody) LIKE '%account%' OR LOWER(MsgBody) LIKE '%program%' OR LOWER(MsgBody) LIKE '%subscription%')) OR
                LOWER(MsgBody) LIKE '%better business%' OR
                LOWER(MsgBody) LIKE '%bbb%' OR
                LOWER(MsgBody) LIKE '%lawyer%'
            )
            AND NOT (
                MsgBody LIKE '%Zelle%' OR
                MsgBody LIKE '%CK.%' OR
                MsgBody LIKE '%Savings%' OR
                MsgBody LIKE '%Bank%' OR
                (MsgBody LIKE '%Refund%' AND MsgBody NOT LIKE '%I want%' AND MsgBody NOT LIKE '%need%' AND MsgBody NOT LIKE '%why%' AND MsgBody NOT LIKE '%stop%') OR
                (MsgBody LIKE '%$%' AND LEN(MsgBody) > 120)
            )
        )
    ORDER BY MsgDateSent DESC
    '''
    params = []
    if start_date:
        sql += ' AND MsgDateSent >= ?'
        params.append(start_date)
    if end_date:
        sql += ' AND MsgDateSent <= ?'
        params.append(end_date)
    if keyword:
        sql += ' AND MsgBody LIKE ?'
        params.append(f'%{keyword}%')
    if severity == 'High':
        sql += ' AND ((CASE WHEN LOWER(MsgBody) LIKE ''%i want%'' AND LOWER(MsgBody) LIKE ''%refund%'' THEN 3 ELSE 0 END) + ... ) >= 3'
    elif severity == 'Moderate':
        sql += ' AND ((CASE WHEN LOWER(MsgBody) LIKE ''%i want%'' AND LOWER(MsgBody) LIKE ''%refund%'' THEN 3 ELSE 0 END) + ... ) >= 2'
    try:
        conn = pyodbc.connect(
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={os.getenv('DB_SERVER')};"
            f"DATABASE={os.getenv('DB_NAME')};"
            f"UID={os.getenv('DB_USER')};"
            f"PWD={os.getenv('DB_PASSWORD')}"
        )
        cursor = conn.cursor()
        cursor.execute(sql, params)
        flagged_messages = cursor.fetchall()
        conn.close()
    except Exception as e:
        flagged_messages = []
        flash(f"Error connecting to main database: {str(e)}", "danger")
    return render_template('dashboard.html', flagged_messages=flagged_messages)

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
    return render_template('conversation.html', messages=messages, case_id=case_id)

@dashboard_bp.route('/followup/<case_id>', methods=['GET', 'POST'])
@login_required
def followup(case_id):
    flagged = FlaggedMessage.query.filter_by(followed_up_by=current_user.Email, smslog_id=case_id).first()
    if request.method == 'POST':
        status = request.form.get('status')
        notes = request.form.get('notes')
        if not flagged:
            flagged = FlaggedMessage(smslog_id=case_id, follow_up_status=status, notes=notes, followed_up_by=current_user.Email)
            db.session.add(flagged)
        else:
            flagged.follow_up_status = status
            flagged.notes = notes
            flagged.followed_up_by = current_user.Email
        db.session.commit()
        return redirect(url_for('dashboard.conversation', case_id=case_id))
    # GET
    if not flagged:
        flagged = FlaggedMessage(follow_up_status='No', notes='', followed_up_by='')
    return render_template('followup.html', flagged=flagged, case_id=case_id) 