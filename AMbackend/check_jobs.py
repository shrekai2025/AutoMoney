"""检查APScheduler任务状态"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.services.strategy.scheduler import strategy_scheduler

def check_scheduler_jobs():
    print("=" * 80)
    print("APScheduler 任务状态检查")
    print("=" * 80)
    
    if not strategy_scheduler.scheduler:
        print("❌ 调度器未初始化")
        return
    
    if not strategy_scheduler.scheduler.running:
        print("❌ 调度器未运行")
        return
    
    print("✅ 调度器正在运行")
    print()
    
    # 获取所有任务
    jobs = strategy_scheduler.scheduler.get_jobs()
    
    if not jobs:
        print("⚠️  没有任何已注册的任务")
        return
    
    print(f"📋 已注册任务数量: {len(jobs)}")
    print()
    
    for job in jobs:
        print(f"任务ID: {job.id}")
        print(f"  名称: {job.name}")
        print(f"  触发器: {job.trigger}")
        print(f"  下次执行: {job.next_run_time}")
        print()

if __name__ == "__main__":
    check_scheduler_jobs()
