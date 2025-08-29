from app import db
from datetime import datetime

class Position(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    fund_id = db.Column(db.Integer, db.ForeignKey('fund.id'), nullable=False)
    shares = db.Column(db.Float, default=0.0)  # 持仓份额
    cost_price = db.Column(db.Float)  # 成本价
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Position User:{self.user_id}, Fund:{self.fund_id}>'