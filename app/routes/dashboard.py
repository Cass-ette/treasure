"""仪表盘蓝图：/, /dashboard"""
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models.user import User
from app.models.position import Position

bp = Blueprint('dashboard', __name__)


@bp.route('/')
@bp.route('/dashboard')
@login_required
def index():
    if current_user.is_main_account:
        # 主账户：所有持仓成本之和作为本金
        total_principal = sum(
            pos.shares * pos.cost_price
            for pos in current_user.positions
            if pos.cost_price and pos.shares > 0
        )
    else:
        total_principal = current_user.principal or 0

    # 计算总市值和持仓图表数据
    total_value = 0.0
    fund_names = []
    fund_values = []
    positions_cost = 0.0

    for pos in current_user.positions:
        if pos.fund and pos.fund.latest_nav:
            fv = pos.shares * pos.fund.latest_nav
            total_value += fv
            fund_names.append(pos.fund.name)
            fund_values.append(fv)
        if pos.cost_price and pos.shares > 0:
            positions_cost += pos.shares * pos.cost_price

    # 次级账户：未投资部分视为现金
    if not current_user.is_main_account:
        cash = max(0, (current_user.principal or 0) - positions_cost)
        total_value += cash

    total_profit = total_value - total_principal

    sub_accounts = []
    if current_user.is_main_account:
        sub_accounts = User.query.filter_by(is_main_account=False).all()

    return render_template(
        'dashboard.html',
        total_principal=total_principal,
        total_value=total_value,
        total_profit=total_profit,
        fund_names=fund_names,
        fund_values=fund_values,
        sub_accounts=sub_accounts,
    )
