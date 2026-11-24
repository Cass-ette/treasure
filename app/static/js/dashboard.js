// dashboard.js — Dashboard page: chart, sort, language, modal

document.addEventListener('DOMContentLoaded', function () {
    initChart();
    initTableSort();
});

// ── Palette: one accent for the largest holding, neutral slate steps for the rest ──
var CHART_COLORS = [
    '#0D9488', '#1B2A4A', '#3F4E6B', '#606F8C', '#8090AC',
    '#9AA8C0', '#B2BFD1', '#C8D2DF', '#D9E0EA', '#E6EBF2'
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

    var totalValue = data.fundValues.reduce(function (a, b) { return a + b; }, 0);
    var labels = data.fundNames.map(function (name, i) {
        var pct = totalValue > 0 ? ((data.fundValues[i] / totalValue) * 100).toFixed(2) : '0.00';
        return name + '  ' + pct + '%';
    });

    new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data.fundValues,
                backgroundColor: colors,
                borderWidth: 2,
                borderColor: '#fff',
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '60%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 12,
                        usePointStyle: true,
                        pointStyle: 'circle',
                        boxWidth: 8,
                        boxHeight: 8,
                        color: '#4B5565',
                        font: { size: 11 }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (ctx) {
                            var val = ctx.raw || 0;
                            return ' ¥' + val.toFixed(2);
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
