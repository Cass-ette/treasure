from datetime import datetime
from app import db

class FundNavHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fund_id = db.Column(db.Integer, db.ForeignKey('fund.id'), nullable=False)
    nav = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 定义与Fund模型的关系
    fund = db.relationship('Fund', backref=db.backref('nav_histories', lazy=True))
    
    def __repr__(self):
        return f'<FundNavHistory fund_id={self.fund_id} date={self.date.strftime("%Y-%m-%d")} nav={self.nav}>'
    
    @staticmethod
    def get_nav_by_date(fund_id, date):
        """根据基金ID和日期获取净值"""
        return FundNavHistory.query.filter_by(
            fund_id=fund_id,
            date=date
        ).first()
        
    @staticmethod
    def get_latest_navs(fund_id, days=30):
        """获取基金最近N个交易日的净值"""
        from datetime import datetime, timedelta
        
        # 获取今天日期
        today = datetime.utcnow().date()
        
        # 查询最近N个交易日的净值，按日期降序排列
        navs = FundNavHistory.query.filter(
            FundNavHistory.fund_id == fund_id,
            FundNavHistory.date <= today
        ).order_by(FundNavHistory.date.desc()).limit(days).all()
        
        # 按日期升序返回
        return list(reversed(navs))