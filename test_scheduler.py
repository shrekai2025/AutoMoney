"""
测试脚本：验证调度器是否正常工作
"""

import asyncio
import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import datetime

# 测试变量
test_counter = 0

async def test_async_job():
    """测试异步Job"""
    global test_counter
    test_counter += 1
    print(f"[{datetime.datetime.now()}] ✓ Async Job executed! Counter: {test_counter}")

async def main():
    """主测试函数"""
    print("=" * 80)
    print("APScheduler AsyncIO 测试")
    print("=" * 80)
    print()

    scheduler = AsyncIOScheduler()

    # 添加测试任务（每3秒执行一次）
    scheduler.add_job(
        test_async_job,
        trigger=IntervalTrigger(seconds=3),
        id="test_job",
        name="测试Job",
        max_instances=1,
    )

    scheduler.start()
    print("✓ 调度器已启动")
    print("等待30秒观察Job执行情况...")
    print()

    # 等待30秒
    await asyncio.sleep(30)

    print()
    print("=" * 80)
    print(f"测试结果: Job 执行了 {test_counter} 次")
    print("预期: 应该执行约 10 次 (30秒 / 3秒)")

    if test_counter >= 8:
        print("✅ 测试通过: 调度器工作正常")
    else:
        print("❌ 测试失败: 调度器未正常工作")

    print("=" * 80)

    scheduler.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
