// dashboard.js — Dashboard page: chart, sort, language/color mode, modal

document.addEventListener('DOMContentLoaded', function () {
    initColorMode();
    initChart();
    initTableSort();
    document.getElementById('toggle-color-mode')
        && document.getElementById('toggle-color-mode').addEventListener('click', toggleMode);
});

// ── Fixed color palette for pie chart ──
var CHART_COLORS = [
    '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6',
    '#EC4899', '#06B6D4', '#F97316', '#14B8A6', '#6366F1'
];

// ── Doughnut Chart ──
function initChart() {
    var data = window.DASHBOARD_DATA;
    if (!data || !data.fundNames || !data.fundNames.length) return;
    var canvas = document.getElementById('positionPieChart');
    if (!canvas) return;

    var colors = data.fundNames.map(function (_, i) {
        return CHART_COLORS[i % CHART_COLORS.length];
    });

    new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: data.fundNames,
            datasets: [{
                data: data.fundValues,
                backgroundColor: colors,
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '60%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { padding: 14, usePointStyle: true }
                },
                tooltip: {
                    callbacks: {
                        label: function (ctx) {
                            var val = ctx.raw || 0;
                            var total = ctx.dataset.data.reduce(function (a, b) { return a + b; }, 0);
                            var pct = total > 0 ? ((val / total) * 100).toFixed(1) : '0.0';
                            return ctx.label + ': ¥' + val.toFixed(2) + ' (' + pct + '%)';
                        }
                    }
                }
            }
        }
    });
}

// ── Table Sort (market value, descending) ──
function initTableSort() {
    var table = document.getElementById('positions-table');
    if (!table) return;
    var tbody = table.querySelector('tbody');
    if (!tbody) return;

    function sortDesc() {
        var rows = Array.from(tbody.querySelectorAll('tr'));
        rows.sort(function (a, b) {
            var va = parseFloat((a.cells[2] ? a.cells[2].textContent : '').replace(/[¥,]/g, '')) || 0;
            var vb = parseFloat((b.cells[2] ? b.cells[2].textContent : '').replace(/[¥,]/g, '')) || 0;
            return vb - va;
        });
        rows.forEach(function (r) { tbody.appendChild(r); });
    }

    sortDesc();
    var header = document.getElementById('th-value');
    if (header) header.addEventListener('click', sortDesc);
}

// ── Language Translations (ID-based) ──
var LANG = {
    'main-title':        { zh: '投资管理仪表盘',   en: 'Investment Dashboard' },
    'principal-label':   { zh: '总本金',           en: 'Total Principal' },
    'market-value-label':{ zh: '总市值',           en: 'Total Market Value' },
    'profit-label':      { zh: '总盈亏',           en: 'Total Profit/Loss' },
    'yield-label':       { zh: '收益率',           en: 'Yield Rate' },
    'positions-title':   { zh: '持仓概览',         en: 'Position Overview' },
    'chart-title':       { zh: '持仓分布',         en: 'Allocation' },
    'th-fund':           { zh: '基金名称',         en: 'Fund Name' },
    'th-cost':           { zh: '成本',             en: 'Cost' },
    'th-value':          { zh: '市值',             en: 'Market Value' },
    'th-profit':         { zh: '盈亏',             en: 'Profit/Loss' },
    'th-return':         { zh: '收益率',           en: 'Return' },
    'th-weight':         { zh: '占比',             en: 'Weight' },
    'sub-title':         { zh: '次级账户管理',     en: 'Sub-account Management' },
    'th-user':           { zh: '用户名',           en: 'Username' },
    'th-principal':      { zh: '本金',             en: 'Principal' },
    'th-status':         { zh: '状态',             en: 'Status' },
    'th-action':         { zh: '操作',             en: 'Action' },
    'modal-title':       { zh: '修改次级账户本金', en: 'Edit Sub-account Principal' }
};

function setLanguage(lang) {
    Object.keys(LANG).forEach(function (id) {
        var el = document.getElementById(id);
        if (!el) return;
        // Preserve child elements (e.g. sort icon)
        var children = Array.from(el.children);
        el.textContent = LANG[id][lang];
        children.forEach(function (c) { el.appendChild(c); });
    });
    document.querySelectorAll('.status-text').forEach(function (el) {
        el.textContent = lang === 'zh' ? '活跃' : 'Active';
    });
    document.querySelectorAll('.btn-edit-principal').forEach(function (el) {
        el.textContent = lang === 'zh' ? '修改本金' : 'Edit';
    });
}

// ── Color Mode + Language Toggle ──
function initColorMode() {
    var saved = localStorage.getItem('colorMode') || 'cn';
    applyMode(saved);
}

function toggleMode() {
    var current = document.documentElement.getAttribute('data-color-mode') || 'cn';
    var next = current === 'cn' ? 'intl' : 'cn';
    localStorage.setItem('colorMode', next);
    applyMode(next);
}

function applyMode(mode) {
    document.documentElement.setAttribute('data-color-mode', mode);
    var btn = document.getElementById('toggle-color-mode');
    var text = document.getElementById('color-mode-text');
    if (mode === 'intl') {
        if (btn) btn.textContent = 'Switch to Chinese Mode';
        if (text) text.textContent = 'International (Green Up)';
        setLanguage('en');
    } else {
        if (btn) btn.textContent = '切换至国际模式';
        if (text) text.textContent = '中国模式 (红涨绿跌)';
        setLanguage('zh');
    }
}

// ── Bootstrap Modal for editing principal ──
window.showEditPrincipalModal = function (accountId, username, principal) {
    document.getElementById('modal-account-id').value = accountId;
    document.getElementById('modal-username').value = username;
    document.getElementById('modal-principal').value = principal;
    new bootstrap.Modal(document.getElementById('editPrincipalModal')).show();
};
