// main.js — Global utilities

document.addEventListener('DOMContentLoaded', function () {
    setActiveNavItem();
    initTooltips();
    initFormValidation();
});

// Highlight current nav item
function setActiveNavItem() {
    var currentPath = window.location.pathname;
    document.querySelectorAll('.navbar-treasure .nav-link').forEach(function (link) {
        var href = link.getAttribute('href');
        if (href && href !== '#' && currentPath.startsWith(href)) {
            link.classList.add('active');
        }
    });
}

// Bootstrap tooltips
function initTooltips() {
    var list = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    [].slice.call(list).forEach(function (el) {
        new bootstrap.Tooltip(el);
    });
}

// Bootstrap-style form validation
function initFormValidation() {
    document.querySelectorAll('form').forEach(function (form) {
        form.addEventListener('submit', function (e) {
            if (!this.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            this.classList.add('was-validated');
        }, false);
    });
}

// Toast notification (used by fund-management.js etc.)
function showNotification(message, type) {
    type = type || 'success';
    var container = document.getElementById('notificationContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notificationContainer';
        container.style.cssText = 'position:fixed;top:20px;right:20px;z-index:1050;';
        document.body.appendChild(container);
    }
    var el = document.createElement('div');
    el.className = 'alert alert-' + type + ' alert-dismissible fade show';
    el.style.minWidth = '280px';
    el.style.marginBottom = '10px';
    el.innerHTML = message + '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>';
    container.appendChild(el);
    setTimeout(function () {
        el.classList.remove('show');
        setTimeout(function () { el.remove(); }, 400);
    }, 3000);
}
