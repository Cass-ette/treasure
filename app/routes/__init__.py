"""注册所有蓝图"""
from app.routes.auth import bp as auth_bp
from app.routes.dashboard import bp as dashboard_bp
from app.routes.funds import bp as funds_bp
from app.routes.positions import bp as positions_bp
from app.routes.accounts import bp as accounts_bp
from app.routes.image import bp as image_bp
from app.routes.reports import bp as reports_bp
from app.routes.ai_assistant import bp as ai_bp


def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(funds_bp)
    app.register_blueprint(positions_bp)
    app.register_blueprint(accounts_bp)
    app.register_blueprint(image_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(ai_bp)
