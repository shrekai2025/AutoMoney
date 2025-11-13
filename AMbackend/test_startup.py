"""测试启动流程"""
import asyncio
import sys

async def test_lifespan():
    print("=" * 80)
    print("测试 FastAPI lifespan 启动流程")
    print("=" * 80)
    
    # 模拟 lifespan startup
    print("\n1. Starting AutoMoney Backend v2.0.0")
    
    # Firebase
    try:
        from app.core.firebase import initialize_firebase
        initialize_firebase()
        print("2. ✓ Firebase initialized successfully")
    except Exception as e:
        print(f"2. ⚠ Warning: Firebase initialization failed: {e}")
    
    # Scheduler
    try:
        from app.services.strategy.scheduler import strategy_scheduler
        print("\n3. 开始启动 Strategy Scheduler...")
        await strategy_scheduler.start()
        print("4. ✓ Strategy scheduler started successfully")
        
        # 检查状态
        if strategy_scheduler.scheduler:
            print(f"   - Scheduler running: {strategy_scheduler.scheduler.running}")
            jobs = strategy_scheduler.scheduler.get_jobs()
            print(f"   - Jobs registered: {len(jobs)}")
            for job in jobs:
                print(f"     * {job.id}: {job.name} (next: {job.next_run_time})")
        else:
            print("   - ❌ Scheduler is None!")
            
    except Exception as e:
        print(f"4. ⚠ Warning: Strategy scheduler initialization failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_lifespan())
