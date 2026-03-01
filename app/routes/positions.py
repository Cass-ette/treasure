"""持仓管理蓝图"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.user import User
from app.models.fund import Fund
from app.models.position import Position

bp = Blueprint('positions', __name__)


@bp.route('/manage_positions', methods=['GET', 'POST'])
@login_required
def manage_positions():
    if not current_user.is_main_account:
        flash('只有管理员账户可以访问此页面', 'error')
        return redirect(url_for('dashboard.index'))

    users = User.query.all()
    funds = Fund.query.all()
    editing_position = None

    if request.args.get('edit'):
        editing_position = Position.query.get(request.args.get('edit'))
        if not editing_position:
            flash('未找到该持仓', 'error')
            return redirect(url_for('positions.manage_positions'))

    if request.method == 'POST':
        position_id = request.form.get('position_id')
        user_id = request.form.get('user_id')
        fund_id = request.form.get('fund_id')
        shares = request.form.get('shares')
        cost_price = request.form.get('cost_price')

        if not user_id or not fund_id or not shares or not cost_price:
            flash('所有字段为必填项', 'error')
            target = url_for('positions.manage_positions', edit=position_id) if position_id else url_for('positions.manage_positions')
            return redirect(target)

        try:
            shares = float(shares)
            cost_price = float(cost_price)
        except ValueError:
            flash('份额和成本价必须为数字', 'error')
            target = url_for('positions.manage_positions', edit=position_id) if position_id else url_for('positions.manage_positions')
            return redirect(target)

        if position_id:
            position = Position.query.get(position_id)
            if not position:
                flash('未找到该持仓', 'error')
                return redirect(url_for('positions.manage_positions'))
            position.user_id = user_id
            position.fund_id = fund_id
            position.shares = shares
            position.cost_price = cost_price
            flash('持仓信息更新成功', 'success')
        else:
            if Position.query.filter_by(user_id=user_id, fund_id=fund_id).first():
                flash('该用户已持有该基金', 'error')
                return redirect(url_for('positions.manage_positions'))
            db.session.add(Position(user_id=user_id, fund_id=fund_id, shares=shares, cost_price=cost_price))
            flash('持仓添加成功', 'success')

        db.session.commit()
        return redirect(url_for('positions.manage_positions'))

    positions = Position.query.order_by(Position.user_id, Position.fund_id).all()
    return render_template('manage_positions.html', positions=positions, users=users, funds=funds, editing_position=editing_position)


@bp.route('/delete_position/<int:position_id>', methods=['POST'])
@login_required
def delete_position(position_id):
    if not current_user.is_main_account:
        flash('只有管理员账户可以执行此操作', 'error')
        return redirect(url_for('dashboard.index'))

    position = Position.query.get(position_id)
    if not position:
        flash('未找到该持仓', 'error')
        return redirect(url_for('positions.manage_positions'))

    try:
        db.session.delete(position)
        db.session.commit()
        flash('持仓删除成功', 'success')
    except Exception as e:
        flash(f'删除持仓失败: {str(e)}', 'error')
    return redirect(url_for('positions.manage_positions'))
