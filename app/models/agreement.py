from app.extensions import db
from datetime import datetime


class Agreement(db.Model):
    __tablename__ = 'agreement'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    profit_share_ratio = db.Column(db.Float, nullable=False)
    is_capital_protected = db.Column(db.Boolean, default=False)
    capital_protection_ratio = db.Column(db.Float, default=1.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Agreement User:{self.user_id}, Ratio:{self.profit_share_ratio}>'
