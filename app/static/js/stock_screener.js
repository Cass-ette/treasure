document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('screen-form');
    if (!form) return;
    document.getElementById('btn-screen').addEventListener('click', loadStocks);
    document.getElementById('btn-reset').addEventListener('click', function () {
        form.reset();
        loadStocks();
    });
    form.addEventListener('submit', function (event) { event.preventDefault(); loadStocks(); });
    loadStocks();
});

let screenRequest = null;

function numberText(value, digits) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) return '-';
    return Number(value).toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

function compactMoney(value) {
    if (value === null || value === undefined) return '-';
    const n = Number(value);
    if (n >= 100000000) return numberText(n / 100000000, 2) + '亿';
    if (n >= 10000) return numberText(n / 10000, 0) + '万';
    return numberText(n, 0);
}

function collectParams() {
    const form = document.getElementById('screen-form');
    const params = new URLSearchParams();
    new FormData(form).forEach((value, key) => {
        if (value !== '') params.set(key, value);
    });
    params.set('exclude_special', document.getElementById('screen-exclude').checked ? '1' : '0');
    params.set('limit', '200');
    return params;
}

async function loadStocks() {
    if (screenRequest) screenRequest.abort();
    const controller = new AbortController();
    screenRequest = controller;
    const status = document.getElementById('screen-status');
    const body = document.querySelector('#screen-table tbody');
    status.children[0].textContent = t('正在获取行情…');
    try {
        const response = await fetch('/stocks/api/screener?' + collectParams(), { signal: controller.signal });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'HTTP ' + response.status);
        const stale = data.stale ? ' · ' + t('使用缓存快照') : '';
        status.children[0].textContent = t('符合条件') + ': ' + data.match_count + ' / ' + data.universe_count + stale;
        status.children[1].textContent = t('数据时间') + ': ' + new Date(data.fetched_at).toLocaleString();
        body.innerHTML = data.rows.length ? data.rows.map(renderRow).join('') : '<tr><td colspan="9" class="text-center text-muted py-4">' + t('没有符合条件的股票') + '</td></tr>';
    } catch (error) {
        if (controller.signal.aborted) return;
        status.children[0].textContent = t('筛选失败') + ': ' + error.message;
        status.children[1].textContent = '';
        body.innerHTML = '<tr><td colspan="9" class="text-center text-danger py-4">' + error.message + '</td></tr>';
    } finally {
        if (screenRequest === controller) screenRequest = null;
    }
}

function renderRow(row) {
    const color = Number(row.change_pct) >= 0 ? 'text-profit' : 'text-loss';
    return '<tr>' +
        '<td><code>' + row.code + '</code></td>' +
        '<td class="text-nowrap">' + escapeHtml(row.name) + '</td>' +
        '<td>' + numberText(row.price, 2) + '</td>' +
        '<td class="' + color + '">' + signed(row.change_pct, 2) + '%</td>' +
        '<td>' + numberText(row.turnover_rate, 2) + '%</td>' +
        '<td>' + compactMoney(row.amount) + '</td>' +
        '<td>' + numberText(row.pe, 2) + '</td>' +
        '<td>' + numberText(row.pb, 2) + '</td>' +
        '<td>' + compactMoney(row.total_market_cap) + '</td>' +
        '</tr>';
}

function signed(value, digits) {
    const text = numberText(value, digits);
    return text === '-' ? text : (Number(value) >= 0 ? '+' : '') + text;
}

function escapeHtml(value) {
    return String(value).replace(/[&<>'"]/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[ch]));
}
