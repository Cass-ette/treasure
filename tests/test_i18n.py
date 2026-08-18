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
