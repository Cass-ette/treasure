"""Stock screening page and API."""
import math

from flask import Blueprint, jsonify, render_template, request
from flask_babel import gettext as _
from flask_login import login_required

from app.services import stock_screener

bp = Blueprint("stocks", __name__, url_prefix="/stocks")


def _number_arg(name: str, *, minimum: float | None = None) -> float | None:
    raw = request.args.get(name, "").strip()
    if raw == "":
        return None
    value = float(raw)
    if not math.isfinite(value) or (minimum is not None and value < minimum):
        raise ValueError(name)
    return value


@bp.route("/screener")
@login_required
def screener_page():
    return render_template("stocks/screener.html")


@bp.route("/api/screener")
@login_required
def screener_data():
    try:
        market = request.args.get("market", "all")
        sort = request.args.get("sort", "change_pct")
        order = request.args.get("order", "desc")
        limit = int(request.args.get("limit", "100"))
        offset = int(request.args.get("offset", "0"))
        if not 1 <= limit <= 200 or not 0 <= offset <= 5000:
            raise ValueError("page")
        if market not in stock_screener.MARKET_FS:
            raise ValueError("market")
        if sort not in stock_screener.SORT_FIELDS or order not in ("asc", "desc"):
            raise ValueError("sort")
        min_amount = _number_arg("min_amount", minimum=0)
        max_amount = _number_arg("max_amount", minimum=0)
        min_market_cap = _number_arg("min_market_cap", minimum=0)
        max_market_cap = _number_arg("max_market_cap", minimum=0)
        filters = {
            "keyword": request.args.get("keyword", ""),
            "market": market,
            "exclude_special": request.args.get("exclude_special", "1") not in ("0", "false"),
            "min_price": _number_arg("min_price", minimum=0),
            "max_price": _number_arg("max_price", minimum=0),
            "min_change": _number_arg("min_change"),
            "max_change": _number_arg("max_change"),
            "min_turnover": _number_arg("min_turnover", minimum=0),
            "max_turnover": _number_arg("max_turnover", minimum=0),
            "min_amount": min_amount * 10000 if min_amount is not None else None,
            "max_amount": max_amount * 10000 if max_amount is not None else None,
            "min_pe": _number_arg("min_pe"),
            "max_pe": _number_arg("max_pe"),
            "min_pb": _number_arg("min_pb"),
            "max_pb": _number_arg("max_pb"),
            "min_market_cap": min_market_cap * 100000000 if min_market_cap is not None else None,
            "max_market_cap": max_market_cap * 100000000 if max_market_cap is not None else None,
            "sort": sort,
            "order": order,
        }
        snapshot = stock_screener.fetch_stock_snapshot(market)
        rows = stock_screener.screen_stocks(snapshot, **filters)
    except (TypeError, ValueError):
        return jsonify({"error": _("筛选参数无效")}), 400
    except stock_screener.StockDataError as exc:
        return jsonify({"error": _(str(exc))}), 503
    page = rows[offset:offset + limit]
    return jsonify({
        "source": "eastmoney",
        "stale": snapshot.stale,
        "fetched_at": snapshot.fetched_at.isoformat(),
        "universe_count": len(snapshot.rows),
        "match_count": len(rows),
        "offset": offset,
        "limit": limit,
        "rows": page,
    })
