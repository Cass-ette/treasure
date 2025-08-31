# 此文件是为了兼容原有的启动方式，实际功能已移至simple_app.py
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入并运行simple_app.py
print("正在使用simple_app.py作为正式版本启动...")
exec(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'simple_app.py')).read())