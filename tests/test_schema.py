"""Existing installations upgrade without losing cached or portfolio data."""
import sqlite3


def test_app_startup_upgrades_legacy_database_idempotently(tmp_path):
    from app import create_app
    from app.config import TestConfig
    from app.extensions import db
    from app.models.etf_kline_cache import EtfKlineCache

    path = tmp_path / 'legacy.db'
    with sqlite3.connect(path) as connection:
        connection.execute('''CREATE TABLE etf_kline_cache (
            id INTEGER PRIMARY KEY, symbol VARCHAR(10), date DATE,
            open FLOAT, high FLOAT, low FLOAT, close FLOAT,
            volume BIGINT, amount FLOAT, name VARCHAR(100),
            created_at DATETIME, updated_at DATETIME)''')
        connection.execute("INSERT INTO etf_kline_cache (symbol, date, close) VALUES ('SZ002624', '2026-01-02', 12.34)")
        connection.execute('CREATE TABLE portfolio_sentinel (value TEXT)')
        connection.execute("INSERT INTO portfolio_sentinel VALUES ('keep me')")

    class Config(TestConfig):
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{path}'

    for _ in range(2):
        app = create_app(Config)
        with app.app_context():
            row = EtfKlineCache.query.one()
            assert row.close == 12.34
            assert row.turnover_rate is None
            db.session.remove()
            db.engine.dispose()
    with sqlite3.connect(path) as connection:
        assert connection.execute('SELECT value FROM portfolio_sentinel').fetchone() == ('keep me',)
