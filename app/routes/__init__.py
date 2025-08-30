from app.routes.auth import bp as auth_bp
from app.routes.dashboard import bp as dashboard_bp
from app.routes.accounts import bp as accounts_bp
from app.routes.funds import bp as funds_bp
from app.routes.transactions import bp as transactions_bp
from app.routes.reports import bp as reports_bp
from app.routes.image_processing import bp as image_processing_bp
from app.routes.auth import bp as auth_bp

# 重新导出蓝图，方便在 app/__init__.py 中注册
auth = auth_bp
accounts = accounts_bp
funds = funds_bp
transactions = transactions_bp
reports = reports_bp
dashboard = dashboard_bp
image_processing = image_processing_bp