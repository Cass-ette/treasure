import schedule
import time
from threading import Thread
from app.services.fund_service import FundService
from app.services.calculation import CalculationService
from app.config import Config

class Scheduler:
    @staticmethod
    def start():
        """启动定时任务"""
        # 每日固定时间更新基金净值并计算盈亏
        schedule.every().day.at(Config.FUND_NAV_UPDATE_TIME).do(Scheduler.daily_task)
        
        # 启动定时任务线程
        thread = Thread(target=Scheduler._run_scheduler)
        thread.daemon = True
        thread.start()
    
    @staticmethod
    def _run_scheduler():
        """运行定时任务"""
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次
    
    @staticmethod
    def daily_task():
        """每日任务：更新基金净值并计算盈亏"""
        print(f'执行每日任务 - {time.strftime("%Y-%m-%d %H:%M:%S")}')
        
        # 更新所有基金净值
        updated_count = FundService.update_all_funds_nav()
        print(f'更新了 {updated_count} 只基金的净值')
        
        # 计算所有用户的盈亏
        processed_count = CalculationService.process_all_users_profit()
        print(f'处理了 {processed_count} 个用户的盈亏计算')