"""Small, additive schema upgrades for installations without Alembic."""
from sqlalchemy import inspect, text

from app.extensions import db


def upgrade_kline_cache():
    """Keep existing databases readable; fresh tables are created by db_init.py."""
    with db.engine.begin() as connection:
        inspector = inspect(connection)
        if not inspector.has_table('etf_kline_cache'):
            return
        columns = {column['name'] for column in inspector.get_columns('etf_kline_cache')}
        if 'turnover_rate' not in columns:
            connection.execute(text('ALTER TABLE etf_kline_cache ADD COLUMN turnover_rate FLOAT'))
