"""测试失败场景的完整流程"""

import asyncio
import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from app.models.strategy_execution import StrategyExecution
from app.services.strategy.strategy_orchestrator import strategy_orchestrator
from app.services.strategy.marketplace_service import marketplace_service

DATABASE_URL = "postgresql+asyncpg://uniteyoo@localhost:5432/automoney"

async def test_failure_scenario():
    """测试Agent失败时的完整流程"""

    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    print("=" * 100)
    print("🔍 测试Agent失败场景的完整流程")
    print("=" * 100)
    print()

    # 模拟失败：传入空的market_data
    print("Step 1: 模拟Agent失败（传入空market_data）")
    print("-" * 100)

    async with AsyncSessionLocal() as db:
        try:
            # 传入空数据会导致所有Agent失败
            result = await strategy_orchestrator.execute_strategy(
                db=db,
                user_id=1,
                portfolio_id="e0d275e1-9e22-479c-b905-de44d9b66519",
                market_data={},  # 空数据
            )
            print(f"❌ 意外：策略执行成功了 (Status: {result.status})")
        except Exception as e:
            print(f"⚠️ 策略执行异常（这可能是正常的）: {e}")

        await db.commit()

    print()
    print("Step 2: 检查数据库中是否记录了失败")
    print("-" * 100)

    async with AsyncSessionLocal() as db:
        # 查询最近的执行记录，包括失败的
        stmt = (
            select(StrategyExecution)
            .where(StrategyExecution.user_id == 1)
            .order_by(StrategyExecution.execution_time.desc())
            .limit(5)
        )
        result = await db.execute(stmt)
        executions = result.scalars().all()

        print(f"\n📊 最近5条执行记录:")
        failed_found = False
        for i, exe in enumerate(executions, 1):
            status_symbol = "❌" if exe.status == "failed" else "✅"
            print(f"\n   {status_symbol} 执行 {i}:")
            print(f"      时间: {exe.execution_time}")
            print(f"      状态: {exe.status}")
            print(f"      Conviction: {exe.conviction_score}")
            print(f"      Signal: {exe.signal}")

            if exe.status == "failed":
                failed_found = True
                print(f"      ⚠️ 错误信息:")
                print(f"         - Error Message: {exe.error_message}")
                print(f"         - Error Details: {exe.error_details}")

                if exe.error_details:
                    print(f"         - Error Type: {exe.error_details.get('error_type')}")
                    print(f"         - Failed Agent: {exe.error_details.get('failed_agent')}")
                    print(f"         - Retry Count: {exe.error_details.get('retry_count')}")

        if not failed_found:
            print("\n   ℹ️  未找到失败记录（可能是因为Agent执行成功或之前没有失败）")

    print()
    print("Step 3: 测试API过滤逻辑")
    print("-" * 100)

    async with AsyncSessionLocal() as db:
        portfolio_id = "e0d275e1-9e22-479c-b905-de44d9b66519"

        # 获取策略详情
        detail = await marketplace_service.get_strategy_detail(db, portfolio_id)

        print(f"\n📊 Conviction Summary (应该只来自成功的执行):")
        print(f"   Score: {detail.conviction_summary.score}")
        print(f"   Updated At: {detail.conviction_summary.updated_at}")

        # 检查最新的成功执行
        success_stmt = (
            select(StrategyExecution)
            .where(StrategyExecution.user_id == 1)
            .where(StrategyExecution.status == "completed")
            .order_by(StrategyExecution.execution_time.desc())
            .limit(1)
        )
        success_result = await db.execute(success_stmt)
        latest_success = success_result.scalar_one_or_none()

        if latest_success:
            print(f"\n   ✅ 最新成功执行:")
            print(f"      时间: {latest_success.execution_time}")
            print(f"      Score: {latest_success.conviction_score}")

            matches = (
                latest_success.conviction_score == detail.conviction_summary.score
                and latest_success.execution_time == detail.conviction_summary.updated_at
            )
            if matches:
                print(f"      ✅ Conviction Summary正确来自最新的成功执行")
            else:
                print(f"      ⚠️ Conviction Summary可能不是来自最新的成功执行")

        print(f"\n📋 Recent Activities:")
        for i, activity in enumerate(detail.recent_activities, 1):
            status_symbol = "❌" if activity.status == "failed" else "✅"
            print(f"\n   {status_symbol} Activity {i}:")
            print(f"      Status: {activity.status}")
            print(f"      Signal: {activity.signal}")

            if activity.status == "failed":
                print(f"      ⚠️ 错误处理验证:")
                print(f"         - 有error_details: {activity.error_details is not None}")
                print(f"         - 有agent_contributions: {activity.agent_contributions is not None}")
                print(f"         - agent_contributions应该为None: {activity.agent_contributions is None}")

                if activity.error_details:
                    print(f"         - Failed Agent: {activity.error_details.get('failed_agent')}")
                    print(f"         - Error Message: {activity.error_details.get('error_message')}")
            else:
                print(f"      ✅ 成功处理验证:")
                print(f"         - 有agent_contributions: {activity.agent_contributions is not None}")
                if activity.agent_contributions:
                    print(f"         - Agent数量: {len(activity.agent_contributions)}")

    print()
    print("=" * 100)
    print("Step 4: 功能验证总结")
    print("=" * 100)

    async with AsyncSessionLocal() as db:
        checks = []

        # Check 1: 失败的执行是否有error_details
        stmt = (
            select(StrategyExecution)
            .where(StrategyExecution.status == "failed")
            .limit(1)
        )
        result = await db.execute(stmt)
        failed_exe = result.scalar_one_or_none()

        if failed_exe:
            has_error_details = failed_exe.error_details is not None
            checks.append(("失败执行有error_details", has_error_details))

            if failed_exe.error_details:
                has_failed_agent = 'failed_agent' in failed_exe.error_details
                has_error_message = 'error_message' in failed_exe.error_details
                checks.append(("error_details包含failed_agent", has_failed_agent))
                checks.append(("error_details包含error_message", has_error_message))
        else:
            checks.append(("找到失败执行记录", False))

        # Check 2: Conviction Summary来自成功执行
        detail = await marketplace_service.get_strategy_detail(
            db, "e0d275e1-9e22-479c-b905-de44d9b66519"
        )

        success_stmt = (
            select(StrategyExecution)
            .where(StrategyExecution.user_id == 1)
            .where(StrategyExecution.status == "completed")
            .order_by(StrategyExecution.execution_time.desc())
            .limit(1)
        )
        success_result = await db.execute(success_stmt)
        latest_success = success_result.scalar_one_or_none()

        if latest_success:
            conviction_from_success = (
                detail.conviction_summary.updated_at == latest_success.execution_time
            )
            checks.append(("Conviction Summary来自成功执行", conviction_from_success))

        # Check 3: RecentActivity正确处理失败状态
        if detail.recent_activities:
            failed_activities = [a for a in detail.recent_activities if a.status == "failed"]
            if failed_activities:
                failed_activity = failed_activities[0]
                no_agent_contrib_on_fail = failed_activity.agent_contributions is None
                has_error_details_on_fail = failed_activity.error_details is not None
                checks.append(("失败Activity无agent_contributions", no_agent_contrib_on_fail))
                checks.append(("失败Activity有error_details", has_error_details_on_fail))

        # 打印检查结果
        print("\n📋 功能检查清单:")
        for check_name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"   {status} {check_name}")

        passed_count = sum(1 for _, p in checks if p)
        total_count = len(checks)

        print(f"\n   总计: {passed_count}/{total_count} 通过")

        if passed_count == total_count:
            print("\n   🎉 所有检查通过！")
        else:
            print(f"\n   ⚠️ {total_count - passed_count}项检查失败")

    print()
    print("=" * 100)
    print("✅ 测试完成")
    print("=" * 100)

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_failure_scenario())
