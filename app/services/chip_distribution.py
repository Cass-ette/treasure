"""Cost-distribution estimates from daily prices, volume and turnover.

These models describe assumptions about cost migration, not observed holdings.
The legacy fixed-decay calculation remains available for comparison.
"""
from dataclasses import dataclass
import math
from typing import Optional

from app.services.quote_provider import ETFDailyBar


@dataclass
class ChipPeak:
    """筹码峰."""
    price: float          # 峰位中心价
    weight: float         # 该桶权重
    intensity: float      # 相对最大权重的比例 (0-1)


@dataclass
class ChipEstimate:
    distribution: list[tuple[float, float, float]]
    metadata: dict


def _valid_bar(bar: ETFDailyBar) -> bool:
    return (
        bar.volume is not None and math.isfinite(bar.volume) and bar.volume > 0
        and all(v is not None and math.isfinite(v) for v in (bar.open, bar.low, bar.high, bar.close))
        and 0 < bar.low <= bar.high
        and bar.low <= bar.open <= bar.high and bar.low <= bar.close <= bar.high
    )


def _has_turnover(bar: ETFDailyBar) -> bool:
    rate = bar.turnover_rate
    return rate is not None and math.isfinite(rate) and rate >= 0


def _daily_mass(bar: ETFDailyBar, edges: list[float], shape: str) -> list[float]:
    """Integrate the daily PDF over bins, including one-price/edge-mode cases.

    OHLC4 is a price proxy for the triangle mode, not a measured volume VWAP.
    """
    low, high = bar.low, bar.high
    if high == low:
        mass = [0.0] * (len(edges) - 1)
        width = edges[1] - edges[0]
        index = max(0, min(len(mass) - 1, int((bar.close - edges[0]) / width)))
        mass[index] = 1.0
        return mass
    mode = (bar.open + bar.high + bar.low + bar.close) / 4

    def cdf(price):
        if price <= low:
            return 0.0
        if price >= high:
            return 1.0
        if shape == 'uniform':
            return (price - low) / (high - low)
        if price <= mode:
            return (price - low) ** 2 / ((high - low) * (mode - low))
        return 1 - (high - price) ** 2 / ((high - low) * (high - mode))

    return [max(0.0, cdf(right) - cdf(left)) for left, right in zip(edges, edges[1:])]


def estimate_chip_distribution(
    bars: list[ETFDailyBar], method: str = 'auto', shape: str = 'triangular',
    decay: float = 0.97, bin_count: int = 80, price_padding: float = 0.02,
) -> ChipEstimate:
    """Prefer turnover migration when every active day has usable turnover.

    Seed the earliest active day with its daily PDF. Subsequently use
    D[t] = (1-r[t])*D[t-1] + r[t]*daily_pdf[t], r=min(turnover_pct/100, 1).
    Missing turnover anywhere in the active window falls back to the legacy
    model for the whole window, rather than inventing rates or mixing models.
    Zero-volume days do not migrate holdings. Initial mass remaining reports
    sensitivity to the unknown holdings predating the window.
    """
    if method not in ('auto', 'turnover', 'legacy') or shape not in ('triangular', 'uniform'):
        raise ValueError('Unknown chip model or daily shape')
    if not 0 < decay <= 1 or bin_count < 1 or not math.isfinite(price_padding) or price_padding < 0:
        raise ValueError('Invalid chip model parameters')
    active = sorted((bar for bar in bars if _valid_bar(bar)), key=lambda b: b.date)
    covered = sum(_has_turnover(bar) for bar in active)
    use_turnover = bool(active) and covered == len(active) and method != 'legacy'
    metadata = {
        'requested': method, 'method': 'turnover' if use_turnover else 'legacy',
        'daily_shape': shape if use_turnover else 'uniform',
        'fallback_reason': 'missing_turnover' if active and covered < len(active) and method != 'legacy' else None,
        'active_days': len(active), 'turnover_days': covered,
        'turnover_coverage': covered / len(active) if active else 0.0,
        'skipped_days': len(bars) - len(active),
        'capped_turnover_days': sum(_has_turnover(b) and b.turnover_rate > 100 for b in active) if use_turnover else 0,
        'initial_mass_remaining': None,
        'start_date': active[0].date if active else None,
        'end_date': active[-1].date if active else None,
        'weight_unit': 'probability' if use_turnover else 'decayed_volume',
        'decay': None if use_turnover else decay,
    }
    if not active:
        return ChipEstimate([], metadata)
    if not use_turnover:
        dist = compute_chip_distribution(active, decay=decay, bin_count=bin_count, price_padding=price_padding)
        return ChipEstimate(dist, metadata)

    low = min(b.low for b in active)
    high = max(b.high for b in active)
    spread = high - low
    if spread < 0.5:
        bin_count = min(bin_count, 40)
    pad = spread * price_padding if spread else max(high * price_padding, 0.01)
    width = (spread + 2 * pad) / bin_count
    edges = [low - pad + i * width for i in range(bin_count + 1)]
    weights = _daily_mass(active[0], edges, shape)
    initial_remaining = 1.0
    for bar in active[1:]:
        rate = min(bar.turnover_rate / 100, 1.0)
        if rate == 0:
            continue
        daily = _daily_mass(bar, edges, shape)
        weights = [(1 - rate) * old + rate * new for old, new in zip(weights, daily)]
        initial_remaining *= 1 - rate
    total = sum(weights)
    metadata['initial_mass_remaining'] = initial_remaining
    return ChipEstimate([
        (edges[i], edges[i + 1], w / total) for i, w in enumerate(weights)
    ], metadata)


