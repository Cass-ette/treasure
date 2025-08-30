from . import app
from app import app
from app.utils.scheduler import Scheduler

if __name__ == '__main__':
    # 启动定时任务
    Scheduler.start()
    
    # 运行Flask应用，绑定到所有网卡地址，支持公网访问
    # 注意：在生产环境中，请确保配置了适当的安全措施
    app.run(host='0.0.0.0', debug=True)