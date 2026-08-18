// etf_chip.js — K线 + 筹码分布双 grid 图表
document.addEventListener('DOMContentLoaded', function () {
    if (!window.CHART_CTX) return;
    initChipChart();
});

let chartInstance = null;
let currentData = null;

function initChipChart() {
    const el = document.getElementById('mainChart');
    if (!el) return;
    chartInstance = echarts.init(el);
    window.addEventListener('resize', () => chartInstance && chartInstance.resize());

    document.getElementById('btn-refresh').addEventListener('click', loadData);
    document.getElementById('param-decay').addEventListener('change', loadData);
    document.getElementById('param-bins').addEventListener('change', loadData);

    loadData();
}

function loadData() {
    const ctx = window.CHART_CTX;
    const decay = document.getElementById('param-decay').value;
    const bins = document.getElementById('param-bins').value;
    const url = ctx.dataUrl + '?decay=' + decay + '&bins=' + bins;

    fetch(url)
        .then(r => {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        })
        .then(data => {
            currentData = data;
            renderChart(data);
            renderMetrics(data);
            renderBinsTable(data);
        })
        .catch(err => {
            if (chartInstance) {
                chartInstance.clear();
                chartInstance.setOption({
                    title: { text: '数据加载失败: ' + err.message, left: 'center', top: 'center', textStyle: { color: '#dc3545' } }
                });
            }
        });
}

function renderChart(data) {
    const klines = data.klines;
    const dist = data.distribution;
    const peaks = data.peaks;

    // candlestick data: [open, close, low, high]
    const candleData = klines.map(k => [k.open, k.close, k.low, k.high]);
    const dates = klines.map(k => k.date);
    const maData = computeMA(klasses(klines, 'close'), 20);

    // 横向平滑曲线: y 轴价格，x 轴权重（先移动平均去毛刺，同花顺风格）
    const smoothedWeights = smoothWeights(dist.map(d => d.weight), 5);
    // 首尾补零权重锚点，让曲线贴合坐标轴而不是悬空
    const distPoints = dist.map((d, i) => [smoothedWeights[i], (d.price_low + d.price_high) / 2]);
    distPoints.unshift([0, distPoints[0][1]]);
    distPoints.push([0, distPoints[distPoints.length - 1][1]]);
    const distData = distPoints.map(pt => ({ value: pt }));

    // 找价格范围（让两个 grid Y 轴一致）
    const allPrices = [];
    klines.forEach(k => { allPrices.push(k.low, k.high); });
    let yMin = Math.min(...allPrices);
    let yMax = Math.max(...allPrices);
    const pad = (yMax - yMin) * 0.05;
    yMin -= pad; yMax += pad;

    // markLine for peaks（K 线图 + 筹码面板共用）
    const peakLines = peaks.slice(0, 3).map((p, i) => ({
        yAxis: p.price,
        label: {
            formatter: (i === 0 ? '主峰 ' : (i === 1 ? '次峰 ' : '峰 ')) + p.price.toFixed(3),
            position: 'insideEndTop'
        },
        lineStyle: {
            color: i === 0 ? '#dc3545' : (i === 1 ? '#fd7e14' : '#6c757d'),
            type: 'dashed',
            width: i === 0 ? 2 : 1
        }
    }));

    // current price line
    peakLines.push({
        yAxis: data.current_price,
        label: { formatter: '现价 ' + data.current_price.toFixed(3), position: 'insideStartTop' },
        lineStyle: { color: '#198754', type: 'solid', width: 2 }
    });

    // 平均成本线（黄虚线）
    if (data.metrics.avg_cost) {
        peakLines.push({
            yAxis: data.metrics.avg_cost,
            label: { formatter: '平均成本 ' + data.metrics.avg_cost.toFixed(3), position: 'insideEndTop' },
            lineStyle: { color: '#ffc107', type: 'dashed', width: 1.5 }
        });
    }

    // 筹码面板的现价线 + 平均成本线（窄标签版，避免遮挡）
    const chipPriceLines = [{
        yAxis: data.current_price,
        label: { formatter: data.current_price.toFixed(3), position: 'insideStartTop', fontSize: 10 },
        lineStyle: { color: '#198754', type: 'solid', width: 2 }
    }];
    if (data.metrics.avg_cost) {
        chipPriceLines.push({
            yAxis: data.metrics.avg_cost,
            label: { formatter: data.metrics.avg_cost.toFixed(3), position: 'insideEndTop', fontSize: 10 },
            lineStyle: { color: '#ffc107', type: 'dashed', width: 1.5 }
        });
    }

    const option = {
        tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
        legend: { data: ['日K', 'MA20', '筹码'], top: 5, right: '30%' },
        axisPointer: { link: [{ yAxisAxisIndex: [0, 1] }] },
        grid: [
            { left: 55, right: '42%', top: 40, bottom: 65 },
            { left: '61%', right: 25, top: 40, bottom: 65 }
        ],
        xAxis: [
            {
                type: 'category', data: dates, scale: true,
                boundaryGap: false, axisLine: { onZero: false }, splitLine: { show: false },
                axisLabel: { rotate: 15, fontSize: 10, interval: 'auto' },
                min: 'dataMin', max: 'dataMax'
            },
            {
                type: 'value', gridIndex: 1, scale: true, min: 0,
                axisLabel: { fontSize: 10, formatter: v => v >= 1000 ? (v / 1000).toFixed(0) + 'k' : v.toFixed(0) },
                splitNumber: 3
            }
        ],
        yAxis: [
            {
                scale: true, min: yMin, max: yMax,
                splitLine: { show: true, lineStyle: { color: '#eee' } }
            },
            {
                scale: true, gridIndex: 1, min: yMin, max: yMax,
                splitLine: { show: false }, axisLabel: { show: false }
            }
        ],
        dataZoom: [
            { type: 'inside', xAxisIndex: 0, start: 60, end: 100 },
            { show: true, type: 'slider', xAxisIndex: 0, start: 60, end: 100, bottom: 10, height: 20 }
        ],
        series: [
            {
                name: '日K', type: 'candlestick', data: candleData,
                itemStyle: {
                    color: '#dc3545', color0: '#198754',
                    borderColor: '#dc3545', borderColor0: '#198754'
                },
                markLine: { symbol: ['none', 'none'], data: peakLines, animation: false, label: { fontSize: 10 } }
            },
            {
                name: 'MA20', type: 'line', data: maData, smooth: true,
                lineStyle: { color: '#fd7e14', width: 1 }, symbol: 'none'
            },
            {
                name: '筹码', type: 'line', xAxisIndex: 1, yAxisIndex: 1,
                data: distData, smooth: true, symbol: 'none',
                lineStyle: { width: 1.5, color: '#0d9488' },
                areaStyle: {
                    color: {
                        type: 'linear', x: 0, y: 0, x2: 1, y2: 0,
                        colorStops: [
                            { offset: 0, color: 'rgba(13, 148, 136, 0.35)' },
                            { offset: 1, color: 'rgba(13, 148, 136, 0.08)' }
                        ]
                    }
                },
                markLine: { symbol: ['none', 'none'], data: chipPriceLines, animation: false }
            }
        ]
    };

    chartInstance.setOption(option, true);
}

