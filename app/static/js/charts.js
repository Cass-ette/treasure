// 图表专用JavaScript文件

// 图表配置常量
const CHART_COLORS = {
    primary: '#0d6efd',
    secondary: '#6c757d',
    success: '#28a745',
    danger: '#dc3545',
    warning: '#ffc107',
    info: '#17a2b8',
    light: '#f8f9fa',
    dark: '#343a40',
    muted: '#6c757d',
    border: '#dee2e6'
};

// 图表类型枚举
const CHART_TYPES = {
    LINE: 'line',
    BAR: 'bar',
    PIE: 'pie',
    DOUGHNUT: 'doughnut',
    RADAR: 'radar',
    POLAR_AREA: 'polarArea',
    SCATTER: 'scatter',
    BUBBLE: 'bubble'
};

// 图表实例管理器
const chartManager = {
    charts: {},
    
    // 创建新图表
    createChart(canvasId, chartType, data, options = {}) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return null;
        
        const ctx = canvas.getContext('2d');
        
        // 如果已有同名图表，销毁它
        this.destroyChart(canvasId);
        
        // 创建新图表
        const chart = new Chart(ctx, {
            type: chartType,
            data: data,
            options: this.mergeOptions(options, chartType)
        });
        
        // 保存图表实例
        this.charts[canvasId] = chart;
        
        return chart;
    },
    
    // 销毁图表
    destroyChart(canvasId) {
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
            delete this.charts[canvasId];
        }
    },
    
    // 更新图表数据
    updateChart(canvasId, data) {
        const chart = this.charts[canvasId];
        if (!chart) return false;
        
        chart.data = data;
        chart.update();
        return true;
    },
    
    // 获取图表实例
    getChart(canvasId) {
        return this.charts[canvasId] || null;
    },
    
    // 合并默认选项
    mergeOptions(options, chartType) {
        const defaultOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: chartType === CHART_TYPES.PIE || chartType === CHART_TYPES.DOUGHNUT ? 'right' : 'top',
                    labels: {
                        boxWidth: 12,
                        padding: 15,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    padding: 10,
                    cornerRadius: 4,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleFont: {
                        size: 13,
                        weight: 'bold'
                    },
                    bodyFont: {
                        size: 12
                    },
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += context.parsed.y;
                            }
                            return label;
                        }
                    }
                }
            }
        };
        
        // 根据图表类型添加特定配置
        if (chartType === CHART_TYPES.LINE || chartType === CHART_TYPES.BAR) {
            defaultOptions.scales = {
                x: {
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                }
            };
        }
        
        if (chartType === CHART_TYPES.DOUGHNUT) {
            defaultOptions.cutout = '65%';
        }
        
        // 合并用户选项
        return {...defaultOptions, ...options};
    }
};

// 性能图表配置生成器
function generatePerformanceChartConfig(labels, datasets) {
    return {
        type: CHART_TYPES.LINE,
        data: {
            labels: labels,
            datasets: datasets.map(dataset => ({
                ...dataset,
                tension: 0.4,
                borderWidth: 2,
                pointBackgroundColor: '#fff',
                pointBorderColor: dataset.borderColor,
                pointBorderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6
            }))
        },
        options: {
            scales: {
                y: {
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += context.parsed.y + '%';
                            }
                            return label;
                        }
                    }
                }
            }
        }
    };
}

// 资产分配图表配置生成器
function generateAllocationChartConfig(labels, values, colors = null) {
    // 如果没有提供颜色，使用默认颜色
    if (!colors) {
        colors = [
            CHART_COLORS.primary,
            CHART_COLORS.success,
            CHART_COLORS.warning,
            CHART_COLORS.danger,
            CHART_COLORS.info,
            CHART_COLORS.secondary
        ];
    }
    
    // 为每个项目生成颜色
    const backgroundColors = values.map((_, index) => 
        colors[index % colors.length]
    );
    
    return {
        type: CHART_TYPES.DOUGHNUT,
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: backgroundColors,
                borderColor: '#fff',
                borderWidth: 2,
                hoverOffset: 10
            }]
        },
        options: {
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.label || '';
                            let value = context.raw || 0;
                            let total = context.dataset.data.reduce((a, b) => a + b, 0);
                            let percentage = Math.round((value / total) * 100);
                            
                            if (label) {
                                label += ': ';
                            }
                            label += `${value} (${percentage}%)`;
                            
                            return label;
                        }
                    }
                }
            }
        }
    };
}

