"""账户管理蓝图：update_sub_account_principal"""
from flask import Blueprint, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.user import User

bp = Blueprint('accounts', __name__)


@bp.route('/update_sub_account_principal', methods=['POST'])
@login_required
def update_sub_account_principal():
    if not current_user.is_main_account:
        flash('只有管理员账户可以执行此操作', 'error')
        return redirect(url_for('dashboard.index'))

    try:
        account_id = request.form.get('account_id')
        principal = request.form.get('principal')

        if not account_id or not principal:
            flash('参数不完整', 'error')
            return redirect(url_for('dashboard.index'))

        principal = float(principal)
        if principal < 0:
            flash('本金不能为负数', 'error')
            return redirect(url_for('dashboard.index'))

        sub_account = User.query.get(account_id)
        if not sub_account or sub_account.is_main_account:
            flash('未找到该次级账户', 'error')
            return redirect(url_for('dashboard.index'))

        sub_account.principal = principal
        db.session.commit()
        flash(f'账户 {sub_account.username} 的本金已更新为 {principal}', 'success')
    except ValueError:
        flash('本金必须为数字', 'error')
    except Exception as e:
        flash(f'更新本金时出错: {str(e)}', 'error')

    return redirect(url_for('dashboard.index'))
