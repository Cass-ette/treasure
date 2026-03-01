"""投资报告蓝图"""
from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.models import User, Profit, Position, Fund, Agreement, FundNavHistory
from datetime import datetime, timedelta

bp = Blueprint('reports', __name__)


@bp.route('/reports')
@login_required
def reports():
    days = request.args.get('days', 30, type=int)

    if current_user.is_main_account:
        users = User.query.filter_by(is_main_account=False).all()
        # 为每个用户计算摘要数据
        user_summaries = []
        for user in users:
            positions = Position.query.filter_by(user_id=user.id).all()
            total_value = sum(
                p.shares * p.fund.latest_nav
                for p in positions
                if p.fund and p.fund.latest_nav
            )
            principal = user.principal or 0
            profit = total_value - principal
            user_summaries.append({
                'user': user,
                'total_value': total_value,
                'principal': principal,
                'profit': profit,
                'yield_rate': (profit / principal * 100) if principal > 0 else 0,
                'position_count': len(positions),
            })
        return render_template('reports/main.html', user_summaries=user_summaries, days=days)
    else:
        return _render_user_report(current_user, days)


@bp.route('/reports/user/<int:user_id>')
@login_required
def user_report(user_id):
    if not current_user.is_main_account:
        return redirect(url_for('reports.reports'))

    days = request.args.get('days', 30, type=int)
    user = User.query.get_or_404(user_id)
    return _render_user_report(user, days, template='reports/user_detail.html')


def _render_user_report(user, days, template='reports/user.html'):
    """渲染用户报告的通用逻辑"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    profits = Profit.query.filter(
        Profit.user_id == user.id,
        Profit.date >= start_date,
        Profit.date <= end_date
    ).order_by(Profit.date).all()

    dates = [p.date.strftime('%Y-%m-%d') for p in profits]
    daily_profits = [p.daily_profit for p in profits]
    cumulative_profits = [p.cumulative_profit for p in profits]

    positions = Position.query.filter_by(user_id=user.id).all()
    total_value = sum(
        p.shares * p.fund.latest_nav
        for p in positions
        if p.fund and p.fund.latest_nav
    )

    principal = user.principal or 0
    if user.is_main_account:
        principal = sum(
            p.shares * p.cost_price
            for p in positions
            if p.cost_price and p.shares > 0
        )

    agreement = Agreement.query.filter_by(user_id=user.id).first()

    # 收集用户持仓的基金ID列表（用于K线图）
    fund_ids = list(set(p.fund_id for p in positions if p.fund))

    return render_template(template,
                           user=user,
                           profits=profits,
                           dates=dates,
                           daily_profits=daily_profits,
                           cumulative_profits=cumulative_profits,
                           days=days,
                           total_value=total_value,
                           principal=principal,
                           agreement=agreement,
                           positions=positions,
                           fund_ids=fund_ids)


@bp.route('/reports/fund/<int:fund_id>')
@login_required
def fund_chart(fund_id):
    fund = Fund.query.get_or_404(fund_id)
    days = request.args.get('days', 90, type=int)
    return render_template('reports/fund_chart.html', fund=fund, days=days)


@bp.route('/api/fund/<int:fund_id>/nav_history')
@login_required
def fund_nav_api(fund_id):
    days = request.args.get('days', 90, type=int)
    fund = Fund.query.get_or_404(fund_id)
    nav_records = FundNavHistory.get_latest_navs(fund_id, days)
    return jsonify({
        'fund_name': fund.name,
        'fund_code': fund.code,
        'dates': [r.date.strftime('%Y-%m-%d') for r in nav_records],
        'navs': [r.nav for r in nav_records],
    })
