"""Real-time ETF and OTC fund quote provider for treasure.

Mirrors etf-cli quote capabilities without CLI dependencies.
"""
from dataclasses import dataclass
from typing import Optional
import requests
import json

EASTMONEY_QUOTE_URL = "https://push2.eastmoney.com/api/qt/stock/get"
TIANTIAN_FUND_URL = "https://fundgz.1234567.com.cn/js"


@dataclass
class ETFQuote:
    """场内 ETF 实时行情."""
    symbol: str
    name: str
    market: str
    latest: float
    open: float
    high: float
    low: float
    prev_close: float
    change_amount: float
    change_pct: float
    volume: int
    amount: int


@dataclass
class OTCFundQuote:
    """场外基金净值/估算."""
    symbol: str
    name: str
    latest_nav: float
    latest_nav_date: str
    estimated_nav: Optional[float]
    estimated_change_pct: Optional[float]
    estimate_time: Optional[str]


def _normalize_symbol(symbol: str) -> tuple[str, str, str]:
    """Normalize ETF symbol to (secid, market, tencent_code)."""
    symbol = symbol.strip().upper()
    if symbol.startswith(("SH", "SZ")):
        symbol = symbol[2:]
    if symbol.startswith(("51", "56", "58", "60", "68", "69")):
        return f"1.{symbol}", "SH", f"sh{symbol.lower()}"
    return f"0.{symbol}", "SZ", f"sz{symbol.lower()}"


def fetch_etf_quote(symbol: str) -> Optional[ETFQuote]:
    """Fetch exchange-traded ETF quote from Eastmoney."""
    secid, market, _ = _normalize_symbol(symbol)
    params = {
        "secid": secid,
        "fields": "f43,f44,f45,f46,f47,f48,f57,f58,f60,f169,f170",
    }
    try:
        resp = requests.get(EASTMONEY_QUOTE_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json().get("data")
        if not data:
            return None

        def price(field: str) -> float:
            val = data.get(field)
            return val / 1000 if val else 0.0

        def pct(field: str) -> float:
            val = data.get(field)
            return val / 100 if val else 0.0

        return ETFQuote(
            symbol=data.get("f57", symbol),
            name=data.get("f58", "Unknown"),
            market=market,
            latest=price("f43"),
            high=price("f44"),
            low=price("f45"),
            open=price("f46"),
            prev_close=price("f60"),
            change_amount=price("f169"),
            change_pct=pct("f170"),
            volume=data.get("f47", 0),
            amount=data.get("f48", 0),
        )
    except Exception:
        return None


def fetch_fund_estimate(symbol: str) -> Optional[OTCFundQuote]:
    """Fetch OTC fund NAV and estimated NAV from Tiantian Fund."""
    symbol = symbol.strip()
    url = f"{TIANTIAN_FUND_URL}/{symbol}.js"
    try:
        import time
        resp = requests.get(url, params={"rt": int(time.time() * 1000)}, timeout=10)
        resp.raise_for_status()
        text = resp.text.strip()
        if not text.startswith("jsonpgz(") or not text.endswith(");"):
            return None
        payload = json.loads(text[len("jsonpgz("):-2])
        return OTCFundQuote(
            symbol=payload.get("fundcode", symbol),
            name=payload.get("name", "Unknown"),
            latest_nav=float(payload.get("dwjz") or 0),
            latest_nav_date=payload.get("jzrq", ""),
            estimated_nav=float(payload["gsz"]) if payload.get("gsz") else None,
            estimated_change_pct=float(payload["gszzl"]) if payload.get("gszzl") else None,
            estimate_time=payload.get("gztime") or None,
        )
    except Exception:
        return None


def build_pair_context(name: str, etf_symbol: str, fund_symbol: str) -> Optional[str]:
    """Build combined ETF/fund pair AI context."""
    etf = fetch_etf_quote(etf_symbol)
    fund = fetch_fund_estimate(fund_symbol)
    if not etf or not fund:
        return None
    lines = [
        f"== 实时行情参考: {name} ==",
        f"场内 ETF 参考: {etf.name} ({etf.symbol})",
        f"  最新价: {etf.latest:.3f}",
        f"  涨跌幅: {etf.change_pct:+.2f}%",
        f"  成交量: {etf.volume:,} 手",
        f"  成交额: {etf.amount:,.0f} 元",
        "",
        f"场外基金实际交易对象: {fund.name} ({fund.symbol})",
        f"  最新单位净值: {fund.latest_nav:.4f} (日期: {fund.latest_nav_date})",
        f"  估算净值: {fund.estimated_nav:.4f}" if fund.estimated_nav else "  估算净值: N/A",
        f"  估算涨跌幅: {fund.estimated_change_pct:+.2f}%" if fund.estimated_change_pct else "  估算涨跌幅: N/A",
        f"  估算时间: {fund.estimate_time or 'N/A'}",
        "",
        "说明:",
        "- 场内 ETF 是交易所实时价格，可作为市场情绪参考",
        "- 场外基金以最终净值成交，估算净值仅供参考",
        "- 15:00 前申购/赎回通常按当日最终净值结算",
    ]
    return "\n".join(lines)
