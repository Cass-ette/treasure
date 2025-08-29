from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'
db = SQLAlchemy(app)

# 用户表
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_main_account = db.Column(db.Boolean, default=False)
    principal = db.Column(db.Float, default=0.0)  # 次级账户的投入本金
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    positions = db.relationship('Position', backref='user', lazy=True)
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    agreement = db.relationship('Agreement', backref='user', uselist=False)
    profits = db.relationship('Profit', backref='user', lazy=True)

# 基金表
class Fund(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    fund_type = db.Column(db.String(50))
    latest_nav = db.Column(db.Float)  # 最新净值
    nav_date = db.Column(db.DateTime)  # 净值日期
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    positions = db.relationship('Position', backref='fund', lazy=True)
    transactions = db.relationship('Transaction', backref='fund', lazy=True)

# 持仓表
class Position(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    fund_id = db.Column(db.Integer, db.ForeignKey('fund.id'), nullable=False)
    shares = db.Column(db.Float, default=0.0)  # 持仓份额
    cost_price = db.Column(db.Float)  # 成本价
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# 交易记录表
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    fund_id = db.Column(db.Integer, db.ForeignKey('fund.id'), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # buy/sell
    amount = db.Column(db.Float, nullable=False)  # 交易金额
    shares = db.Column(db.Float, nullable=False)  # 交易份额
    price = db.Column(db.Float, nullable=False)  # 交易价格
    fee = db.Column(db.Float, default=0.0)  # 手续费
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 分成协议表
class Agreement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    profit_share_ratio = db.Column(db.Float, nullable=False)  # 分成比例 (0-1之间)
    is_capital_protected = db.Column(db.Boolean, default=False)  # 是否保本
    capital_protection_ratio = db.Column(db.Float, default=1.0)  # 保本比例
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# 收益记录表
class Profit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    daily_profit = db.Column(db.Float, default=0.0)  # 当日盈亏
    cumulative_profit = db.Column(db.Float, default=0.0)  # 累计盈亏
    share_amount = db.Column(db.Float, default=0.0)  # 分成金额
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 创建数据库表
with app.app_context():
    db.create_all()
    
    # 创建主账户
    from werkzeug.security import generate_password_hash
    main_user = User(username='admin', password=generate_password_hash('admin123'), is_main_account=True)
    db.session.add(main_user)
    db.session.commit()
    
    print('数据库初始化完成！主账户已创建。')