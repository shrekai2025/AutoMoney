"""API v1 router aggregation"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    market_data,
    research,
    portfolio,
    strategy,
    trades,
    admin,
    strategy_definitions,
    strategy_instances,
    exploration,
    system_monitoring,
    agent_monitor,
    api_test,
)


api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"],
)

api_router.include_router(
    market_data.router,
    prefix="/market",
    tags=["market-data"],
)

api_router.include_router(
    research.router,
    prefix="/research",
    tags=["research-chat"],
)

api_router.include_router(
    portfolio.router,
    prefix="/portfolios",
    tags=["portfolios"],
)

api_router.include_router(
    strategy.router,
    prefix="/strategy",
    tags=["strategy"],
)

api_router.include_router(
    trades.router,
    prefix="/trades",
    tags=["trades"],
)

api_router.include_router(
    admin.router,
    prefix="/admin",
    tags=["admin"],
)

api_router.include_router(
    strategy_definitions.router,
    prefix="/strategy-definitions",
    tags=["strategy-definitions"],
)

api_router.include_router(
    strategy_instances.router,
    prefix="/strategies",
    tags=["strategies"],
)

api_router.include_router(
    exploration.router,
    prefix="/exploration",
    tags=["exploration"],
)

api_router.include_router(
    system_monitoring.router,
    prefix="/monitoring",
    tags=["system-monitoring"],
)

api_router.include_router(
    agent_monitor.router,
    prefix="/agent-monitor",
    tags=["agent-monitor"],
)

api_router.include_router(
    api_test.router,
    prefix="/api-test",
    tags=["api-test"],
)
