#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
直接生成从上周五开始的基金净值历史数据

此脚本会自动生成从上周五开始到今天的基金净值历史数据，
只包含交易日数据（跳过周末），并在±1.0%范围内随机波动。
适合新项目快速初始化净值历史数据。
"""

import sys
import os
import random
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# 创建最小化的Flask应用
app = Flask(__name__)

# 使用与simple_app.py相同的数据库路径
database_path = 'e:/桌面/treasure/instance/database.db'
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

# 生成从上周五开始的净值历史数据
def generate_friday_start_nav_history():
    with app.app_context():
        # 确保表结构存在
        db.create_all()
        
        # 计算上周五的日期
        today = datetime.now().date()
        if today.weekday() <= 4:  # 如果今天是周一到周五
            days_ago = today.weekday() + 3  # 周一前推3天=上周五，周二前推4天，依此类推
        else:  # 如果今天是周六或周日
            days_ago = today.weekday() - 4  # 周六前推2天=上周五，周日前推1天
        start_date = today - timedelta(days=days_ago)
        
        print(f"\n===== 开始生成基金净值历史数据 =====")
        print(f"当前日期: {today.strftime('%Y-%m-%d')}")
        print(f"开始日期: {start_date.strftime('%Y-%m-%d')} (上周五)")
        print(f"使用数据库路径: {database_path}")
        
        # 获取所有基金
        funds = Fund.query.all()
        if not funds:
            print("错误: 没有找到基金数据")
            return
        
        print(f"共找到 {len(funds)} 只基金")
        
        # 遍历每只基金
        for fund in funds:
            print(f"\n处理基金: {fund.name} (代码: {fund.code}) 基金ID: {fund.id}")
            
            # 先清除该基金现有的历史记录
            existing_records = FundNavHistory.query.filter_by(fund_id=fund.id).all()
            for record in existing_records:
                db.session.delete(record)
            
            # 基于fund.latest_nav生成合理的历史净值
            current_nav = fund.latest_nav or 1.0  # 如果没有最新净值，使用1.0作为初始值
            
            # 生成从start_date到今天的净值数据（排除周末）
            current_date = start_date
            records_added = 0
            nav_values = []  # 存储生成的净值值，用于统计
            
            while current_date <= today:
                # 跳过周末
                if current_date.weekday() >= 5:  # 0=周一, 1=周二, ..., 4=周五, 5=周六, 6=周日
                    current_date += timedelta(days=1)
                    continue
                
                # 生成随机波动（±1.0%范围内，模拟实际基金波动）
                if records_added > 0:  # 第一条记录不波动
                    change_percent = random.uniform(-0.01, 0.01)
                    current_nav = current_nav * (1 + change_percent)
                    current_nav = round(current_nav, 4)  # 保留4位小数
                
                # 保存净值值以便后续统计
                nav_values.append(current_nav)
                
                # 创建净值历史记录
                nav_history = FundNavHistory(
                    fund_id=fund.id,
                    nav=current_nav,
                    date=datetime.combine(current_date, datetime.min.time())
                )
                db.session.add(nav_history)
                records_added += 1
                
                current_date += timedelta(days=1)
            
            db.session.commit()
            
            # 计算生成的净值数据统计信息
            if nav_values:
                avg_nav = sum(nav_values) / len(nav_values)
                min_nav = min(nav_values)
                max_nav = max(nav_values)
                print(f"  已生成 {records_added} 条净值历史记录")
                print(f"  平均净值: {avg_nav:.4f}")
                print(f"  最低净值: {min_nav:.4f}")
                print(f"  最高净值: {max_nav:.4f}")
                
                # 计算最近可用交易日的平均值
                latest_available_days = min(30, len(nav_values))  # 使用可用的交易日数据，最多30天
                recent_navs = nav_values[-latest_available_days:]
                recent_avg = sum(recent_navs) / len(recent_navs)
                print(f"  最近{latest_available_days}个交易日平均净值: {recent_avg:.4f}")
                print(f"  最新净值: {nav_values[-1]:.4f}")
                print(f"  平均与最新净值差异: {abs(recent_avg - nav_values[-1]):.4f} ({abs(recent_avg - nav_values[-1])/nav_values[-1]*100:.2f}%)")
            else:
                print(f"  未生成任何净值历史记录")
        
        print("\n===== 数据生成完成 =====")
        print("现在系统已经包含了从上周五开始的基金净值历史数据。")
        print("您可以运行以下命令测试前三十日平均净值API:")
        print("python test_average_nav_api.py")

if __name__ == "__main__":
    print("===== 基金净值历史数据生成工具 =====")
    print("此工具会自动生成从上周五开始到今天的基金净值历史数据")
    generate_friday_start_nav_history()