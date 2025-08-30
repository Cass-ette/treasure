#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""简化版的Flask应用，用于展示模拟数据"""

from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
import os
import requests
from bs4 import BeautifulSoup
import schedule

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
# 使用绝对路径连接数据库
basedir = os.path.abspath(os.path.dirname(__file__))
database_path = os.path.join(basedir, 'instance', 'database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 初始化Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 定义简化的模型类
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_main_account = db.Column(db.Boolean, default=False)
    principal = db.Column(db.Float, default=0.0)
    positions = db.relationship('Position', backref='user', lazy=True)
    profits = db.relationship('Profit', backref='user', lazy=True)

class Fund(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    fund_type = db.Column(db.String(50))
    latest_nav = db.Column(db.Float)
    nav_date = db.Column(db.DateTime)
    positions = db.relationship('Position', backref='fund', lazy=True)

class Position(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    fund_id = db.Column(db.Integer, db.ForeignKey('fund.id'), nullable=False)
    shares = db.Column(db.Float, default=0.0)
    cost_price = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Profit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    daily_profit = db.Column(db.Float, default=0.0)
    cumulative_profit = db.Column(db.Float, default=0.0)

# 用户加载回调
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 登录页面
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('用户名或密码错误')
    return render_template('simple_login.html')

# 登出功能
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# 仪表盘页面
@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    # 获取当前用户的总本金和总市值
    if current_user.is_main_account:
        # 对于管理员账户，计算所有持仓的成本总和作为总本金
        total_principal = 0
        for position in current_user.positions:
            if position.cost_price and position.shares > 0:
                total_principal += position.shares * position.cost_price
    else:
        # 对于次级账户，使用设定的本金
        total_principal = current_user.principal if current_user.principal else 0
    
    # 计算总市值
    total_value = 0
    fund_names = []
    fund_values = []
    
    # 计算持仓成本总和
    positions_cost = 0
    for position in current_user.positions:
        if position.fund and position.fund.latest_nav:
            fund_value = position.shares * position.fund.latest_nav
            total_value += fund_value
            fund_names.append(position.fund.name)
            fund_values.append(fund_value)
        # 累加持仓成本
        if position.cost_price and position.shares > 0:
            positions_cost += position.shares * position.cost_price
    
    # 对于次级账户，将未用于持仓的本金视为现金
    if not current_user.is_main_account:
        # 现金部分 = 本金 - 持仓成本
        cash = max(0, current_user.principal - positions_cost)
        total_value += cash
    
    # 计算总盈亏
    total_profit = total_value - total_principal
    
    # 如果是主账户，获取所有次级账户
    sub_accounts = []
    if current_user.is_main_account:
        sub_accounts = User.query.filter_by(is_main_account=False).all()
    
    return render_template('simple_dashboard.html',
                           total_principal=total_principal,
                           total_value=total_value,
                           total_profit=total_profit,
                           fund_names=fund_names,
                           fund_values=fund_values,
                           sub_accounts=sub_accounts)

# 基金管理页面
@app.route('/manage_funds', methods=['GET', 'POST'])
@login_required
def manage_funds():
    # 检查是否为管理员账户
    if not current_user.is_main_account:
        flash('只有管理员账户可以访问此页面', 'error')
        return redirect(url_for('dashboard'))
    
    editing_fund = None
    
    # 检查是否有编辑请求
    if request.args.get('edit'):
        fund_id = request.args.get('edit')
        editing_fund = Fund.query.get(fund_id)
        if not editing_fund:
            flash('未找到该基金', 'error')
            return redirect(url_for('manage_funds'))
    
    # 处理表单提交
    if request.method == 'POST':
        fund_id = request.form.get('fund_id')
        code = request.form.get('code')
        name = request.form.get('name')
        fund_type = request.form.get('fund_type')
        latest_nav = request.form.get('latest_nav')
        nav_date = request.form.get('nav_date')
        
        # 验证必填字段
        if not code:
            flash('基金代码为必填项', 'error')
            return redirect(url_for('manage_funds', edit=fund_id) if fund_id else url_for('manage_funds'))
        
        # 如果是新基金且名称为空，尝试通过基金代码获取名称
        if not fund_id and not name:
            # 由于前端已有自动填充功能，这里添加双重保障
            # 如果前端自动填充失败，在这里调用爬虫函数获取基金名称和净值
            print(f"[基金添加] 开始处理新基金，代码: {code}，尝试自动获取基金信息")
            try:
                # 调用爬虫函数获取基金信息
                print(f"[基金添加] 调用update_fund_nav爬虫函数获取基金信息")
                result = update_fund_nav(code)
                print(f"[基金添加] 爬虫函数执行结果: {result}")
                
                # 重新查询数据库，获取可能新添加的基金信息
                print(f"[基金添加] 重新查询数据库，检查基金信息是否已添加")
                fund_info = Fund.query.filter_by(code=code).first()
                
                if fund_info:
                    print(f"[基金添加] 数据库中找到基金记录: ID={fund_info.id}, 名称={fund_info.name}")
                    if fund_info.name:
                        name = fund_info.name
                        print(f"[基金添加] 成功获取基金名称: {name}")
                    else:
                        print("[基金添加] 基金记录存在但名称为空")
                    
                    # 如果数据库中已存在该基金，直接重定向到基金列表并显示成功消息
                    # 这样可以避免后续代码中再次检查基金代码是否存在的问题
                    flash(f'基金 {code} - {name} 已通过爬虫自动添加', 'success')
                    return redirect(url_for('manage_funds'))
                else:
                    print("[基金添加] 数据库中未找到基金记录")
            except Exception as e:
                print(f"[基金添加] 调用爬虫函数时发生错误: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # 检查基金代码是否已存在（编辑时排除当前基金）
        existing_fund = Fund.query.filter_by(code=code).first()
        if existing_fund and (not fund_id or str(existing_fund.id) != fund_id):
            flash('该基金代码已存在', 'error')
            return redirect(url_for('manage_funds', edit=fund_id) if fund_id else url_for('manage_funds'))
        
        if fund_id:
            # 编辑现有基金
            fund = Fund.query.get(fund_id)
            if not fund:
                flash('未找到该基金', 'error')
                return redirect(url_for('manage_funds'))
            
            fund.code = code
            fund.name = name
            fund.fund_type = fund_type
            fund.latest_nav = float(latest_nav) if latest_nav else None
            fund.nav_date = datetime.strptime(nav_date, '%Y-%m-%d') if nav_date else None
            flash('基金信息更新成功', 'success')
        else:
            # 添加新基金
            fund = Fund(
                code=code,
                name=name,
                fund_type=fund_type,
                latest_nav=float(latest_nav) if latest_nav else None,
                nav_date=datetime.strptime(nav_date, '%Y-%m-%d') if nav_date else None
            )
            db.session.add(fund)
            flash('基金添加成功', 'success')
        
        db.session.commit()
        return redirect(url_for('manage_funds'))
    
    # 获取所有基金
    funds = Fund.query.all()
    
    return render_template('manage_funds.html', funds=funds, editing_fund=editing_fund)

# 删除基金
@app.route('/delete_fund/<int:fund_id>', methods=['POST'])
@login_required
def delete_fund(fund_id):
    # 检查是否为管理员账户
    if not current_user.is_main_account:
        flash('只有管理员账户可以执行此操作', 'error')
        return redirect(url_for('dashboard'))
    
    fund = Fund.query.get(fund_id)
    if not fund:
        flash('未找到该基金', 'error')
        return redirect(url_for('manage_funds'))
    
    try:
        # 直接删除基金，不检查关联持仓
        db.session.delete(fund)
        db.session.commit()
        flash('基金删除成功', 'success')
    except Exception as e:
        flash(f'删除基金失败: {str(e)}', 'error')
    
    return redirect(url_for('manage_funds'))

# 管理持仓页面
@app.route('/manage_positions', methods=['GET', 'POST'])
@login_required
def manage_positions():
    # 检查是否为管理员账户
    if not current_user.is_main_account:
        flash('只有管理员账户可以访问此页面', 'error')
        return redirect(url_for('dashboard'))
    
    # 获取所有用户
    users = User.query.all()
    # 获取所有基金
    funds = Fund.query.all()
    
    editing_position = None
    
    # 检查是否有编辑请求
    if request.args.get('edit'):
        position_id = request.args.get('edit')
        editing_position = Position.query.get(position_id)
        if not editing_position:
            flash('未找到该持仓', 'error')
            return redirect(url_for('manage_positions'))
    
    # 处理表单提交
    if request.method == 'POST':
        position_id = request.form.get('position_id')
        user_id = request.form.get('user_id')
        fund_id = request.form.get('fund_id')
        shares = request.form.get('shares')
        cost_price = request.form.get('cost_price')
        
        # 验证必填字段
        if not user_id or not fund_id or not shares or not cost_price:
            flash('所有字段为必填项', 'error')
            return redirect(url_for('manage_positions', edit=position_id) if position_id else url_for('manage_positions'))
        
        try:
            shares = float(shares)
            cost_price = float(cost_price)
        except ValueError:
            flash('份额和成本价必须为数字', 'error')
            return redirect(url_for('manage_positions', edit=position_id) if position_id else url_for('manage_positions'))
        
        if position_id:
            # 编辑现有持仓
            position = Position.query.get(position_id)
            if not position:
                flash('未找到该持仓', 'error')
                return redirect(url_for('manage_positions'))
            
            position.user_id = user_id
            position.fund_id = fund_id
            position.shares = shares
            position.cost_price = cost_price
            flash('持仓信息更新成功', 'success')
        else:
            # 检查是否已存在相同的用户-基金持仓
            existing_position = Position.query.filter_by(user_id=user_id, fund_id=fund_id).first()
            if existing_position:
                flash('该用户已持有该基金', 'error')
                return redirect(url_for('manage_positions'))
            
            # 添加新持仓
            position = Position(
                user_id=user_id,
                fund_id=fund_id,
                shares=shares,
                cost_price=cost_price
            )
            db.session.add(position)
            flash('持仓添加成功', 'success')
        
        db.session.commit()
        return redirect(url_for('manage_positions'))
    
    # 获取所有持仓
    positions = Position.query.order_by(Position.user_id, Position.fund_id).all()
    
    return render_template('manage_positions.html', 
                           positions=positions, 
                           users=users, 
                           funds=funds, 
                           editing_position=editing_position)

# 删除持仓
@app.route('/delete_position/<int:position_id>', methods=['POST'])
@login_required
def delete_position(position_id):
    # 检查是否为管理员账户
    if not current_user.is_main_account:
        flash('只有管理员账户可以执行此操作', 'error')
        return redirect(url_for('dashboard'))
    
    position = Position.query.get(position_id)
    if not position:
        flash('未找到该持仓', 'error')
        return redirect(url_for('manage_positions'))
    
    try:
        db.session.delete(position)
        db.session.commit()
        flash('持仓删除成功', 'success')
    except Exception as e:
        flash(f'删除持仓失败: {str(e)}', 'error')
    
    return redirect(url_for('manage_positions'))

# 爬取基金净值
@app.route('/crawl_fund_nav', methods=['GET', 'POST'])
@login_required
def crawl_fund_nav():
    # 检查是否为管理员账户
    if not current_user.is_main_account:
        flash('只有管理员账户可以执行此操作', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        # 检查是否是批量爬取
        is_batch = request.form.get('batch') or not request.form.get('fund_id')
        
        if is_batch:
            print("接收到批量爬取请求")
            # 爬取所有基金
            success_count = 0
            fail_count = 0
            fail_funds = []
            
            funds = Fund.query.all()
            print(f"共有 {len(funds)} 个基金需要爬取")
            
            for fund in funds:
                print(f"开始爬取基金：{fund.code} - {fund.name}")
                if update_fund_nav(fund.code):
                    success_count += 1
                    print(f"基金 {fund.code} - {fund.name} 爬取成功")
                else:
                    fail_count += 1
                    fail_funds.append(f"{fund.code} - {fund.name}")
                    print(f"基金 {fund.code} - {fund.name} 爬取失败")
            
            message = f'批量更新完成：成功 {success_count} 个，失败 {fail_count} 个'
            if fail_funds:
                message += f"\n失败的基金：{', '.join(fail_funds[:5])}{'...' if len(fail_funds) > 5 else ''}"
            
            flash(message, 'success')
            return redirect(url_for('crawl_fund_nav'))
        else:
            # 爬取单个基金
            fund_id = request.form.get('fund_id')
            if fund_id:
                fund = Fund.query.get(fund_id)
                if fund:
                    print(f"接收到单个基金爬取请求：{fund.code} - {fund.name}")
                    result = update_fund_nav(fund.code)
                    if result:
                        flash(f'基金 {fund.code} - {fund.name} 净值更新成功', 'success')
                    else:
                        flash(f'基金 {fund.code} - {fund.name} 净值更新失败', 'error')
                return redirect(url_for('crawl_fund_nav'))
    
    # 获取所有基金
    funds = Fund.query.all()
    
    return render_template('crawl_fund_nav.html', funds=funds)

# 更新基金净值的函数
def update_fund_nav(fund_code):
    try:
        # 使用天天基金网作为数据源
        url = f"http://fund.eastmoney.com/{fund_code}.html"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        
        print(f"尝试爬取基金 {fund_code} 的净值数据，URL: {url}")
        response = requests.get(url, headers=headers, timeout=20)
        response.encoding = 'utf-8'
        
        print(f"服务器响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 尝试获取基金名称
            fund_name = None
            fund_name_elem = soup.find('div', class_='fundDetail-tit') or soup.find('h1')
            if fund_name_elem:
                fund_name_text = fund_name_elem.get_text(strip=True)
                # 提取基金名称（通常格式为"基金名称 (基金代码)"）
                import re
                name_match = re.search(r'([^\(]+)', fund_name_text)
                if name_match:
                    fund_name = name_match.group(1).strip()
                    print(f"提取到基金名称: {fund_name}")
            
            if not fund_name:
                # 尝试其他方式获取基金名称
                fund_name_meta = soup.find('meta', attrs={'name': 'keywords'})
                if fund_name_meta and fund_name_meta.get('content'):
                    keywords = fund_name_meta['content'].split(',')
                    if keywords and len(keywords) > 1:
                        fund_name = keywords[0].strip()
                        print(f"从meta标签提取到基金名称: {fund_name}")
            
            # 尝试获取基金类型
            fund_type = None
            # 方法1: 查找基金类型信息
            fund_type_elem = soup.find('div', class_='fundInfoItem', text=re.compile(r'基金类型'))
            if fund_type_elem:
                fund_type_text = fund_type_elem.get_text(strip=True)
                # 提取基金类型（通常格式为"基金类型：XXX"）
                type_match = re.search(r'基金类型[:：]\s*(\S+)', fund_type_text)
                if type_match:
                    fund_type = type_match.group(1).strip()
                    print(f"提取到基金类型: {fund_type}")
            
            # 方法2: 如果方法1失败，尝试通过基金名称判断类型
            if not fund_type and fund_name:
                # 常见基金类型关键字
                type_keywords = {
                    '股票': '股票型',
                    '混合': '混合型',
                    '债券': '债券型',
                    '货币': '货币型',
                    '指数': '指数型',
                    'QDII': 'QDII',
                    'ETF': 'ETF',
                    'LOF': 'LOF',
                    'C': 'C类份额',
                    'A': 'A类份额'
                }
                
                for keyword, type_name in type_keywords.items():
                    if keyword in fund_name:
                        fund_type = type_name
                        print(f"通过基金名称判断类型: {fund_type}")
                        break
            
            # 方法3: 尝试从meta标签获取
            if not fund_type:
                fund_type_meta = soup.find('meta', attrs={'name': 'description'})
                if fund_type_meta and fund_type_meta.get('content'):
                    description = fund_type_meta['content']
                    for keyword, type_name in type_keywords.items():
                        if keyword in description:
                            fund_type = type_name
                            print(f"从meta描述提取基金类型: {fund_type}")
                            break
            
            # 尝试多种方式查找最新净值
            # 方式1: 原始的查找方式
            latest_nav_elem = soup.find('dl', class_='dataItem02')
            
            # 方式2: 尝试查找其他可能的元素类名
            if not latest_nav_elem:
                latest_nav_elem = soup.find('div', class_='fundInfoItem')
                print("未找到 dataItem02，尝试查找 fundInfoItem")
            
            # 方式3: 尝试直接查找包含净值的元素
            if not latest_nav_elem:
                latest_nav_elem = soup.find(text=re.compile(r'单位净值'))
                if latest_nav_elem:
                    latest_nav_elem = latest_nav_elem.parent
                    print("找到包含'单位净值'的文本元素")
            
            if latest_nav_elem:
                # 提取净值文本
                nav_text = latest_nav_elem.get_text(strip=True)
                print(f"找到净值元素，文本内容: {nav_text[:100]}...")
                
                # 使用正则表达式提取数字，尝试多种模式
                
                # 模式1: 原始模式
                nav_match = re.search(r'单位净值：([0-9.]+)', nav_text)
                date_match = re.search(r'更新时间：([0-9-]+)', nav_text)
                
                # 模式2: 尝试其他可能的格式
                if not nav_match:
                    nav_match = re.search(r'单位净值:([0-9.]+)', nav_text)
                    print("尝试使用无空格格式查找单位净值")
                
                if not date_match:
                    date_match = re.search(r'更新日期：([0-9-]+)', nav_text)
                    print("尝试使用'更新日期'查找日期")
                
                # 模式3: 适配新的网页结构格式 - 单位净值(YYYY-MM-DD)XXXX
                if not nav_match and not date_match:
                    # 使用更精确的正则表达式提取日期和净值
                    date_match = re.search(r'单位净值\(([0-9-]+)\)', nav_text)
                    if date_match:
                        print("匹配到新格式: 单位净值(YYYY-MM-DD)XXXX")
                        # 提取日期后的第一个有效净值数值
                        nav_part = nav_text.split(date_match.group(0))[1] if date_match else nav_text
                        # 只提取第一个有效的浮点数
                        nav_match = re.search(r'(\d+\.\d{4})', nav_part)  # 假设净值通常有4位小数
                        if nav_match:
                            print(f"提取到净值: {nav_match.group(1)}")
                
                # 模式4: 尝试直接提取所有数字序列，寻找合理的净值数值
                if not nav_match:
                    all_numbers = re.findall(r'[0-9.]+', nav_text)
                    # 寻找看起来像净值的数字（通常在0-10之间的数值）
                    for num in all_numbers:
                        try:
                            float_num = float(num)
                            if 0 < float_num < 10:
                                nav_match = type('obj', (object,), {'group': lambda s, x=1: float_num})
                                print(f"通过数值范围匹配到可能的净值: {float_num}")
                                break
                        except ValueError:
                            continue
                
                # 如果日期仍然未找到，使用当前日期作为后备
                if not date_match:
                    print("未能提取日期，使用当前日期作为后备")
                    date_match = type('obj', (object,), {'group': lambda s, x=1: datetime.now().strftime('%Y-%m-%d')})
                
                if nav_match and date_match:
                    latest_nav = float(nav_match.group(1))
                    nav_date = datetime.strptime(date_match.group(1), '%Y-%m-%d')
                    print(f"成功提取净值: {latest_nav}, 日期: {nav_date}")
                    
                    # 更新数据库
                    fund = Fund.query.filter_by(code=fund_code).first()
                    if fund:
                        old_nav = fund.latest_nav
                        fund.latest_nav = latest_nav
                        fund.nav_date = nav_date
                        # 如果获取到了基金名称，更新基金名称
                        if fund_name and not fund.name:
                            fund.name = fund_name
                            print(f"更新基金名称为: {fund_name}")
                        # 如果获取到了基金类型，更新基金类型
                        if fund_type and (not fund.fund_type or fund.fund_type == '未知'):
                            fund.fund_type = fund_type
                            print(f"更新基金类型为: {fund_type}")
                        db.session.commit()
                        
                        # 如果净值有变化，计算收益率
                        if old_nav and old_nav != latest_nav:
                            calculate_returns(fund.id, old_nav, latest_nav)
                        
                        return True
                    else:
                        # 如果数据库中没有该基金记录，自动创建新记录
                        print(f"数据库中未找到基金 {fund_code}，创建新记录")
                        new_fund = Fund(
                            code=fund_code,
                            name=fund_name or f"基金{fund_code}",
                            fund_type=fund_type or '未知',  # 使用爬取的类型，如果没有则使用默认值
                            latest_nav=latest_nav,
                            nav_date=nav_date
                        )
                        db.session.add(new_fund)
                        db.session.commit()
                        print(f"成功创建新基金记录: {new_fund.name} ({new_fund.code}), 类型: {new_fund.fund_type}")
                        return True
                else:
                    print("未能从文本中提取有效的净值和日期")
                    print(f"nav_match: {nav_match}, date_match: {date_match}")
            else:
                print("未能找到包含净值信息的元素")
                # 打印页面的一部分以进行调试
                print(f"页面内容预览: {soup.text[:200]}...")
        else:
            print(f"请求失败，状态码: {response.status_code}")
            print(f"响应头: {response.headers}")
        
        # 如果天天基金网爬取失败，尝试使用新浪财经作为备用数据源
        print(f"尝试使用备用数据源爬取基金 {fund_code}")
        try:
            sina_url = f"http://finance.sina.com.cn/fund/quotes/{fund_code}/nav.shtml"
            sina_response = requests.get(sina_url, headers=headers, timeout=10)
            sina_response.encoding = 'utf-8'
            
            if sina_response.status_code == 200:
                sina_soup = BeautifulSoup(sina_response.text, 'html.parser')
                
                # 尝试从新浪财经提取净值信息
                nav_elem = sina_soup.find('div', class_='fundDetail-tit')
                if nav_elem:
                    nav_text = nav_elem.get_text(strip=True)
                    nav_match = re.search(r'([0-9.]+)', nav_text)
                    
                    if nav_match:
                        latest_nav = float(nav_match.group(1))
                        nav_date = datetime.now()  # 新浪财经可能需要不同的日期提取方式
                        
                        # 更新数据库
                        fund = Fund.query.filter_by(code=fund_code).first()
                        if fund:
                            old_nav = fund.latest_nav
                            fund.latest_nav = latest_nav
                            fund.nav_date = nav_date
                            # 如果获取到了基金名称，更新基金名称
                            if fund_name and not fund.name:
                                fund.name = fund_name
                                print(f"更新基金名称为: {fund_name}")
                            # 如果获取到了基金类型，更新基金类型
                            if fund_type and (not fund.fund_type or fund.fund_type == '未知'):
                                fund.fund_type = fund_type
                                print(f"更新基金类型为: {fund_type}")
                            db.session.commit()
                            
                            if old_nav and old_nav != latest_nav:
                                calculate_returns(fund.id, old_nav, latest_nav)
                            
                            print(f"从新浪财经成功获取净值: {latest_nav}")
                            return True
        except Exception as e:
            print(f"备用数据源爬取失败: {str(e)}")
            
        return False
    except Exception as e:
        print(f"爬取基金 {fund_code} 净值时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

# 计算收益率
def calculate_returns(fund_id, old_nav, new_nav):
    try:
        # 获取所有持有该基金的持仓
        positions = Position.query.filter_by(fund_id=fund_id).all()
        
        for position in positions:
            # 计算该持仓的收益率
            if position.cost_price and position.shares > 0:
                # 计算基于成本价的收益率
                cost_value = position.shares * position.cost_price
                current_value = position.shares * new_nav
                profit = current_value - cost_value
                
                # 如果需要，可以在这里更新Profit表
                # 这里只是简单实现，实际应用中可能需要更复杂的逻辑
                
        db.session.commit()
    except Exception as e:
        print(f"计算收益率时出错: {str(e)}")

# 根据基金代码获取基金信息的API接口
@app.route('/get_fund_info')
@login_required
def get_fund_info():
    """根据基金代码获取基金信息的API接口"""
    # 检查是否为管理员账户
    if not current_user.is_main_account:
        return jsonify({
            'success': False,
            'message': '只有管理员账户可以执行此操作'
        })
    
    fund_code = request.args.get('code')
    if not fund_code or not fund_code.isdigit() or len(fund_code) != 6:
        return jsonify({
            'success': False,
            'message': '基金代码必须是6位数字'
        })
    
    try:
        # 首先检查数据库中是否已有该基金
        fund = Fund.query.filter_by(code=fund_code).first()
        
        if fund:
            # 如果数据库中已有该基金，直接返回信息
            return jsonify({
                'success': True,
                'name': fund.name,
                'latest_nav': fund.latest_nav,
                'nav_date': fund.nav_date.strftime('%Y-%m-%d') if fund.nav_date else None
            })
        else:
            # 如果数据库中没有该基金，尝试爬取信息
            print(f"尝试爬取新基金 {fund_code} 的信息")
            # 调用update_fund_nav函数尝试爬取基金信息
            result = update_fund_nav(fund_code)
            
            # 再次查询数据库，获取可能新添加的基金信息
            fund = Fund.query.filter_by(code=fund_code).first()
            
            if fund:
                # 如果爬取成功并添加到数据库，返回信息
                return jsonify({
                    'success': True,
                    'name': fund.name,
                    'latest_nav': fund.latest_nav,
                    'nav_date': fund.nav_date.strftime('%Y-%m-%d') if fund.nav_date else None
                })
            else:
                # 如果爬取失败或未能添加到数据库
                return jsonify({
                    'success': False,
                    'message': '无法获取该基金信息，请检查基金代码是否正确'
                })
    except Exception as e:
        print(f"获取基金信息时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取基金信息时发生错误: {str(e)}'
        })

# 更新次级账户本金
@app.route('/update_sub_account_principal', methods=['POST'])
@login_required
def update_sub_account_principal():
    # 检查是否为管理员账户
    if not current_user.is_main_account:
        flash('只有管理员账户可以执行此操作', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        account_id = request.form.get('account_id')
        principal = request.form.get('principal')
        
        # 验证参数
        if not account_id or not principal:
            flash('参数不完整', 'error')
            return redirect(url_for('dashboard'))
        
        # 转换本金为浮点数
        principal = float(principal)
        if principal < 0:
            flash('本金不能为负数', 'error')
            return redirect(url_for('dashboard'))
        
        # 查找次级账户
        sub_account = User.query.get(account_id)
        if not sub_account or sub_account.is_main_account:
            flash('未找到该次级账户', 'error')
            return redirect(url_for('dashboard'))
        
        # 更新本金
        sub_account.principal = principal
        db.session.commit()
        
        flash(f'账户 {sub_account.username} 的本金已更新为 {principal}', 'success')
    except ValueError:
        flash('本金必须为数字', 'error')
    except Exception as e:
        flash(f'更新本金时出错: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))

# 批量更新所有基金净值的函数（用于定时任务）
def batch_update_all_funds():
    with app.app_context():
        try:
            print("[定时任务] 开始批量更新所有基金净值")
            success_count = 0
            fail_count = 0
            fail_funds = []
            
            funds = Fund.query.all()
            print(f"[定时任务] 共有 {len(funds)} 个基金需要更新")
            
            for fund in funds:
                print(f"[定时任务] 开始更新基金：{fund.code} - {fund.name}")
                if update_fund_nav(fund.code):
                    success_count += 1
                    print(f"[定时任务] 基金 {fund.code} - {fund.name} 更新成功")
                else:
                    fail_count += 1
                    fail_funds.append(f"{fund.code} - {fund.name}")
                    print(f"[定时任务] 基金 {fund.code} - {fund.name} 更新失败")
            
            message = f'[定时任务] 批量更新完成：成功 {success_count} 个，失败 {fail_count} 个'
            if fail_funds:
                message += f"\n失败的基金：{', '.join(fail_funds[:5])}{'...' if len(fail_funds) > 5 else ''}"
            
            print(message)
        except Exception as e:
            print(f"[定时任务] 批量更新时发生错误：{str(e)}")
            import traceback
            traceback.print_exc()

# 启动定时任务
import threading
import time

def start_scheduler():
    print("[定时任务] 启动基金净值自动更新调度器")
    # 每天下午15:30（基金净值通常在此时更新）执行自动更新
    schedule.every().day.at("15:30").do(batch_update_all_funds)
    
    # 如果需要测试，可以取消下面一行的注释，每分钟执行一次
    # schedule.every(1).minutes.do(batch_update_all_funds)
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # 每分钟检查一次

if __name__ == '__main__':
    print("正在启动简化版投资管理系统...")
    print("访问 http://127.0.0.1:5000 进行登录")
    print("可用账户信息：")
    print("- 管理员账户：username=admin, password=admin123")
    print("- 次级账户：username=user1/user2/user3, password=user123")
    
    # 启动定时任务线程
    scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
    scheduler_thread.start()
    
    app.run(debug=True)