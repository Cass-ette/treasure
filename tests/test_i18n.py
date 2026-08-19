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