def compute_chip_distribution(
    bars: list[ETFDailyBar],
    decay: float = 0.97,
    bin_count: int = 80,
    price_padding: float = 0.02,
) -> list[tuple[float, float, float]]:
    """计算筹码分布。

    每日成交量在 [low, high] 区间内均匀分配到桶里，
    按 decay^N 衰减（N = 距今天数）。

    Returns: [(bin_lower, bin_upper, weight), ...] 按价格升序。
    """
    if not bars:
        return []

    # 极差过小（如货币基金）自适应桶数
    lows = [b.low for b in bars if b.volume and b.volume > 0]
    highs = [b.high for b in bars if b.volume and b.volume > 0]
    if not lows or not highs:
        return []
    price_min = min(lows)
    price_max = max(highs)
    spread = price_max - price_min
    if spread < 0.5 and bin_count > 40:
        bin_count = 40

    # 价格范围外扩 padding
    pad = spread * price_padding if spread > 0 else max(price_max * price_padding, 0.01)
    lo_bound = price_min - pad
    hi_bound = price_max + pad
    bin_width = (hi_bound - lo_bound) / bin_count

    weights = [0.0] * bin_count

    # 按时间倒序：今天 N=0
    sorted_bars = sorted(bars, key=lambda b: b.date, reverse=True)
    for n, bar in enumerate(sorted_bars):
        if not bar.volume or bar.volume <= 0:
            continue
        daily_weight = bar.volume * (decay ** n)

        bar_lo = bar.low
        bar_hi = bar.high
        if bar_hi <= bar_lo:
            # 一字板：全部 weight 落入 close 对应的桶
            close = bar.close if bar.close else bar_lo
            idx = int((close - lo_bound) / bin_width)
            idx = max(0, min(bin_count - 1, idx))
            weights[idx] += daily_weight
            continue

        # 均匀分配：遍历所有与 [bar_lo, bar_hi] 有交集的桶
        first_idx = max(0, int((bar_lo - lo_bound) / bin_width))
        last_idx = min(bin_count - 1, int((bar_hi - lo_bound) / bin_width))

        for i in range(first_idx, last_idx + 1):
            bin_lo = lo_bound + i * bin_width
            bin_hi = bin_lo + bin_width
            # 交集
            inter_lo = max(bar_lo, bin_lo)
            inter_hi = min(bar_hi, bar_hi)
            inter_hi = min(inter_hi, bin_hi)
            if inter_hi <= inter_lo:
                continue
            ratio = (inter_hi - inter_lo) / (bar_hi - bar_lo)
            weights[i] += daily_weight * ratio

    return [
        (lo_bound + i * bin_width, lo_bound + (i + 1) * bin_width, weights[i])
        for i in range(bin_count)
    ]


