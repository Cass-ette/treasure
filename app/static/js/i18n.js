// i18n.js — 翻译 helper + 语言/颜色切换
window.t = function (k) { return (window.I18N || {})[k] || k; };

window.setLocale = function (lang) {
    fetch('/locale/set', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: 'lang=' + encodeURIComponent(lang)
    }).then(function (r) { return r.json(); })
      .then(function (d) { if (d.ok) location.reload(); })
      .catch(function (err) { console.error('setLocale failed:', err); });
};

// 颜色模式三态：follow / cn / intl
window.setColorMode = function (mode) {
    var el = document.documentElement;
    var lang = el.getAttribute('lang') === 'en-US' ? 'en' : 'zh';
    if (mode === 'follow') {
        localStorage.removeItem('colorMode');
        el.setAttribute('data-color-mode', lang === 'zh' ? 'cn' : 'intl');
    } else {
        localStorage.setItem('colorMode', mode);
        el.setAttribute('data-color-mode', mode);
    }
    updateColorLabel(mode);
};

function updateColorLabel(mode) {
    var label = document.getElementById('color-mode-label');
    if (!label) return;
    var names = { follow: t('跟随语言'), cn: t('红涨绿跌'), intl: t('绿涨红跌') };
    label.textContent = names[mode] || mode;
}

document.addEventListener('DOMContentLoaded', function () {
    var stored = localStorage.getItem('colorMode');
    updateColorLabel(stored || 'follow');
});
