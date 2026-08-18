"""Babel i18n 初始化：locale 探测 + JS 字典导出 + .mo 自动编译."""
from pathlib import Path

from flask import request
from flask_babel import Babel, get_translations

babel = Babel()

TRANSLATIONS_DIR = Path(__file__).parent / 'translations'
LOCALES = ('zh_CN', 'en_US')


def get_locale():
    """cookie 'locale' 优先；否则 Accept-Language（en* → en_US，其余 → zh_CN）。"""
    cookie = request.cookies.get('locale')
    if cookie == 'zh':
        return 'zh_CN'
    if cookie == 'en':
        return 'en_US'
    best = request.accept_languages.best_match(['zh', 'en'], default='zh')
    return 'en_US' if best == 'en' else 'zh_CN'


def _ensure_mo_compiled():
    """.po 比 .mo 新（或 .mo 缺失）时自动编译，免手工 pybabel compile。"""
    from babel.messages.pofile import read_po
    from babel.messages.mofile import write_mo

    for locale in LOCALES:
        po = TRANSLATIONS_DIR / locale / 'LC_MESSAGES' / 'messages.po'
        mo = TRANSLATIONS_DIR / locale / 'LC_MESSAGES' / 'messages.mo'
        if not po.exists():
            continue
        if mo.exists() and mo.stat().st_mtime >= po.stat().st_mtime:
            continue
        with open(po, 'rb') as f:
            catalog = read_po(f)
        with open(mo, 'wb') as f:
            write_mo(f, catalog)


def js_translations():
    """当前 locale 的 {msgid: msgstr} 字典，注入 window.I18N。"""
    _ensure_mo_compiled()
    cat = get_translations()
    out = {}
    for msgid, msgstr in getattr(cat, '_catalog', {}).items():
        if isinstance(msgid, str) and msgid:
            out[msgid] = msgstr or msgid
    return out


def init_babel(app):
    _ensure_mo_compiled()
    app.config['BABEL_TRANSLATION_DIRECTORIES'] = str(TRANSLATIONS_DIR)
    babel.init_app(app, locale_selector=get_locale)

    # 模板里可用 {{ js_translations() }}
    app.jinja_env.globals['js_translations'] = js_translations

    @app.context_processor
    def _inject_locale():
        return {'current_locale': get_locale()[:2]}
