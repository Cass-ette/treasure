"""定时任务：批量更新所有基金净值"""
import threading
import time
import schedule


def batch_update_all_funds(app):
    """批量更新所有基金净值（传入 app 以获取上下文）"""
    with app.app_context():
        try:
            from app.models import Fund
            from app.services.crawler import update_fund_nav

            print("[定时任务] 开始批量更新所有基金净值")
            funds = Fund.query.all()
            print(f"[定时任务] 共有 {len(funds)} 个基金需要更新")

            success_count = 0
            fail_count = 0
            fail_funds = []

            for fund in funds:
                print(f"[定时任务] 开始更新基金：{fund.code} - {fund.name}")
                if update_fund_nav(fund.code):
                    success_count += 1
                    print(f"[定时任务] 基金 {fund.code} - {fund.name} 更新成功")
                else:
                    fail_count += 1
                    fail_funds.append(f"{fund.code} - {fund.name}")
                    print(f"[定时任务] 基金 {fund.code} - {fund.name} 更新失败")

            msg = f'[定时任务] 批量更新完成：成功 {success_count} 个，失败 {fail_count} 个'
            if fail_funds:
                preview = ', '.join(fail_funds[:5])
                ellipsis = '...' if len(fail_funds) > 5 else ''
                msg += f"\n失败的基金：{preview}{ellipsis}"
            print(msg)

        except Exception as e:
            print(f"[定时任务] 批量更新时发生错误：{str(e)}")
            import traceback
            traceback.print_exc()


def start_scheduler(app):
    """启动定时任务线程（每天 15:30 执行）"""
    print("[定时任务] 启动基金净值自动更新调度器")
    schedule.every().day.at("15:30").do(batch_update_all_funds, app)

    def _run():
        while True:
            schedule.run_pending()
            time.sleep(60)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return t
