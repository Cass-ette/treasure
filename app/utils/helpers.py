"""通用工具函数"""


def allowed_file(filename, allowed_extensions=None):
    """检查文件是否为允许的类型"""
    if allowed_extensions is None:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
