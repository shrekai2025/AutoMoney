"""全面debug agent重试机制"""

import asyncio
import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, desc
from app.models.portfolio import Portfolio
from app.models.strategy_execution import StrategyExecution
from app.models.agent_execution import AgentExecution
from app.services.strategy.scheduler import strategy_scheduler
from app.services.strategy.marketplace_service import marketplace_service

DATABASE_URL = "postgresql+asyncpg://uniteyoo@localhost:5432/automoney"

async def debug_full_flow():
    """全面测试从执行到展示的完整流程"""

    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    print("=" * 100)
    print("🔍 全面Debug Agent重试机制")
    print("=" * 100)
    print()

    # Step 1: 执行策略
    print("=" * 100)
    print("Step 1: 执行策略")
    print("=" * 100)

    await strategy_scheduler.initialize()
    portfolio_id = "e0d275e1-9e22-479c-b905-de44d9b66519"

    try:
        await strategy_scheduler.execute_single_portfolio(portfolio_id)
        print("✅ 策略执行完成")
    except Exception as e:
        print(f"⚠️ 策略执行异常: {e}")
    print()

    await strategy_scheduler.engine.dispose()

    # Step 2: 检查数据库中的执行记录
    print("=" * 100)
    print("Step 2: 检查数据库中的最新执行记录")
    print("=" * 100)

    async with AsyncSessionLocal() as db:
        # 查询最新的策略执行
        stmt = (
            select(StrategyExecution)
            .where(StrategyExecution.user_id == 1)
            .order_by(StrategyExecution.execution_time.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        latest_execution = result.scalar_one_or_none()

        if latest_execution:
            print(f"📊 策略执行记录:")
            print(f"   ID: {latest_execution.id}")
            print(f"   执行时间: {latest_execution.execution_time}")
            print(f"   状态: {latest_execution.status}")
            print(f"   Conviction Score: {latest_execution.conviction_score}")
            print(f"   Signal: {latest_execution.signal}")
            print(f"   错误消息: {latest_execution.error_message}")
            print(f"   错误详情: {latest_execution.error_details}")
            print()

            # 查询关联的Agent执行记录
            agent_stmt = (
                select(AgentExecution)
                .where(AgentExecution.strategy_execution_id == str(latest_execution.id))
            )
            agent_result = await db.execute(agent_stmt)
            agent_executions = agent_result.scalars().all()

            print(f"📋 关联的Agent执行记录 (共{len(agent_executions)}条):")
            for agent_exec in agent_executions:
                print(f"   - Agent: {agent_exec.agent_name}")
                print(f"     Status: {agent_exec.status}")
                print(f"     Signal: {agent_exec.signal}")
                print(f"     Confidence: {agent_exec.confidence}")
                print(f"     Score: {agent_exec.score}")
                print(f"     执行时长: {agent_exec.execution_duration_ms}ms")
            print()

    # Step 3: 测试API返回的数据
    print("=" * 100)
    print("Step 3: 测试API返回的策略详情")
    print("=" * 100)

    async with AsyncSessionLocal() as db:
        detail = await marketplace_service.get_strategy_detail(db, portfolio_id)

        print(f"📊 Conviction Summary:")
        print(f"   Score: {detail.conviction_summary.score}")
        print(f"   Message: {detail.conviction_summary.message[:150]}...")
        print(f"   Updated At: {detail.conviction_summary.updated_at}")
        print()

        print(f"📋 Recent Activities (最近{len(detail.recent_activities)}条):")
        for i, activity in enumerate(detail.recent_activities, 1):
            print(f"\n   🔸 Activity {i}:")
            print(f"      Date: {activity.date}")
            print(f"      Status: {activity.status}")
            print(f"      Signal: {activity.signal}")
            print(f"      Conviction Score: {activity.conviction_score}")

            if activity.status == "failed":
                print(f"      ⚠️ 错误状态检测:")
                print(f"         - Error Details存在: {activity.error_details is not None}")
                if activity.error_details:
                    print(f"         - Error Type: {activity.error_details.get('error_type')}")
                    print(f"         - Failed Agent: {activity.error_details.get('failed_agent')}")
                    print(f"         - Error Message: {activity.error_details.get('error_message')}")
                    print(f"         - Retry Count: {activity.error_details.get('retry_count')}")
                print(f"         - Agent Contributions: {activity.agent_contributions}")
            else:
                print(f"      ✅ 成功状态:")
                print(f"         - Action: {activity.action}")
                print(f"         - Result: {activity.result}")
                if activity.agent_contributions:
                    print(f"         - Agent Contributions: {len(activity.agent_contributions)}个agents")
                    for contrib in activity.agent_contributions:
                        print(f"           • {contrib.display_name}: {contrib.signal} (Score: {contrib.score}, Confidence: {contrib.confidence})")

    print()
    print("=" * 100)
    print("Step 4: 检查数据完整性")
    print("=" * 100)

    async with AsyncSessionLocal() as db:
        # 检查最近10条执行记录
        stmt = (
            select(StrategyExecution)
            .where(StrategyExecution.user_id == 1)
            .order_by(StrategyExecution.execution_time.desc())
            .limit(10)
        )
        result = await db.execute(stmt)
        executions = result.scalars().all()

        print(f"📊 最近10条执行记录统计:")
        success_count = 0
        failed_count = 0

        for exe in executions:
            if exe.status == "completed":
                success_count += 1
            elif exe.status == "failed":
                failed_count += 1
                print(f"   ❌ 失败记录: {exe.execution_time}")
                print(f"      Error: {exe.error_message}")
                print(f"      Details: {exe.error_details}")

        print(f"\n   总计: {len(executions)}条")
        print(f"   成功: {success_count}条")
        print(f"   失败: {failed_count}条")
        print()

    print("=" * 100)
    print("Step 5: 验证关键功能点")
    print("=" * 100)

    async with AsyncSessionLocal() as db:
        checks = []

        # Check 1: StrategyExecution模型是否有error_details字段
        stmt = select(StrategyExecution).limit(1)
        result = await db.execute(stmt)
        exe = result.scalar_one_or_none()
        if exe:
            has_error_details = hasattr(exe, 'error_details')
            checks.append(("StrategyExecution.error_details 字段存在", has_error_details))

        # Check 2: 最新的成功执行是否有完整的agent_executions
        stmt = (
            select(StrategyExecution)
            .where(StrategyExecution.user_id == 1)
            .where(StrategyExecution.status == "completed")
            .order_by(StrategyExecution.execution_time.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        success_exe = result.scalar_one_or_none()

        if success_exe:
            agent_stmt = (
                select(AgentExecution)
                .where(AgentExecution.strategy_execution_id == str(success_exe.id))
            )
            agent_result = await db.execute(agent_stmt)
            agent_execs = agent_result.scalars().all()

            has_3_agents = len(agent_execs) == 3
            checks.append(("成功执行有3个Agent记录", has_3_agents))

            all_agents_have_score = all(a.score is not None for a in agent_execs)
            checks.append(("所有Agent都有score字段", all_agents_have_score))

        # Check 3: API返回的RecentActivity是否包含status和error_details
        detail = await marketplace_service.get_strategy_detail(db, portfolio_id)
        if detail.recent_activities:
            first_activity = detail.recent_activities[0]
            has_status = hasattr(first_activity, 'status') and first_activity.status is not None
            has_error_details = hasattr(first_activity, 'error_details')
            checks.append(("RecentActivity有status字段", has_status))
            checks.append(("RecentActivity有error_details字段", has_error_details))

        # 打印检查结果
        print("\n📋 功能检查清单:")
        for check_name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"   {status} {check_name}")

        all_passed = all(passed for _, passed in checks)
        print()
        if all_passed:
            print("🎉 所有检查通过！")
        else:
            print("⚠️ 部分检查失败，请查看上面的详情")

    print()
    print("=" * 100)
    print("✅ Debug完成")
    print("=" * 100)

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(debug_full_flow())
