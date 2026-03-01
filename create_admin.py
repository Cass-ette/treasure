#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""创建管理员账户"""
from app import create_app
from app.extensions import db
from app.models.user import User
from werkzeug.security import generate_password_hash

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
        main_account = User.query.filter_by(is_main_account=True).first()
        if main_account:
            print(f'主账户已存在: {main_account.username}')
        else:
            username = 'admin'
            password = 'admin123'
            user = User(
                username=username,
                password=generate_password_hash(password),
                is_main_account=True,
            )
            db.session.add(user)
            db.session.commit()
            print('主账户创建成功！')
            print(f'用户名: {username}')
            print(f'密码: {password}')
            print('请在登录后修改密码！')
