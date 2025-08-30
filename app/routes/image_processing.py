from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_required
from werkzeug.utils import secure_filename
import os
from app.services.ocr import OCRService

# 创建蓝图
bp = Blueprint('image_processing', __name__)

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# 配置上传文件夹
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads')

# 确保上传文件夹存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """检查文件是否为允许的类型"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/image/upload', methods=['GET', 'POST'])
@login_required
def upload_image():
    """上传图片并识别基金信息"""
    if request.method == 'POST':
        # 检查请求中是否有文件部分
        if 'file' not in request.files:
            flash('未找到文件！', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        
        # 如果用户没有选择文件，浏览器也会提交一个空文件
        if file.filename == '':
            flash('未选择文件！', 'danger')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            # 读取文件内容用于OCR
            file_content = file.read()
            
            # 尝试识别基金信息
            fund_info = OCRService.get_fund_info_from_image(file_content)
            
            if fund_info and (fund_info['code'] or fund_info['name']):
                # 显示识别结果
                return render_template('image_processing/result.html', fund_info=fund_info)
            else:
                flash('无法从图片中识别基金信息，请尝试另一张图片！', 'danger')
        else:
            flash('不支持的文件类型，请上传PNG、JPG、JPEG或GIF格式的图片！', 'danger')
    
    return render_template('image_processing/upload.html')

@bp.route('/image/history')
@login_required
def image_history():
    """查看图片处理历史记录"""
    # 目前只是一个简单的占位符，可以根据需要扩展
    return render_template('image_processing/history.html')