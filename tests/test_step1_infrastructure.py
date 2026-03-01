"""Step 1 tests: extensions & config"""
import os


def test_config_db_path():
    """Config 中的数据库路径应指向 instance/database.db"""
    from app.config import Config
    assert 'instance' in Config.SQLALCHEMY_DATABASE_URI
    assert Config.SQLALCHEMY_DATABASE_URI.startswith('sqlite:///')


def test_test_config_uses_memory_db():
    """TestConfig 应使用内存数据库"""
    from app.config import TestConfig
    assert TestConfig.SQLALCHEMY_DATABASE_URI == 'sqlite://'
    assert TestConfig.TESTING is True


def test_extensions_not_bound():
    """扩展实例创建时不应绑定到 app"""
    from app.extensions import db, login_manager
    # 验证可以正常导入，且 login_view 已预设
    assert login_manager.login_view == 'auth.login'
    # db 对象存在且是 SQLAlchemy 实例
    from flask_sqlalchemy import SQLAlchemy
    assert isinstance(db, SQLAlchemy)
