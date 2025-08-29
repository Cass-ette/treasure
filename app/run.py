from . import app
from app.utils.scheduler import Scheduler

if __name__ == '__main__':
    # 启动定时任务
    Scheduler.start()
    
    # 运行Flask应用
    app.run(debug=True)