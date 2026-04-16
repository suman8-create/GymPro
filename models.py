from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import date, datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='trainer')
    trainer_id = db.Column(db.Integer, db.ForeignKey('trainer.id'), nullable=True)
    trainer = db.relationship('Trainer', backref='user_account', uselist=False)

class Trainer(db.Model):
    __tablename__ = 'trainer'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    specialty = db.Column(db.String(100), nullable=False)
    members = db.relationship('Member', backref='trainer', lazy=True)

class Member(db.Model):
    __tablename__ = 'member'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    join_date = db.Column(db.Date, default=date.today)
    subscription_end_date = db.Column(db.Date, nullable=True) 
    plan_type = db.Column(db.String(20), default='Monthly')
    trainer_id = db.Column(db.Integer, db.ForeignKey('trainer.id'), nullable=True)
    
    attendance_records = db.relationship('Attendance', backref='member', lazy=True)
    payments = db.relationship('Payment', backref='member', lazy=True)
    notifications = db.relationship('NotificationLog', backref='member', lazy=True)

    @property
    def is_active(self):
        if not self.subscription_end_date:
            return False
        return self.subscription_end_date >= date.today()

class Payment(db.Model):
    __tablename__ = 'payment'
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, default=date.today, nullable=False)
    plan_credited = db.Column(db.String(20), nullable=False)

class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)

class NotificationLog(db.Model):
    __tablename__ = 'notification_log'
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('member.id'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    sent_date = db.Column(db.DateTime, default=datetime.now)