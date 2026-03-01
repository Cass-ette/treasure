"""AI 分析助手蓝图（DeepSeek API）"""
import requests as http_requests
from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from app.extensions import db
from app.models import User, Fund, Position, Profit, FundNavHistory, Agreement
from datetime import datetime, timedelta

bp = Blueprint('ai', __name__)

DEEPSEEK_API_URL = 'https://api.deepseek.com/chat/completions'


@bp.route('/ai')
@login_required
def assistant():
    api_key = current_app.config.get('DEEPSEEK_API_KEY', '')
    has_key = bool(api_key)
    return render_template('ai_assistant.html', has_key=has_key)


@bp.route('/ai/chat', methods=['POST'])
@login_required
def chat():
    api_key = current_app.config.get('DEEPSEEK_API_KEY', '')
    if not api_key:
        return jsonify({'error': '未配置 DEEPSEEK_API_KEY，请在环境变量中设置'}), 400

    data = request.get_json()
    user_message = data.get('message', '').strip()
    if not user_message:
        return jsonify({'error': '消息不能为空'}), 400

    context = _build_investment_context()

    system_prompt = f"""你是一个专业的投资分析助手。用户正在使用一个基金投资管理系统。
以下是用户当前的投资数据：

{context}

请基于这些数据回答用户的问题。提供专业、清晰的分析。
注意：你提供的是参考分析，不构成投资建议。"""

    try:
        resp = http_requests.post(
            DEEPSEEK_API_URL,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'deepseek-chat',
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_message},
                ],
                'max_tokens': 2048,
                'temperature': 0.7,
            },
            timeout=60,
        )
        resp.raise_for_status()
        result = resp.json()
        reply = result['choices'][0]['message']['content']
        return jsonify({'reply': reply})
    except http_requests.exceptions.Timeout:
        return jsonify({'error': 'AI 请求超时，请重试'}), 504
    except http_requests.exceptions.RequestException as e:
        return jsonify({'error': f'AI 请求失败: {str(e)}'}), 500
    except (KeyError, IndexError):
        return jsonify({'error': 'AI 返回格式异常'}), 500


def _build_investment_context():
    """构建当前用户的投资数据上下文"""
    lines = []

    lines.append(f"用户: {current_user.username}")
    lines.append(f"账户类型: {'主账户' if current_user.is_main_account else '次级账户'}")
    if not current_user.is_main_account:
        lines.append(f"本金: ¥{current_user.principal or 0:.2f}")

    positions = Position.query.filter_by(user_id=current_user.id).all()
    if positions:
        lines.append("\n== 当前持仓 ==")
        total_cost = 0
        total_value = 0
        for pos in positions:
            if pos.fund:
                cost = pos.shares * (pos.cost_price or 0)
                value = pos.shares * (pos.fund.latest_nav or 0)
                pnl = value - cost
                total_cost += cost
                total_value += value
                if cost > 0:
                    lines.append(
                        f"- {pos.fund.name}({pos.fund.code}): "
                        f"份额={pos.shares:.2f}, 成本价={pos.cost_price:.4f}, "
                        f"最新净值={pos.fund.latest_nav or 0:.4f}, "
                        f"成本=¥{cost:.2f}, 市值=¥{value:.2f}, "
                        f"盈亏=¥{pnl:.2f} ({pnl/cost*100:.2f}%)"
                    )
                else:
                    lines.append(
                        f"- {pos.fund.name}({pos.fund.code}): "
                        f"份额={pos.shares:.2f}, 最新净值={pos.fund.latest_nav or 0:.4f}"
                    )
        lines.append(f"\n总成本: ¥{total_cost:.2f}")
        lines.append(f"总市值: ¥{total_value:.2f}")
        lines.append(f"总盈亏: ¥{total_value - total_cost:.2f}")
        if total_cost > 0:
            lines.append(f"总收益率: {(total_value - total_cost) / total_cost * 100:.2f}%")
    else:
        lines.append("\n暂无持仓数据")

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)
    profits = Profit.query.filter(
        Profit.user_id == current_user.id,
        Profit.date >= start_date,
        Profit.date <= end_date
    ).order_by(Profit.date).all()

    if profits:
        lines.append("\n== 近30天收益 ==")
        for p in profits[-10:]:
            lines.append(f"- {p.date.strftime('%Y-%m-%d')}: 日收益=¥{p.daily_profit:.2f}, 累计=¥{p.cumulative_profit:.2f}")
        if len(profits) > 10:
            lines.append(f"  (共{len(profits)}条记录，仅显示最近10条)")

    fund_ids = set(p.fund_id for p in positions if p.fund)
    if fund_ids:
        lines.append("\n== 持仓基金近期净值 ==")
        for fid in fund_ids:
            fund = Fund.query.get(fid)
            if not fund:
                continue
            navs = FundNavHistory.get_latest_navs(fid, 10)
            if navs:
                nav_str = ", ".join(f"{n.date.strftime('%m-%d')}:{n.nav:.4f}" for n in navs)
                lines.append(f"- {fund.name}: {nav_str}")

    agreement = Agreement.query.filter_by(user_id=current_user.id).first()
    if agreement:
        lines.append(f"\n== 分成协议 ==")
        lines.append(f"分成比例: {agreement.profit_share_ratio * 100:.0f}%")
        lines.append(f"保本: {'是' if agreement.is_capital_protected else '否'}")

    return "\n".join(lines)