function renderMetrics(data) {
    const card = document.getElementById('metricsCard');
    if (!card) return;
    card.style.display = '';
    document.getElementById('m-profit').textContent = (data.metrics.profit_ratio * 100).toFixed(1) + '%';
    document.getElementById('m-conc').textContent = (data.metrics.concentration * 100).toFixed(1) + '%';
    const avgCostEl = document.getElementById('m-avgcost');
    avgCostEl.textContent = data.metrics.avg_cost ? data.metrics.avg_cost.toFixed(3) : '-';
    const avgProfitEl = document.getElementById('m-avgprofit');
    if (data.metrics.avg_profit_pct !== null && data.metrics.avg_profit_pct !== undefined) {
        const ap = data.metrics.avg_profit_pct;
        avgProfitEl.textContent = (ap >= 0 ? '+' : '') + ap.toFixed(2) + '%';
        avgProfitEl.style.color = ap >= 0 ? '#dc3545' : '#198754';
    } else {
        avgProfitEl.textContent = '-';
        avgProfitEl.style.color = '';
    }
    document.getElementById('m-peak1').textContent = data.metrics.main_peak ? data.metrics.main_peak.toFixed(3) : '-';
    document.getElementById('m-peak2').textContent = data.metrics.secondary_peak ? data.metrics.secondary_peak.toFixed(3) : '-';
    document.getElementById('m-price').textContent = data.current_price.toFixed(3);
    const chg = data.change_pct || 0;
    const chgEl = document.getElementById('m-chg');
    chgEl.textContent = (chg >= 0 ? '+' : '') + chg.toFixed(2) + '%';
    chgEl.style.color = chg >= 0 ? '#dc3545' : '#198754';
}

function renderBinsTable(data) {
    const tbody = document.querySelector('#binsTable tbody');
    if (!tbody) return;
    const dist = data.distribution.slice().sort((a, b) => b.weight - a.weight).slice(0, 10);
    const total = data.distribution.reduce((s, d) => s + d.weight, 0) || 1;
    tbody.innerHTML = dist.map(d => {
        const pct = (d.weight / total * 100).toFixed(1);
        const range = d.price_low.toFixed(3) + ' - ' + d.price_high.toFixed(3);
        return '<tr><td>' + range + '</td><td>' + d.weight.toFixed(0) + '</td><td>' + pct + '%</td></tr>';
    }).join('');
}

function peakColor(d, peaks) {
    const center = (d.price_low + d.price_high) / 2;
    if (peaks.length > 0 && Math.abs(center - peaks[0].price) < (d.price_high - d.price_low)) return '#dc3545';
    if (peaks.length > 1 && Math.abs(center - peaks[1].price) < (d.price_high - d.price_low)) return '#fd7e14';
    return '#6c757d';
}

function klasses(arr, key) {
    return arr.map(x => x[key]);
}

function computeMA(values, period) {
    const out = new Array(values.length).fill(null);
    for (let i = period - 1; i < values.length; i++) {
        let s = 0;
        for (let j = 0; j < period; j++) s += values[i - j];
        out[i] = s / period;
    }
    return out;
}

function smoothWeights(values, window) {
    if (values.length < window) return values.slice();
    const out = new Array(values.length);
    const half = Math.floor(window / 2);
    for (let i = 0; i < values.length; i++) {
        const lo = Math.max(0, i - half);
        const hi = Math.min(values.length, i + half + 1);
        let s = 0;
        for (let j = lo; j < hi; j++) s += values[j];
        out[i] = s / (hi - lo);
    }
    return out;
}
