"""场内 ETF 技术分析蓝图：筹码峰等."""
import re
from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import login_required

from app.services import quote_provider, chip_distribution

bp = Blueprint('charts', __name__, url_prefix='/charts')

_SYMBOL_RE = re.compile(r'^[A-Za-z]{0,2}\d{6}$')


def _validate_symbol(symbol: str):
    """返回规范化 prefixed symbol（如 'SH562500'），非法返回 None。"""
    s = symbol.strip().upper()
    if not _SYMBOL_RE.match(s):
        return None
    try:
        return quote_provider._prefixed_symbol(s)
    except Exception:
        return None


@bp.route('/etf/<symbol>/chip')
@login_required
def etf_chip_page(symbol: str):
    """筹码峰 HTML 页面."""
    prefixed = _validate_symbol(symbol)
    if not prefixed:
        abort(404)
    quote = quote_provider.fetch_etf_quote(symbol)
    cached_name = quote_provider.get_cached_etf_name(symbol)
    name = None
    if quote and quote.name and quote.name != 'Unknown':
        name = quote.name
    elif cached_name:
        name = cached_name
    return render_template(
        'charts/etf_chip.html',
        symbol=prefixed,
        raw_symbol=symbol,
        quote=quote,
        etf_name=name,
    )


@bp.route('/api/etf/<symbol>/chip-data')
@login_required
def etf_chip_data(symbol: str):
    """筹码峰 JSON 数据."""
    prefixed = _validate_symbol(symbol)
    if not prefixed:
        abort(404)

    days = request.args.get('days', 250, type=int)
    decay = request.args.get('decay', 0.97, type=float)
    bins = request.args.get('bins', 80, type=int)
    band = request.args.get('band', 0.05, type=float)

    bars = quote_provider.fetch_etf_daily_kline(symbol, days=days)
    if not bars:
        abort(404)

    quote = quote_provider.fetch_etf_quote(symbol)
    cached_name = quote_provider.get_cached_etf_name(symbol)
    current_price = quote.latest if quote and quote.latest > 0 else bars[-1].close

    dist = chip_distribution.compute_chip_distribution(bars, decay=decay, bin_count=bins)
    peaks = chip_distribution.find_peaks(dist, top_k=3)
    concentration = chip_distribution.compute_concentration(dist, current_price, band_pct=band)
    profit_ratio = chip_distribution.compute_profit_ratio(dist, current_price)

    if quote and quote.name and quote.name != 'Unknown':
        name = quote.name
    elif cached_name:
        name = cached_name
    else:
        name = prefixed

    return jsonify({
        'symbol': prefixed,
        'name': name,
        'current_price': current_price,
        'change_pct': quote.change_pct if quote else 0.0,
        'klines': [
            {'date': b.date, 'open': b.open, 'high': b.high, 'low': b.low,
             'close': b.close, 'volume': b.volume, 'amount': b.amount}
            for b in bars
        ],
        'distribution': [
            {'price_low': lo, 'price_high': hi, 'weight': w}
            for lo, hi, w in dist
        ],
        'peaks': [
            {'price': p.price, 'weight': p.weight, 'intensity': p.intensity}
            for p in peaks
        ],
        'metrics': {
            'concentration': concentration,
            'profit_ratio': profit_ratio,
            'main_peak': peaks[0].price if peaks else None,
            'secondary_peak': peaks[1].price if len(peaks) > 1 else None,
        },
    })
