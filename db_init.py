#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""初始化数据库（创建所有表）"""
from app import create_app
from app.extensions import db
from app.models import User, Fund, Position, Transaction, Agreement, Profit, FundNavHistory
from werkzeug.security import generate_password_hash

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
        print('数据库表创建完成！')

        if not User.query.filter_by(is_main_account=True).first():
            main_user = User(
                username='admin',
                password=generate_password_hash('admin123'),
                is_main_account=True,
            )
            db.session.add(main_user)
            db.session.commit()
            print('主账户已创建：admin / admin123')
