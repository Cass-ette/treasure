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
    with charts_app.app_context():
        db.session.rollback()
        db.drop_all()


@pytest.fixture
def charts_client(charts_app, charts_db):
    return charts_app.test_client()


@pytest.fixture
def admin_user(charts_db, charts_app):
    from app.models import User
    with charts_app.app_context():
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
        assert data['model']['method'] == 'legacy'
        assert data['model']['fallback_reason'] == 'missing_turnover'
        assert sum(d['share'] for d in data['distribution']) == pytest.approx(1)

    def test_no_kline_data_returns_404_with_friendly_error(self, logged_in_client, monkeypatch):
        """远端拉不到任何 K 线 → 404 + 友好提示（供前端展示）。"""
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
        body = resp.get_json()
        assert body is not None
        assert 'error' in body
        assert '场内 ETF' in body['error']

    def test_no_kline_data_error_translated(self, logged_in_client, monkeypatch):
        """友好错误信息随语言切换。"""
        from app.services import quote_provider
        from app.services.quote_provider import ETFQuote

        monkeypatch.setattr(quote_provider, 'fetch_etf_daily_kline', lambda s, days=250: [])
        fake_quote = ETFQuote(
            symbol='SH999999', name='XXX', market='SH',
            latest=1.0, open=1.0, high=1.0, low=1.0, prev_close=1.0,
            change_amount=0, change_pct=0, volume=0, amount=0,
        )
        monkeypatch.setattr(quote_provider, 'fetch_etf_quote', lambda s: fake_quote)

        logged_in_client.set_cookie('locale', 'en')
        resp = logged_in_client.get('/charts/api/etf/999999/chip-data')
        assert resp.status_code == 404
        body = resp.get_json()
        assert 'ETF' in body['error'] and 'exchange' in body['error'].lower()

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

    @pytest.mark.parametrize('query', [
        'days=0', 'days=1251', 'days=abc', 'bins=0', 'bins=241', 'bins=abc',
        'decay=nan', 'decay=inf', 'decay=0', 'decay=1.1', 'decay=abc',
        'band=nan', 'band=0', 'band=1', 'model=invalid', 'shape=invalid',
    ])
    def test_invalid_parameters_are_rejected_before_fetch(self, logged_in_client, monkeypatch, query):
        from app.services import quote_provider
        monkeypatch.setattr(quote_provider, 'fetch_etf_daily_kline',
                            lambda *a, **k: pytest.fail('Invalid parameters must not fetch'))
        response = logged_in_client.get('/charts/api/etf/002624/chip-data?' + query)
        assert response.status_code == 400
        assert response.get_json()['error']

    def test_turnover_model_returns_provenance_and_allows_legacy_comparison(self, logged_in_client, monkeypatch):
        from app.services import quote_provider
        from app.services.quote_provider import ETFDailyBar
        captured = []

        def history(symbol, days=250):
            captured.append(days)
            return [ETFDailyBar('2026-01-01', 10, 12, 9, 11, 100, 10000, 1.5),
                    ETFDailyBar('2026-01-02', 11, 14, 10, 13, 200, 20000, 5)]

        monkeypatch.setattr(quote_provider, 'fetch_etf_daily_kline', history)
        monkeypatch.setattr(quote_provider, 'fetch_etf_quote', lambda s: None)
        data = logged_in_client.get('/charts/api/etf/002624/chip-data?days=60').get_json()
        assert captured == [60]
        assert data['model']['method'] == 'turnover'
        assert data['model']['daily_shape'] == 'triangular'
        assert data['model']['turnover_days'] == 2
        assert data['model']['initial_mass_remaining'] == pytest.approx(0.95)
        assert data['klines'][0]['turnover_rate'] == 1.5
        assert sum(d['weight'] for d in data['distribution']) == pytest.approx(1)
        assert data['current_price'] == 13
        legacy = logged_in_client.get('/charts/api/etf/002624/chip-data?model=legacy').get_json()
        assert legacy['model']['method'] == 'legacy'
        assert legacy['model']['fallback_reason'] is None

    def test_empty_traded_distribution_is_valid_json(self, logged_in_client, monkeypatch):
        from app.services import quote_provider
        from app.services.quote_provider import ETFDailyBar
        monkeypatch.setattr(quote_provider, 'fetch_etf_daily_kline', lambda *a, **k: [
            ETFDailyBar('2026-01-01', 10, 10, 10, 10, 0, 0, None)])
        monkeypatch.setattr(quote_provider, 'fetch_etf_quote', lambda s: None)
        data = logged_in_client.get('/charts/api/etf/002624/chip-data').get_json()
        assert data['distribution'] == []
        assert data['metrics']['avg_cost'] is None
        assert data['model']['active_days'] == 0

    def test_page_preserves_requested_trading_window(self, logged_in_client, monkeypatch):
        from app.services import quote_provider
        monkeypatch.setattr(quote_provider, 'fetch_etf_quote', lambda s: None)
        response = logged_in_client.get('/charts/etf/002624/chip?days=60')
        assert response.status_code == 200
        assert 'days: 60' in response.text
        assert 'param-model' in response.text
        assert 'param-shape' in response.text


class TestAkshareTestEndpoint:
    """GET /charts/api/etf/<symbol>/akshare-test akshare 可用性测试口."""

    def test_invalid_symbol_returns_404(self, logged_in_client):
        resp = logged_in_client.get('/charts/api/etf/ABC/akshare-test')
        assert resp.status_code == 404

    def test_returns_kline_json(self, logged_in_client, monkeypatch):
        """akshare 拉取成功时返回 K 线 JSON。"""
        from app.services import quote_provider
        from app.services.quote_provider import ETFDailyBar

        bars = [
            ETFDailyBar(date='2026-01-02', open=1.05, high=1.08, low=1.04, close=1.07, volume=100000, amount=105000),
            ETFDailyBar(date='2026-01-03', open=1.07, high=1.10, low=1.06, close=1.09, volume=120000, amount=130000),
        ]
        monkeypatch.setattr(quote_provider, 'fetch_etf_daily_kline_akshare', lambda s, days=250: bars)

        resp = logged_in_client.get('/charts/api/etf/562500/akshare-test?days=30')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['source'] == 'akshare'
        assert data['ok'] is True
        assert len(data['klines']) == 2
        assert data['klines'][0]['date'] == '2026-01-02'

    def test_returns_error_status_when_akshare_fails(self, logged_in_client, monkeypatch):
        """akshare 拉取失败时返回 ok=False + 错误信息（不 500）。"""
        from app.services import quote_provider
        monkeypatch.setattr(
            quote_provider, 'fetch_etf_daily_kline_akshare',
            lambda s, days=250: (_ for _ in ()).throw(RuntimeError('akshare failed')),
        )

        resp = logged_in_client.get('/charts/api/etf/562500/akshare-test')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['ok'] is False
        assert 'akshare failed' in data['error']
