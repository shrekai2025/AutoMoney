"""检查调度器状态"""
import asyncio
import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from app.services.strategy.scheduler import strategy_scheduler


async def check_scheduler():
    """检查调度器状态"""
    if not strategy_scheduler.scheduler:
        print("❌ 调度器未初始化")
        return

    print("=" * 80)
    print("调度器状态")
    print("=" * 80)
    print(f"运行状态: {strategy_scheduler.scheduler.state}")
    print(f"时区: {strategy_scheduler.scheduler.timezone}")
    print()

    jobs = strategy_scheduler.scheduler.get_jobs()
    print(f"任务数量: {len(jobs)}")
    print()

    for job in jobs:
        print(f"任务ID: {job.id}")
        print(f"  名称: {job.name}")
        print(f"  触发器: {job.trigger}")
        print(f"  下次运行: {job.next_run_time}")
        print(f"  函数: {job.func}")
        if job.args:
            print(f"  参数: {job.args}")
        print()


if __name__ == "__main__":
    asyncio.run(check_scheduler())
