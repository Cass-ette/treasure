"""图片处理蓝图：upload, history"""
import os
import random
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.utils.helpers import allowed_file
from app.models.fund import Fund

bp = Blueprint('image', __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@bp.route('/image/upload', methods=['GET', 'POST'])
@login_required
def upload_image():
    """上传图片并识别基金信息（支持批量上传）"""
    if request.method == 'POST':
        files = []
        if 'files[]' in request.files:
            files = request.files.getlist('files[]')
        elif 'file' in request.files:
            files = [request.files['file']]

        if not files or all(f.filename == '' for f in files):
            flash('请选择至少一个文件！')
            return redirect(request.url)

        for f in files:
            if f and not allowed_file(f.filename):
                flash('不支持的文件类型，请仅上传PNG、JPG、JPEG或GIF格式的图片！')
                return redirect(request.url)

        # 模拟批量识别结果
        funds = Fund.query.all()
        recognized_funds = []

        example_codes = ['161725', '161726', '000001', '000002', '000003',
                         '000004', '000005', '000006', '001186', '001410']
        example_names = ['招商中证白酒指数(LOF)A', '招商中证白酒指数(LOF)C', '华夏成长混合', '华夏成长混合(后端)',
                         '华夏大盘精选混合', '华夏回报混合A', '华夏回报混合B', '华夏兴华混合A',
                         '易方达中小盘混合', '工银瑞信新金融股票']

        for f in files:
            if f and f.filename != '':
                num = random.randint(1, 3)
                for _ in range(num):
                    already = [r['code'] for r in recognized_funds]
                    available = [fd for fd in funds if fd.code not in already]
                    if available:
                        rf = random.choice(available)
                        recognized_funds.append({'code': rf.code, 'name': rf.name})
                    else:
                        idx = min(len(recognized_funds), len(example_codes) - 1)
                        recognized_funds.append({'code': example_codes[idx], 'name': example_names[idx]})

        return render_template('image_processing/batch_result.html', funds=recognized_funds)

    return render_template('image_processing/upload.html')


@bp.route('/image/history')
@login_required
def image_history():
    return render_template('image_processing/history.html')
