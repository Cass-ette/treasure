from app.extensions import db
from datetime import datetime, timedelta


class FundNavHistory(db.Model):
    __tablename__ = 'fund_nav_history'

    id = db.Column(db.Integer, primary_key=True)
    fund_id = db.Column(db.Integer, db.ForeignKey('fund.id'), nullable=False)
    nav = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    fund = db.relationship('Fund', backref=db.backref('nav_histories', lazy=True))

    def __repr__(self):
        return f'<FundNavHistory fund_id={self.fund_id} date={self.date.strftime("%Y-%m-%d")} nav={self.nav}>'

    @staticmethod
    def get_nav_by_date(fund_id, date):
        """根据基金ID和日期获取净值"""
        return FundNavHistory.query.filter_by(fund_id=fund_id, date=date).first()

    @staticmethod
    def get_latest_navs(fund_id, max_days=30):
        """获取基金最近指定天数的净值历史数据（排除周末）"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=max_days * 3)

        nav_records = FundNavHistory.query.filter(
            FundNavHistory.fund_id == fund_id,
            FundNavHistory.date >= start_date,
            FundNavHistory.date <= end_date
        ).order_by(FundNavHistory.date.desc()).all()

        trading_days = []
        for record in nav_records:
            if record.date.weekday() < 5:
                trading_days.append(record)
                if len(trading_days) >= max_days:
                    break

        trading_days.sort(key=lambda x: x.date)
        return trading_days
