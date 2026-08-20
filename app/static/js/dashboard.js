// dashboard.js — Dashboard page: chart, sort, language, modal

document.addEventListener('DOMContentLoaded', function () {
    initChart();
    initTableSort();
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

// ── Bootstrap Modal for editing principal ──
window.showEditPrincipalModal = function (accountId, username, principal) {
    document.getElementById('modal-account-id').value = accountId;
    document.getElementById('modal-username').value = username;
    document.getElementById('modal-principal').value = principal;
    new bootstrap.Modal(document.getElementById('editPrincipalModal')).show();
};
