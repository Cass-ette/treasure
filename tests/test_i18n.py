"""i18n 测试：locale 探测、翻译、JS 字典注入、颜色模式."""
import pytest
from werkzeug.security import generate_password_hash


@pytest.fixture
def i18n_app():
    from app import create_app
    return create_app('app.config.TestConfig')


@pytest.fixture
def i18n_client(i18n_app):
    return i18n_app.test_client()


class TestGetLocale:
    def test_default_zh_when_no_signals(self, i18n_app):
        from app.babel import get_locale
        with i18n_app.test_request_context('/'):
            assert str(get_locale()) == 'zh_CN'

    def test_accept_language_en(self, i18n_app):
        from app.babel import get_locale
        with i18n_app.test_request_context('/', headers={'Accept-Language': 'en-US,en;q=0.9'}):
            assert str(get_locale()) == 'en_US'

    def test_accept_language_other_falls_back_zh(self, i18n_app):
        from app.babel import get_locale
        with i18n_app.test_request_context('/', headers={'Accept-Language': 'ja-JP,ja;q=0.9'}):
            assert str(get_locale()) == 'zh_CN'

    def test_cookie_overrides_accept_language(self, i18n_app):
        from app.babel import get_locale
        with i18n_app.test_request_context('/', headers={'Accept-Language': 'en-US,en;q=0.9'}):
            from flask import request
            request.cookies = {'locale': 'zh'}
            assert str(get_locale()) == 'zh_CN'


class TestSetLocale:
    def test_set_locale_sets_cookie(self, i18n_client):
        resp = i18n_client.post('/locale/set', data={'lang': 'en'})
        assert resp.status_code == 200
        assert resp.get_json() == {'ok': True}
        cookies = resp.headers.getlist('Set-Cookie')
        assert any('locale=en' in c for c in cookies)

    def test_set_locale_invalid_lang_returns_400(self, i18n_client):
        resp = i18n_client.post('/locale/set', data={'lang': 'fr'})
        assert resp.status_code == 400
        assert resp.get_json()['ok'] is False


class TestTemplateI18n:
    def test_js_dict_injected(self, i18n_client):
        resp = i18n_client.get('/login')
        assert resp.status_code == 200
        assert b'window.I18N' in resp.data

    def test_lang_attr_zh_default(self, i18n_client):
        resp = i18n_client.get('/login')
        assert resp.status_code == 200
        assert b'lang="zh-CN"' in resp.data or b"lang='zh-CN'" in resp.data

    def test_color_mode_cn_for_zh(self, i18n_client):
        resp = i18n_client.get('/login')
        assert b'data-color-mode="cn"' in resp.data

    def test_color_mode_intl_for_en(self, i18n_client):
        i18n_client.set_cookie('locale', 'en')
        resp = i18n_client.get('/login')
        assert b'data-color-mode="intl"' in resp.data
        assert b'lang="en-US"' in resp.data or b"lang='en-US'" in resp.data

    def test_locale_dropdown_present_on_login_page(self, i18n_client):
        """登录页（未登录）也能看到语言下拉。"""
        resp = i18n_client.get('/login')
        assert resp.status_code == 200
        assert b'setLocale' in resp.data


class TestPilotPages:
    def test_login_page_zh_default(self, i18n_client):
        resp = i18n_client.get('/login')
        assert '登录'.encode() in resp.data
        assert b'Sign in' not in resp.data

    def test_login_page_en(self, i18n_client):
        i18n_client.set_cookie('locale', 'en')
        resp = i18n_client.get('/login')
        assert b'Sign in' in resp.data

    def test_color_dropdown_translated(self, i18n_client):
        """颜色三态下拉在英文下也翻译。"""
        i18n_client.set_cookie('locale', 'en')
        resp = i18n_client.get('/login')
        assert b'Follow language' in resp.data


class TestReportsI18n:
    def test_reports_page_en(self, i18n_app, i18n_client):
        from app.models import User
        from app.extensions import db
        with i18n_app.app_context():
            db.create_all()
            u = User(username='i18nadmin', password=generate_password_hash('pw123', method='pbkdf2:sha256'), is_main_account=True)
            db.session.add(u)
            db.session.commit()
        i18n_client.post('/login', data={'username': 'i18nadmin', 'password': 'pw123'})
        i18n_client.set_cookie('locale', 'en')
        resp = i18n_client.get('/reports')
        assert resp.status_code == 200
        assert b'Report' in resp.data


