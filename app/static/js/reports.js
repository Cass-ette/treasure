// reports.js — Profit chart + Fund NAV charts

document.addEventListener('DOMContentLoaded', function () {
    if (window.REPORT_DATA) {
        initProfitChart();
        initFundNavCharts();
    }
    if (window.FUND_CHART_DATA) {
        initSingleFundChart();
    }
});

// ── Profit Line Chart (daily + cumulative) ──
function initProfitChart() {
    var data = window.REPORT_DATA;
    if (!data.dates || !data.dates.length) return;
    var canvas = document.getElementById('profitChart');
    if (!canvas) return;

    new Chart(canvas, {
        type: 'line',
        data: {
            labels: data.dates,
            datasets: [
                {
                    label: '累计收益',
                    data: data.cumulativeProfits,
                    borderColor: '#3B82F6',
                    backgroundColor: 'rgba(59, 130, 246, 0.08)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 2,
                    borderWidth: 2
                },
                {
                    label: '日收益',
                    data: data.dailyProfits,
                    borderColor: '#10B981',
                    backgroundColor: 'rgba(16, 185, 129, 0.08)',
                    fill: false,
                    tension: 0.3,
                    pointRadius: 1,
                    borderWidth: 1.5
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { position: 'top', labels: { usePointStyle: true } },
                tooltip: {
                    callbacks: {
                        label: function (ctx) {
                            return ctx.dataset.label + ': ¥' + (ctx.raw || 0).toFixed(2);
                        }
                    }
                }
            },
            scales: {
                x: { grid: { display: false } },
                y: {
                    grid: { color: '#F1F5F9' },
                    ticks: {
                        callback: function (v) { return '¥' + v.toFixed(0); }
                    }
                }
            }
        }
    });
}

// ── Inline Fund NAV Mini Charts ──
function initFundNavCharts() {
    var charts = document.querySelectorAll('.fund-nav-chart');
    charts.forEach(function (canvas) {
        var fundId = canvas.getAttribute('data-fund-id');
        if (!fundId) return;
        fetchNavAndDraw(canvas, fundId, 30);
    });
}

function fetchNavAndDraw(canvas, fundId, days) {
    fetch('/api/fund/' + fundId + '/nav_history?days=' + days)
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (!data.dates || !data.dates.length) {
                canvas.parentNode.innerHTML = '<div class="text-center text-muted py-3" style="font-size:0.85rem">暂无净值数据</div>';
                return;
            }
            drawNavChart(canvas, data);
        })
        .catch(function () {
            canvas.parentNode.innerHTML = '<div class="text-center text-muted py-3" style="font-size:0.85rem">加载失败</div>';
        });
}

function drawNavChart(canvas, data) {
    var first = data.navs[0];
    var last = data.navs[data.navs.length - 1];
    var isUp = last >= first;
    var color = isUp ? '#DC2626' : '#16A34A';
    // Respect color mode
    if (document.documentElement.getAttribute('data-color-mode') === 'intl') {
        color = isUp ? '#16A34A' : '#DC2626';
    }

    new Chart(canvas, {
        type: 'line',
        data: {
            labels: data.dates,
            datasets: [{
                data: data.navs,
                borderColor: color,
                backgroundColor: color.replace(')', ', 0.08)').replace('rgb', 'rgba'),
                fill: true,
                tension: 0.3,
                pointRadius: 0,
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title: function (ctx) { return ctx[0].label; },
                        label: function (ctx) { return '净值: ' + ctx.raw.toFixed(4); }
                    }
                }
            },
            scales: {
                x: { display: false },
                y: {
                    display: false,
                    beginAtZero: false
                }
            }
        }
    });
}

// ── Single Fund Full Chart ──
function initSingleFundChart() {
    var cfg = window.FUND_CHART_DATA;
    if (!cfg) return;

    fetch('/api/fund/' + cfg.fundId + '/nav_history?days=' + cfg.days)
        .then(function (r) { return r.json(); })
        .then(function (data) {
            if (!data.dates || !data.dates.length) {
                document.getElementById('fundNavChart').parentNode.innerHTML =
                    '<div class="text-center text-muted py-5">暂无净值数据</div>';
                return;
            }
            drawFullNavChart(data);
            updateStats(data);
        })
        .catch(function () {
            document.getElementById('fundNavChart').parentNode.innerHTML =
                '<div class="text-center text-muted py-5">加载失败</div>';
        });
}

function drawFullNavChart(data) {
    var canvas = document.getElementById('fundNavChart');
    if (!canvas) return;

    var first = data.navs[0];
    var last = data.navs[data.navs.length - 1];
    var isUp = last >= first;
    var color = isUp ? '#DC2626' : '#16A34A';
    if (document.documentElement.getAttribute('data-color-mode') === 'intl') {
        color = isUp ? '#16A34A' : '#DC2626';
    }

    new Chart(canvas, {
        type: 'line',
        data: {
            labels: data.dates,
            datasets: [{
                label: data.fund_name + ' 净值',
                data: data.navs,
                borderColor: color,
                backgroundColor: color.replace(')', ', 0.06)').replace('rgb', 'rgba'),
                fill: true,
                tension: 0.2,
                pointRadius: 3,
                pointHoverRadius: 6,
                borderWidth: 2.5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function (ctx) { return '净值: ' + ctx.raw.toFixed(4); }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { maxRotation: 45, font: { size: 11 } }
                },
                y: {
                    beginAtZero: false,
                    grid: { color: '#F1F5F9' },
                    ticks: {
                        callback: function (v) { return v.toFixed(4); }
                    }
                }
            }
        }
    });
}

function updateStats(data) {
    var navs = data.navs;
    if (!navs.length) return;

    var max = Math.max.apply(null, navs);
    var min = Math.min.apply(null, navs);
    var avg = navs.reduce(function (a, b) { return a + b; }, 0) / navs.length;
    var change = navs[navs.length - 1] - navs[0];
    var changeRate = navs[0] > 0 ? (change / navs[0] * 100) : 0;

    var el = function (id) { return document.getElementById(id); };
    if (el('statMax')) el('statMax').textContent = max.toFixed(4);
    if (el('statMin')) el('statMin').textContent = min.toFixed(4);
    if (el('statAvg')) el('statAvg').textContent = avg.toFixed(4);
    if (el('statDays')) el('statDays').textContent = navs.length;

    var changeEl = el('statChange');
    var rateEl = el('statChangeRate');
    if (changeEl) {
        changeEl.textContent = (change >= 0 ? '+' : '') + change.toFixed(4);
        changeEl.className = 'fw-bold ' + (change >= 0 ? 'text-profit' : 'text-loss');
    }
    if (rateEl) {
        rateEl.textContent = (changeRate >= 0 ? '+' : '') + changeRate.toFixed(2) + '%';
        rateEl.className = 'fw-bold ' + (changeRate >= 0 ? 'text-profit' : 'text-loss');
    }
}
