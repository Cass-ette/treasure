from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import User, Fund, Position, Profit
from datetime import datetime, timedelta

# 创建蓝图
bp = Blueprint('dashboard', __name__)

@bp.route('/')
@bp.route('/dashboard')
@login_required
def index():
    """仪表盘首页"""
    # 获取数据用于仪表盘显示
    
    # 1. 总本金和当前总市值
    if current_user.is_main_account:
        # 主账户：显示所有账户的汇总数据
        users = User.query.all()
        total_principal = sum(user.principal for user in users if not user.is_main_account)
        
        # 计算所有持仓的当前市值
        total_value = 0.0
        for user in users:
            for position in user.positions:
                if position.fund.latest_nav:
                    total_value += position.shares * position.fund.latest_nav
        
        # 获取次级账户列表
        sub_accounts = []
        for user in users:
            if not user.is_main_account:
                # 获取最新盈亏记录
                latest_profit = 0.0
                latest_record = Profit.query.filter_by(user_id=user.id).order_by(Profit.date.desc()).first()
                if latest_record:
                    latest_profit = latest_record.daily_profit
                
                sub_accounts.append({
                    'id': user.id,
                    'username': user.username,
                    'latest_profit': latest_profit
                })
    else:
        # 次级账户：只显示自己的数据
        user = current_user
        total_principal = user.principal
        
        # 计算自己持仓的当前市值
        total_value = 0.0
        for position in user.positions:
            if position.fund.latest_nav:
                total_value += position.shares * position.fund.latest_nav
        
        sub_accounts = []
    
    # 计算总盈亏
    total_profit = total_value - total_principal
    
    # 获取盈亏趋势数据（最近30天）
    days = 30
    profit_dates = []
    profit_values = []
    
    for i in range(days, 0, -1):
        date = (datetime.now() - timedelta(days=i)).date()
        profit_dates.append(date.strftime('%Y-%m-%d'))
        
        # 计算当天的盈亏
        daily_profit = 0.0
        if current_user.is_main_account:
            # 主账户：所有用户的盈亏总和
            for user in User.query.all():
                profit_record = Profit.query.filter_by(user_id=user.id, date=date).first()
                if profit_record:
                    daily_profit += profit_record.daily_profit
        else:
            # 次级账户：自己的盈亏
            profit_record = Profit.query.filter_by(user_id=current_user.id, date=date).first()
            if profit_record:
                daily_profit = profit_record.daily_profit
        
        profit_values.append(daily_profit)
    
    # 获取持仓分布数据
    fund_names = []
    fund_values = []
    
    if current_user.is_main_account:
        # 主账户：所有基金的持仓分布
        funds = Fund.query.all()
        for fund in funds:
            fund_value = 0.0
            for position in fund.positions:
                if position.fund.latest_nav:
                    fund_value += position.shares * position.fund.latest_nav
            
            if fund_value > 0:
                fund_names.append(fund.name)
                fund_values.append(fund_value)
    else:
        # 次级账户：自己的基金持仓分布
        for position in current_user.positions:
            if position.fund.latest_nav:
                fund_value = position.shares * position.fund.latest_nav
                if fund_value > 0:
                    fund_names.append(position.fund.name)
                    fund_values.append(fund_value)
    
    return render_template('dashboard/index.html',
                          total_principal=total_principal,
                          total_value=total_value,
                          total_profit=total_profit,
                          sub_accounts=sub_accounts,
                          profit_dates=profit_dates,
                          profit_values=profit_values,
                          fund_names=fund_names,
                          fund_values=fund_values)