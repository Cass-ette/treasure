from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app import db
from app.models import Transaction, Fund, Position, User
from datetime import datetime

# 创建蓝图
bp = Blueprint('transactions', __name__)

@bp.route('/transactions')
@login_required

def list_transactions():
    """交易记录列表"""
    if current_user.is_main_account:
        # 主账户：查看所有交易记录
        transactions = Transaction.query.order_by(Transaction.transaction_date.desc()).all()
    else:
        # 次级账户：只查看自己的交易记录
        transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.transaction_date.desc()).all()
    
    return render_template('transactions/list.html', transactions=transactions)

@bp.route('/transactions/add', methods=['GET', 'POST'])
@login_required

def add_transaction():
    """添加交易记录"""
    funds = Fund.query.all()
    
    if request.method == 'POST':
        user_id = request.form.get('user_id') if current_user.is_main_account else current_user.id
        fund_id = request.form.get('fund_id')
        transaction_type = request.form.get('transaction_type')
        amount = float(request.form.get('amount'))
        price = float(request.form.get('price'))
        fee = float(request.form.get('fee', 0))
        
        # 计算份额
        shares = amount / price if price > 0 else 0
        
        # 创建交易记录
        transaction = Transaction(
            user_id=user_id,
            fund_id=fund_id,
            transaction_type=transaction_type,
            amount=amount,
            shares=shares,
            price=price,
            fee=fee
        )
        db.session.add(transaction)
        
        # 更新持仓
        update_position(user_id, fund_id, transaction_type, shares, price)
        
        db.session.commit()
        flash('交易记录添加成功！', 'success')
        
        return redirect(url_for('transactions.list_transactions'))
    
    # 如果是主账户，获取所有次级账户列表
    users = User.query.filter_by(is_main_account=False).all() if current_user.is_main_account else []
    
    return render_template('transactions/add.html', funds=funds, users=users)

def update_position(user_id, fund_id, transaction_type, shares, price):
    """更新用户持仓"""
    # 查找现有持仓
    position = Position.query.filter_by(user_id=user_id, fund_id=fund_id).first()
    
    if transaction_type == 'buy':
        if position:
            # 已有持仓，更新份额和成本价
            total_shares = position.shares + shares
            total_cost = (position.shares * position.cost_price) + (shares * price)
            position.shares = total_shares
            position.cost_price = total_cost / total_shares if total_shares > 0 else 0
        else:
            # 新建持仓
            position = Position(user_id=user_id, fund_id=fund_id, shares=shares, cost_price=price)
            db.session.add(position)
    elif transaction_type == 'sell':
        if position and position.shares >= shares:
            # 减少份额
            position.shares -= shares
            if position.shares == 0:
                # 如果份额为0，删除持仓记录
                db.session.delete(position)