#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""生成模拟数据的脚本 - 不依赖akshare的简化版本"""

import random
from datetime import datetime, timedelta
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 避免加载完整的应用，直接创建必要的数据库连接
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

# 创建最小化的Flask应用
app = Flask(__name__)
# 使用绝对路径连接数据库
import os
basedir = os.path.abspath(os.path.dirname(__file__))
database_path = os.path.join(basedir, 'instance', 'database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 定义简化的模型类 - 表名与db_init.py保持一致
class User(db.Model):
    # 不指定__tablename__，让SQLAlchemy使用默认的单数形式
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_main_account = db.Column(db.Boolean, default=False)
    principal = db.Column(db.Float, default=0.0)
    positions = db.relationship('Position', backref='user', lazy=True)
    profits = db.relationship('Profit', backref='user', lazy=True)

class Fund(db.Model):
    # 不指定__tablename__，让SQLAlchemy使用默认的单数形式
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    fund_type = db.Column(db.String(50))
    latest_nav = db.Column(db.Float)
    nav_date = db.Column(db.DateTime)
    positions = db.relationship('Position', backref='fund', lazy=True)

class Position(db.Model):
    # 不指定__tablename__，让SQLAlchemy使用默认的单数形式
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    fund_id = db.Column(db.Integer, db.ForeignKey('fund.id'), nullable=False)
    shares = db.Column(db.Float, default=0.0)
    cost_price = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Profit(db.Model):
    # 不指定__tablename__，让SQLAlchemy使用默认的单数形式
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    daily_profit = db.Column(db.Float, default=0.0)
    cumulative_profit = db.Column(db.Float, default=0.0)

# 确保在应用上下文中运行
with app.app_context():
    print("开始生成模拟数据...")
    
    # 1. 生成基金数据（如果不存在）
    if Fund.query.count() == 0:
        funds = [
            {
                'code': '161725',
                'name': '招商中证白酒指数',
                'fund_type': '股票型',
                'latest_nav': 1.5234,
                'nav_date': datetime.now()
            },
            {
                'code': '003096',
                'name': '中欧医疗健康混合',
                'fund_type': '混合型',
                'latest_nav': 2.8675,
                'nav_date': datetime.now()
            },
            {
                'code': '001550',
                'name': '天弘中证银行指数',
                'fund_type': '指数型',
                'latest_nav': 1.1245,
                'nav_date': datetime.now()
            },
            {
                'code': '000166',
                'name': '嘉实环保低碳股票',
                'fund_type': '股票型',
                'latest_nav': 3.2567,
                'nav_date': datetime.now()
            },
            {
                'code': '000939',
                'name': '中银医疗保健混合',
                'fund_type': '混合型',
                'latest_nav': 2.1890,
                'nav_date': datetime.now()
            }
        ]
        
        for fund_data in funds:
            fund = Fund(**fund_data)
            db.session.add(fund)
        
        db.session.commit()
        print(f"已生成 {len(funds)} 条基金数据")
    else:
        print("基金数据已存在，跳过生成")
    
    # 2. 获取admin用户
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        print("未找到admin用户，请先运行create_admin.py创建管理员账户")
        exit()
    
    # 3. 创建次级账户（如果不存在）
    if User.query.filter_by(is_main_account=False).count() == 0:
        sub_accounts = [
            {
                'username': 'user1',
                'password': generate_password_hash('user123'),
                'principal': 50000.0,
                'is_main_account': False
            },
            {
                'username': 'user2',
                'password': generate_password_hash('user123'),
                'principal': 80000.0,
                'is_main_account': False
            },
            {
                'username': 'user3',
                'password': generate_password_hash('user123'),
                'principal': 30000.0,
                'is_main_account': False
            }
        ]
        
        for account_data in sub_accounts:
            user = User(**account_data)
            db.session.add(user)
        
        db.session.commit()
        print(f"已生成 {len(sub_accounts)} 个次级账户")
    else:
        print("次级账户已存在，跳过生成")
    
    # 4. 获取所有用户和基金
    all_users = User.query.all()
    all_funds = Fund.query.all()
    
    # 5. 生成持仓数据（如果不存在）
    if Position.query.count() == 0:
        for user in all_users:
            # 为每个用户生成2-4个不同的持仓
            num_positions = random.randint(2, 4)
            selected_funds = random.sample(all_funds, num_positions)
            
            for fund in selected_funds:
                # 根据用户本金计算持仓份额
                max_investment = user.principal * random.uniform(0.1, 0.4) if user.principal else 10000
                shares = max_investment / fund.latest_nav
                
                position = Position(
                    user_id=user.id,
                    fund_id=fund.id,
                    shares=shares,
                    cost_price=fund.latest_nav,
                    created_at=datetime.now() - timedelta(days=random.randint(30, 180))
                )
                db.session.add(position)
        
        db.session.commit()
        print(f"已生成 {Position.query.count()} 条持仓数据")
    else:
        print("持仓数据已存在，跳过生成")
    
    # 6. 生成盈亏记录数据（最近30天）
    days_to_generate = 30
    
    # 检查是否已经有盈亏记录
    has_profit_records = Profit.query.count() > 0
    
    for i in range(days_to_generate):
        date = datetime.now().date() - timedelta(days=i)
        
        for user in all_users:
            # 检查该用户在该日期是否已有盈亏记录
            if has_profit_records and Profit.query.filter_by(user_id=user.id, date=date).first():
                continue
            
            # 生成随机盈亏数据
            # 基于用户本金的±5%范围内的随机值
            principal = user.principal if user.principal else 10000
            daily_profit = principal * random.uniform(-0.05, 0.05)
            
            # 确保盈亏数据有一定的连续性
            if i > 0:
                prev_date = date + timedelta(days=1)
                prev_profit = Profit.query.filter_by(user_id=user.id, date=prev_date).first()
                if prev_profit:
                    # 新的盈亏在旧盈亏的±30%范围内波动
                    daily_profit = prev_profit.daily_profit * random.uniform(0.7, 1.3)
            
            profit = Profit(
                user_id=user.id,
                date=datetime.combine(date, datetime.min.time()),
                daily_profit=daily_profit,
                cumulative_profit=daily_profit  # 简化处理，实际应累计计算
            )
            db.session.add(profit)
        
    db.session.commit()
    print(f"已生成 {Profit.query.count()} 条盈亏记录数据")
    
    print("模拟数据生成完成！")
    print("\n可用账户信息：")
    print("- 管理员账户：username=admin, password=admin123")
    for user in User.query.filter_by(is_main_account=False).all():
        print(f"- 次级账户：username={user.username}, password=user123")