"""基金管理蓝图"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app.extensions import db
from app.models.fund import Fund
from app.models.fund_nav_history import FundNavHistory

bp = Blueprint('funds', __name__)


def _admin_required():
    if not current_user.is_main_account:
        flash('只有管理员账户可以访问此页面', 'error')
        return redirect(url_for('dashboard.index'))
    return None


@bp.route('/manage_funds', methods=['GET', 'POST'])
@login_required
def manage_funds():
    guard = _admin_required()
    if guard:
        return guard

    editing_fund = None
    if request.args.get('edit'):
        editing_fund = Fund.query.get(request.args.get('edit'))
        if not editing_fund:
            flash('未找到该基金', 'error')
            return redirect(url_for('funds.manage_funds'))

    if request.method == 'POST':
        fund_id = request.form.get('fund_id')
        code = request.form.get('code')
        name = request.form.get('name')
        fund_type = request.form.get('fund_type')
        latest_nav = request.form.get('latest_nav')
        nav_date = request.form.get('nav_date')

        if not code:
            flash('基金代码为必填项', 'error')
            return redirect(url_for('funds.manage_funds', edit=fund_id) if fund_id else url_for('funds.manage_funds'))

        # 新基金且没有名称：尝试爬取
        if not fund_id and not name:
            try:
                from app.services.crawler import update_fund_nav
                update_fund_nav(code)
                fund_info = Fund.query.filter_by(code=code).first()
                if fund_info:
                    flash(f'基金 {code} - {fund_info.name} 已通过爬虫自动添加', 'success')
                    return redirect(url_for('funds.manage_funds'))
            except Exception as e:
                print(f"[基金添加] 调用爬虫时出错: {e}")

        # 检查代码重复
        existing = Fund.query.filter_by(code=code).first()
        if existing and (not fund_id or str(existing.id) != fund_id):
            flash('该基金代码已存在', 'error')
            return redirect(url_for('funds.manage_funds', edit=fund_id) if fund_id else url_for('funds.manage_funds'))

        if fund_id:
            fund = Fund.query.get(fund_id)
            if not fund:
                flash('未找到该基金', 'error')
                return redirect(url_for('funds.manage_funds'))
            fund.code = code
            fund.name = name
            fund.fund_type = fund_type
            fund.latest_nav = float(latest_nav) if latest_nav else None
            fund.nav_date = datetime.strptime(nav_date, '%Y-%m-%d') if nav_date else None
            flash('基金信息更新成功', 'success')
        else:
            fund = Fund(
                code=code,
                name=name,
                fund_type=fund_type,
                latest_nav=float(latest_nav) if latest_nav else None,
                nav_date=datetime.strptime(nav_date, '%Y-%m-%d') if nav_date else None,
            )
            db.session.add(fund)
            flash('基金添加成功', 'success')

        db.session.commit()
        return redirect(url_for('funds.manage_funds'))

    funds = Fund.query.all()
    return render_template('manage_funds.html', funds=funds, editing_fund=editing_fund)


@bp.route('/delete_fund/<int:fund_id>', methods=['POST'])
@login_required
def delete_fund(fund_id):
    guard = _admin_required()
    if guard:
        return guard

    fund = Fund.query.get(fund_id)
    if not fund:
        flash('未找到该基金', 'error')
        return redirect(url_for('funds.manage_funds'))
    try:
        db.session.delete(fund)
        db.session.commit()
        flash('基金删除成功', 'success')
    except Exception as e:
        flash(f'删除基金失败: {str(e)}', 'error')
    return redirect(url_for('funds.manage_funds'))


@bp.route('/crawl_fund_nav', methods=['GET', 'POST'])
@login_required
def crawl_fund_nav():
    guard = _admin_required()
    if guard:
        return guard

    if request.method == 'POST':
        from app.services.crawler import update_fund_nav
        is_batch = request.form.get('batch') or not request.form.get('fund_id')

        if is_batch:
            funds = Fund.query.all()
            success_count = fail_count = 0
            fail_funds = []
            for fund in funds:
                if update_fund_nav(fund.code):
                    success_count += 1
                else:
                    fail_count += 1
                    fail_funds.append(f"{fund.code} - {fund.name}")
            msg = f'批量更新完成：成功 {success_count} 个，失败 {fail_count} 个'
            if fail_funds:
                msg += f"\n失败：{', '.join(fail_funds[:5])}{'...' if len(fail_funds) > 5 else ''}"
            flash(msg, 'success')
        else:
            fund_id = request.form.get('fund_id')
            fund = Fund.query.get(fund_id)
            if fund:
                if update_fund_nav(fund.code):
                    flash(f'基金 {fund.code} - {fund.name} 净值更新成功', 'success')
                else:
                    flash(f'基金 {fund.code} - {fund.name} 净值更新失败', 'error')
        return redirect(url_for('funds.crawl_fund_nav'))

    funds = Fund.query.all()
    return render_template('crawl_fund_nav.html', funds=funds)


@bp.route('/get_fund_info')
@login_required
def get_fund_info():
    if not current_user.is_main_account:
        return jsonify({'success': False, 'message': '只有管理员账户可以执行此操作'})

    fund_code = request.args.get('code')
    if not fund_code or not fund_code.isdigit() or len(fund_code) != 6:
        return jsonify({'success': False, 'message': '基金代码必须是6位数字'})

    try:
        fund = Fund.query.filter_by(code=fund_code).first()
        if fund:
            return jsonify({
                'success': True,
                'name': fund.name,
                'latest_nav': fund.latest_nav,
                'nav_date': fund.nav_date.strftime('%Y-%m-%d') if fund.nav_date else None,
            })

        from app.services.crawler import update_fund_nav
        update_fund_nav(fund_code)
        fund = Fund.query.filter_by(code=fund_code).first()
        if fund:
            return jsonify({
                'success': True,
                'name': fund.name,
                'latest_nav': fund.latest_nav,
                'nav_date': fund.nav_date.strftime('%Y-%m-%d') if fund.nav_date else None,
            })
        return jsonify({'success': False, 'message': '无法获取该基金信息，请检查基金代码是否正确'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取基金信息时发生错误: {str(e)}'})


@bp.route('/get_fund_30_day_average')
@login_required
def get_fund_30_day_average():
    if not current_user.is_main_account:
        return jsonify({'success': False, 'message': '只有管理员账户可以执行此操作'})

    fund_id = request.args.get('fund_id')
    if not fund_id or not fund_id.isdigit():
        return jsonify({'success': False, 'message': '基金ID必须是有效的数字'})

    try:
        fund = Fund.query.get(int(fund_id))
        if not fund:
            return jsonify({'success': False, 'message': '基金不存在'})

        nav_records = FundNavHistory.get_latest_navs(int(fund_id), 30)
        if not nav_records:
            return jsonify({'success': False, 'message': '暂无净值历史数据'})

        average_nav = sum(r.nav for r in nav_records) / len(nav_records)
        return jsonify({
            'success': True,
            'average_nav': average_nav,
            'trading_days_count': len(nav_records),
            'message': f'基于最近{len(nav_records)}个交易日计算的平均净值',
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取前三十日平均净值时发生错误: {str(e)}'})


@bp.route('/add_fund_from_recognition')
@login_required
def add_fund_from_recognition():
    guard = _admin_required()
    if guard:
        return guard

    fund_code = request.args.get('code')
    fund_name = request.args.get('name')

    if not fund_code:
        flash('基金代码不能为空', 'error')
        return redirect(url_for('funds.manage_funds'))

    existing = Fund.query.filter_by(code=fund_code).first()
    if existing:
        flash(f'基金 {fund_code} - {existing.name} 已存在于系统中', 'info')
    else:
        try:
            from app.services.crawler import update_fund_nav
            update_fund_nav(fund_code)
            added = Fund.query.filter_by(code=fund_code).first()
            if added:
                flash(f'基金 {added.code} - {added.name} 已成功添加到系统', 'success')
            else:
                new_fund = Fund(code=fund_code, name=fund_name or f"基金{fund_code}", fund_type='未知')
                db.session.add(new_fund)
                db.session.commit()
                flash(f'基金 {new_fund.code} - {new_fund.name} 已成功添加到系统（使用识别信息创建）', 'success')
        except Exception as e:
            flash(f'添加基金时出错: {str(e)}', 'error')

    return redirect(url_for('funds.manage_funds'))
