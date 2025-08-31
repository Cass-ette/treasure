from app import db
from app.models.fund import Fund
from app.models.fund_nav_history import FundNavHistory
from app.utils.crawler import FundCrawler
from datetime import datetime, time
from app import db
from dateutil.relativedelta import relativedelta
import calendar

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
        
        # 尝试获取历史净值数据
        FundService.fetch_and_save_historical_navs(fund.id)
        
        return fund
    
    @staticmethod
    def update_fund_nav(fund_id):
        """更新基金净值并保存到历史记录"""
        fund = Fund.query.get(fund_id)
        if not fund:
            return False
        
        nav_data = FundCrawler.get_fund_nav(fund.code)
        if nav_data:
            # 更新基金最新净值
            fund.latest_nav = nav_data['nav']
            fund.nav_date = nav_data['date']
            
            # 检查是否已经存在该日期的净值记录
            existing_history = FundNavHistory.get_nav_by_date(fund.id, nav_data['date'].date())
            if not existing_history:
                # 创建新的历史记录
                nav_history = FundNavHistory(
                    fund_id=fund.id,
                    nav=nav_data['nav'],
                    date=nav_data['date']
                )
                db.session.add(nav_history)
            
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
    
    @staticmethod
    def fetch_and_save_historical_navs(fund_id, days=30):
        """获取并保存基金历史净值数据"""
        fund = Fund.query.get(fund_id)
        if not fund:
            return False
        
        # 获取历史净值数据
        historical_navs = FundCrawler.get_fund_historical_navs(fund.code, days)
        
        # 保存历史净值数据
        saved_count = 0
        for nav_data in historical_navs:
            # 检查是否已经存在该日期的净值记录
            existing_history = FundNavHistory.get_nav_by_date(fund.id, nav_data['date'].date())
            if not existing_history:
                # 创建新的历史记录
                nav_history = FundNavHistory(
                    fund_id=fund.id,
                    nav=nav_data['nav'],
                    date=nav_data['date']
                )
                db.session.add(nav_history)
                saved_count += 1
        
        if saved_count > 0:
            db.session.commit()
        
        return saved_count
    
    @staticmethod
    def calculate_30_day_average(fund_id):
        """计算基金前三十日（开盘日）的净值平均值"""
        # 获取最近30个交易日的净值
        nav_histories = FundNavHistory.get_latest_navs(fund_id, 30)
        
        if not nav_histories:
            return None
        
        # 计算平均值
        total_nav = sum(history.nav for history in nav_histories)
        average_nav = total_nav / len(nav_histories)
        
        return average_nav
    
    @staticmethod
    def is_market_day(date=None):
        """判断是否为交易日（排除周末和节假日）"""
        if date is None:
            date = datetime.utcnow().date()
        
        # 排除周末
        if date.weekday() >= 5:
            return False
        
        # 添加法定节假日判断（这里列出了2023年和2024年的主要节假日）
        # 实际应用中应该从权威来源获取最新的交易日历
        holidays = [
            # 2023年节假日
            datetime(2023, 1, 1).date(),  # 元旦
            datetime(2023, 1, 21).date(), datetime(2023, 1, 22).date(), 
            datetime(2023, 1, 23).date(), datetime(2023, 1, 24).date(), 
            datetime(2023, 1, 25).date(),  # 春节
            datetime(2023, 4, 5).date(),  # 清明节
            datetime(2023, 5, 1).date(), datetime(2023, 5, 2).date(), 
            datetime(2023, 5, 3).date(),  # 劳动节
            datetime(2023, 6, 22).date(), datetime(2023, 6, 23).date(),  # 端午节
            datetime(2023, 9, 29).date(), datetime(2023, 9, 30).date(),  # 中秋节
            datetime(2023, 10, 1).date(), datetime(2023, 10, 2).date(), 
            datetime(2023, 10, 3).date(), datetime(2023, 10, 4).date(), 
            datetime(2023, 10, 5).date(),  # 国庆节
            
            # 2024年节假日
            datetime(2024, 1, 1).date(),  # 元旦
            datetime(2024, 2, 10).date(), datetime(2024, 2, 11).date(), 
            datetime(2024, 2, 12).date(), datetime(2024, 2, 13).date(), 
            datetime(2024, 2, 14).date(),  # 春节
            datetime(2024, 4, 4).date(),  # 清明节
            datetime(2024, 5, 1).date(), datetime(2024, 5, 2).date(), 
            datetime(2024, 5, 3).date(),  # 劳动节
            datetime(2024, 6, 10).date(),  # 端午节
            datetime(2024, 9, 17).date(),  # 中秋节
            datetime(2024, 10, 1).date(), datetime(2024, 10, 2).date(), 
            datetime(2024, 10, 3).date(), datetime(2024, 10, 4).date(), 
            datetime(2024, 10, 5).date()  # 国庆节
        ]
        
        # 判断是否为节假日
        if date in holidays:
            return False
        
        # 判断是否为调休上班日（周末调休）
        # 这里需要添加调休上班日列表
        workdays = [
            # 2023年调休上班日
            datetime(2023, 1, 28).date(),  # 春节调休
            datetime(2023, 2, 18).date(),  # 春节调休
            datetime(2023, 4, 23).date(),  # 劳动节调休
            datetime(2023, 5, 6).date(),   # 劳动节调休
            datetime(2023, 9, 23).date(),  # 中秋节调休
            datetime(2023, 10, 7).date(),  # 国庆节调休
            datetime(2023, 10, 8).date(),  # 国庆节调休
            
            # 2024年调休上班日
            datetime(2024, 2, 4).date(),   # 春节调休
            datetime(2024, 2, 18).date(),  # 春节调休
            datetime(2024, 4, 28).date(),  # 劳动节调休
            datetime(2024, 5, 11).date(),  # 劳动节调休
            datetime(2024, 9, 15).date(),  # 中秋节调休
            datetime(2024, 10, 12).date()  # 国庆节调休
        ]
        
        # 如果是调休上班日且是周末，返回True
        if date in workdays:
            return True
        
        return True
    
    @staticmethod
    def should_update_nav():
        """判断当前是否应该更新净值（工作日15:30至次日凌晨2点）"""
        now = datetime.now()
        current_time = now.time()
        
        # 判断是否为交易日
        if not FundService.is_market_day(now.date()):
            # 非交易日的凌晨2点前不更新
            if current_time < time(2, 0):
                return False
            else:
                # 非交易日的凌晨2点后也不更新
                return False
        
        # 交易日：15:30至次日凌晨2点之间可以更新
        if current_time >= time(15, 30) or current_time < time(2, 0):
            return True
        
        return False