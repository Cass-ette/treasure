// 主应用JavaScript文件

// DOM加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化页面功能
    initPage();
    
    // 初始化表单验证
    initFormValidation();
    
    // 初始化图表功能（如果页面需要）
    initCharts();
});

// 页面初始化函数
function initPage() {
    // 添加淡入动画效果
    document.querySelectorAll('.container').forEach(function(element) {
        element.classList.add('fade-in');
    });
    
    // 处理导航栏激活状态
    setActiveNavItem();
    
    // 添加工具提示功能
    initTooltips();
}

// 设置导航栏当前激活项
function setActiveNavItem() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        const linkPath = link.getAttribute('href');
        if (currentPath.includes(linkPath) && linkPath !== '#') {
            link.classList.add('active');
        }
    });
}

// 初始化Bootstrap工具提示
function initTooltips() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => 
        new bootstrap.Tooltip(tooltipTriggerEl)
    );
}

// 表单验证初始化
function initFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!this.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            // 添加验证状态样式
            this.classList.add('was-validated');
        }, false);
    });
}

// 初始化图表功能
function initCharts() {
    // 检查是否存在Chart.js库
    if (typeof Chart !== 'undefined') {
        // 处理所有图表容器
        document.querySelectorAll('.chart-container canvas').forEach(function(canvas) {
            // 根据canvas ID决定创建什么类型的图表
            const chartId = canvas.id;
            const ctx = canvas.getContext('2d');
            
            switch(chartId) {
                case 'performanceChart':
                    createPerformanceChart(ctx);
                    break;
                case 'allocationChart':
                    createAllocationChart(ctx);
                    break;
                case 'transactionChart':
                    createTransactionChart(ctx);
                    break;
                default:
                    // 可以在这里添加默认图表配置
                    break;
            }
        });
    }
}

// 创建性能图表
function createPerformanceChart(ctx) {
    // 这里使用模拟数据，实际应用中应该从后端获取
    const labels = ['一月', '二月', '三月', '四月', '五月', '六月'];
    const datasets = [
        {
            label: '总收益率',
            data: [5.2, 6.5, 7.3, 8.1, 7.8, 9.2],
            borderColor: '#0d6efd',
            backgroundColor: 'rgba(13, 110, 253, 0.1)',
            tension: 0.4,
            fill: true
        },
        {
            label: '市场基准',
            data: [3.5, 4.8, 5.2, 6.1, 5.9, 6.8],
            borderColor: '#6c757d',
            backgroundColor: 'transparent',
            borderDash: [5, 5],
            tension: 0.4
        }
    ];
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
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
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
}

// 创建资产分配图表
function createAllocationChart(ctx) {
    // 模拟数据
    const data = {
        labels: ['股票型基金', '债券型基金', '混合型基金', '货币市场基金'],
        datasets: [{
            data: [45, 30, 20, 5],
            backgroundColor: [
                '#0d6efd',
                '#28a745',
                '#ffc107',
                '#6c757d'
            ],
            borderWidth: 2,
            borderColor: '#fff'
        }]
    };
    
    new Chart(ctx, {
        type: 'doughnut',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed !== null) {
                                label += context.parsed + '%';
                            }
                            return label;
                        }
                    }
                }
            },
            cutout: '65%'
        }
    });
}

// 创建交易记录图表
function createTransactionChart(ctx) {
    // 模拟数据
    const labels = ['一月', '二月', '三月', '四月', '五月', '六月'];
    const datasets = [
        {
            label: '买入金额',
            data: [5000, 3500, 6200, 4800, 7100, 5900],
            backgroundColor: 'rgba(40, 167, 69, 0.7)',
            borderColor: '#28a745',
            borderWidth: 1
        },
        {
            label: '卖出金额',
            data: [2500, 1800, 3100, 2200, 4500, 3800],
            backgroundColor: 'rgba(220, 53, 69, 0.7)',
            borderColor: '#dc3545',
            borderWidth: 1
        }
    ];
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
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
    });
}

// 工具函数：格式化金额
function formatCurrency(amount) {
    return '¥' + parseFloat(amount).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

// 工具函数：格式化百分比
function formatPercentage(value) {
    return parseFloat(value).toFixed(2) + '%';
}

// 处理AJAX请求的工具函数
function makeAjaxRequest(url, method, data = null) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        
        xhr.open(method, url);
        xhr.setRequestHeader('Content-Type', 'application/json');
        
        xhr.onload = function() {
            if (xhr.status >= 200 && xhr.status < 300) {
                resolve(JSON.parse(xhr.responseText));
            } else {
                reject({ status: xhr.status, message: xhr.statusText });
            }
        };
        
        xhr.onerror = function() {
            reject({ status: 0, message: 'Network error' });
        };
        
        if (data) {
            xhr.send(JSON.stringify(data));
        } else {
            xhr.send();
        }
    });
}

// 显示通知消息
function showNotification(message, type = 'success') {
    // 检查是否已经存在通知容器
    let notificationContainer = document.getElementById('notificationContainer');
    
    if (!notificationContainer) {
        notificationContainer = document.createElement('div');
        notificationContainer.id = 'notificationContainer';
        notificationContainer.style.position = 'fixed';
        notificationContainer.style.top = '20px';
        notificationContainer.style.right = '20px';
        notificationContainer.style.zIndex = '1050';
        document.body.appendChild(notificationContainer);
    }
    
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show`;
    notification.role = 'alert';
    notification.style.minWidth = '300px';
    notification.style.marginBottom = '10px';
    
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    notificationContainer.appendChild(notification);
    
    // 3秒后自动关闭
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 500);
    }, 3000);
}