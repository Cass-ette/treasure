# 场内 ETF 筹码峰判断 - 设计文档

**日期**：2026-08-11
**状态**：已批准，待实现
**作者**：Cass-ette

## 背景

treasure 当前对场内 ETF 的支持有限：

- `app/templates/reports/fund_chart.html` 的"K线图"实际是净值折线图，无蜡烛、无成交量
- `app/services/quote_provider.py` 只做实时快照行情，没有历史 OHLCV
- 没有任何筹码/成交量分布相关代码

用户希望针对场内 ETF 提供**筹码峰可视化页面**，用于判断支撑/压力位。

## 目标

可视化页面，用户手动查看。布局：K 线主图 + 右侧筹码分布直方图（同花顺/通达信风格）。

## 非目标

- 不接入 AI 助手（设计阶段已确认，留口子供未来扩展）
- 不做信号标签 / 自动告警
- 不支持分钟级数据

## 关键决策

| 维度 | 选择 | 理由 |
|---|---|---|
| 数据源 | 东方财富 `push2his.eastmoney.com/api/qt/stock/kline/get` | 与现有 quote_provider 同源，免费免 key |
| 复权方式 | 前复权 (`fqt=1`) | 避免分红除权造成假密集区 |
| 算法 | 指数衰减（`decay=0.97`） | 近期权重大，约 60 日半衰期 |
| 容器分布 | 每日成交量在 `[low, high]` 均匀分配 | 行业主流，简单；三角分布略贴近但慢 3 倍 |
| 缓存 | SQLite 持久化（新增表 `etf_kline_cache`） | 部署友好，跨 worker 共享，重启不丢，增量更新 |
| 图表库 | ECharts 5 (CDN) | 原生 candlestick + 双 grid 同步 Y 轴 |
| Blueprint | 新建 `charts.py` | 与 funds/positions 解耦，未来分析类页面归属 |
| 入口点 | user_detail ETF 持仓按钮 + dashboard 输入框 | 既能从持仓进，也能查任意代码 |

## 架构

```
app/services/
  quote_provider.py        [扩展] fetch_etf_daily_kline() + DB 缓存增量更新
  chip_distribution.py     [新增] 纯算法层
app/models/
  etf_kline_cache.py       [新增] DB 模型
app/routes/
  charts.py                [新增 Blueprint]
    GET  /charts/etf/<symbol>/chip            HTML 页面
    GET  /charts/api/etf/<symbol>/chip-data   JSON API
app/templates/charts/
  etf_chip.html            [新增] ECharts 双 grid 页面
tests/
  test_chip_distribution.py  [新增]
```

## 数据模型

```python
class EtfKlineCache(db.Model):
    __tablename__ = 'etf_kline_cache'
    id       = db.Column(db.Integer, primary_key=True)
    symbol   = db.Column(db.String(10), nullable=False, index=True)  # 'SH562500'
    date     = db.Column(db.Date, nullable=False, index=True)
    open     = db.Column(db.Float)
    high     = db.Column(db.Float)
    low      = db.Column(db.Float)
    close    = db.Column(db.Float)
    volume   = db.Column(db.BigInteger)
    amount   = db.Column(db.Float)
    __table_args__ = (db.UniqueConstraint('symbol', 'date'),)
```

## 数据层

```python
@dataclass
class ETFDailyBar:
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    amount: float

def fetch_etf_daily_kline(symbol: str, days: int = 250) -> list[ETFDailyBar]:
    """从东方财富拉日 K，前复权。DB 缓存增量更新。

    流程：
    1. 查 DB 该 symbol 最新日期
    2. 若最新日期 == 今天/最近交易日 → 直接返回 DB 中 days 条
    3. 否则 → 调远端拉「最新日期+1」到今天的增量
    4. 写入 DB，返回 days 条
    5. 远端失败 → 回退用 DB 中已有数据，日志告警
    """
```

## 算法层

```python
@dataclass
class ChipPeak:
    price: float
    weight: float
    intensity: float  # 相对最大权重比例 (0-1)

def compute_chip_distribution(
    bars: list[ETFDailyBar],
    decay: float = 0.97,
    bin_count: int = 80,
    price_padding: float = 0.02,
) -> list[tuple[float, float, float]]:
    """返回 [(bin_lower, bin_upper, weight), ...] 价格升序。

    算法：
    1. 价格范围 [min(low), max(high)] * (1+padding)
    2. 划分 bin_count 个等宽桶
    3. 倒序遍历 bars（今天 N=0），weight = volume * decay^N
    4. 每日 weight 在 [low, high] 区间内的桶里按交集宽度均匀分配
    5. high==low（一字板）→ 全部 weight 落入 close 桶
    6. volume==0（停牌）→ 跳过
    """

def find_peaks(
    distribution, top_k=3, smoothing_window=3
) -> list[ChipPeak]:
    """3 桶滑动平均去噪后找局部最大值，按权重排序取 top_k。"""

def compute_concentration(
    distribution, current_price, band_pct=0.05
) -> float:
    """当前价 ±5% 区间内筹码占比 (0-1)。"""

def compute_profit_ratio(
    distribution, current_price
) -> float:
    """获利盘比例：当前价以下的筹码占比 (0-1)。"""
```

## 路由

```python
charts_bp = Blueprint('charts', __name__, url_prefix='/charts')

@charts_bp.route('/etf/<symbol>/chip')
def etf_chip_page(symbol): ...

@charts_bp.route('/api/etf/<symbol>/chip-data')
def etf_chip_data(symbol): ...
    # query: days=250, decay=0.97, bins=80, band=0.05
    # return: {symbol, name, current_price, klines, distribution, peaks, metrics}
```

## 错误处理

| 场景 | 行为 |
|---|---|
| symbol 非法（非 6 位 / 非 ETF 代码段） | 404 |
| 远端 API 5xx / 超时 | 503 + 友好提示 |
| 远端返回空 K 线 | 404 |
| DB 命中且 < 最新交易日 | 用 DB + 顶部黄色 banner |
| 一字板（high==low） | 全部 weight 落入 close 桶 |
| 停牌日（volume=0） | 该日不参与累加 |
| 极差 < 0.5（货币基金等） | 强制 bins=40 |

## 测试策略

`tests/test_chip_distribution.py`：

**纯算法**（不打网络）：
- `test_compute_distribution_basic`
- `test_compute_distribution_uniform_day` (一字板)
- `test_decay_weights_recent_more`
- `test_bin_count_partition`
- `test_find_peaks_returns_top_k`
- `test_find_peaks_smoothing`
- `test_concentration_band`
- `test_profit_ratio`

**数据层**（mock requests）：
- `test_fetch_etf_daily_kline_parses_response`
- `test_fetch_etf_daily_kline_handles_empty`
- `test_kline_cache_incremental`

**路由**：
- `test_chip_page_html`
- `test_chip_data_json`
- `test_chip_page_invalid_symbol`
- `test_chip_data_remote_failure`

## 未来扩展（不在本次范围）

- 接入 AI 助手：`_build_quote_context_for_positions` 增加 chip distribution 上下文
- 多 ETF 筹码对比页
- 分钟级实时筹码（性能与频控评估后再做）
- 三角分布算法切换
