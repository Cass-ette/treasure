from app import db
from datetime import datetime

class Fund(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    fund_type = db.Column(db.String(50))
    latest_nav = db.Column(db.Float)  # 最新净值
    nav_date = db.Column(db.DateTime)  # 净值日期
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    positions = db.relationship('Position', backref='fund', lazy=True)
    transactions = db.relationship('Transaction', backref='fund', lazy=True)
    
    def __repr__(self):
        return f'<Fund {self.name} ({self.code})>'