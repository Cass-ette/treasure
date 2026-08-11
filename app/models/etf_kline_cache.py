from datetime import datetime

from app.extensions import db


class EtfKlineCache(db.Model):
    """场内 ETF 日 K 缓存（前复权）。

    用于筹码峰分析等需要历史 OHLCV 的功能，避免反复打远端。
    """
    __tablename__ = 'etf_kline_cache'

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False, index=True)  # 'SH562500'
    date = db.Column(db.Date, nullable=False, index=True)
    open = db.Column(db.Float)
    high = db.Column(db.Float)
    low = db.Column(db.Float)
    close = db.Column(db.Float)
    volume = db.Column(db.BigInteger)
    amount = db.Column(db.Float)
    name = db.Column(db.String(100))   # ETF 名称（冗余存，取最新行的）
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('symbol', 'date', name='uq_etf_kline_symbol_date'),
    )

    def __repr__(self):
        return f'<EtfKlineCache {self.symbol} {self.date} close={self.close}>'

    @staticmethod
    def get_latest_date(symbol: str):
        """返回该 symbol 在缓存里的最新日期，无数据返回 None。"""
        row = (
            EtfKlineCache.query
            .filter_by(symbol=symbol)
            .order_by(EtfKlineCache.date.desc())
            .first()
        )
        return row.date if row else None

    @staticmethod
    def get_recent(symbol: str, days: int):
        """返回最近 days 个交易日（含）的 K 线，按日期升序。"""
        rows = (
            EtfKlineCache.query
            .filter_by(symbol=symbol)
            .order_by(EtfKlineCache.date.desc())
            .limit(days)
            .all()
        )
        rows.sort(key=lambda r: r.date)
        return rows

    @staticmethod
    def get_latest_name(symbol: str):
        """返回该 symbol 最新一行记录的 name，无数据返回 None。"""
        row = (
            EtfKlineCache.query
            .filter_by(symbol=symbol)
            .order_by(EtfKlineCache.date.desc())
            .first()
        )
        return row.name if row else None
