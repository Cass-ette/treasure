from app import db
from datetime import datetime

class Profit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    daily_profit = db.Column(db.Float, default=0.0)  # 当日盈亏
    cumulative_profit = db.Column(db.Float, default=0.0)  # 累计盈亏
    share_amount = db.Column(db.Float, default=0.0)  # 分成金额
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Profit User:{self.user_id}, Date:{self.date.strftime("%Y-%m-%d")}, Profit:{self.daily_profit}>'