"""API v1 router aggregation"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, market_data, research, portfolio, strategy, trades, marketplace, admin


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
    marketplace.router,
    prefix="/marketplace",
    tags=["marketplace"],
)

api_router.include_router(
    admin.router,
    prefix="/admin",
    tags=["admin"],
)
