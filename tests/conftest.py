"""tests/conftest.py — shared fixtures"""
import pytest
import sys
import os

# 确保项目根目录在 path 中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def app():
    """创建测试用 app 实例"""
    from app import create_app
    app = create_app('app.config.TestConfig')
    yield app


@pytest.fixture
def client(app):
    """Flask 测试客户端"""
    return app.test_client()


@pytest.fixture
def db(app):
    """初始化/清理测试数据库"""
    from app.extensions import db as _db
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.rollback()
        _db.drop_all()
