"""Chip distribution algorithm tests: TDD for 场内 ETF 筹码峰分析."""
import pytest
from datetime import date, timedelta

from app.services.quote_provider import ETFDailyBar


def _make_bar(d_offset: int, high: float, low: float, close: float = None,
              volume: int = 1000, open_: float = None) -> ETFDailyBar:
    """生成测试用 K 线。d_offset=0 表示今天。"""
    today = date.today()
    d = today - timedelta(days=d_offset)
    return ETFDailyBar(
        date=d.strftime('%Y-%m-%d'),
        open=open_ if open_ is not None else low,
        high=high,
        low=low,
        close=close if close is not None else (high + low) / 2,
        volume=volume,
        amount=volume * ((high + low) / 2),
    )


class TestComputeChipDistribution:
    """compute_chip_distribution: 历史成交量 → 价位桶分布."""

    def test_returns_empty_for_empty_bars(self):
        from app.services.chip_distribution import compute_chip_distribution
        result = compute_chip_distribution([])
        assert result == []

    def test_basic_distribution_returns_bins_in_price_order(self):
        """单日数据：所有 weight 落入 [low, high] 区间内的桶。"""
        from app.services.chip_distribution import compute_chip_distribution
        bar = _make_bar(d_offset=0, high=1.10, low=1.00, volume=1000)
        dist = compute_chip_distribution([bar], bin_count=10)
        # 返回非空
        assert len(dist) == 10
        # 每个 bin 是 (low, high, weight) 三元组
        for entry in dist:
            assert len(entry) == 3
        # 桶按价格升序
        prices = [entry[0] for entry in dist]
        assert prices == sorted(prices)

    def test_total_weight_equals_total_volume_with_no_decay_limit(self):
        """decay=1.0 时（不衰减），所有桶的 weight 之和应等于总成交量。"""
        from app.services.chip_distribution import compute_chip_distribution
        bars = [
            _make_bar(0, high=1.10, low=1.00, volume=1000),
            _make_bar(1, high=1.05, low=0.95, volume=500),
        ]
        dist = compute_chip_distribution(bars, decay=1.0, bin_count=20)
        total = sum(w for _, _, w in dist)
        # 容差 1% 处理浮点（桶边缘可能略丢）
        assert abs(total - 1500) < 30

    def test_uniform_day_high_equal_low_all_weight_in_one_bin(self):
        """一字板（high == low）：当日 weight 全部落入 close 对应的桶。"""
        from app.services.chip_distribution import compute_chip_distribution
        bar = _make_bar(0, high=1.05, low=1.05, close=1.05, volume=1000)
        dist = compute_chip_distribution([bar], bin_count=10)
        nonzero = [(lo, hi, w) for lo, hi, w in dist if w > 0]
        assert len(nonzero) == 1
        lo, hi, w = nonzero[0]
        assert lo <= 1.05 <= hi
        assert abs(w - 1000) < 50

    def test_decay_makes_recent_days_weight_more(self):
        """近期成交量权重大于远期（按 K 线列表下标衰减，decay < 1）。"""
        from app.services.chip_distribution import compute_chip_distribution
        # 构造连续 2 个交易日，价位完全不重叠
        recent = _make_bar(0, high=2.00, low=1.90, volume=1000)
        old = _make_bar(1, high=1.10, low=1.00, volume=1000)
        dist = compute_chip_distribution([recent, old], decay=0.9, bin_count=40)

        def weight_at(price):
            for lo, hi, w in dist:
                if lo <= price < hi:
                    return w
            return 0

        recent_w = weight_at(1.95)
        old_w = weight_at(1.05)
        # 列表下标 N=0 / N=1，预期 ratio = 1/0.9 ≈ 1.11
        assert recent_w > old_w
        ratio = recent_w / old_w if old_w > 0 else float('inf')
        assert 1.05 < ratio < 1.25

    def test_decay_accumulates_over_more_days(self):
        """多个连续交易日，远期桶的总权重大幅低于近期桶。"""
        from app.services.chip_distribution import compute_chip_distribution
        # 连续 3 天，每天 volume=1000，价位区间一致
        bars = [
            _make_bar(0, high=1.10, low=1.00, volume=1000),
            _make_bar(1, high=1.10, low=1.00, volume=1000),
            _make_bar(2, high=1.10, low=1.00, volume=1000),
        ]
        dist = compute_chip_distribution(bars, decay=0.9, bin_count=20)
        total = sum(w for _, _, w in dist)
        # 预期总权重 ≈ 1000*(1 + 0.9 + 0.81) = 2710
        assert 2400 < total < 3000

    def test_zero_volume_day_skipped(self):
        """停牌日（volume=0）不参与累加。"""
        from app.services.chip_distribution import compute_chip_distribution
        bars = [
            _make_bar(0, high=1.10, low=1.00, volume=0),  # 停牌
            _make_bar(1, high=1.10, low=1.00, volume=1000),
        ]
        dist = compute_chip_distribution(bars, decay=1.0, bin_count=10)
        total = sum(w for _, _, w in dist)
        # 停牌日 weight 0，总 weight 应等于有效日的 1000
        assert abs(total - 1000) < 30


