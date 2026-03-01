# -*- coding: utf-8 -*-

"""用于检查基金净值数据的脚本"""

import sys
import os
import random
from datetime import datetime, timedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# 创建最小化的Flask应用
app = Flask(__name__)
# 使用绝对路径连接数据库，与generate_mock_data.py保持一致
basedir = os.path.abspath(os.path.dirname(__file__))
database_path = os.path.join(basedir, 'instance', 'database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 定义简化的模型类
class Fund(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    fund_type = db.Column(db.String(50))
    latest_nav = db.Column(db.Float)
    nav_date = db.Column(db.DateTime)

class FundNavHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fund_id = db.Column(db.Integer, db.ForeignKey('fund.id'), nullable=False)
    nav = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<FundNavHistory fund_id={self.fund_id} date={self.date.strftime("%Y-%m-%d")} nav={self.nav}>'
    
    @staticmethod
    def get_latest_navs(fund_id, days=30):
        """获取基金最近N个交易日的净值"""
        # 获取今天日期
        today = datetime.utcnow().date()
        
        # 查询最近N个交易日的净值，按日期降序排列
        navs = FundNavHistory.query.filter(
            FundNavHistory.fund_id == fund_id,
            FundNavHistory.date <= today
        ).order_by(FundNavHistory.date.desc()).limit(days).all()
        
        # 按日期升序返回
        return list(reversed(navs))

# 模拟FundService类的简化实现
class FundService:
    @staticmethod
    def calculate_30_day_average(fund_id):
        # 获取最近30天的净值
        latest_navs = FundNavHistory.get_latest_navs(fund_id)
        
        if not latest_navs:
            print(f"基金ID {fund_id}：没有足够的净值数据")
            return None
        
        # 计算平均值
        total_nav = sum(nav.nav for nav in latest_navs)
        average_nav = total_nav / len(latest_navs)
        
        return average_nav

# 生成模拟净值历史数据
def generate_mock_nav_history():
    with app.app_context():
        # 确保基金表存在且有数据
        funds = Fund.query.all()
        if not funds:
            print("没有找到基金数据，无法生成净值历史记录")
            return
        
        # 为每个基金生成最近60天的净值历史数据
        for fund in funds:
            # 检查是否已有净值历史数据
            existing_records = FundNavHistory.query.filter_by(fund_id=fund.id).count()
            if existing_records > 0:
                print(f"基金 {fund.name} 已有 {existing_records} 条净值历史记录，跳过生成")
                continue
            
            print(f"为基金 {fund.name} 生成净值历史记录...")
            
            # 基于fund.latest_nav生成随机波动的历史净值
            current_nav = fund.latest_nav
            for i in range(60):  # 生成60天的数据
                date = datetime.now().date() - timedelta(days=i)
                
                # 跳过周末
                if date.weekday() >= 5:  # 0=周一, 1=周二, ..., 4=周五, 5=周六, 6=周日
                    continue
                
                # 生成随机波动（±1.5%范围内）
                change_percent = random.uniform(-0.015, 0.015)
                current_nav = current_nav * (1 + change_percent)
                
                # 创建净值历史记录
                nav_history = FundNavHistory(
                    fund_id=fund.id,
                    nav=round(current_nav, 4),
                    date=datetime.combine(date, datetime.min.time())
                )
                db.session.add(nav_history)
            
            db.session.commit()
            print(f"  已生成 {FundNavHistory.query.filter_by(fund_id=fund.id).count()} 条净值历史记录")

# 检查基金数据
def check_fund_data():
    with app.app_context():
        # 确保表结构存在
        db.create_all()
        
        # 检查基金表数据
        funds = Fund.query.all()
        print(f"系统中共有 {len(funds)} 个基金")
        
        if not funds:
            print("没有基金数据，请先运行generate_mock_data.py生成基金数据")
            return
        
        # 检查是否有净值历史数据，如果没有则生成
        if FundNavHistory.query.count() == 0:
            print("没有找到净值历史数据，开始生成模拟数据...")
            generate_mock_nav_history()
        
        for fund in funds:
            print(f"\n基金代码: {fund.code}, 基金名称: {fund.name}")
            
            # 检查净值历史数据
            nav_histories = FundNavHistory.query.filter_by(fund_id=fund.id).all()
            print(f"  净值历史记录数量: {len(nav_histories)}")
            
            # 计算30日平均净值
            average_nav = FundService.calculate_30_day_average(fund.id)
            if average_nav:
                print(f"  30日平均净值: {average_nav:.4f}")
            else:
                print("  30日平均净值: 暂无数据")

# 主函数
if __name__ == "__main__":
    check_fund_data()