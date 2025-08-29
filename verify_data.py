import os
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from simple_app import User, Fund, Position, Profit

# 使用与主应用相同的数据库连接
basedir = os.path.abspath(os.path.dirname(__file__))
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'database.db')

# 创建数据库引擎和会话
engine = create_engine(SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()

print("=== 验证投资管理系统数据 ===")

# 检查用户数据
print("\n1. 用户数据：")
users = session.query(User).all()
print(f"总用户数: {len(users)}")
for user in users:
        role = "管理员账户" if user.is_main_account else "次级账户"
        print(f"- {user.username} (类型: {role}) - 本金: {user.principal}元")

# 检查基金数据
print("\n2. 基金数据：")
funds = session.query(Fund).all()
print(f"总基金数: {len(funds)}")
for fund in funds[:3]:  # 只显示前3个基金
    print(f"- {fund.name} ({fund.code}) - 类型: {fund.fund_type} - 最新净值: {fund.latest_nav}")
if len(funds) > 3:
    print(f"... 还有 {len(funds) - 3} 个基金")

# 检查持仓数据
print("\n3. 持仓数据：")
positions = session.query(Position).all()
print(f"总持仓数: {len(positions)}")
for position in positions[:3]:  # 只显示前3个持仓
    fund = session.query(Fund).get(position.fund_id)
    print(f"- 用户: {position.user_id} - 基金: {fund.name} - 份额: {position.shares} - 成本价: {position.cost_price}")
if len(positions) > 3:
    print(f"... 还有 {len(positions) - 3} 个持仓")

# 检查盈亏记录
print("\n4. 盈亏记录：")
profits = session.query(Profit).all()
print(f"总盈亏记录数: {len(profits)}")

# 按日期统计盈亏记录
if profits:
    min_date = session.query(func.min(Profit.date)).scalar()
    max_date = session.query(func.max(Profit.date)).scalar()
    print(f"盈亏记录日期范围: {min_date} 至 {max_date}")

print("\n=== 数据验证完成 ===")
session.close()