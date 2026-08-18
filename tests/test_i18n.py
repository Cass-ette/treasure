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
