"""
Flask 扩展实例（解决循环导入问题）
所有扩展在此定义，在 create_app() 中绑定到 app
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