def _smooth(values: list[float], window: int = 3) -> list[float]:
    """3 桶滑动平均。"""
    if window <= 1 or len(values) < window:
        return list(values)
    half = window // 2
    out = []
    n = len(values)
    for i in range(n):
        lo = max(0, i - half)
        hi = min(n, i + half + 1)
        out.append(sum(values[lo:hi]) / (hi - lo))
    return out


def find_peaks(
    distribution: list[tuple[float, float, float]],
    top_k: int = 3,
    smoothing_window: int = 3,
) -> list[ChipPeak]:
    """从分布中找 top_k 个局部最大值（峰位）。"""
    if not distribution:
        return []

    weights = [w for _, _, w in distribution]
    smoothed = _smooth(weights, smoothing_window)

    max_w = max(smoothed) if smoothed else 0.0
    if max_w <= 0:
        return []

    # 找局部最大值
    candidates = []
    n = len(smoothed)
    for i in range(n):
        left = smoothed[i - 1] if i > 0 else -1
        right = smoothed[i + 1] if i < n - 1 else -1
        if smoothed[i] >= left and smoothed[i] >= right and smoothed[i] > 0:
            # 峰位价格取桶中心
            bin_lo, bin_hi, _ = distribution[i]
            price = (bin_lo + bin_hi) / 2
            candidates.append((smoothed[i], price, i))

    # 按权重降序，去相邻（距离 < 3 桶的视为同一峰）
    candidates.sort(reverse=True)
    picked_indices: set[int] = set()
    peaks: list[ChipPeak] = []
    for w, price, idx in candidates:
        if any(abs(idx - p_idx) < 3 for p_idx in picked_indices):
            continue
        picked_indices.add(idx)
        peaks.append(ChipPeak(
            price=price,
            weight=w,
            intensity=w / max_w,
        ))
        if len(peaks) >= top_k:
            break

    return peaks


def compute_concentration(
    distribution: list[tuple[float, float, float]],
    current_price: float,
    band_pct: float = 0.05,
) -> float:
    """当前价 ±band_pct 区间内筹码占比 (0-1)。"""
    if not distribution:
        return 0.0
    total = sum(w for _, _, w in distribution)
    if total <= 0:
        return 0.0
    band_lo = current_price * (1 - band_pct)
    band_hi = current_price * (1 + band_pct)
    in_band = 0.0
    for bin_lo, bin_hi, w in distribution:
        if bin_hi <= band_lo or bin_lo >= band_hi:
            continue
        # 部分重叠时按比例算
        overlap = min(bin_hi, band_hi) - max(bin_lo, band_lo)
        bin_size = bin_hi - bin_lo
        if bin_size > 0 and overlap > 0:
            in_band += w * (overlap / bin_size)
        elif overlap > 0:
            in_band += w
    return min(1.0, in_band / total)


def compute_profit_ratio(
    distribution: list[tuple[float, float, float]],
    current_price: float,
) -> float:
    """获利盘比例：当前价以下的筹码占比 (0-1)。

    跨越当前价的桶按比例分摊。
    """
    if not distribution:
        return 0.0
    total = sum(w for _, _, w in distribution)
    if total <= 0:
        return 0.0
    below = 0.0
    for bin_lo, bin_hi, w in distribution:
        if bin_hi <= current_price:
            below += w
        elif bin_lo < current_price < bin_hi:
            # 部分获利
            ratio = (current_price - bin_lo) / (bin_hi - bin_lo)
            below += w * ratio
    return min(1.0, below / total)


def compute_avg_cost(
    distribution: list[tuple[float, float, float]],
) -> Optional[float]:
    """筹码加权平均成本 = Σ(桶中心价 × 权重) / Σ(权重)。

    无有效权重返回 None。
    """
    if not distribution:
        return None
    total_w = 0.0
    weighted_sum = 0.0
    for bin_lo, bin_hi, w in distribution:
        center = (bin_lo + bin_hi) / 2
        weighted_sum += center * w
        total_w += w
    if total_w <= 0:
        return None
    return weighted_sum / total_w
