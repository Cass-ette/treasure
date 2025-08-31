from app import app, db
from app.models.fund import Fund
from datetime import datetime

# 要检查的基金代码
fund_codes = ['020404', '006328', '270042']

with app.app_context():
    print("检查基金日期信息...")
    print("="*60)
    
    # 遍历所有基金
    for fund_code in fund_codes:
        fund = Fund.query.filter_by(code=fund_code).first()
        if fund:
            print(f"基金代码: {fund.code}")
            print(f"基金名称: {fund.name}")
            print(f"基金类型: {fund.fund_type}")
            print(f"最新净值: {fund.latest_nav}")
            print(f"净值日期: {fund.nav_date.strftime('%Y-%m-%d') if fund.nav_date else '无'}")
            print(f"是否使用今天的日期: {'是' if fund.nav_date and fund.nav_date.date() == datetime.now().date() else '否'}")
        else:
            print(f"基金 {fund_code} 不存在于数据库中")
        print("-"*40)
    
    # 显示当前日期信息
    today = datetime.now().date()
    print(f"当前日期: {today}")
    print(f"星期几: {today.strftime('%A')}")
    print("="*60)