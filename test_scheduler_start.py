"""测试调度器启动"""

import asyncio
import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from app.services.strategy.scheduler import strategy_scheduler


async def main():
    print("=" * 100)
    print("测试调度器启动")
    print("=" * 100)
    print()

    try:
        print("1. 调用 strategy_scheduler.start()...")
        await strategy_scheduler.start()
        print("   ✓ start() 执行成功")
        print()

        print("2. 检查调度器状态...")
        print(f"   运行状态: {strategy_scheduler.scheduler.running}")
        print(f"   已注册任务: {len(strategy_scheduler.scheduler.get_jobs())}")
        print()

        if strategy_scheduler.scheduler.get_jobs():
            print("3. 任务列表:")
            for job in strategy_scheduler.scheduler.get_jobs():
                print(f"   - {job.id}: {job.name}")
                print(f"     下次执行: {job.next_run_time}")
        else:
            print("3. ⚠️ 没有任务被注册")

        print()
        print("等待10秒观察任务执行...")
        await asyncio.sleep(10)

        print()
        print("4. 停止调度器...")
        strategy_scheduler.stop()
        print("   ✓ 调度器已停止")

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 100)


if __name__ == "__main__":
    asyncio.run(main())
