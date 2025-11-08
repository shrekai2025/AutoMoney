"""检查调度器状态"""

import asyncio
import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from app.services.strategy.scheduler import strategy_scheduler


async def main():
    print("=" * 100)
    print("调度器状态检查")
    print("=" * 100)
    print()

    # 检查调度器对象
    print(f"1. Scheduler对象: {strategy_scheduler}")
    print(f"   类型: {type(strategy_scheduler)}")
    print()

    # 检查scheduler属性
    print(f"2. APScheduler实例: {strategy_scheduler.scheduler}")
    print()

    # 检查是否运行
    if hasattr(strategy_scheduler.scheduler, 'running'):
        print(f"3. 调度器运行状态: {strategy_scheduler.scheduler.running}")
    else:
        print(f"3. 调度器运行状态: Unknown")
    print()

    # 检查所有jobs
    if hasattr(strategy_scheduler.scheduler, 'get_jobs'):
        jobs = strategy_scheduler.scheduler.get_jobs()
        print(f"4. 已注册的任务数量: {len(jobs)}")

        if jobs:
            print()
            print("   任务列表:")
            for job in jobs:
                print(f"   - ID: {job.id}")
                print(f"     名称: {job.name}")
                print(f"     下次执行: {job.next_run_time}")
                print()
        else:
            print("   ⚠️ 没有任何任务被注册!")
    else:
        print(f"4. 无法获取任务列表")

    print()
    print("=" * 100)


if __name__ == "__main__":
    asyncio.run(main())
