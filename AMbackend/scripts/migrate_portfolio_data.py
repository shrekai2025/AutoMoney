"""Data migration script to populate missing portfolio fields

This script fixes portfolios that were created before the strategy system refactoring.
It populates:
- instance_name (from existing 'name' field)
- strategy_definition_id (creates a default strategy definition if needed)
- instance_params (migrates old configuration fields)
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

from app.core.config import settings
from app.models.strategy_definition import StrategyDefinition
from app.models.portfolio import Portfolio


async def create_default_strategy_definition(session: AsyncSession) -> int:
    """Create a default strategy definition for legacy portfolios"""

    # Check if default strategy already exists
    result = await session.execute(
        select(StrategyDefinition).where(StrategyDefinition.name == "legacy_multi_agent_btc")
    )
    existing = result.scalar_one_or_none()

    if existing:
        print(f"Default strategy definition already exists (ID: {existing.id})")
        return existing.id

    # Create default strategy definition
    default_strategy = StrategyDefinition(
        name="legacy_multi_agent_btc",
        display_name="Legacy Multi-Agent BTC Strategy",
        description="Legacy strategy for migrated portfolios",
        decision_agent_module="app.decision_agents.multi_agent_conviction",
        decision_agent_class="MultiAgentConvictionDecision",
        business_agents=[
            {
                "agent_name": "macro_agent",
                "weight": 0.4
            },
            {
                "agent_name": "onchain_agent",
                "weight": 0.4
            },
            {
                "agent_name": "ta_agent",
                "weight": 0.2
            }
        ],
        trade_channel="paper",
        trade_symbol="BTC",
        rebalance_period_minutes=10,
        default_params={
            "consecutive_signal_threshold": 30,
            "acceleration_multiplier_min": 1.1,
            "acceleration_multiplier_max": 2.0,
            "fg_circuit_breaker_threshold": 20,
            "fg_position_adjust_threshold": 30,
            "buy_threshold": 50.0,
            "partial_sell_threshold": 50.0,
            "full_sell_threshold": 45.0,
            "agent_weights": {
                "macro": 0.4,
                "onchain": 0.4,
                "ta": 0.2
            }
        },
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    session.add(default_strategy)
    await session.flush()

    print(f"Created default strategy definition (ID: {default_strategy.id})")
    return default_strategy.id


async def migrate_portfolio_data():
    """Main migration function"""

    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # Get all portfolios
            result = await session.execute(select(Portfolio))
            portfolios = result.scalars().all()

            print(f"\nFound {len(portfolios)} portfolios to migrate")

            # Create default strategy definition if needed
            default_strategy_id = await create_default_strategy_definition(session)

            # Migrate each portfolio
            migrated_count = 0
            for portfolio in portfolios:
                needs_update = False

                # 1. Populate instance_name if missing
                if not portfolio.instance_name:
                    portfolio.instance_name = portfolio.name or "Legacy Portfolio"
                    needs_update = True
                    print(f"  Portfolio {portfolio.id}: Set instance_name = '{portfolio.instance_name}'")

                # 2. Populate strategy_definition_id if missing
                if not portfolio.strategy_definition_id:
                    portfolio.strategy_definition_id = default_strategy_id
                    needs_update = True
                    print(f"  Portfolio {portfolio.id}: Set strategy_definition_id = {default_strategy_id}")

                # 3. Populate instance_params if missing
                if not portfolio.instance_params:
                    portfolio.instance_params = {
                        "rebalance_period_minutes": 10,
                        "consecutive_signal_threshold": 30,
                        "acceleration_multiplier_min": 1.1,
                        "acceleration_multiplier_max": 2.0,
                        "fg_circuit_breaker_threshold": 20,
                        "fg_position_adjust_threshold": 30,
                        "buy_threshold": 50.0,
                        "partial_sell_threshold": 50.0,
                        "full_sell_threshold": 45.0,
                        "agent_weights": {
                            "macro": 0.4,
                            "onchain": 0.4,
                            "ta": 0.2
                        }
                    }
                    needs_update = True
                    print(f"  Portfolio {portfolio.id}: Set default instance_params")

                if needs_update:
                    portfolio.updated_at = datetime.utcnow()
                    migrated_count += 1

            # Commit all changes
            await session.commit()

            print(f"\n✅ Migration completed successfully!")
            print(f"   Total portfolios: {len(portfolios)}")
            print(f"   Migrated: {migrated_count}")
            print(f"   Skipped (already migrated): {len(portfolios) - migrated_count}")

        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            await session.rollback()
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    print("Starting portfolio data migration...")
    print("=" * 60)
    asyncio.run(migrate_portfolio_data())