class TestFundsI18n:
    def test_manage_funds_page_en(self, i18n_app, i18n_client):
        from app.models import User
        from app.extensions import db
        with i18n_app.app_context():
            db.create_all()
            u = User(username='i18nadmin2', password=generate_password_hash('pw123', method='pbkdf2:sha256'), is_main_account=True)
            db.session.add(u); db.session.commit()
        i18n_client.post('/login', data={'username': 'i18nadmin2', 'password': 'pw123'})
        i18n_client.set_cookie('locale', 'en')
        resp = i18n_client.get('/manage_funds')
        assert resp.status_code == 200
        assert b'Fund Management' in resp.data

    def test_crawl_fund_nav_page_en(self, i18n_app, i18n_client):
        from app.models import User
        from app.extensions import db
        with i18n_app.app_context():
            db.create_all()
            u = User(username='i18nadmin3', password=generate_password_hash('pw123', method='pbkdf2:sha256'), is_main_account=True)
            db.session.add(u); db.session.commit()
        i18n_client.post('/login', data={'username': 'i18nadmin3', 'password': 'pw123'})
        i18n_client.set_cookie('locale', 'en')
        resp = i18n_client.get('/crawl_fund_nav')
        assert resp.status_code == 200
        assert b'NAV Update' in resp.data


class TestPositionsI18n:
    def test_manage_positions_page_en(self, i18n_app, i18n_client):
        from app.models import User
        from app.extensions import db
        with i18n_app.app_context():
            db.create_all()
            u = User(username='i18nadmin4', password=generate_password_hash('pw123', method='pbkdf2:sha256'), is_main_account=True)
            db.session.add(u); db.session.commit()
        i18n_client.post('/login', data={'username': 'i18nadmin4', 'password': 'pw123'})
        i18n_client.set_cookie('locale', 'en')
        resp = i18n_client.get('/manage_positions')
        assert resp.status_code == 200
        assert b'Position Management' in resp.data


class TestImageI18n:
    def test_upload_page_en(self, i18n_app, i18n_client):
        from app.models import User
        from app.extensions import db
        with i18n_app.app_context():
            db.create_all()
            u = User(username='i18nadmin5', password=generate_password_hash('pw123', method='pbkdf2:sha256'), is_main_account=True)
            db.session.add(u); db.session.commit()
        i18n_client.post('/login', data={'username': 'i18nadmin5', 'password': 'pw123'})
        i18n_client.set_cookie('locale', 'en')
        resp = i18n_client.get('/image/upload')
        assert resp.status_code == 200
        assert b'Image Recognition Fund' in resp.data

    def test_history_page_en(self, i18n_app, i18n_client):
        from app.models import User
        from app.extensions import db
        with i18n_app.app_context():
            db.create_all()
            u = User(username='i18nadmin5', password=generate_password_hash('pw123', method='pbkdf2:sha256'), is_main_account=True)
            db.session.add(u); db.session.commit()
        i18n_client.post('/login', data={'username': 'i18nadmin5', 'password': 'pw123'})
        i18n_client.set_cookie('locale', 'en')
        resp = i18n_client.get('/image/history')
        assert resp.status_code == 200
        assert b'Image Recognition History' in resp.data


class TestAiChartsI18n:
    def test_ai_assistant_page_en(self, i18n_app, i18n_client):
        from app.models import User
        from app.extensions import db
        with i18n_app.app_context():
            db.create_all()
            u = User(username='i18nadmin6', password=generate_password_hash('pw123', method='pbkdf2:sha256'), is_main_account=True)
            db.session.add(u); db.session.commit()
        i18n_client.post('/login', data={'username': 'i18nadmin6', 'password': 'pw123'})
        i18n_client.set_cookie('locale', 'en')
        resp = i18n_client.get('/ai')
        assert resp.status_code == 200
        assert b'AI Analysis Assistant' in resp.data
        assert b'Export data' in resp.data

    def test_etf_chip_page_en(self, i18n_app, i18n_client):
        from app.models import User
        from app.extensions import db
        with i18n_app.app_context():
            db.create_all()
            u = User(username='i18nadmin7', password=generate_password_hash('pw123', method='pbkdf2:sha256'), is_main_account=True)
            db.session.add(u); db.session.commit()
        i18n_client.post('/login', data={'username': 'i18nadmin7', 'password': 'pw123'})
        i18n_client.set_cookie('locale', 'en')
        # symbol 校验失败会 404，但 404 页面不含筹码峰文案；直接断言英文文案出现在 200 页面
        # 用 mock 不值得，改为检查模板渲染：通过 test_request_context 渲染模板
        with i18n_app.test_request_context('/charts/etf/562500/chip', headers={'Accept-Language': 'en-US'}):
            from flask import render_template
            from unittest.mock import patch
            with patch('app.routes.charts.quote_provider.fetch_etf_quote', return_value=None), \
                 patch('app.routes.charts.quote_provider.get_cached_etf_name', return_value='Robot ETF'), \
                 patch('app.routes.charts._validate_symbol', return_value='SH562500'):
                html = render_template('charts/etf_chip.html', symbol='SH562500', raw_symbol='562500', quote=None, etf_name='Robot ETF')
        assert b'K-line + Chip Distribution' in html.encode()
        assert b'Profit ratio' in html.encode()


