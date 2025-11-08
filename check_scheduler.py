"""
检查当前运行的调度器状态
"""

import asyncio
import sys
import requests

sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

async def check_scheduler_status():
    """检查调度器状态"""

    print("=" * 100)
    print("检查调度器状态")
    print("=" * 100)
    print()

    # 尝试通过API检查
    print("方法1: 通过后端日志检查")
    print()

    with open('/Users/uniteyoo/Documents/AutoMoney/.pids/backend.log', 'r') as f:
        lines = f.readlines()

    # 查找调度器相关日志
    print("📋 最近的调度器日志:")
    scheduler_logs = [line for line in lines if 'Scheduler' in line or '调度器' in line or 'scheduler' in line.lower()]

    if scheduler_logs:
        for log in scheduler_logs[-20:]:  # 最后20条
            print(f"  {log.strip()}")
    else:
        print("  ❌ 未找到调度器日志")

    print()
    print("-" * 100)
    print()

    # 查找策略执行日志
    print("📋 查找策略执行相关日志:")
    execution_logs = [line for line in lines if '策略执行' in line or 'execute_strategy' in line or 'execute_single_portfolio' in line]

    if execution_logs:
        for log in execution_logs[-10:]:
            print(f"  {log.strip()}")
    else:
        print("  ❌ 未找到策略执行日志")

    print()
    print("=" * 100)
    print("分析结论:")
    print("=" * 100)

    if scheduler_logs and '已为 1 个活跃策略添加定时任务' in ' '.join(scheduler_logs):
        print("✅ 调度器已启动并添加了任务")
    else:
        print("❌ 调度器未正确启动")

    if execution_logs:
        print("✅ 有策略执行记录")
    else:
        print("❌ 没有策略执行记录 - 定时任务可能未触发")
        print()
        print("可能原因:")
        print("1. 距离上次启动时间不到18分钟（执行周期）")
        print("2. 定时任务的回调函数有问题")
        print("3. 异步函数未被正确调度")

if __name__ == "__main__":
    asyncio.run(check_scheduler_status())
