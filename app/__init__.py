"""App factory"""
import os
from flask import Flask
from app.extensions import db, login_manager


def create_app(config_object=None):
    """应用工厂函数"""
    app = Flask(__name__, template_folder='templates', static_folder='static')

    # 加载配置
    if config_object is None:
        config_object = os.environ.get('APP_CONFIG', 'app.config.Config')
    app.config.from_object(config_object)

    # 确保 instance/ 和 uploads/ 目录存在
    os.makedirs(os.path.join(app.root_path, '..', 'instance'), exist_ok=True)
    upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
    if upload_folder:
        os.makedirs(upload_folder, exist_ok=True)

    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)

    # 注册 user_loader
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # 注册蓝图
    from app.routes import register_blueprints
    register_blueprints(app)

    return app
