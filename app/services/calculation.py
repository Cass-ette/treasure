"""计算服务：收益率计算"""
from datetime import datetime


def calculate_returns(fund_id, old_nav, new_nav, _db=None):
    """
    计算基金净值变化引发的收益。
    _db 参数可用于注入测试用的数据库对象。
    """
    if _db is None:
        from app.extensions import db as _db

    from app.models import Position

    try:
        positions = Position.query.filter_by(fund_id=fund_id).all()
        for position in positions:
            if position.cost_price and position.shares > 0:
                cost_value = position.shares * position.cost_price
                current_value = position.shares * new_nav
                profit = current_value - cost_value  # noqa: F841（暂不写库，保留扩展点）
        _db.session.commit()
    except Exception as e:
        print(f"计算收益率时出错: {str(e)}")


class CalculationService:
    """保留旧 app/ 中的 CalculationService，修复导入路径"""

    @staticmethod
    def calculate_daily_profit(user_id):
        from app.extensions import db
        from app.models import User, Profit

        user = User.query.get(user_id)
        if not user:
            return 0.0

        total_value = sum(
            pos.shares * pos.fund.latest_nav
            for pos in user.positions
            if pos.fund and pos.fund.latest_nav
        )

        if user.is_main_account:
            all_sub = User.query.filter_by(is_main_account=False).all()
            total_principal = sum(u.principal for u in all_sub)
            profit = total_value - total_principal
        else:
            profit = total_value - user.principal

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
    def get_cumulative_profit(user_id):
        from app.models import Profit
        profits = Profit.query.filter_by(user_id=user_id).all()
        return sum(p.daily_profit for p in profits)

    @staticmethod
    def process_all_users_profit():
        from app.models import User
        users = User.query.all()
        for user in users:
            CalculationService.calculate_daily_profit(user.id)
        return len(users)