class TestSpecCoverage:
    """spec 覆盖：I18N 注入兜底 / flash 翻译 / jsonify 翻译 / .mo 同步."""

    def test_missing_key_falls_back(self, i18n_client):
        """I18N 字典注入且已翻译键有非空英文值；缺失键兜底由 JS t() 保证。"""
        import json
        import re
        i18n_client.set_cookie('locale', 'en')
        resp = i18n_client.get('/login')
        data = resp.data.decode()
        m = re.search(r'window\.I18N = (\{.*?\});', data, re.S)
        assert m, 'window.I18N 未注入'
        d = json.loads(m.group(1))
        # 已翻译键（登录）应有非空英文值
        assert d.get('登录'), '登录 键缺失或为空'
        assert d['登录'] != '登录'
        assert d['登录'] == 'Sign in'
        # 缺失键：字典无此键，JS t() 应回退到键本身
        assert '__nonexistent_key__' not in d
        js = i18n_client.get('/static/js/i18n.js').data.decode()
        assert 'return (window.I18N || {})[k] || k' in js, 'JS t() 兜底逻辑缺失'

    def test_flash_messages_translated(self, i18n_app, i18n_client):
        from app.extensions import db
        from app.models import User
        with i18n_app.app_context():
            db.create_all()
            u = User(username='i18nflash', password=generate_password_hash('pw123', method='pbkdf2:sha256'), is_main_account=True)
            db.session.add(u)
            db.session.commit()
        i18n_client.set_cookie('locale', 'en')
        resp = i18n_client.post('/login', data={'username': 'i18nflash', 'password': 'wrong'}, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Invalid username or password' in resp.data

    def test_json_api_messages_translated(self, i18n_app, i18n_client):
        """funds.py /get_fund_info 对非法代码返回 jsonify 消息，en 下不含中文。"""
        from app.extensions import db
        from app.models import User
        with i18n_app.app_context():
            db.create_all()
            u = User(username='i18njson', password=generate_password_hash('pw123', method='pbkdf2:sha256'), is_main_account=True)
            db.session.add(u)
            db.session.commit()
        i18n_client.post('/login', data={'username': 'i18njson', 'password': 'pw123'})
        i18n_client.set_cookie('locale', 'en')
        resp = i18n_client.get('/get_fund_info', query_string={'code': 'abc'})
        assert resp.status_code == 200
        body = resp.get_json()
        assert body['success'] is False
        assert body['message'] == 'Fund code must be 6 digits'
        assert not any('一' <= ch <= '鿿' for ch in body['message'])

    def test_po_mo_synced(self):
        """抽查关键 msgid 在 en 的 .mo 里存在且已翻译（防漏编译）。"""
        import pathlib
        from babel.messages.mofile import read_mo
        from app.babel import _ensure_mo_compiled
        _ensure_mo_compiled()
        mo_path = pathlib.Path(__file__).parent.parent / 'app/translations/en_US/LC_MESSAGES/messages.mo'
        assert mo_path.exists(), '.mo 未生成'
        with open(mo_path, 'rb') as f:
            catalog = read_mo(f)
        assert '登录' in catalog
        assert '用户名' in catalog
        assert catalog['登录'].string == 'Sign in'
        assert catalog['用户名'].string == 'Username'
        assert catalog['用户名或密码错误'].string == 'Invalid username or password'
