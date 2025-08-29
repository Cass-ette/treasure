from datetime import datetime
from app import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_main_account = db.Column(db.Boolean, default=False)
    principal = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    positions = db.relationship('Position', backref='user', lazy=True)
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    agreement = db.relationship('Agreement', backref='user', uselist=False)
    profits = db.relationship('Profit', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'