from app import create_app, db
from app.models import User, Keyword, SMSLog
from datetime import datetime, timedelta

app = create_app()

with app.app_context():
    db.create_all()
    # SuperAdmin
    if not User.query.filter_by(Email='lindsey.stevens@tra').first():
        u = User(Email='lindsey.stevens@tra', FirstName='Lindsey', LastName='Stevens', IsActive=True)
        u.set_password('adminpass123')
        db.session.add(u)
    # Keywords
    if not Keyword.query.first():
        db.session.add_all([
            Keyword(text='refund', match_type='fuzzy', severity='High', routing_tag='Billing'),
            Keyword(text='cancel', match_type='fuzzy', severity='High', routing_tag='Retention'),
            Keyword(text='lawyer', match_type='fuzzy', severity='Moderate', routing_tag='Escalation'),
        ])
    # Dummy SMSLog
    if not SMSLog.query.first():
        now = datetime.utcnow()
        db.session.add_all([
            SMSLog(CaseID='C123', MsgDirection='inbound', MsgDateSent=now-timedelta(hours=2), MsgBody='I want a refund', MsgFrom='+15551234567', MsgTo='+15557654321'),
            SMSLog(CaseID='C123', MsgDirection='outbound', MsgDateSent=now-timedelta(hours=1), MsgBody='We are reviewing your request', MsgFrom='+15557654321', MsgTo='+15551234567'),
            SMSLog(CaseID='C124', MsgDirection='inbound', MsgDateSent=now-timedelta(hours=3), MsgBody='I will call my lawyer', MsgFrom='+15559876543', MsgTo='+15557654321'),
        ])
    db.session.commit()
    print('Seeded SuperAdmin, keywords, and dummy SMSLog.') 