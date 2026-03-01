#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""应用入口（替代 simple_app.py）"""

try:
    with open('banner.txt', 'r', encoding='utf-8') as f:
        print(f.read())
except Exception:
    print("投资管理系统启动中...")

from app import create_app
from app.services.scheduler import start_scheduler

app = create_app()

if __name__ == '__main__':
    print("正在启动投资管理系统...")
    print("应用已配置为绑定到所有网卡地址（0.0.0.0:5000）")
    print("您可以通过以下方式访问：")
    print("- 本地访问：http://127.0.0.1:5000")
    print("- 局域网访问：http://服务器局域网IP:5000")
    print("\n可用账户信息：")
    print("- 管理员账户：username=admin, password=admin123")

    # 启动定时任务线程
    start_scheduler(app)

    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)
