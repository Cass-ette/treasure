"""Real-time ETF and OTC fund quote provider for treasure.

Mirrors etf-cli quote capabilities without CLI dependencies.
"""
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional
import logging
import requests
import json

EASTMONEY_QUOTE_URL = "https://push2.eastmoney.com/api/qt/stock/get"
EASTMONEY_KLINE_URL = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
TIANTIAN_FUND_URL = "https://fundgz.1234567.com.cn/js"

logger = logging.getLogger(__name__)


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


@dataclass
class ETFDailyBar:
    """场内 ETF 日 K 线（前复权）."""
    date: str          # 'YYYY-MM-DD'
    open: float
    high: float
    low: float
    close: float
    volume: int        # 成交量（股）
    amount: float      # 成交额（元）


def _normalize_symbol(symbol: str) -> tuple[str, str, str]:
    """Normalize ETF symbol to (secid, market, tencent_code)."""
    symbol = symbol.strip().upper()
    if symbol.startswith(("SH", "SZ")):
        symbol = symbol[2:]
    if symbol.startswith(("51", "56", "58", "60", "68", "69")):
        return f"1.{symbol}", "SH", f"sh{symbol.lower()}"
    return f"0.{symbol}", "SZ", f"sz{symbol.lower()}"


def _prefixed_symbol(symbol: str) -> str:
    """传入 '562500' 或 'SH562500'，返回 'SH562500'。"""
    _, market, _ = _normalize_symbol(symbol)
    bare = symbol.strip().upper()
    if bare.startswith(("SH", "SZ")):
        bare = bare[2:]
    return f"{market}{bare}"


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


