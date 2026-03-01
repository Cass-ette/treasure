#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""生成模拟数据的脚本"""

import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import User, Fund, Position, Profit

app = create_app()

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
            num_positions = random.randint(2, 4)
            selected_funds = random.sample(all_funds, num_positions)

            for fund in selected_funds:
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
    has_profit_records = Profit.query.count() > 0

    for i in range(days_to_generate):
        date = datetime.now().date() - timedelta(days=i)

        for user in all_users:
            if has_profit_records and Profit.query.filter_by(user_id=user.id, date=date).first():
                continue

            principal = user.principal if user.principal else 10000
            daily_profit = principal * random.uniform(-0.05, 0.05)

            if i > 0:
                prev_date = date + timedelta(days=1)
                prev_profit = Profit.query.filter_by(user_id=user.id, date=prev_date).first()
                if prev_profit:
                    daily_profit = prev_profit.daily_profit * random.uniform(0.7, 1.3)

            profit = Profit(
                user_id=user.id,
                date=datetime.combine(date, datetime.min.time()),
                daily_profit=daily_profit,
                cumulative_profit=daily_profit
            )
            db.session.add(profit)

    db.session.commit()
    print(f"已生成 {Profit.query.count()} 条盈亏记录数据")

    print("模拟数据生成完成！")
    print("\n可用账户信息：")
    print("- 管理员账户：username=admin, password=admin123")
    for user in User.query.filter_by(is_main_account=False).all():
        print(f"- 次级账户：username={user.username}, password=user123")
