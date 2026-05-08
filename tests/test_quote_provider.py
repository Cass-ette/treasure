"""Quote provider tests: TDD for ETF/fund real-time quotes in treasure."""
import pytest
import json


class TestETFQuote:
    """场内 ETF 实时行情获取测试."""

    def test_fetch_eastmoney_etf_success(self, monkeypatch):
        """东方财富 ETF 接口能正确解析价格和成交额."""
        from app.services.quote_provider import fetch_etf_quote

        class FakeResponse:
            def raise_for_status(self):
                return

            def json(self):
                return {
                    "data": {
                        "f43": 1122,      # 最新价 * 1000
                        "f44": 1130,      # 最高 * 1000
                        "f45": 1118,      # 最低 * 1000
                        "f46": 1120,      # 开盘 * 1000
                        "f47": 123456,    # 成交量(手)
                        "f48": 9876543,   # 成交额(元)
                        "f57": "562500",  # 代码
                        "f58": "机器人ETF华夏",  # 名称
                        "f60": 1105,      # 昨收 * 1000
                        "f169": 17,       # 涨跌额 * 1000
                        "f170": 154,      # 涨跌幅 * 100
                    }
                }

        def fake_get(url, params, timeout, **kwargs):
            assert "push2.eastmoney.com" in url
            return FakeResponse()

        monkeypatch.setattr("app.services.quote_provider.requests.get", fake_get)

        quote = fetch_etf_quote("562500")
        assert quote is not None
        assert quote.symbol == "562500"
        assert quote.name == "机器人ETF华夏"
        assert quote.latest == 1.122
        assert quote.open == 1.120
        assert quote.high == 1.130
        assert quote.low == 1.118
        assert quote.prev_close == 1.105
        assert quote.change_amount == 0.017
        assert quote.change_pct == 1.54  # 1.54%
        assert quote.volume == 123456
        assert quote.amount == 9876543

    def test_fetch_eastmoney_returns_none_on_http_error(self, monkeypatch):
        """HTTP 失败时返回 None."""
        from app.services.quote_provider import fetch_etf_quote
        import requests

        def fake_get(url, params, timeout, **kwargs):
            raise requests.exceptions.RequestException("timeout")

        monkeypatch.setattr("app.services.quote_provider.requests.get", fake_get)

        quote = fetch_etf_quote("562500")
        assert quote is None

    def test_fetch_eastmoney_returns_none_on_no_data(self, monkeypatch):
        """响应中没有 data 字段时返回 None."""
        from app.services.quote_provider import fetch_etf_quote

        class FakeResponse:
            def raise_for_status(self):
                return

            def json(self):
                return {"data": None}

        monkeypatch.setattr("app.services.quote_provider.requests.get", lambda **kw: FakeResponse())

        quote = fetch_etf_quote("562500")
        assert quote is None


class TestOTCFundQuote:
    """场外基金估算净值测试."""

    def test_fetch_tiantian_fund_success(self, monkeypatch):
        """天天基金接口能正确解析 JSONP."""
        from app.services.quote_provider import fetch_fund_estimate

        class FakeResponse:
            def raise_for_status(self):
                return

            @property
            def text(self):
                return 'jsonpgz({"fundcode":"018344","name":"华夏中证机器人ETF发起式联接A","jzrq":"2026-05-08","dwjz":"1.3222","gsz":"1.3542","gszzl":"2.42","gztime":"2026-05-08 15:00"});'

        def fake_get(url, params, timeout, **kwargs):
            assert "fundgz.1234567.com.cn" in url
            assert "018344.js" in url
            return FakeResponse()

        monkeypatch.setattr("app.services.quote_provider.requests.get", fake_get)

        quote = fetch_fund_estimate("018344")
        assert quote is not None
        assert quote.symbol == "018344"
        assert quote.name == "华夏中证机器人ETF发起式联接A"
        assert quote.latest_nav == 1.3222
        assert quote.latest_nav_date == "2026-05-08"
        assert quote.estimated_nav == 1.3542
        assert quote.estimated_change_pct == 2.42
        assert quote.estimate_time == "2026-05-08 15:00"

    def test_fetch_tiantian_returns_none_on_invalid_format(self, monkeypatch):
        """JSONP 格式不对时返回 None."""
        from app.services.quote_provider import fetch_fund_estimate

        class FakeResponse:
            def raise_for_status(self):
                return

            @property
            def text(self):
                return "not valid jsonp"

        monkeypatch.setattr("app.services.quote_provider.requests.get", lambda **kw: FakeResponse())

        quote = fetch_fund_estimate("018344")
        assert quote is None


