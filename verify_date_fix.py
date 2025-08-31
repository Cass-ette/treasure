from app import app, db
from app.services.fund_service import FundService
from app.models.fund import Fund
from datetime import datetime

# 要测试的基金代码
fund_codes = ['020404', '006328', '270042']

with app.app_context():
    print("验证日期提取修复效果...")
    print("="*80)
    
    # 首先，为测试添加这些基金
    for fund_code in fund_codes:
        # 检查基金是否已存在
        existing_fund = Fund.query.filter_by(code=fund_code).first()
        if not existing_fund:
            # 基金类型和名称信息
            fund_info = {
                '020404': {'name': '易方达新常态灵活配置混合', 'type': '普通基金'},
                '006328': {'name': '易方达中证海外互联网50ETF联接', 'type': 'QDII基金'},
                '270042': {'name': '广发纳斯达克100ETF联接', 'type': 'QDII基金'}
            }
            info = fund_info.get(fund_code, {'name': f'基金{fund_code}', 'type': '未知'})
            
            # 创建基金实例
            FundService.add_fund(fund_code, info['name'], info['type'])
            print(f"添加基金: {info['name']}({fund_code})")
    
    print("\n开始更新基金净值和日期...")
    
    # 尝试更新这些基金的净值和日期
    for fund_code in fund_codes:
        print(f"\n更新基金: {fund_code}")
        # 找到基金对象
        fund_model = Fund.query.filter_by(code=fund_code).first()
        if fund_model:
            # 更新基金净值
            result = FundService.update_fund_nav(fund_model.id)
            print(f"更新结果: {'成功' if result else '失败'}")
            
            # 刷新基金对象以获取最新数据
            db.session.refresh(fund_model)
            
            # 打印更新后的信息
            print(f"基金代码: {fund_model.code}")
            print(f"基金名称: {fund_model.name}")
            print(f"最新净值: {fund_model.latest_nav}")
            print(f"净值日期: {fund_model.nav_date.strftime('%Y-%m-%d') if fund_model.nav_date else '无'}")
            print(f"是否为今天日期: {'是' if fund_model.nav_date and fund_model.nav_date.date() == datetime.now().date() else '否'}")
        print("-"*60)
    
    print("\n验证完成！")
    print(f"当前日期: {datetime.now().strftime('%Y-%m-%d')}")
    print("="*80)