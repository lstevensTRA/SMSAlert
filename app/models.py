from . import db
from flask_login import UserMixin
from datetime import datetime
import bcrypt
import uuid
from sqlalchemy.dialects.postgresql import UUID

class User(UserMixin, db.Model):
    __tablename__ = 'Users'
    UserID = db.Column(db.Integer, primary_key=True)
    Email = db.Column(db.String(120), unique=True, nullable=False)
    Password = db.Column(db.String(128), nullable=False)
    IsActive = db.Column(db.Boolean, default=True)
    EmailVerified = db.Column(db.Boolean, default=False)
    FirstName = db.Column(db.String(50))
    LastName = db.Column(db.String(50))
    LastLogin = db.Column(db.DateTime)

    def set_password(self, password):
        self.Password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.Password.encode('utf-8'))

    def get_id(self):
        return str(self.UserID)

    def __repr__(self):
        return f'<User {self.Email}>'

class Keyword(db.Model):
    __tablename__ = 'Keywords'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(100), nullable=False)
    match_type = db.Column(db.String(10), default='fuzzy')
    severity = db.Column(db.String(10), default='Low')
    routing_tag = db.Column(db.String(50))

    def __repr__(self):
        return f'<Keyword {self.text}>'

class SMSLog(db.Model):
    __tablename__ = 'SMSLog'
    id = db.Column(db.Integer, primary_key=True)
    CaseID = db.Column(db.String(50))
    MsgDirection = db.Column(db.String(20))
    MsgDateSent = db.Column(db.DateTime)
    MsgBody = db.Column(db.Text)
    MsgFrom = db.Column(db.String(50))
    MsgTo = db.Column(db.String(50))

    def __repr__(self):
        return f'<SMSLog {self.CaseID} {self.MsgDateSent}>'

class FlaggedMessage(db.Model):
    __tablename__ = 'FlaggedMessages'
    id = db.Column(db.Integer, primary_key=True)
    smslog_id = db.Column(db.Integer, db.ForeignKey('SMSLog.id'))
    keyword_id = db.Column(db.Integer, db.ForeignKey('Keywords.id'))
    score = db.Column(db.Float)
    flagged_at = db.Column(db.DateTime, default=datetime.utcnow)
    follow_up_status = db.Column(db.String(10), default='No')
    follow_up_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    followed_up_by = db.Column(db.String(120))

    smslog = db.relationship('SMSLog')
    keyword = db.relationship('Keyword')

    def __repr__(self):
        return f'<FlaggedMessage {self.id}>'

class AuditLog(db.Model):
    __tablename__ = 'AuditLogs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.UserID'))
    action = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    device_info = db.Column(db.String(200))

    user = db.relationship('User')

    def __repr__(self):
        return f'<AuditLog {self.action} by {self.user_id}>'

class Settings(db.Model):
    __tablename__ = 'Settings'
    id = db.Column(db.Integer, primary_key=True)
    alert_recipients = db.Column(db.Text)  # comma-separated emails

    def __repr__(self):
        return f'<Settings {self.id}>'

class SupabaseFlaggedMessage(db.Model):
    __tablename__ = 'flagged_messages'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = db.Column(db.String)
    msg_body = db.Column(db.Text)
    msg_date = db.Column(db.DateTime)
    direction = db.Column(db.String)
    from_identity = db.Column(db.String)
    keyword_hit = db.Column(db.String)
    score = db.Column(db.Integer)
    status = db.Column(db.String, default='flagged')
    followed_up = db.Column(db.Boolean, default=False)
    followed_up_date = db.Column(db.DateTime)
    reviewed_by = db.Column(db.String)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow) 