def _fetch_klines_from_remote(secid: str, beg: str, end: str, limit: int) -> Optional[tuple]:
    """调用东方财富日 K 接口。

    Returns: (klines_list, name) 或 None。
    """
    params = {
        "secid": secid,
        "klt": "101",     # 日 K
        "fqt": "1",       # 前复权
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
        "beg": beg,
        "end": end,
        "lmt": str(limit),
    }
    try:
        resp = requests.get(EASTMONEY_KLINE_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json().get("data")
        if not data:
            return None
        name = data.get("name") or None
        return (data.get("klines") or [], name)
    except Exception as e:
        logger.warning("fetch_etf_daily_kline remote failed: %s", e)
        return None


# 模块级 name 缓存（symbol -> name），避免实时行情接口失败时丢失名称
_etf_name_cache: dict[str, str] = {}


def get_cached_etf_name(symbol: str) -> Optional[str]:
    """返回已缓存的 ETF 名称。

    优先内存缓存；其次查 DB 里 K 线表 name 列；都没有返回 None。
    """
    prefixed = _prefixed_symbol(symbol)
    if prefixed in _etf_name_cache:
        return _etf_name_cache[prefixed]
    try:
        from app.models.etf_kline_cache import EtfKlineCache
        db_name = EtfKlineCache.get_latest_name(prefixed)
        if db_name:
            _etf_name_cache[prefixed] = db_name
            return db_name
    except Exception:
        pass
    return None


def _parse_kline_line(line: str) -> Optional[tuple]:
    """解析单行 kline 字符串。

    格式：date,open,close,high,low,volume,amount,amplitude,pct_chg,change,turnover
    返回 (date_str, open, close, high, low, volume, amount) 或 None。
    """
    parts = line.split(",")
    if len(parts) < 7:
        return None
    try:
        return (
            parts[0],                          # date
            float(parts[1]),                   # open
            float(parts[2]),                   # close
            float(parts[3]),                   # high
            float(parts[4]),                   # low
            int(float(parts[5])),              # volume
            float(parts[6]),                   # amount
        )
    except (ValueError, IndexError):
        return None


def fetch_etf_daily_kline(symbol: str, days: int = 250) -> list[ETFDailyBar]:
    """拉取场内 ETF 历史 K 线（日 K，前复权），带 DB 缓存。

    流程：
    1. 查 DB 该 symbol 最新日期
    2. 若最新日期 == 今天/最近交易日 → 直接返回 DB 中最近 days 条
    3. 否则调远端拉增量，写 DB
    4. 远端失败 → 回退用 DB 中已有数据

    Returns: ETFDailyBar 列表，按日期升序。空数据返回 []。
    """
    from app.models.etf_kline_cache import EtfKlineCache

    secid, _, _ = _normalize_symbol(symbol)
    prefixed = _prefixed_symbol(symbol)
    today = date.today()

    latest_cached = EtfKlineCache.get_latest_date(prefixed)

    # 缓存命中且为今天：直接返回 DB
    if latest_cached is not None and latest_cached >= today:
        rows = EtfKlineCache.get_recent(prefixed, days)
        return [
            ETFDailyBar(
                date=r.date.strftime('%Y-%m-%d'),
                open=r.open, high=r.high, low=r.low, close=r.close,
                volume=r.volume or 0, amount=r.amount or 0.0,
            )
            for r in rows
        ]

    # 需要拉增量
    beg = (latest_cached + timedelta(days=1)).strftime("%Y%m%d") if latest_cached else "19900101"
    end = today.strftime("%Y%m%d")
    # 拉取数量：始终拉 days 条上限，保证 DB 里至少有这么多
    limit = max(days, 30)

    remote_result = _fetch_klines_from_remote(secid, beg, end, limit)
    klines = remote_result[0] if remote_result else None
    remote_name = remote_result[1] if remote_result else None
    if remote_name:
        _etf_name_cache[prefixed] = remote_name

    if klines is None:
        # 东财失败 → fallback akshare 新浪源
        try:
            ak_bars = fetch_etf_daily_kline_akshare(symbol, days=days)
            if ak_bars:
                from app.extensions import db
                new_rows = []
                for b in ak_bars:
                    d = datetime.strptime(b.date, "%Y-%m-%d").date()
                    exists = EtfKlineCache.query.filter_by(symbol=prefixed, date=d).first()
                    if exists:
                        continue
                    new_rows.append(EtfKlineCache(
                        symbol=prefixed, date=d,
                        open=b.open, high=b.high, low=b.low, close=b.close,
                        volume=b.volume, amount=b.amount,
                    ))
                if new_rows:
                    db.session.bulk_save_objects(new_rows)
                    db.session.commit()
                logger.info("kline fallback to akshare sina: %s (%d bars)", prefixed, len(ak_bars))
        except Exception as e:
            logger.warning("akshare fallback failed for %s: %s", prefixed, e)

    if klines is not None:
        # 写入 DB
        new_rows = []
        for line in klines:
            parsed = _parse_kline_line(line)
            if not parsed:
                continue
            d_str, o, c, hi, lo, vol, amt = parsed
            try:
                d = datetime.strptime(d_str, "%Y-%m-%d").date()
            except ValueError:
                continue
            exists = EtfKlineCache.query.filter_by(symbol=prefixed, date=d).first()
            if exists:
                continue
            new_rows.append(EtfKlineCache(
                symbol=prefixed, date=d,
                open=o, high=hi, low=lo, close=c,
                volume=vol, amount=amt,
                name=remote_name,
            ))
        if new_rows:
            from app.extensions import db
            db.session.bulk_save_objects(new_rows)
            db.session.commit()
    elif EtfKlineCache.get_latest_date(prefixed) is None:
        # 东财 + akshare 都失败，且 DB 无数据
        return []

    # 返回 DB 中最近 days 条
    rows = EtfKlineCache.get_recent(prefixed, days)
    return [
        ETFDailyBar(
            date=r.date.strftime('%Y-%m-%d'),
            open=r.open, high=r.high, low=r.low, close=r.close,
            volume=r.volume or 0, amount=r.amount or 0.0,
        )
        for r in rows
    ]


def fetch_etf_daily_kline_akshare(symbol: str, days: int = 250) -> list[ETFDailyBar]:
    """用 akshare 新浪源拉取场内 ETF 历史 K 线（前复权）。

    作为东方财富源的备用数据源。失败抛异常（由调用方处理）。

    Returns: ETFDailyBar 列表，按日期升序。
    """
    import akshare as ak

    prefixed = _prefixed_symbol(symbol)
    # 新浪格式：sh562500 / sz159915
    sina_symbol = prefixed.lower()
    df = ak.fund_etf_hist_sina(symbol=sina_symbol)
    if df is None or df.empty:
        raise RuntimeError(f"akshare 新浪源无数据: {sina_symbol}")

    bars = []
    for _, row in df.iterrows():
        bars.append(ETFDailyBar(
            date=str(row['date']),
            open=float(row['open']),
            high=float(row['high']),
            low=float(row['low']),
            close=float(row['close']),
            volume=int(row['volume']) if row['volume'] else 0,
            amount=float(row['amount']) if row['amount'] else 0.0,
        ))
    bars.sort(key=lambda b: b.date)
    return bars[-days:]


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
