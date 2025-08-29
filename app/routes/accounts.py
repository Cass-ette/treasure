from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app import db
from app.models import User
from werkzeug.security import generate_password_hash

# 创建蓝图
bp = Blueprint('accounts', __name__)

@bp.route('/accounts')
@login_required

def list_accounts():
    """账户列表（仅主账户可见）"""
    if not current_user.is_main_account:
        # 次级账户无权查看账户列表
        return redirect(url_for('dashboard.index'))
    
    users = User.query.filter_by(is_main_account=False).all()
    return render_template('accounts/list.html', users=users)

@bp.route('/accounts/add', methods=['GET', 'POST'])
@login_required

def add_account():
    """添加次级账户（仅主账户可见）"""
    if not current_user.is_main_account:
        # 次级账户无权添加账户
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # 检查用户名是否已存在
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('用户名已存在，请选择其他用户名。', 'danger')
            return redirect(url_for('accounts.add_account'))
        
        # 检查邮箱是否已存在
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('邮箱已被注册，请使用其他邮箱。', 'danger')
            return redirect(url_for('accounts.add_account'))
        
        # 创建新用户
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            is_main_account=False
        )
        db.session.add(user)
        db.session.commit()
        
        flash('账户添加成功！', 'success')
        return redirect(url_for('accounts.list_accounts'))
    
    return render_template('accounts/add.html')

@bp.route('/accounts/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required

def edit_account(user_id):
    """编辑次级账户信息（仅主账户可见）"""
    if not current_user.is_main_account:
        # 次级账户无权编辑账户
        return redirect(url_for('dashboard.index'))
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        
        # 如果提供了新密码，则更新密码
        new_password = request.form.get('password')
        if new_password:
            user.password_hash = generate_password_hash(new_password)
        
        db.session.commit()
        
        flash('账户信息已更新！', 'success')
        return redirect(url_for('accounts.list_accounts'))
    
    return render_template('accounts/edit.html', user=user)