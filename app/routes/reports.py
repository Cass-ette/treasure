from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from app.models import User, Profit, Position, Fund, Agreement
from datetime import datetime, timedelta

# 创建蓝图
bp = Blueprint('reports', __name__)

@bp.route('/reports')
@login_required

def reports():
    """报告页面"""
    # 默认显示最近30天的报告
    days = request.args.get('days', 30, type=int)
    
    if current_user.is_main_account:
        # 主账户：显示所有账户的报告
        users = User.query.filter_by(is_main_account=False).all()
        return render_template('reports/main.html', users=users, days=days)
    else:
        # 次级账户：只显示自己的报告
        return render_template('reports/user.html', days=days)

@bp.route('/reports/user/<int:user_id>')
@login_required

def user_report(user_id):
    """单个用户报告（主账户查看）"""
    if not current_user.is_main_account:
        # 次级账户不能查看其他用户报告
        return redirect(url_for('reports.reports'))
    
    days = request.args.get('days', 30, type=int)
    user = User.query.get_or_404(user_id)
    
    # 获取收益历史数据
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # 获取用户的收益记录
    profits = Profit.query.filter(
        Profit.user_id == user_id,
        Profit.date >= start_date,
        Profit.date <= end_date
    ).order_by(Profit.date).all()
    
    # 格式化数据用于图表显示
    dates = []
    daily_profits = []
    cumulative_profits = []
    
    for profit in profits:
        dates.append(profit.date.strftime('%Y-%m-%d'))
        daily_profits.append(profit.daily_profit)
        cumulative_profits.append(profit.cumulative_profit)
    
    # 获取当前持仓
    positions = Position.query.filter_by(user_id=user_id).all()
    
    # 计算总市值
    total_value = 0.0
    for position in positions:
        if position.fund.latest_nav:
            total_value += position.shares * position.fund.latest_nav
    
    # 获取分成协议
    agreement = Agreement.query.filter_by(user_id=user_id).first()
    
    return render_template('reports/user_detail.html', 
                          user=user, 
                          profits=profits, 
                          dates=dates, 
                          daily_profits=daily_profits, 
                          cumulative_profits=cumulative_profits, 
                          days=days, 
                          total_value=total_value, 
                          agreement=agreement)