class TestFindPeaks:
    """find_peaks: 从分布中找 top_k 个局部最大值."""

    def test_finds_single_peak(self):
        from app.services.chip_distribution import find_peaks, compute_chip_distribution
        # 构造一个明显的单峰：成交量集中在 1.00-1.10
        bars = [_make_bar(0, high=1.10, low=1.00, volume=1000)]
        dist = compute_chip_distribution(bars, bin_count=20)
        peaks = find_peaks(dist, top_k=3)
        assert len(peaks) >= 1
        # 主峰价格在 [1.00, 1.10] 范围
        assert 1.00 <= peaks[0].price <= 1.10

    def test_finds_two_distinct_peaks(self):
        from app.services.chip_distribution import find_peaks, compute_chip_distribution
        # 两个价位区间分别成交
        bars = [
            _make_bar(0, high=1.10, low=1.00, volume=1000),    # 近期在高位
            _make_bar(5, high=0.60, low=0.50, volume=1000),    # 远期在低位
        ]
        dist = compute_chip_distribution(bars, decay=1.0, bin_count=40)
        peaks = find_peaks(dist, top_k=2)
        assert len(peaks) <= 2
        # 应该有位于 [0.50, 0.60] 和 [1.00, 1.10] 的峰
        prices = [p.price for p in peaks]
        low_peak = any(0.50 <= p <= 0.60 for p in prices)
        high_peak = any(1.00 <= p <= 1.10 for p in prices)
        assert low_peak and high_peak

    def test_top_k_limits_result_count(self):
        from app.services.chip_distribution import find_peaks, compute_chip_distribution
        bars = [_make_bar(0, high=1.10, low=1.00, volume=1000)]
        dist = compute_chip_distribution(bars, bin_count=20)
        peaks = find_peaks(dist, top_k=1)
        assert len(peaks) <= 1

    def test_intensity_normalized_to_max(self):
        """intensity 是相对最大权重的比例，最大值为 1.0 左右。"""
        from app.services.chip_distribution import find_peaks, compute_chip_distribution
        bars = [_make_bar(0, high=1.10, low=1.00, volume=1000)]
        dist = compute_chip_distribution(bars, bin_count=20)
        peaks = find_peaks(dist, top_k=3)
        if peaks:
            # 最强峰的 intensity 应接近 1.0
            assert peaks[0].intensity >= 0.9
            assert all(0 <= p.intensity <= 1.01 for p in peaks)


class TestConcentration:
    """compute_concentration: 当前价 ±band 区间内筹码占比."""

    def test_concentration_returns_float_between_zero_and_one(self):
        from app.services.chip_distribution import compute_chip_distribution, compute_concentration
        bars = [_make_bar(0, high=1.10, low=1.00, volume=1000)]
        dist = compute_chip_distribution(bars, bin_count=20)
        c = compute_concentration(dist, current_price=1.05, band_pct=0.05)
        assert isinstance(c, float)
        assert 0.0 <= c <= 1.0

    def test_concentration_one_when_all_weight_in_band(self):
        """所有筹码都在 band 范围内时，集中度接近 1.0。"""
        from app.services.chip_distribution import compute_chip_distribution, compute_concentration
        bars = [_make_bar(0, high=1.05, low=1.00, volume=1000)]
        dist = compute_chip_distribution(bars, bin_count=10)
        c = compute_concentration(dist, current_price=1.025, band_pct=0.10)
        assert c > 0.9

    def test_concentration_zero_when_no_weight_in_band(self):
        """所有筹码都在 band 外时，集中度接近 0.0。"""
        from app.services.chip_distribution import compute_chip_distribution, compute_concentration
        bars = [_make_bar(0, high=2.00, low=1.90, volume=1000)]
        dist = compute_chip_distribution(bars, bin_count=10)
        c = compute_concentration(dist, current_price=1.00, band_pct=0.01)
        assert c < 0.1


class TestProfitRatio:
    """compute_profit_ratio: 获利盘 = 当前价以下的筹码占比."""

    def test_returns_float_between_zero_and_one(self):
        from app.services.chip_distribution import compute_chip_distribution, compute_profit_ratio
        bars = [_make_bar(0, high=1.10, low=1.00, volume=1000)]
        dist = compute_chip_distribution(bars, bin_count=20)
        r = compute_profit_ratio(dist, current_price=1.05)
        assert isinstance(r, float)
        assert 0.0 <= r <= 1.0

    def test_profit_ratio_one_when_current_above_all(self):
        """当前价高于所有筹码 → 获利盘 100%。"""
        from app.services.chip_distribution import compute_chip_distribution, compute_profit_ratio
        bars = [_make_bar(0, high=1.10, low=1.00, volume=1000)]
        dist = compute_chip_distribution(bars, bin_count=20)
        r = compute_profit_ratio(dist, current_price=2.00)
        assert r > 0.95

    def test_profit_ratio_zero_when_current_below_all(self):
        """当前价低于所有筹码 → 获利盘 0%。"""
        from app.services.chip_distribution import compute_chip_distribution, compute_profit_ratio
        bars = [_make_bar(0, high=1.10, low=1.00, volume=1000)]
        dist = compute_chip_distribution(bars, bin_count=20)
        r = compute_profit_ratio(dist, current_price=0.50)
        assert r < 0.05

    def test_profit_ratio_half_when_current_in_middle(self):
        """当前价在分布中间 → 获利盘接近 50%。"""
        from app.services.chip_distribution import compute_chip_distribution, compute_profit_ratio
        bars = [_make_bar(0, high=1.10, low=1.00, volume=1000)]
        dist = compute_chip_distribution(bars, bin_count=20)
        r = compute_profit_ratio(dist, current_price=1.05)
        # 应在 30-70% 之间
        assert 0.3 < r < 0.7
