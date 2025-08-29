from app import db
from datetime import datetime

class Agreement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    profit_share_ratio = db.Column(db.Float, nullable=False)  # 分成比例 (0-1之间)
    is_capital_protected = db.Column(db.Boolean, default=False)  # 是否保本
    capital_protection_ratio = db.Column(db.Float, default=1.0)  # 保本比例
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Agreement User:{self.user_id}, Ratio:{self.profit_share_ratio}>'