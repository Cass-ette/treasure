# -*- coding: utf-8 -*-

"""修复前三十日平均净值获取失败的问题"""

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

# 生成模拟净值历史数据
def generate_mock_nav_history():
    with app.app_context():
        # 确保表结构存在
        db.create_all()
        
        # 检查基金表数据
        funds = Fund.query.all()
        if not funds:
            print("没有找到基金数据，请先运行generate_mock_data.py生成基金数据")
            return
        
        # 为每个基金生成最近60天的净值历史数据
        for fund in funds:
            # 检查是否已有净值历史数据
            existing_records = FundNavHistory.query.filter_by(fund_id=fund.id).count()
            if existing_records >= 30:
                print(f"基金 {fund.name} 已有足够的净值历史记录 ({existing_records} 条)，跳过生成")
                continue
            
            print(f"为基金 {fund.name} 生成净值历史记录...")
            
            # 基于fund.latest_nav生成随机波动的历史净值
            current_nav = fund.latest_nav or 1.0  # 如果没有最新净值，使用1.0作为初始值
            
            # 如果现有记录不足30条，补充到至少30条
            records_to_add = max(30 - existing_records, 0)
            
            # 获取最后一条记录的日期作为起点
            last_record = FundNavHistory.query.filter_by(fund_id=fund.id).order_by(FundNavHistory.date.desc()).first()
            start_date = last_record.date.date() if last_record else datetime.now().date() - timedelta(days=60)
            
            days_added = 0
            days_checked = 0
            
            while days_added < records_to_add and days_checked < 120:  # 最多检查120天
                check_date = start_date - timedelta(days=days_checked)
                days_checked += 1
                
                # 跳过周末
                if check_date.weekday() >= 5:  # 0=周一, 1=周二, ..., 4=周五, 5=周六, 6=周日
                    continue
                
                # 检查该日期是否已有记录
                existing_date = FundNavHistory.query.filter(
                    FundNavHistory.fund_id == fund.id,
                    FundNavHistory.date == datetime.combine(check_date, datetime.min.time())
                ).first()
                
                if existing_date:
                    continue
                
                # 生成随机波动（±1.5%范围内）
                change_percent = random.uniform(-0.015, 0.015)
                current_nav = current_nav * (1 + change_percent)
                
                # 创建净值历史记录
                nav_history = FundNavHistory(
                    fund_id=fund.id,
                    nav=round(current_nav, 4),
                    date=datetime.combine(check_date, datetime.min.time())
                )
                db.session.add(nav_history)
                days_added += 1
            
            db.session.commit()
            total_records = FundNavHistory.query.filter_by(fund_id=fund.id).count()
            print(f"  已生成 {days_added} 条净值历史记录，总计 {total_records} 条记录")

# 检查并修复数据库路径配置
def check_and_fix_database_config():
    # 检查关键文件中的数据库路径配置
    files_to_check = [
        'app/__init__.py',
        'simple_app.py',
        'app/config.py',
    ]
    
    for file_path in files_to_check:
        full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_path)
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 检查是否包含instance/database.db路径
                if 'instance/database.db' not in content:
                    print(f"注意: 文件 {file_path} 可能使用了不同的数据库路径")
                else:
                    print(f"文件 {file_path} 使用了正确的数据库路径")
            except Exception as e:
                print(f"读取文件 {file_path} 时出错: {e}")
        else:
            print(f"文件 {file_path} 不存在")

# 检查前三十日平均净值计算功能
def check_30_day_average_calculation():
    with app.app_context():
        funds = Fund.query.all()
        print(f"\n=== 检查前三十日平均净值计算功能 ===")
        
        for fund in funds:
            # 获取最近30个交易日的净值
            nav_histories = FundNavHistory.query.filter(
                FundNavHistory.fund_id == fund.id
            ).order_by(FundNavHistory.date.desc()).limit(30).all()
            
            print(f"\n基金: {fund.code} - {fund.name}")
            print(f"净值历史记录数量: {len(nav_histories)}")
            
            if len(nav_histories) >= 30:
                # 计算平均值
                total_nav = sum(history.nav for history in nav_histories)
                average_nav = total_nav / len(nav_histories)
                print(f"前三十日平均净值: {average_nav:.4f}")
            else:
                print("历史数据不足30条，无法计算前三十日平均净值")

# 主函数
def main():
    print("===== 前三十日平均净值修复工具 =====")
    print(f"使用数据库路径: {database_path}")
    
    # 检查数据库配置
    check_and_fix_database_config()
    
    # 生成模拟净值历史数据
    generate_mock_nav_history()
    
    # 检查前三十日平均净值计算功能
    check_30_day_average_calculation()
    
    print("\n===== 修复完成 =====")
    print("现在前端页面应该可以正确显示前三十日平均净值了。")
    print("如果问题仍然存在，请刷新页面或清除浏览器缓存后重试。")

if __name__ == "__main__":
    main()