#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
重置基金净值历史数据工具

此工具用于：
1. 查看当前所有基金的净值历史数据
2. 清除所有模拟生成的净值历史数据
3. 重新生成合理的净值历史数据（基于实际开始日期）

使用说明：
- 运行此脚本后，根据提示选择操作
- 如果选择清除数据，只会保留实际获取的最新净值数据
- 如果选择重新生成数据，可以指定开始日期
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

# 显示基金净值历史数据信息
def show_nav_history_info():
    with app.app_context():
        # 确保表结构存在
        db.create_all()
        
        # 检查基金表数据
        funds = Fund.query.all()
        if not funds:
            print("没有找到基金数据")
            return
        
        print(f"\n=== 当前基金净值历史数据信息 ===")
        for fund in funds:
            # 统计该基金的净值历史记录数量
            nav_records = FundNavHistory.query.filter_by(fund_id=fund.id).count()
            
            # 获取最早和最晚的记录日期
            earliest_record = FundNavHistory.query.filter_by(fund_id=fund.id).order_by(FundNavHistory.date.asc()).first()
            latest_record = FundNavHistory.query.filter_by(fund_id=fund.id).order_by(FundNavHistory.date.desc()).first()
            
            earliest_date = earliest_record.date.strftime('%Y-%m-%d') if earliest_record else '无'
            latest_date = latest_record.date.strftime('%Y-%m-%d') if latest_record else '无'
            
            print(f"基金名称: {fund.name} (代码: {fund.code})")
            print(f"  净值历史记录数量: {nav_records} 条")
            print(f"  最早记录日期: {earliest_date}")
            print(f"  最晚记录日期: {latest_date}")
            print(f"  最新净值: {fund.latest_nav}")
            print(f"  最新净值日期: {fund.nav_date.strftime('%Y-%m-%d') if fund.nav_date else '无'}")
            print("-")

# 清除所有模拟生成的净值历史数据
def clear_mock_nav_history():
    with app.app_context():
        funds = Fund.query.all()
        
        print(f"\n=== 开始清除模拟净值历史数据 ===")
        
        for fund in funds:
            # 查询并删除所有净值历史记录，但保留最新净值
            records = FundNavHistory.query.filter_by(fund_id=fund.id).all()
            deleted_count = len(records)
            
            for record in records:
                db.session.delete(record)
            
            db.session.commit()
            
            print(f"已清除基金 {fund.name} 的 {deleted_count} 条净值历史记录")
            print(f"保留了基金的最新净值: {fund.latest_nav} (日期: {fund.nav_date.strftime('%Y-%m-%d') if fund.nav_date else '无'})")

# 重新生成合理的净值历史数据（基于实际开始日期）
def regenerate_reasonable_nav_history(start_date=None, max_days=60):
    with app.app_context():
        # 如果用户没有指定开始日期，默认为上周五
        if not start_date:
            today = datetime.now().date()
            # 计算上周五的日期
            if today.weekday() <= 4:  # 如果今天是周一到周五
                days_ago = today.weekday() + 3  # 周一前推3天=上周五，周二前推4天，依此类推
            else:  # 如果今天是周六或周日
                days_ago = today.weekday() - 4  # 周六前推2天=上周五，周日前推1天
            start_date = today - timedelta(days=days_ago)
        
        print(f"\n=== 重新生成净值历史数据 ===")
        print(f"使用开始日期: {start_date.strftime('%Y-%m-%d')}")
        
        funds = Fund.query.all()
        for fund in funds:
            # 先清除该基金现有的历史记录
            existing_records = FundNavHistory.query.filter_by(fund_id=fund.id).all()
            for record in existing_records:
                db.session.delete(record)
            
            print(f"\n为基金 {fund.name} 重新生成净值历史记录...")
            
            # 基于fund.latest_nav生成合理的历史净值
            current_nav = fund.latest_nav or 1.0  # 如果没有最新净值，使用1.0作为初始值
            
            # 生成从start_date到今天的净值数据（排除周末）
            current_date = start_date
            today = datetime.now().date()
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
                
                # 计算最近可用交易日的平均值（如果有多个交易日）
                if len(nav_values) > 1:
                    latest_available_days = min(30, len(nav_values))  # 使用可用的交易日数据，最多30天
                    recent_navs = nav_values[-latest_available_days:]
                    recent_avg = sum(recent_navs) / len(recent_navs)
                    print(f"  最近{latest_available_days}个交易日平均净值: {recent_avg:.4f}")
                    print(f"  最新净值: {nav_values[-1]:.4f}")
                    print(f"  平均与最新净值差异: {abs(recent_avg - nav_values[-1]):.4f} ({abs(recent_avg - nav_values[-1])/nav_values[-1]*100:.2f}%)")
                else:
                    print(f"  最新净值: {nav_values[-1]:.4f}")
            else:
                print(f"  未生成任何净值历史记录")
        
        print("\n=== 数据生成完成 ===")
        print("现在您可以运行测试脚本来验证前三十日平均净值API的行为。")
        print("注意：由于是新项目，数据量可能不足30个交易日，系统会使用所有可用的交易日数据计算平均值。")

