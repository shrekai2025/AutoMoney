"""Test scheduler execution manually"""
import asyncio
import sys
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from app.services.strategy.scheduler import strategy_scheduler

async def test_execution():
    """测试策略执行"""
    print("=== Testing Strategy Scheduler ===\n")

    # 初始化调度器
    await strategy_scheduler.initialize()

    # 检查调度器状态
    if strategy_scheduler.scheduler is None:
        print("❌ Scheduler not initialized")
        return

    print(f"✓ Scheduler initialized")
    print(f"  Scheduler state: {strategy_scheduler.scheduler}")

    # 手动执行策略模板 ID=3 (H.I.M.E.)
    print("\n=== Manually executing strategy template 3 (H.I.M.E.) ===")
    try:
        await strategy_scheduler.batch_execute_by_template(definition_id=3)
        print("✓ Execution completed")
    except Exception as e:
        print(f"❌ Execution failed: {e}")
        import traceback
        traceback.print_exc()

    # 手动执行策略模板 ID=1 (Multi-Agent)
    print("\n=== Manually executing strategy template 1 (Multi-Agent) ===")
    try:
        await strategy_scheduler.batch_execute_by_template(definition_id=1)
        print("✓ Execution completed")
    except Exception as e:
        print(f"❌ Execution failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_execution())
