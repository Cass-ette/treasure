from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

# 导入Flask
from flask import Flask

app = Flask(__name__)
app.config.from_object('app.config.Config')

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

# 导入模型
from app.models import User, Fund, Position, Transaction, Agreement, Profit, FundNavHistory

# 导入路由蓝图
from app.routes import auth, accounts, funds, transactions, reports, dashboard, image_processing

# 用户加载器回调函数，用于 Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 注册蓝图
def register_blueprints():
    app.register_blueprint(auth)
    app.register_blueprint(dashboard)
    app.register_blueprint(accounts)
    app.register_blueprint(funds)
    app.register_blueprint(transactions)
    app.register_blueprint(reports)
    app.register_blueprint(image_processing)

register_blueprints()