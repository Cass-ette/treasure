import time
import schedule
from threading import Thread
from app.services.fund_service import FundService
from app.services.calculation import CalculationService
from app.config import Config
import time
from datetime import datetime, time as datetime_time

class Scheduler:
    # 定义交易时间区间
    TRADING_START_TIME = datetime_time(15, 30)  # 下午3:30开始
    TRADING_END_TIME = datetime_time(2, 0)  # 凌晨2:00结束
    
    @staticmethod
    def start():
        """启动定时任务"""
        # 每日固定时间更新基金净值并计算盈亏
        schedule.every().day.at(Config.FUND_NAV_UPDATE_TIME).do(Scheduler.daily_task)
        
        # 启动定时检查任务（每分钟检查一次是否需要更新净值）
        schedule.every(1).minutes.do(Scheduler.check_and_update_nav)
        
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
    
    @staticmethod
    def check_and_update_nav():
        """检查是否需要更新净值并执行更新（交易日15:30至次日凌晨2点）"""
        if FundService.should_update_nav():
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f'[{current_time}] 执行定时净值更新...')
            
            # 更新所有基金净值
            updated_count = FundService.update_all_funds_nav()
            
            # 如果有净值更新，则计算盈亏
            if updated_count > 0:
                print(f'[{current_time}] 更新了 {updated_count} 只基金的净值，开始计算用户盈亏...')
                processed_count = CalculationService.process_all_users_profit()
                print(f'[{current_time}] 处理了 {processed_count} 个用户的盈亏计算')
            else:
                print(f'[{current_time}] 没有基金净值需要更新')