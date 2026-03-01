// fund-management.js — AJAX fund code lookup + 30-day average NAV

document.addEventListener('DOMContentLoaded', function () {
    initFundCodeLookup();
    fetchAverageNavs();
});

function debounce(fn, ms) {
    var timer;
    return function () {
        var ctx = this, args = arguments;
        clearTimeout(timer);
        timer = setTimeout(function () { fn.apply(ctx, args); }, ms);
    };
}

function initFundCodeLookup() {
    var codeInput = document.getElementById('code');
    if (!codeInput) return;

    var nameInput = document.getElementById('name');
    var navInput = document.getElementById('latest_nav');
    var dateInput = document.getElementById('nav_date');

    var spinner = document.createElement('span');
    spinner.className = 'spinner-inline ms-2';
    spinner.style.display = 'none';
    codeInput.parentNode.appendChild(spinner);

    var doLookup = debounce(function () {
        var code = codeInput.value.trim();
        if (code.length !== 6 || !/^\d{6}$/.test(code)) return;

        spinner.style.display = 'inline-block';

        fetch('/get_fund_info?code=' + encodeURIComponent(code))
            .then(function (r) { return r.json(); })
            .then(function (data) {
                spinner.style.display = 'none';
                if (data.success) {
                    if (data.name) nameInput.value = data.name;
                    if (data.latest_nav) navInput.value = data.latest_nav;
                    if (data.nav_date) dateInput.value = data.nav_date;
                    showNotification('基金信息获取成功', 'success');
                } else {
                    showNotification(data.message || '获取基金信息失败', 'warning');
                }
            })
            .catch(function () {
                spinner.style.display = 'none';
                showNotification('获取基金信息时发生错误', 'danger');
            });
    }, 500);

    codeInput.addEventListener('blur', doLookup);
    codeInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') doLookup();
    });
}

function fetchAverageNavs() {
    document.querySelectorAll('.avg-nav-cell[data-fund-id]').forEach(function (cell) {
        var fundId = cell.getAttribute('data-fund-id');

        fetch('/get_fund_30_day_average?fund_id=' + encodeURIComponent(fundId))
            .then(function (r) { return r.json(); })
            .then(function (data) {
                cell.textContent = (data.success && data.average_nav)
                    ? data.average_nav.toFixed(4)
                    : '暂无数据';
            })
            .catch(function () {
                cell.textContent = '获取失败';
            });
    });
}
