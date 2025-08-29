from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User

# 创建蓝图
bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        # 验证用户
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('登录成功！', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('用户名或密码错误！', 'danger')
    
    return render_template('auth/login.html')

@bp.route('/logout')
@login_required
def logout():
    """用户退出登录"""
    logout_user()
    return redirect(url_for('auth.login'))

@bp.route('/profile')
@login_required
def profile():
    """用户个人资料"""
    return render_template('auth/profile.html', user=current_user)