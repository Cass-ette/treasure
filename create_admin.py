from app import app, db
from app.models import User, Fund, Position, Transaction, Agreement, Profit
from werkzeug.security import generate_password_hash

# 创建应用上下文
if __name__ == '__main__':
    with app.app_context():
        # 初始化数据库表结构
        print('初始化数据库表结构...')
        db.create_all()
        
        # 检查是否已有主账户
        main_account = User.query.filter_by(is_main_account=True).first()
        
        if main_account:
            print(f'主账户已存在: {main_account.username}')
        else:
            # 创建新的主账户
            username = 'admin'
            password = 'admin123'
            
            user = User(
                username=username,
                password=generate_password_hash(password),
                is_main_account=True
            )
            
            db.session.add(user)
            db.session.commit()
            
            print(f'主账户创建成功！')
            print(f'用户名: {username}')
            print(f'密码: {password}')
            print(f'请在登录后修改密码！')