# 主函数
def main():
    print("===== 基金净值历史数据重置工具 =====")
    print(f"使用数据库路径: {database_path}")
    print(f"当前日期: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"今天是周{['一', '二', '三', '四', '五', '六', '日'][datetime.now().weekday()]}")
    
    # 显示当前数据信息
    show_nav_history_info()
    
    # 询问用户操作选择
    print("\n请选择操作:")
    print("1. 清除所有净值历史数据（只保留最新净值）")
    print("2. 重新生成合理的净值历史数据（使用默认配置）")
    print("3. 自定义重新生成净值历史数据（可指定参数）")
    print("4. 退出")
    
    choice = input("请输入选择 (1-4): ")
    
    if choice == '1':
        confirm = input("确定要清除所有净值历史数据吗？(y/n): ")
        if confirm.lower() == 'y':
            clear_mock_nav_history()
            print("\n清除完成！现在系统将只显示基金的最新净值。")
            print("后续系统会自动获取并存储每日的真实净值数据。")
        else:
            print("操作已取消。")
    elif choice == '2':
        # 使用默认配置重新生成数据（从上周五开始）
        print("\n使用默认配置重新生成净值历史数据...")
        print("- 开始日期: 上周五")
        print("- 最大天数: 60天")
        print("- 只生成交易日数据（跳过周末）")
        print("- 净值波动范围: ±1.0%")
        
        confirm = input("继续吗？(y/n): ")
        if confirm.lower() == 'y':
            regenerate_reasonable_nav_history()
        else:
            print("操作已取消。")
    elif choice == '3':
        # 自定义重新生成数据
        print("\n自定义重新生成净值历史数据")
        
        # 选择开始日期
        use_custom_date = input("是否要指定开始日期？(y/n，默认为上周五): ")
        start_date = None
        
        if use_custom_date.lower() == 'y':
            date_str = input("请输入开始日期 (格式: YYYY-MM-DD): ")
            try:
                start_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                # 验证开始日期是否合理
                today = datetime.now().date()
                if start_date > today:
                    print("开始日期不能晚于今天，使用默认的上周五。")
                    start_date = None
                elif (today - start_date).days > 365:
                    print("开始日期过于久远，使用默认的上周五。")
                    start_date = None
            except ValueError:
                print("日期格式不正确，使用默认的上周五。")
                start_date = None
        
        # 选择最大天数
        use_custom_max_days = input("是否要指定最大天数？(y/n，默认为60天): ")
        max_days = 60
        
        if use_custom_max_days.lower() == 'y':
            days_str = input("请输入最大天数 (1-365，默认为60天): ")
            try:
                days_input = int(days_str)
                if 1 <= days_input <= 365:
                    max_days = days_input
                else:
                    print("天数必须在1-365之间，使用默认值60天。")
            except ValueError:
                print("天数格式不正确，使用默认值60天。")
        
        # 显示配置摘要
        print("\n配置摘要:")
        print(f"- 开始日期: {'自定义' if start_date else '上周五'}")
        if start_date:
            print(f"  - 具体日期: {start_date.strftime('%Y-%m-%d')}")
        print(f"- 最大天数: {max_days}天")
        print("- 只生成交易日数据（跳过周末）")
        print("- 净值波动范围: ±1.0%")
        
        confirm = input("继续吗？(y/n): ")
        if confirm.lower() == 'y':
            regenerate_reasonable_nav_history(start_date, max_days)
        else:
            print("操作已取消。")
    elif choice == '4':
        print("已退出。")
        return
    else:
        print("无效的选择，已退出。")
    
    # 显示操作后的结果
    if choice != '4':  # 只有在不是退出的情况下才显示结果
        print("\n=== 操作后的基金数据信息 ===")
        show_nav_history_info()
    
    print("\n===== 操作完成 =====")
    print("\n使用说明:")
    print("1. 若要测试前三十日平均净值API，请运行: python test_average_nav_api.py")
    print("2. 对于新基金，系统会使用所有可用的交易日数据计算平均值")
    print("3. 系统会自动在交易日更新基金净值数据")

if __name__ == "__main__":
    main()