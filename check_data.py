#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""检查数据库中的模拟数据"""

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

# 数据库URL
DATABASE_URL = 'sqlite:///database.db'

# 创建引擎
engine = create_engine(DATABASE_URL)

# 创建会话
Session = sessionmaker(bind=engine)
session = Session()

# 使用inspect来获取表信息
inspector = inspect(engine)

print("== 数据库表结构检查 ==")
# 获取所有表
all_tables = inspector.get_table_names()
print(f"找到的表: {all_tables}")

print("\n== 模拟数据统计 ==")

# 检查user表
if 'user' in all_tables:
    # 使用session.execute和text对象
    result = session.execute(text("SELECT COUNT(*) FROM user"))
    user_count = result.scalar()
    print(f"用户表记录数: {user_count}")
    
    # 查看所有用户名
    result = session.execute(text("SELECT username, is_main_account FROM user"))
    users = result.fetchall()
    print("用户列表:")
    for user in users:
        role = "主账户" if user[1] else "次级账户"
        print(f"- {user[0]} ({role})")

# 检查fund表
if 'fund' in all_tables:
    result = session.execute(text("SELECT COUNT(*) FROM fund"))
    fund_count = result.scalar()
    print(f"基金表记录数: {fund_count}")
    
    # 查看前3个基金
    result = session.execute(text("SELECT code, name FROM fund LIMIT 3"))
    funds = result.fetchall()
    print("部分基金:")
    for fund in funds:
        print(f"- {fund[0]}: {fund[1]}")

# 检查position表
if 'position' in all_tables:
    result = session.execute(text("SELECT COUNT(*) FROM position"))
    position_count = result.scalar()
    print(f"持仓表记录数: {position_count}")
    
    # 查看user1的持仓
    result = session.execute(text("""
    SELECT f.name, p.shares, p.cost_price 
    FROM position p 
    JOIN fund f ON p.fund_id = f.id 
    JOIN user u ON p.user_id = u.id 
    WHERE u.username = 'user1' LIMIT 3
    """))
    positions = result.fetchall()
    print("user1的部分持仓:")
    for pos in positions:
        print(f"- {pos[0]}: {pos[1]}股 @ ¥{pos[2]}")

# 检查profit表
if 'profit' in all_tables:
    result = session.execute(text("SELECT COUNT(*) FROM profit"))
    profit_count = result.scalar()
    print(f"盈亏记录表记录数: {profit_count}")
    
    # 查看最近的3条盈亏记录
    result = session.execute(text("""
    SELECT u.username, p.date, p.daily_profit, p.cumulative_profit 
    FROM profit p 
    JOIN user u ON p.user_id = u.id 
    ORDER BY p.date DESC LIMIT 3
    """))
    profits = result.fetchall()
    print("最近的盈亏记录:")
    for profit in profits:
        print(f"- {profit[0]} ({profit[1]}): 日盈亏 ¥{profit[2]}, 累计盈亏 ¥{profit[3]}")

# 检查数据库连接是否正常
print("\n== 数据库连接状态 ==")
try:
    # 尝试执行一个简单的查询
    result = session.execute(text("SELECT 1"))
    print("数据库连接正常")
except Exception as e:
    print(f"数据库连接异常: {e}")

# 关闭会话
session.close()