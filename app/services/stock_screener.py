"""Public A-share snapshot retrieval and deterministic local screening."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import math
import threading
from typing import Any

import requests


EASTMONEY_STOCK_LIST_URL = "https://push2.eastmoney.com/api/qt/clist/get"
SNAPSHOT_TTL_SECONDS = 300
SNAPSHOT_FIELDS = (
    "f2,f3,f4,f5,f6,f7,f8,f9,f12,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f62,f184"
)
MARKET_FS = {
    "all": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
    "sh": "m:1+t:2,m:1+t:23",
    "sz": "m:0+t:6,m:0+t:80",
    "main": "m:0+t:6,m:1+t:2",
    "gem": "m:0+t:80",
    "star": "m:1+t:23",
}


class StockDataError(RuntimeError):
    """Raised when no stock snapshot is available."""


@dataclass
class StockSnapshot:
    rows: list[dict[str, Any]]
    fetched_at: datetime
    stale: bool = False


_cache: dict[str, StockSnapshot] = {}
_cache_lock = threading.Lock()


def _number(value: Any) -> float | None:
    try:
        value = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return value if math.isfinite(value) else None


def _market_for_code(code: str) -> str:
    return "SH" if code.startswith(("60", "68", "69")) else "SZ"


def _board_for_code(code: str) -> str:
    if code.startswith("68"):
        return "star"
    if code.startswith(("30", "301")):
        return "gem"
    return "main"


def _normalize_row(raw: dict[str, Any]) -> dict[str, Any] | None:
    code = str(raw.get("f12") or "").strip()
    name = str(raw.get("f14") or "").strip()
    if not code.isdigit() or len(code) != 6 or not name:
        return None
    return {
        "code": code,
        "name": name,
        "market": _market_for_code(code),
        "board": _board_for_code(code),
        "price": _number(raw.get("f2")),
        "change_pct": _number(raw.get("f3")),
        "change_amount": _number(raw.get("f4")),
        "volume": _number(raw.get("f5")),
        "amount": _number(raw.get("f6")),
        "amplitude": _number(raw.get("f7")),
        "turnover_rate": _number(raw.get("f8")),
        "pe": _number(raw.get("f9")),
        "total_market_cap": _number(raw.get("f20")),
        "float_market_cap": _number(raw.get("f21")),
        "pb": _number(raw.get("f23")),
        "change_60d": _number(raw.get("f24")),
        "change_ytd": _number(raw.get("f25")),
        "main_inflow": _number(raw.get("f62")),
        "main_inflow_pct": _number(raw.get("f184")),
    }


def _fetch_remote(market: str) -> StockSnapshot:
    response = requests.get(
        EASTMONEY_STOCK_LIST_URL,
        params={
            "pn": "1",
            "pz": "6000",
            "po": "1",
            "np": "1",
            "fltt": "2",
            "invt": "2",
            "fid": "f3",
            "fs": MARKET_FS[market],
            "fields": SNAPSHOT_FIELDS,
        },
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    data = payload.get("data") or {}
    raw_rows = data.get("diff") or []
    if isinstance(raw_rows, dict):
        raw_rows = list(raw_rows.values())
    rows = [row for raw in raw_rows if isinstance(raw, dict) and (row := _normalize_row(raw))]
    if not rows:
        raise StockDataError("股票行情接口返回了空数据")
    return StockSnapshot(rows=rows, fetched_at=datetime.now(timezone.utc))


def fetch_stock_snapshot(market: str = "all", force: bool = False) -> StockSnapshot:
    """Fetch a short-lived public snapshot, falling back to stale memory data."""
    if market not in MARKET_FS:
        raise ValueError("unsupported market")
    now = datetime.now(timezone.utc)
    with _cache_lock:
        cached = _cache.get(market)
        if cached and not force and (now - cached.fetched_at).total_seconds() < SNAPSHOT_TTL_SECONDS:
            return cached
    try:
        snapshot = _fetch_remote(market)
    except Exception as exc:
        with _cache_lock:
            cached = _cache.get(market)
        if cached:
            return StockSnapshot(cached.rows, cached.fetched_at, stale=True)
        raise StockDataError("暂时无法获取股票行情，请稍后重试") from exc
    with _cache_lock:
        _cache[market] = snapshot
    return snapshot


def clear_snapshot_cache() -> None:
    """Test/support hook for explicit refreshes."""
    with _cache_lock:
        _cache.clear()


def _in_range(value: float | None, minimum: float | None, maximum: float | None) -> bool:
    if value is None:
        return minimum is None and maximum is None
    return (minimum is None or value >= minimum) and (maximum is None or value <= maximum)


SORT_FIELDS = {
    "change_pct": "change_pct",
    "amount": "amount",
    "turnover_rate": "turnover_rate",
    "pe": "pe",
    "pb": "pb",
    "total_market_cap": "total_market_cap",
    "price": "price",
    "code": "code",
    "name": "name",
}


def screen_stocks(
    snapshot: StockSnapshot,
    *,
    keyword: str = "",
    market: str = "all",
    exclude_special: bool = True,
    min_price: float | None = None,
    max_price: float | None = None,
    min_change: float | None = None,
    max_change: float | None = None,
    min_turnover: float | None = None,
    max_turnover: float | None = None,
    min_amount: float | None = None,
    max_amount: float | None = None,
    min_pe: float | None = None,
    max_pe: float | None = None,
    min_pb: float | None = None,
    max_pb: float | None = None,
    min_market_cap: float | None = None,
    max_market_cap: float | None = None,
    sort: str = "change_pct",
    order: str = "desc",
) -> list[dict[str, Any]]:
    """Apply filters locally; money inputs are in yuan."""
    if sort not in SORT_FIELDS or order not in ("asc", "desc") or market not in MARKET_FS:
        raise ValueError("unsupported screening option")
    needle = keyword.strip().lower()
    result = []
    for row in snapshot.rows:
        if market == "sh" and row["market"] != "SH":
            continue
        if market == "sz" and row["market"] != "SZ":
            continue
        if market == "main" and row["board"] != "main":
            continue
        if market in ("gem", "star") and row["board"] != market:
            continue
        if exclude_special and any(token in row["name"].upper() for token in ("ST", "退")):
            continue
        if needle and needle not in (row["code"] + row["name"]).lower():
            continue
        if not _in_range(row["price"], min_price, max_price):
            continue
        if not _in_range(row["change_pct"], min_change, max_change):
            continue
        if not _in_range(row["turnover_rate"], min_turnover, max_turnover):
            continue
        if not _in_range(row["amount"], min_amount, max_amount):
            continue
        if not _in_range(row["pe"], min_pe, max_pe):
            continue
        if not _in_range(row["pb"], min_pb, max_pb):
            continue
        if not _in_range(row["total_market_cap"], min_market_cap, max_market_cap):
            continue
        result.append(row)
    field = SORT_FIELDS[sort]
    present = [row for row in result if row[field] is not None]
    missing = [row for row in result if row[field] is None]
    present.sort(key=lambda row: row[field], reverse=order == "desc")
    return present + missing
