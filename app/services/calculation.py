from app import db
from app.models import User, Fund, Position, Agreement, Profit
from datetime import datetime, timedelta

class CalculationService:
    @staticmethod
    def calculate_daily_profit(user_id):
        """计算用户当日盈亏"""
        user = User.query.get(user_id)
        if not user:
            return 0.0
        
        total_value = 0.0
        
        # 计算所有持仓的当前市值
        for position in user.positions:
            if position.fund.latest_nav:
                total_value += position.shares * position.fund.latest_nav
        
        # 计算盈亏
        if user.is_main_account:
            # 主账户：总市值 - 所有投入资金
            profit = total_value - sum(user.principal for user in User.query.filter_by(is_main_account=False).all())
        else:
            # 次级账户：总市值 - 投入本金
            profit = total_value - user.principal
        
        # 记录收益
        today = datetime.now().date()
        existing_profit = Profit.query.filter_by(user_id=user_id, date=today).first()
        
        if existing_profit:
            existing_profit.daily_profit = profit
            existing_profit.cumulative_profit = CalculationService.get_cumulative_profit(user_id)
        else:
            cumulative_profit = CalculationService.get_cumulative_profit(user_id)
            new_profit = Profit(
                user_id=user_id,
                date=today,
                daily_profit=profit,
                cumulative_profit=cumulative_profit
            )
            db.session.add(new_profit)
        
        db.session.commit()
        
        return profit
    
    @staticmethod
    def calculate_share_amount(user_id):
        """计算分成金额"""
        user = User.query.get(user_id)
        if user.is_main_account or not user.agreement:
            return 0.0
        
        # 获取当日盈亏
        today = datetime.now().date()
        profit_record = Profit.query.filter_by(user_id=user_id, date=today).first()
        
        if not profit_record or profit_record.daily_profit <= 0:
            # 亏损时，若保本则计算补偿金额
            if user.agreement.is_capital_protected:
                capital_guarantee = user.principal * user.agreement.capital_protection_ratio
                # 计算当前总市值
                total_value = 0.0
                for position in user.positions:
                    if position.fund.latest_nav:
                        total_value += position.shares * position.fund.latest_nav
                
                # 计算补偿金额
                if total_value < capital_guarantee:
                    compensation = capital_guarantee - total_value
                    profit_record.share_amount = -compensation  # 负数表示主账户需补偿
                    db.session.commit()
                    return -compensation
        else:
            # 盈利时，按比例计算分成
            share_amount = profit_record.daily_profit * user.agreement.profit_share_ratio
            profit_record.share_amount = share_amount
            db.session.commit()
            return share_amount
        
        return 0.0
    
    @staticmethod
    def get_cumulative_profit(user_id):
        """获取累计盈亏"""
        # 简单实现：计算所有历史收益的总和
        profits = Profit.query.filter_by(user_id=user_id).all()
        return sum(profit.daily_profit for profit in profits)
    
    @staticmethod
    def process_all_users_profit():
        """处理所有用户的盈亏计算"""
        users = User.query.all()
        
        for user in users:
            CalculationService.calculate_daily_profit(user.id)
            if not user.is_main_account:
                CalculationService.calculate_share_amount(user.id)
        
        return len(users)