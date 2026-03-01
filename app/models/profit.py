from app.extensions import db
from datetime import datetime


class Profit(db.Model):
    __tablename__ = 'profit'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    daily_profit = db.Column(db.Float, default=0.0)
    cumulative_profit = db.Column(db.Float, default=0.0)
    share_amount = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Profit User:{self.user_id}, Date:{self.date.strftime("%Y-%m-%d")}>'
