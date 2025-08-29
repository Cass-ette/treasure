from app import db
from datetime import datetime

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    fund_id = db.Column(db.Integer, db.ForeignKey('fund.id'), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # buy/sell
    amount = db.Column(db.Float, nullable=False)  # 交易金额
    shares = db.Column(db.Float, nullable=False)  # 交易份额
    price = db.Column(db.Float, nullable=False)  # 交易价格
    fee = db.Column(db.Float, default=0.0)  # 手续费
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Transaction User:{self.user_id}, Fund:{self.fund_id}, Type:{self.transaction_type}>'