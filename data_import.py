#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""数据导入工具 - 用于导入真实数据到投资管理系统"""

import os
import sys
import csv
from datetime import datetime
import argparse

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 创建最小化的Flask应用以连接数据库
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

# 创建Flask应用和数据库连接
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
database_path = os.path.join(basedir, 'instance', 'database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 定义数据库模型 - 与db_init.py保持一致
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_main_account = db.Column(db.Boolean, default=False)
    principal = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    positions = db.relationship('Position', backref='user', lazy=True)
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    agreement = db.relationship('Agreement', backref='user', uselist=False)
    profits = db.relationship('Profit', backref='user', lazy=True)

class Fund(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    fund_type = db.Column(db.String(50))
    latest_nav = db.Column(db.Float)
    nav_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    positions = db.relationship('Position', backref='fund', lazy=True)
    transactions = db.relationship('Transaction', backref='fund', lazy=True)

class Position(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    fund_id = db.Column(db.Integer, db.ForeignKey('fund.id'), nullable=False)
    shares = db.Column(db.Float, default=0.0)
    cost_price = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    fund_id = db.Column(db.Integer, db.ForeignKey('fund.id'), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    shares = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    fee = db.Column(db.Float, default=0.0)
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Agreement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    profit_share_ratio = db.Column(db.Float, nullable=False)
    is_capital_protected = db.Column(db.Boolean, default=False)
    capital_protection_ratio = db.Column(db.Float, default=1.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Profit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    daily_profit = db.Column(db.Float, default=0.0)
    cumulative_profit = db.Column(db.Float, default=0.0)
    share_amount = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class DataImporter:
    """数据导入器类，提供各种数据导入功能"""
    
    @staticmethod
    def import_funds(file_path):
        """从CSV文件导入基金数据
        
        CSV格式要求：
        code,name,fund_type,latest_nav,nav_date
        示例：
        161725,招商中证白酒指数,股票型,1.5234,2023-06-15
        """
        try:
            with app.app_context():
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    count = 0
                    
                    for row in reader:
                        # 检查基金是否已存在
                        existing_fund = Fund.query.filter_by(code=row['code']).first()
                        if existing_fund:
                            # 更新现有基金数据
                            existing_fund.name = row['name']
                            existing_fund.fund_type = row.get('fund_type', '')
                            existing_fund.latest_nav = float(row.get('latest_nav', 0)) if row.get('latest_nav') else None
                            existing_fund.nav_date = datetime.strptime(row['nav_date'], '%Y-%m-%d') if row.get('nav_date') else datetime.now()
                        else:
                            # 创建新基金
                            fund = Fund(
                                code=row['code'],
                                name=row['name'],
                                fund_type=row.get('fund_type', ''),
                                latest_nav=float(row.get('latest_nav', 0)) if row.get('latest_nav') else None,
                                nav_date=datetime.strptime(row['nav_date'], '%Y-%m-%d') if row.get('nav_date') else datetime.now()
                            )
                            db.session.add(fund)
                        count += 1
                    
                    db.session.commit()
                    print(f"成功导入 {count} 条基金数据")
        except Exception as e:
            print(f"导入基金数据失败: {str(e)}")
    
    @staticmethod
    def import_sub_accounts(file_path):
        """从CSV文件导入次级账户数据
        
        CSV格式要求：
        username,password,principal
        示例：
        nailoong,user123,300000.00
        """
        try:
            with app.app_context():
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    count = 0
                    
                    for row in reader:
                        # 检查用户是否已存在
                        existing_user = User.query.filter_by(username=row['username']).first()
                        if existing_user:
                            # 更新现有用户数据
                            existing_user.password = generate_password_hash(row['password'])
                            existing_user.principal = float(row.get('principal', 0))
                        else:
                            # 创建新用户
                            user = User(
                                username=row['username'],
                                password=generate_password_hash(row['password']),
                                principal=float(row.get('principal', 0)),
                                is_main_account=False
                            )
                            db.session.add(user)
                        count += 1
                    
                    db.session.commit()
                    print(f"成功导入 {count} 个次级账户数据")
        except Exception as e:
            print(f"导入次级账户数据失败: {str(e)}")
    
    @staticmethod
    def import_positions(file_path):
        """从CSV文件导入持仓数据
        
        CSV格式要求：
        username,fund_code,shares,cost_price,created_at
        示例：
        nailoong,161725,10000,1.5234,2023-01-15
        """
        try:
            with app.app_context():
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    count = 0
                    
                    for row in reader:
                        # 获取用户和基金
                        user = User.query.filter_by(username=row['username']).first()
                        fund = Fund.query.filter_by(code=row['fund_code']).first()
                        
                        if not user:
                            print(f"警告: 未找到用户 '{row['username']}'，跳过该持仓数据")
                            continue
                        if not fund:
                            print(f"警告: 未找到基金 '{row['fund_code']}'，跳过该持仓数据")
                            continue
                        
                        # 检查持仓是否已存在
                        existing_position = Position.query.filter_by(user_id=user.id, fund_id=fund.id).first()
                        if existing_position:
                            # 更新现有持仓
                            existing_position.shares = float(row['shares'])
                            existing_position.cost_price = float(row['cost_price'])
                            existing_position.created_at = datetime.strptime(row['created_at'], '%Y-%m-%d') if row.get('created_at') else datetime.now()
                        else:
                            # 创建新持仓
                            position = Position(
                                user_id=user.id,
                                fund_id=fund.id,
                                shares=float(row['shares']),
                                cost_price=float(row['cost_price']),
                                created_at=datetime.strptime(row['created_at'], '%Y-%m-%d') if row.get('created_at') else datetime.now()
                            )
                            db.session.add(position)
                        count += 1
                    
                    db.session.commit()
                    print(f"成功导入 {count} 条持仓数据")
        except Exception as e:
            print(f"导入持仓数据失败: {str(e)}")
    
    @staticmethod
    def import_profits(file_path):
        """从CSV文件导入盈亏数据
        
        CSV格式要求：
        username,date,daily_profit,cumulative_profit
        示例：
        nailoong,2023-06-15,1500.50,15000.75
        """
        try:
            with app.app_context():
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    count = 0
                    
                    for row in reader:
                        # 获取用户
                        user = User.query.filter_by(username=row['username']).first()
                        if not user:
                            print(f"警告: 未找到用户 '{row['username']}'，跳过该盈亏数据")
                            continue
                        
                        # 创建盈亏记录
                        profit = Profit(
                            user_id=user.id,
                            date=datetime.strptime(row['date'], '%Y-%m-%d'),
                            daily_profit=float(row['daily_profit']),
                            cumulative_profit=float(row['cumulative_profit'])
                        )
                        db.session.add(profit)
                        count += 1
                    
                    db.session.commit()
                    print(f"成功导入 {count} 条盈亏数据")
        except Exception as e:
            print(f"导入盈亏数据失败: {str(e)}")

# 创建示例CSV模板文件
def create_template_files():
    """创建数据导入模板文件"""
    
    # 基金数据模板
    funds_template = """code,name,fund_type,latest_nav,nav_date
161725,招商中证白酒指数,股票型,1.5234,2023-06-15
003096,中欧医疗健康混合,混合型,2.8675,2023-06-15
"""
    
    # 次级账户数据模板
    accounts_template = """username,password,principal
nailoong,user123,300000.00
user2,user123,300000.00
"""
    
    # 持仓数据模板
    positions_template = """username,fund_code,shares,cost_price,created_at
nailoong,161725,10000,1.5234,2023-01-15
nailoong,003096,5000,2.8675,2023-02-20
"""
    
    # 盈亏数据模板
    profits_template = """username,date,daily_profit,cumulative_profit
nailoong,2023-06-15,1500.50,15000.75
nailoong,2023-06-16,2300.25,17301.00
"""
    
    # 写入模板文件
    templates_dir = os.path.join(basedir, 'data_templates')
    os.makedirs(templates_dir, exist_ok=True)
    
    with open(os.path.join(templates_dir, 'funds_template.csv'), 'w', encoding='utf-8') as f:
        f.write(funds_template)
    
    with open(os.path.join(templates_dir, 'accounts_template.csv'), 'w', encoding='utf-8') as f:
        f.write(accounts_template)
    
    with open(os.path.join(templates_dir, 'positions_template.csv'), 'w', encoding='utf-8') as f:
        f.write(positions_template)
    
    with open(os.path.join(templates_dir, 'profits_template.csv'), 'w', encoding='utf-8') as f:
        f.write(profits_template)
    
    print(f"数据导入模板已创建在 {templates_dir} 目录下")

def main():
    parser = argparse.ArgumentParser(description='投资管理系统数据导入工具')
    parser.add_argument('--create-templates', action='store_true', help='创建数据导入模板文件')
    parser.add_argument('--import-funds', type=str, help='导入基金数据的CSV文件路径')
    parser.add_argument('--import-accounts', type=str, help='导入次级账户数据的CSV文件路径')
    parser.add_argument('--import-positions', type=str, help='导入持仓数据的CSV文件路径')
    parser.add_argument('--import-profits', type=str, help='导入盈亏数据的CSV文件路径')
    
    args = parser.parse_args()
    
    if args.create_templates:
        create_template_files()
    elif args.import_funds:
        DataImporter.import_funds(args.import_funds)
    elif args.import_accounts:
        DataImporter.import_sub_accounts(args.import_accounts)
    elif args.import_positions:
        DataImporter.import_positions(args.import_positions)
    elif args.import_profits:
        DataImporter.import_profits(args.import_profits)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()