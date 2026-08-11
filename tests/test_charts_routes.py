"""Charts Blueprint 路由测试."""
import pytest
from werkzeug.security import generate_password_hash


@pytest.fixture
def charts_app():
    from app import create_app
    return create_app('app.config.TestConfig')


@pytest.fixture
def charts_db(charts_app):
    from app.extensions import db
    with charts_app.app_context():
        db.create_all()
        yield db
        db.session.rollback()
        db.drop_all()


@pytest.fixture
def charts_client(charts_app, charts_db):
    return charts_app.test_client()


@pytest.fixture
def admin_user(charts_db):
    from app.models import User
    u = User(
        username='admin',
        password=generate_password_hash('admin123', method='pbkdf2:sha256'),
        is_main_account=True,
    )
    charts_db.session.add(u)
    charts_db.session.commit()
    return u


@pytest.fixture
def logged_in_client(charts_client, admin_user):
    charts_client.post('/login', data={'username': 'admin', 'password': 'admin123'}, follow_redirects=True)
    return charts_client


class TestChipPageRoute:
    """GET /charts/etf/<symbol>/chip HTML 页面."""

    def test_invalid_symbol_returns_404(self, logged_in_client):
        """非 6 位代码返回 404。"""
        resp = logged_in_client.get('/charts/etf/ABC/chip')
        assert resp.status_code == 404

    def test_valid_symbol_renders_template(self, logged_in_client, monkeypatch):
        """合法代码渲染 etf_chip.html（mock 远端行情）。"""
        from app.services import quote_provider
        from app.services.quote_provider import ETFQuote

        fake = ETFQuote(
            symbol='SH562500', name='机器人ETF华夏', market='SH',
            latest=1.234, open=1.22, high=1.24, low=1.21, prev_close=1.22,
            change_amount=0.014, change_pct=1.15,
            volume=100000, amount=123000,
        )
        monkeypatch.setattr(quote_provider, 'fetch_etf_quote', lambda s: fake)

        resp = logged_in_client.get('/charts/etf/562500/chip')
        assert resp.status_code == 200
        assert b'562500' in resp.data


class TestChipDataAPI:
    """GET /charts/api/etf/<symbol>/chip-data JSON."""

    def test_invalid_symbol_returns_404(self, logged_in_client):
        resp = logged_in_client.get('/charts/api/etf/XYZ/chip-data')
        assert resp.status_code == 404

    def test_valid_symbol_returns_json(self, logged_in_client, monkeypatch):
        from app.services import quote_provider
        from app.services.quote_provider import ETFDailyBar, ETFQuote

        bars = [
            ETFDailyBar(date='2026-01-02', open=1.05, high=1.08, low=1.04, close=1.07, volume=100000, amount=105000),
            ETFDailyBar(date='2026-01-03', open=1.07, high=1.10, low=1.06, close=1.09, volume=120000, amount=130000),
        ]
        monkeypatch.setattr(quote_provider, 'fetch_etf_daily_kline', lambda s, days=250: bars)

        fake_quote = ETFQuote(
            symbol='SH562500', name='机器人ETF华夏', market='SH',
            latest=1.09, open=1.07, high=1.10, low=1.06, prev_close=1.07,
            change_amount=0.02, change_pct=1.87,
            volume=120000, amount=130000,
        )
        monkeypatch.setattr(quote_provider, 'fetch_etf_quote', lambda s: fake_quote)

        resp = logged_in_client.get('/charts/api/etf/562500/chip-data?days=30')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data is not None
        assert data['symbol'] == 'SH562500'
        assert data['name'] == '机器人ETF华夏'
        assert 'current_price' in data
        assert isinstance(data['klines'], list)
        assert len(data['klines']) == 2
        assert 'distribution' in data
        assert 'peaks' in data
        assert 'metrics' in data
        assert 'concentration' in data['metrics']
        assert 'profit_ratio' in data['metrics']

    def test_no_kline_data_returns_404(self, logged_in_client, monkeypatch):
        """远端拉不到任何 K 线 → 404。"""
        from app.services import quote_provider
        from app.services.quote_provider import ETFQuote

        monkeypatch.setattr(quote_provider, 'fetch_etf_daily_kline', lambda s, days=250: [])
        fake_quote = ETFQuote(
            symbol='SH999999', name='XXX', market='SH',
            latest=1.0, open=1.0, high=1.0, low=1.0, prev_close=1.0,
            change_amount=0, change_pct=0, volume=0, amount=0,
        )
        monkeypatch.setattr(quote_provider, 'fetch_etf_quote', lambda s: fake_quote)

        resp = logged_in_client.get('/charts/api/etf/999999/chip-data')
        assert resp.status_code == 404

    def test_custom_params_passed_through(self, logged_in_client, monkeypatch):
        """URL 参数 decay/bins 透传给算法。"""
        from app.services import quote_provider
        from app.services.quote_provider import ETFDailyBar, ETFQuote
        from app.services import chip_distribution

        bars = [
            ETFDailyBar(date='2026-01-0' + str(i), open=1.0 + i * 0.01, high=1.05 + i * 0.01,
                        low=0.95 + i * 0.01, close=1.02 + i * 0.01, volume=100000, amount=105000)
            for i in range(1, 6)
        ]
        monkeypatch.setattr(quote_provider, 'fetch_etf_daily_kline', lambda s, days=250: bars)
        fake_quote = ETFQuote(
            symbol='SH562500', name='X', market='SH',
            latest=1.05, open=1.04, high=1.06, low=1.03, prev_close=1.04,
            change_amount=0.01, change_pct=0.95, volume=100000, amount=105000,
        )
        monkeypatch.setattr(quote_provider, 'fetch_etf_quote', lambda s: fake_quote)

        captured = {}
        orig = chip_distribution.compute_chip_distribution

        def spy(bars_arg, decay=None, bin_count=None, price_padding=0.02):
            captured['decay'] = decay
            captured['bin_count'] = bin_count
            return orig(bars_arg, decay=decay, bin_count=bin_count, price_padding=price_padding)

        monkeypatch.setattr(chip_distribution, 'compute_chip_distribution', spy)

        resp = logged_in_client.get('/charts/api/etf/562500/chip-data?decay=0.99&bins=40')
        assert resp.status_code == 200
        assert captured['decay'] == 0.99
        assert captured['bin_count'] == 40