// 交易记录图表配置生成器
function generateTransactionChartConfig(labels, buyData, sellData) {
    return {
        type: CHART_TYPES.BAR,
        data: {
            labels: labels,
            datasets: [
                {
                    label: '买入金额',
                    data: buyData,
                    backgroundColor: 'rgba(40, 167, 69, 0.7)',
                    borderColor: CHART_COLORS.success,
                    borderWidth: 1
                },
                {
                    label: '卖出金额',
                    data: sellData,
                    backgroundColor: 'rgba(220, 53, 69, 0.7)',
                    borderColor: CHART_COLORS.danger,
                    borderWidth: 1
                }
            ]
        },
        options: {
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += '¥' + context.parsed.y.toLocaleString();
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '¥' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    };
}

// 模拟数据生成器
function generateMockData(type, count = 6) {
    switch(type) {
        case 'performance':
            return {
                labels: ['一月', '二月', '三月', '四月', '五月', '六月'].slice(0, count),
                datasets: [
                    {
                        label: '总收益率',
                        data: Array.from({length: count}, () => (Math.random() * 6 + 3).toFixed(1)),
                        borderColor: CHART_COLORS.primary,
                        backgroundColor: 'rgba(13, 110, 253, 0.1)',
                        fill: true
                    },
                    {
                        label: '市场基准',
                        data: Array.from({length: count}, () => (Math.random() * 4 + 2).toFixed(1)),
                        borderColor: CHART_COLORS.secondary,
                        backgroundColor: 'transparent',
                        borderDash: [5, 5]
                    }
                ]
            };
            
        case 'allocation':
            const labels = ['股票型基金', '债券型基金', '混合型基金', '货币市场基金', '其他'];
            const values = Array.from({length: labels.length}, () => 
                Math.floor(Math.random() * 30) + 5
            );
            // 确保总和为100%
            const sum = values.reduce((a, b) => a + b, 0);
            const normalizedValues = values.map(v => Math.round((v / sum) * 100));
            
            return {
                labels: labels,
                values: normalizedValues
            };
            
        case 'transactions':
            const months = ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月'];
            return {
                labels: months.slice(0, count),
                buyData: Array.from({length: count}, () => Math.floor(Math.random() * 5000) + 3000),
                sellData: Array.from({length: count}, () => Math.floor(Math.random() * 3000) + 1000)
            };
            
        default:
            return null;
    }
}

// 图表动画控制函数
function animateChart(chart, duration = 1000) {
    if (!chart) return;
    
    // 触发图表动画
    chart.update({
        duration: duration,
        easing: 'easeOutQuart'
    });
}

// 图表导出功能
function exportChart(canvasId, format = 'png') {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;
    
    // 创建临时链接
    const link = document.createElement('a');
    link.download = `chart-${canvasId}-${new Date().toISOString().slice(0, 10)}.${format}`;
    
    if (format === 'png') {
        link.href = canvas.toDataURL('image/png');
    } else if (format === 'jpeg') {
        link.href = canvas.toDataURL('image/jpeg');
    } else if (format === 'pdf') {
        // 简单的PDF导出实现
        const pdf = new jsPDF({
            orientation: 'landscape',
            unit: 'mm'
        });
        pdf.addImage(canvas.toDataURL('image/png'), 'PNG', 10, 10, 277, 155);
        pdf.save(link.download.replace('.pdf', ''));
        return;
    }
    
    link.click();
    return link.href;
}

// 响应式图表处理
function handleResponsiveCharts() {
    const resizeObserver = new ResizeObserver(entries => {
        entries.forEach(entry => {
            // 查找entry中的所有图表容器
            const chartContainers = entry.target.querySelectorAll('.chart-container');
            chartContainers.forEach(container => {
                const canvas = container.querySelector('canvas');
                if (canvas) {
                    const chart = chartManager.getChart(canvas.id);
                    if (chart) {
                        chart.resize();
                    }
                }
            });
        });
    });
    
    // 观察主容器
    const mainContainer = document.querySelector('.container');
    if (mainContainer) {
        resizeObserver.observe(mainContainer);
    }
    
    return resizeObserver;
}

// 数据更新函数 - 使用模拟数据更新所有图表
function updateAllChartsWithMockData() {
    // 检查是否存在图表容器
    const performanceCanvas = document.getElementById('performanceChart');
    const allocationCanvas = document.getElementById('allocationChart');
    const transactionCanvas = document.getElementById('transactionChart');
    
    // 更新性能图表
    if (performanceCanvas) {
        const performanceData = generateMockData('performance');
        const config = generatePerformanceChartConfig(
            performanceData.labels,
            performanceData.datasets
        );
        chartManager.createChart('performanceChart', config.type, config.data, config.options);
    }
    
    // 更新资产分配图表
    if (allocationCanvas) {
        const allocationData = generateMockData('allocation');
        const config = generateAllocationChartConfig(
            allocationData.labels,
            allocationData.values
        );
        chartManager.createChart('allocationChart', config.type, config.data, config.options);
    }
    
    // 更新交易记录图表
    if (transactionCanvas) {
        const transactionData = generateMockData('transactions');
        const config = generateTransactionChartConfig(
            transactionData.labels,
            transactionData.buyData,
            transactionData.sellData
        );
        chartManager.createChart('transactionChart', config.type, config.data, config.options);
    }
}

// 导出图表管理器和工具函数
export { chartManager, CHART_TYPES, CHART_COLORS, generatePerformanceChartConfig, generateAllocationChartConfig, generateTransactionChartConfig, generateMockData, animateChart, exportChart, handleResponsiveCharts, updateAllChartsWithMockData };