from flask import Blueprint, send_file
from flask_login import login_required
from ..models import FlaggedMessage
import pandas as pd
import io

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports/flagged.csv')
@login_required
def download_flagged_csv():
    # Placeholder: fetch flagged messages
    flagged = FlaggedMessage.query.all()
    data = [{
        'CaseID': f.smslog.CaseID if f.smslog else '',
        'Date': f.smslog.MsgDateSent if f.smslog else '',
        'Message': f.smslog.MsgBody if f.smslog else '',
        'Keyword': f.keyword.text if f.keyword else '',
        'Severity': f.keyword.severity if f.keyword else '',
        'Follow-up': f.follow_up_status
    } for f in flagged]
    df = pd.DataFrame(data)
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return send_file(io.BytesIO(buf.read().encode()), mimetype='text/csv', as_attachment=True, download_name='flagged_messages.csv') 