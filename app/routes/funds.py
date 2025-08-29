from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required
from app import db
from app.models.fund import Fund
from app.services.fund_service import FundService
from datetime import datetime

# 创建蓝图
bp = Blueprint('funds', __name__)

@bp.route('/funds')
@login_required

def list_funds():
    """基金列表"""
    funds = Fund.query.all()
    return render_template('funds/list.html', funds=funds)

@bp.route('/funds/add', methods=['GET', 'POST'])
@login_required

def add_fund():
    """添加基金"""
    if request.method == 'POST':
        code = request.form.get('code')
        name = request.form.get('name')
        fund_type = request.form.get('fund_type')
        
        # 检查基金是否已存在
        existing_fund = Fund.query.filter_by(code=code).first()
        if existing_fund:
            flash('该基金代码已存在！', 'danger')
            return redirect(url_for('funds.add_fund'))
        
        # 创建新基金
        fund = Fund(code=code, name=name, fund_type=fund_type)
        db.session.add(fund)
        db.session.commit()
        
        # 尝试获取基金最新净值
        try:
            FundService.update_fund_nav(code)
            flash('基金添加成功并已更新净值！', 'success')
        except Exception as e:
            flash('基金添加成功，但获取净值失败：' + str(e), 'warning')
        
        return redirect(url_for('funds.list_funds'))
    
    return render_template('funds/add.html')

@bp.route('/funds/update_nav/<string:code>')
@login_required

def update_fund_nav(code):
    """更新单只基金净值"""
    try:
        FundService.update_fund_nav(code)
        flash('基金净值更新成功！', 'success')
    except Exception as e:
        flash('基金净值更新失败：' + str(e), 'danger')
    
    return redirect(url_for('funds.list_funds'))

@bp.route('/funds/update_all_nav')
@login_required

def update_all_funds_nav():
    """更新所有基金净值"""
    try:
        FundService.update_all_funds_nav()
        flash('所有基金净值更新成功！', 'success')
    except Exception as e:
        flash('更新失败：' + str(e), 'danger')
    
    return redirect(url_for('funds.list_funds'))