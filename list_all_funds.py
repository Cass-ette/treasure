from app import app, db
from app.models.fund import Fund

with app.app_context():
    print("数据库中的所有基金：")
    print("="*60)
    
    funds = Fund.query.all()
    for fund in funds:
        print(f"代码: {fund.code}")
        print(f"名称: {fund.name}")
        print(f"类型: {fund.fund_type}")
        print(f"最新净值: {fund.latest_nav}")
        print(f"净值日期: {fund.nav_date.strftime('%Y-%m-%d') if fund.nav_date else '无'}")
        print("-"*40)
    
    print(f"共 {len(funds)} 只基金")