class TestBuildPairContext:
    """Pair 上下文生成测试."""

    def test_build_pair_context_returns_markdown_format(self, monkeypatch):
        """返回的上下文包含场内 ETF 和场外基金的关键信息."""
        from app.services.quote_provider import build_pair_context, ETFQuote, OTCFundQuote

        # mock ETF quote
        etf = ETFQuote(
            symbol="562500",
            name="机器人ETF华夏",
            market="SH",
            latest=1.122,
            open=1.100,
            high=1.126,
            low=1.091,
            prev_close=1.097,
            change_amount=0.025,
            change_pct=2.28,
            volume=14041248,
            amount=156357 * 10000,
        )
        # mock Fund quote
        fund = OTCFundQuote(
            symbol="018344",
            name="华夏中证机器人ETF发起式联接A",
            latest_nav=1.3222,
            latest_nav_date="2026-05-08",
            estimated_nav=1.3542,
            estimated_change_pct=2.42,
            estimate_time="2026-05-08 15:00",
        )

        monkeypatch.setattr(
            "app.services.quote_provider.fetch_etf_quote", lambda s: etf
        )
        monkeypatch.setattr(
            "app.services.quote_provider.fetch_fund_estimate", lambda s: fund
        )

        ctx = build_pair_context("robot", "562500", "018344")
        assert ctx is not None
        assert "机器人ETF华夏" in ctx
        assert "562500" in ctx
        assert "1.122" in ctx or "+2.28%" in ctx
        assert "华夏中证机器人ETF发起式联接A" in ctx
        assert "018344" in ctx
        assert "1.3222" in ctx or "1.3542" in ctx
        assert "场内" in ctx and "场外" in ctx
        assert "实时" in ctx and "估算" in ctx

    def test_build_pair_context_returns_none_when_quote_fails(self, monkeypatch):
        """任一报价失败时返回 None."""
        from app.services.quote_provider import build_pair_context

        monkeypatch.setattr("app.services.quote_provider.fetch_etf_quote", lambda s: None)

        ctx = build_pair_context("robot", "562500", "018344")
        assert ctx is None


class TestQuoteContextIntegration:
    """Quote context integration with AI assistant tests."""

    def test_build_quote_context_for_positions_with_known_pair(self, monkeypatch, db):
        """持仓包含已知 pair 时返回行情上下文."""
        from app.routes.ai_assistant import _build_quote_context_for_positions
        from app.services.quote_provider import ETFQuote, OTCFundQuote
        from app.models import Fund, Position

        # 创建测试基金和持仓
        fund = Fund(code="018344", name="华夏中证机器人ETF发起式联接A")
        db.session.add(fund)
        db.session.commit()
        pos = Position(user_id=1, fund_id=fund.id, shares=100.0, cost_price=1.30)
        db.session.add(pos)
        db.session.commit()

        # mock quote provider
        def mock_build_pair(name, etf, fund_code):
            return f"实时行情: {name}\nETF: {etf}\nFund: {fund_code}"

        monkeypatch.setattr(
            "app.services.quote_provider.build_pair_context", mock_build_pair
        )

        ctx = _build_quote_context_for_positions([pos])
        assert ctx is not None
        assert "实时行情: robot" in ctx
        assert "ETF: 562500" in ctx
        assert "Fund: 018344" in ctx

    def test_build_quote_context_returns_none_for_unknown_fund(self, db):
        """持仓不包含已知 pair 时返回 None."""
        from app.routes.ai_assistant import _build_quote_context_for_positions
        from app.models import Fund, Position

        fund = Fund(code="999999", name="未知基金")
        db.session.add(fund)
        db.session.commit()
        pos = Position(user_id=1, fund_id=fund.id, shares=100.0, cost_price=1.00)
        db.session.add(pos)
        db.session.commit()

        ctx = _build_quote_context_for_positions([pos])
        assert ctx is None
