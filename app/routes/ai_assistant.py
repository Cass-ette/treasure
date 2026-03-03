"""AI 分析助手蓝图（多模型支持：DeepSeek / Claude）"""
import requests as http_requests
from flask import Blueprint, render_template, request, jsonify, current_app, Response
from flask_login import login_required, current_user
from app.extensions import db
from app.models import User, Fund, Position, Profit, FundNavHistory, Agreement
from app.models.user_setting import UserSetting
from app.models.chat_conversation import ChatConversation
from datetime import datetime, timedelta

bp = Blueprint('ai', __name__)

DEEPSEEK_API_URL = 'https://api.deepseek.com/chat/completions'
CLAUDE_API_URL = 'https://api.anthropic.com/v1/messages'


# ── 辅助函数 ──────────────────────────────────────────────

def _get_api_key(provider):
    """获取 API key：数据库优先，环境变量 fallback"""
    key_map = {
        'deepseek': ('deepseek_api_key', 'DEEPSEEK_API_KEY'),
        'claude': ('anthropic_api_key', 'ANTHROPIC_API_KEY'),
    }
    db_key, env_key = key_map.get(provider, (None, None))
    if not db_key:
        return None
    # 数据库中的用户配置优先
    val = UserSetting.get_value(current_user.id, db_key)
    if val:
        return val
    return current_app.config.get(env_key, '')


def _call_deepseek(api_key, system_prompt, user_message):
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
    return result['choices'][0]['message']['content']


def _call_claude(api_key, system_prompt, user_message):
    resp = http_requests.post(
        CLAUDE_API_URL,
        headers={
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01',
            'Content-Type': 'application/json',
        },
        json={
            'model': 'claude-sonnet-4-20250514',
            'max_tokens': 2048,
            'system': system_prompt,
            'messages': [
                {'role': 'user', 'content': user_message},
            ],
        },
        timeout=60,
    )
    resp.raise_for_status()
    result = resp.json()
    return result['content'][0]['text']


# ── 页面路由 ─────────────────────────────────────────────

@bp.route('/ai')
@login_required
def assistant():
    has_deepseek_key = bool(_get_api_key('deepseek'))
    has_claude_key = bool(_get_api_key('claude'))
    preferred_model = UserSetting.get_value(current_user.id, 'ai_model_preference', 'deepseek')
    conversations = ChatConversation.query.filter_by(
        user_id=current_user.id
    ).order_by(ChatConversation.updated_at.desc()).all()
    return render_template(
        'ai_assistant.html',
        has_deepseek_key=has_deepseek_key,
        has_claude_key=has_claude_key,
        has_key=has_deepseek_key or has_claude_key,
        preferred_model=preferred_model,
        conversations=[c.to_dict() for c in conversations],
    )


# ── 聊天 ─────────────────────────────────────────────────

@bp.route('/ai/chat', methods=['POST'])
@login_required
def chat():
    data = request.get_json()
    user_message = data.get('message', '').strip()
    model = data.get('model', 'deepseek')
    if not user_message:
        return jsonify({'error': '消息不能为空'}), 400

    provider = 'claude' if model == 'claude' else 'deepseek'
    api_key = _get_api_key(provider)
    if not api_key:
        name = 'Claude' if provider == 'claude' else 'DeepSeek'
        return jsonify({'error': f'未配置 {name} API Key，请在设置中配置'}), 400

    context = _build_investment_context()
    system_prompt = f"""你是一个专业的投资分析助手。用户正在使用一个基金投资管理系统。
以下是用户当前的投资数据：

{context}

请基于这些数据回答用户的问题。提供专业、清晰的分析。
注意：你提供的是参考分析，不构成投资建议。"""

    try:
        if provider == 'claude':
            reply = _call_claude(api_key, system_prompt, user_message)
        else:
            reply = _call_deepseek(api_key, system_prompt, user_message)
        return jsonify({'reply': reply})
    except http_requests.exceptions.Timeout:
        return jsonify({'error': 'AI 请求超时，请重试'}), 504
    except http_requests.exceptions.RequestException as e:
        return jsonify({'error': f'AI 请求失败: {str(e)}'}), 500
    except (KeyError, IndexError):
        return jsonify({'error': 'AI 返回格式异常'}), 500


# ── 设置 ─────────────────────────────────────────────────

@bp.route('/ai/settings', methods=['POST'])
@login_required
def save_settings():
    data = request.get_json()
    deepseek_key = data.get('deepseek_api_key', '').strip()
    anthropic_key = data.get('anthropic_api_key', '').strip()
    preferred = data.get('preferred_model', '').strip()

    if deepseek_key:
        UserSetting.set_value(current_user.id, 'deepseek_api_key', deepseek_key)
    if anthropic_key:
        UserSetting.set_value(current_user.id, 'anthropic_api_key', anthropic_key)
    if preferred in ('deepseek', 'claude'):
        UserSetting.set_value(current_user.id, 'ai_model_preference', preferred)

    return jsonify({'ok': True})


# ── 导出数据上下文 ───────────────────────────────────────

@bp.route('/ai/export-context')
@login_required
def export_context():
    context = _build_investment_context()
    md = f"# 投资数据导出\n\n导出时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n```\n{context}\n```\n"
    return Response(
        md,
        mimetype='text/markdown',
        headers={'Content-Disposition': 'attachment; filename=investment-context.md'},
    )


# ── 对话管理 ─────────────────────────────────────────────

@bp.route('/ai/conversations/save', methods=['POST'])
@login_required
def save_conversation():
    data = request.get_json()
    title = data.get('title', '').strip() or '新对话'
    messages = data.get('messages', [])
    model = data.get('model', 'deepseek')
    conv_id = data.get('id')

    if conv_id:
        conv = ChatConversation.query.filter_by(id=conv_id, user_id=current_user.id).first()
        if not conv:
            return jsonify({'error': '对话不存在'}), 404
        conv.title = title
        conv.model = model
        conv.set_messages(messages)
        conv.updated_at = datetime.utcnow()
    else:
        conv = ChatConversation(
            user_id=current_user.id,
            title=title,
            model=model,
        )
        conv.set_messages(messages)
        db.session.add(conv)

    db.session.commit()
    return jsonify(conv.to_dict())


@bp.route('/ai/conversations')
@login_required
def list_conversations():
    convs = ChatConversation.query.filter_by(
        user_id=current_user.id
    ).order_by(ChatConversation.updated_at.desc()).all()
    return jsonify([c.to_dict() for c in convs])


@bp.route('/ai/conversations/<int:conv_id>')
@login_required
def get_conversation(conv_id):
    conv = ChatConversation.query.filter_by(id=conv_id, user_id=current_user.id).first()
    if not conv:
        return jsonify({'error': '对话不存在'}), 404
    return jsonify(conv.to_dict())


@bp.route('/ai/conversations/<int:conv_id>', methods=['DELETE'])
@login_required
def delete_conversation(conv_id):
    conv = ChatConversation.query.filter_by(id=conv_id, user_id=current_user.id).first()
    if not conv:
        return jsonify({'error': '对话不存在'}), 404
    db.session.delete(conv)
    db.session.commit()
    return jsonify({'ok': True})


# ── 投资数据上下文 ───────────────────────────────────────

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
