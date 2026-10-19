import pytest
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash


@pytest.fixture
def authenticated_client(app, client, db):
    from app.models import User
    user = User(username="screenadmin", password=generate_password_hash("pw123"), is_main_account=True)
    db.session.add(user)
    db.session.commit()
    client.post("/login", data={"username": "screenadmin", "password": "pw123"})
    return client


def _snapshot():
    from app.services.stock_screener import StockSnapshot
    return StockSnapshot([
        {
            "code": "002624", "name": "完美世界", "market": "SZ", "board": "main",
            "price": 14.56, "change_pct": 4.0, "change_amount": 0.56,
            "volume": 100000, "amount": 100000000, "amplitude": 5.0,
            "turnover_rate": 3.2, "pe": 18.0, "total_market_cap": 28000000000,
            "float_market_cap": 20000000000, "pb": 1.6, "change_60d": 12.0,
            "change_ytd": 8.0, "main_inflow": 1000000, "main_inflow_pct": 2.0,
        },
        {
            "code": "600000", "name": "浦发银行", "market": "SH", "board": "main",
            "price": 10.0, "change_pct": -1.0, "change_amount": -0.1,
            "volume": 200000, "amount": 50000000, "amplitude": 2.0,
            "turnover_rate": 0.5, "pe": 5.0, "total_market_cap": 290000000000,
            "float_market_cap": 250000000000, "pb": 0.4, "change_60d": -4.0,
            "change_ytd": -2.0, "main_inflow": -100000, "main_inflow_pct": -1.0,
        },
        {
            "code": "300001", "name": "ST测试", "market": "SZ", "board": "gem",
            "price": 2.0, "change_pct": 10.0, "change_amount": 0.18,
            "volume": 1, "amount": 1, "amplitude": 10.0,
            "turnover_rate": 20.0, "pe": None, "total_market_cap": None,
            "float_market_cap": None, "pb": None, "change_60d": None,
            "change_ytd": None, "main_inflow": None, "main_inflow_pct": None,
        },
    ], datetime.now(timezone.utc))


class TestStockScreenerService:
    def test_normalizes_eastmoney_fields(self):
        from app.services.stock_screener import _normalize_row
        row = _normalize_row({"f12": "002624", "f14": "完美世界", "f2": 14.56,
                              "f3": 4, "f8": "-", "f9": -2, "f20": 28000000000,
                              "f21": 20000000000, "f23": 1.6})
        assert row["market"] == "SZ"
        assert row["price"] == 14.56
        assert row["turnover_rate"] is None
        assert row["pe"] == -2

    def test_filters_keyword_ranges_and_excludes_special(self):
        from app.services.stock_screener import screen_stocks
        rows = screen_stocks(_snapshot(), keyword="完美", min_change=0,
                             min_turnover=1, max_pe=30)
        assert [row["code"] for row in rows] == ["002624"]

        rows = screen_stocks(_snapshot(), min_price=1, max_price=12,
                             exclude_special=False, sort="price", order="asc")
        assert [row["code"] for row in rows] == ["300001", "600000"]

    def test_missing_sort_values_are_after_real_values(self):
        from app.services.stock_screener import screen_stocks
        rows = screen_stocks(_snapshot(), exclude_special=False, sort="pe", order="desc")
        assert [row["code"] for row in rows] == ["002624", "600000", "300001"]

    def test_market_filter_is_applied_locally(self):
        from app.services.stock_screener import screen_stocks
        assert [row["code"] for row in screen_stocks(_snapshot(), market="sh")] == ["600000"]
        assert [row["code"] for row in screen_stocks(_snapshot(), market="gem", exclude_special=False)] == ["300001"]

    def test_remote_cache_and_stale_fallback(self, monkeypatch):
        from app.services import stock_screener
        stock_screener.clear_snapshot_cache()
        calls = []

        class Response:
            def raise_for_status(self):
                pass

            def json(self):
                return {"data": {"diff": [{"f12": "002624", "f14": "完美世界", "f2": 14.56}]}}

        monkeypatch.setattr(stock_screener.requests, "get", lambda *a, **k: (calls.append(1) or Response()))
        first = stock_screener.fetch_stock_snapshot("all")
        second = stock_screener.fetch_stock_snapshot("all")
        assert len(first.rows) == 1 and second.rows == first.rows
        assert len(calls) == 1

        def fail(*args, **kwargs):
            raise RuntimeError("network")
        monkeypatch.setattr(stock_screener.requests, "get", fail)
        stale = stock_screener.fetch_stock_snapshot("all", force=True)
        assert stale.stale is True
        stock_screener.clear_snapshot_cache()


class TestStockScreenerRoutes:
    def test_page_requires_login(self, client):
        assert client.get("/stocks/screener").status_code == 302

    def test_page_renders_for_authenticated_user(self, authenticated_client):
        response = authenticated_client.get("/stocks/screener")
        assert response.status_code == 200
        assert "股票筛选".encode() in response.data
        assert b"stock_screener.js" in response.data

    def test_api_filters_and_converts_money_units(self, authenticated_client, monkeypatch):
        from app.services import stock_screener
        monkeypatch.setattr(stock_screener, "fetch_stock_snapshot", lambda market: _snapshot())
        response = authenticated_client.get(
            "/stocks/api/screener?min_amount=8000&min_market_cap=100&min_change=0&limit=20"
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["match_count"] == 1
        assert data["rows"][0]["code"] == "002624"

    @pytest.mark.parametrize("query", [
        "limit=0", "limit=201", "offset=-1", "min_price=nan", "max_turnover=-1",
        "market=invalid", "sort=unknown", "order=sideways",
    ])
    def test_invalid_parameters_return_400(self, authenticated_client, monkeypatch, query):
        from app.services import stock_screener
        monkeypatch.setattr(stock_screener, "fetch_stock_snapshot",
                            lambda *args: pytest.fail("invalid request must not fetch"))
        response = authenticated_client.get("/stocks/api/screener?" + query)
        assert response.status_code == 400
