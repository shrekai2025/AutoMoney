"""检查阈值配置是否生效"""

import asyncio
import sys
sys.path.insert(0, '/Users/uniteyoo/Documents/AutoMoney/AMbackend')

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, desc
from app.models.portfolio import Portfolio
from app.models.strategy_execution import StrategyExecution
from datetime import datetime, timedelta

DATABASE_URL = "postgresql+asyncpg://uniteyoo@localhost:5432/automoney"

async def check_threshold_changes():
    """检查阈值配置是否生效"""

    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    print("=" * 100)
    print("🔍 检查阈值配置是否生效")
    print("=" * 100)
    print()

    async with AsyncSessionLocal() as db:
        # 获取Portfolio
        portfolio_id = "e0d275e1-9e22-479c-b905-de44d9b66519"
        result = await db.execute(
            select(Portfolio).where(Portfolio.id == portfolio_id)
        )
        portfolio = result.scalar_one_or_none()

        if not portfolio:
            print("❌ Portfolio不存在")
            return

        print(f"📊 Portfolio: {portfolio.name}")
        print(f"   User ID: {portfolio.user_id}")
        print()

        # 显示当前阈值配置
        print("=" * 100)
        print("🎛️  当前阈值配置")
        print("=" * 100)
        print()

        print("Fear & Greed 相关阈值:")
        print(f"  • 熔断阈值 (Circuit Breaker): {portfolio.fg_circuit_breaker_threshold}")
        print(f"    → Fear & Greed < {portfolio.fg_circuit_breaker_threshold} 时，停止所有交易")
        print()
        print(f"  • 仓位调整阈值 (Position Adjust): {portfolio.fg_position_adjust_threshold}")
        print(f"    → Fear & Greed < {portfolio.fg_position_adjust_threshold} 时，减少仓位20%")
        print()

        print("Conviction Score 相关阈值:")
        print(f"  • 买入阈值 (Buy): {portfolio.buy_threshold}")
        print(f"    → Conviction Score >= {portfolio.buy_threshold} 时，生成BUY信号")
        print()
        print(f"  • 部分减仓阈值 (Partial Sell): {portfolio.partial_sell_threshold}")
        print(f"    → {portfolio.full_sell_threshold} <= Score < {portfolio.partial_sell_threshold} 时，部分减仓")
        print()
        print(f"  • 全部清仓阈值 (Full Sell): {portfolio.full_sell_threshold}")
        print(f"    → Conviction Score < {portfolio.full_sell_threshold} 时，全部清仓")
        print()

        # 检查是否是默认值
        is_default = (
            portfolio.fg_circuit_breaker_threshold == 20 and
            portfolio.fg_position_adjust_threshold == 30 and
            portfolio.buy_threshold == 50 and
            portfolio.partial_sell_threshold == 50 and
            portfolio.full_sell_threshold == 45
        )

        if is_default:
            print("💡 状态: 使用默认配置")
        else:
            print("✅ 状态: 已自定义配置")

            # 显示与默认值的差异
            print()
            print("与默认值的差异:")
            if portfolio.fg_circuit_breaker_threshold != 20:
                print(f"  • FG熔断阈值: {portfolio.fg_circuit_breaker_threshold} (默认: 20)")
            if portfolio.fg_position_adjust_threshold != 30:
                print(f"  • FG仓位调整阈值: {portfolio.fg_position_adjust_threshold} (默认: 30)")
            if portfolio.buy_threshold != 50:
                print(f"  • 买入阈值: {portfolio.buy_threshold} (默认: 50)")
            if portfolio.partial_sell_threshold != 50:
                print(f"  • 部分减仓阈值: {portfolio.partial_sell_threshold} (默认: 50)")
            if portfolio.full_sell_threshold != 45:
                print(f"  • 全部清仓阈值: {portfolio.full_sell_threshold} (默认: 45)")

        print()

        # 查看最近的策略执行记录
        print("=" * 100)
        print("📋 最近5条策略执行记录")
        print("=" * 100)
        print()

        stmt = (
            select(StrategyExecution)
            .where(StrategyExecution.user_id == portfolio.user_id)
            .order_by(StrategyExecution.execution_time.desc())
            .limit(5)
        )
        result = await db.execute(stmt)
        executions = result.scalars().all()

        if not executions:
            print("   暂无执行记录")
        else:
            for i, exe in enumerate(executions, 1):
                print(f"{i}. 执行时间: {exe.execution_time}")
                print(f"   状态: {exe.status}")

                if exe.conviction_score is not None:
                    print(f"   Conviction Score: {exe.conviction_score:.2f}")

                    # 根据当前阈值判断预期信号
                    if exe.conviction_score >= portfolio.buy_threshold:
                        expected = "BUY"
                    elif exe.conviction_score >= portfolio.full_sell_threshold:
                        expected = "SELL (部分)"
                    else:
                        expected = "SELL (全部)"

                    print(f"   信号: {exe.signal} (当前阈值下预期: {expected})")
                else:
                    print(f"   Conviction Score: N/A")
                    print(f"   信号: {exe.signal}")

                if exe.position_size:
                    print(f"   仓位大小: {exe.position_size:.6f}")

                print()

        # 检查Portfolio的更新时间
        print("=" * 100)
        print("🕐 配置更新历史")
        print("=" * 100)
        print()

        print(f"Portfolio创建时间: {portfolio.created_at}")
        print(f"最后更新时间: {portfolio.updated_at}")

        # 检查是否最近更新过
        if portfolio.updated_at:
            time_since_update = datetime.now() - portfolio.updated_at.replace(tzinfo=None)

            if time_since_update < timedelta(minutes=5):
                print(f"⏰ 最近更新: {int(time_since_update.total_seconds())}秒前")
                print("   ✅ 配置刚刚更新过")
            elif time_since_update < timedelta(hours=1):
                print(f"⏰ 最近更新: {int(time_since_update.total_seconds() / 60)}分钟前")
            else:
                print(f"⏰ 最近更新: {time_since_update}")

        print()

        # 提供测试建议
        print("=" * 100)
        print("📝 验证建议")
        print("=" * 100)
        print()

        print("如果你刚刚在前端修改了阈值，检查以下几点:")
        print()
        print("1. 确认上面显示的阈值是你期望的值")
        print("2. 如果阈值正确，说明前端→API→数据库的链路正常 ✅")
        print("3. 下次策略执行时，会使用上面显示的阈值")
        print("4. 可以通过查看'最近5条策略执行记录'验证信号是否符合预期")
        print()
        print("如果阈值不正确:")
        print("  • 检查前端是否成功保存（有无报错）")
        print("  • 检查浏览器控制台的Network请求")
        print("  • 确认API返回了success: true")

        print()
        print("=" * 100)
        print("✅ 检查完成")
        print("=" * 100)

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_threshold_changes())
