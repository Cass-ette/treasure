from app import db
from app.models.fund import Fund
from app.utils.crawler import FundCrawler
from datetime import datetime
from app import db

class FundService:
    @staticmethod
    def add_fund(code, name, fund_type=None):
        """添加基金"""
        existing_fund = Fund.query.filter_by(code=code).first()
        if existing_fund:
            return existing_fund
        
        fund = Fund(code=code, name=name, fund_type=fund_type)
        db.session.add(fund)
        db.session.commit()
        
        # 获取并更新净值
        FundService.update_fund_nav(fund.id)
        
        return fund
    
    @staticmethod
    def update_fund_nav(fund_id):
        """更新基金净值"""
        fund = Fund.query.get(fund_id)
        if not fund:
            return False
        
        nav_data = FundCrawler.get_fund_nav(fund.code)
        if nav_data:
            fund.latest_nav = nav_data['nav']
            fund.nav_date = nav_data['date']
            db.session.commit()
            return True
        
        return False
    
    @staticmethod
    def update_all_funds_nav():
        """更新所有基金净值"""
        funds = Fund.query.all()
        updated_count = 0
        
        for fund in funds:
            if FundService.update_fund_nav(fund.id):
                updated_count += 1
        
        return updated_count