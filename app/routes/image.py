"""基金图片识别蓝图：上传图片 → OCR识别 → 天天基金网搜索 → 选择导入"""
import os
import re
import io
import requests
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.utils.helpers import allowed_file
from app.extensions import db
from app.models.fund import Fund

bp = Blueprint('image', __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

SEARCH_API = 'https://fundsuggest.eastmoney.com/FundSearch/api/FundSearchAPI.ashx'
HEADERS = {
    'Referer': 'https://fund.eastmoney.com/',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
}


def _ocr_extract_keywords(image_bytes):
    """用 OCR 从图片中提取基金代码和中文关键词"""
    try:
        import pytesseract
        from PIL import Image, ImageFilter, ImageEnhance
    except ImportError:
        return []

    img = Image.open(io.BytesIO(image_bytes))

    # 灰度 + 增强对比度，提升 OCR 准确率
    img = img.convert('L')
    img = ImageEnhance.Contrast(img).enhance(2.0)
    img = img.filter(ImageFilter.SHARPEN)

    text = pytesseract.image_to_string(img, lang='chi_sim+eng', config='--psm 11')

    keywords = set()

    # 提取6位纯数字基金代码
    for code in re.findall(r'\b\d{6}\b', text):
        keywords.add(code)

    # 提取2字以上的中文词（过滤单字噪音）
    chinese_words = re.findall(r'[\u4e00-\u9fa5]{2,}', text)
    for word in chinese_words:
        # 过滤常见无意义词
        if word not in {'基金', '净值', '日期', '份额', '持仓', '收益', '累计', '单位', '万元',
                        '账户', '金额', '时间', '更新', '今日', '昨日', '市值', '成本', '盈亏'}:
            keywords.add(word)

    return list(keywords)


def _search_eastmoney(keyword):
    """从天天基金网搜索基金"""
    try:
        resp = requests.get(
            SEARCH_API,
            params={'m': 1, 'key': keyword},
            headers=HEADERS,
            timeout=8,
        )
        data = resp.json()
        if data.get('ErrCode') != 0:
            return []

        results = []
        for item in data.get('Datas', []):
            if item.get('CATEGORY') != 700:  # 只要基金
                continue
            base = item.get('FundBaseInfo') or {}
            code = item.get('CODE', '')
            results.append({
                'code': code,
                'name': item.get('NAME', ''),
                'type': base.get('FTYPE', ''),
                'nav': base.get('DWJZ'),
                'nav_date': base.get('FSRQ', ''),
                'company': base.get('JJGS', ''),
                'manager': base.get('JJJL', ''),
                'in_system': Fund.query.filter_by(code=code).first() is not None,
            })
        return results
    except Exception:
        return []


@bp.route('/image/upload')
@login_required
def upload_image():
    return render_template('image_processing/upload.html')


@bp.route('/image/recognize', methods=['POST'])
@login_required
def recognize():
    """上传图片，OCR识别后搜索天天基金网，返回候选基金列表"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '请选择图片文件'})

    f = request.files['file']
    if not f.filename or not allowed_file(f.filename):
        return jsonify({'success': False, 'message': '不支持的文件类型，请上传 PNG/JPG/JPEG/GIF'})

    image_bytes = f.read()
    keywords = _ocr_extract_keywords(image_bytes)

    if not keywords:
        return jsonify({'success': False, 'message': '未能从图片中识别出任何基金相关信息，请确认图片清晰且包含基金信息'})

    # 对每个关键词搜索，合并去重结果
    seen_codes = set()
    all_funds = []
    for kw in keywords[:8]:  # 最多取8个关键词避免请求过多
        for fund in _search_eastmoney(kw):
            if fund['code'] not in seen_codes:
                seen_codes.add(fund['code'])
                all_funds.append(fund)

    if not all_funds:
        return jsonify({
            'success': True,
            'keywords': keywords,
            'funds': [],
            'message': f'识别到关键词 {", ".join(keywords[:5])}，但未在天天基金网找到匹配基金'
        })

    return jsonify({
        'success': True,
        'keywords': keywords[:10],
        'funds': all_funds[:30],  # 最多返回30条
    })


@bp.route('/image/search', methods=['POST'])
@login_required
def search_fund():
    """手动关键词搜索（用于修正/补充识别结果）"""
    keyword = request.form.get('keyword', '').strip()
    if not keyword:
        return jsonify({'success': False, 'message': '请输入搜索关键词'})
    funds = _search_eastmoney(keyword)
    return jsonify({'success': True, 'funds': funds})


@bp.route('/image/import_fund', methods=['POST'])
@login_required
def import_fund():
    """将选中的基金导入系统"""
    if not current_user.is_main_account:
        return jsonify({'success': False, 'message': '只有管理员可以导入基金'})

    code = request.form.get('code', '').strip()
    name = request.form.get('name', '').strip()
    fund_type = request.form.get('type', '').strip()
    nav = request.form.get('nav', '').strip()
    nav_date = request.form.get('nav_date', '').strip()

    if not code:
        return jsonify({'success': False, 'message': '基金代码不能为空'})

    if Fund.query.filter_by(code=code).first():
        return jsonify({'success': False, 'message': f'基金 {code} 已存在于系统中'})

    try:
        from datetime import datetime
        fund = Fund(
            code=code,
            name=name,
            fund_type=fund_type or None,
            latest_nav=float(nav) if nav else None,
            nav_date=datetime.strptime(nav_date, '%Y-%m-%d') if nav_date else None,
        )
        db.session.add(fund)
        db.session.commit()
        return jsonify({'success': True, 'message': f'{name} 导入成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'导入失败: {str(e)}'})


@bp.route('/image/history')
@login_required
def image_history():
    return render_template('image_processing/history.html')
