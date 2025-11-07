"""Market data API endpoints"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.services.data_collectors.manager import data_manager
from app.schemas.market_data import MarketDataSnapshot
from app.schemas.indicators import TechnicalIndicators

router = APIRouter()


@router.get("/snapshot", response_model=MarketDataSnapshot)
async def get_market_snapshot():
    """
    Get complete market data snapshot including:
    - BTC and ETH prices
    - OHLCV data (7 days)
    - On-chain metrics (if available)
    - Macro economic data (if available)
    - Fear & Greed Index

    This endpoint aggregates data from all configured sources.
    """
    try:
        snapshot = await data_manager.collect_all()
        return snapshot
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch market data: {str(e)}"
        )


@router.get("/fear-greed")
async def get_fear_greed_index():
    """
    Get current Fear & Greed Index from Alternative.me

    Returns:
        - value: Index value (0-100)
        - classification: "Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed"
        - timestamp: Unix timestamp of the data
    """
    try:
        data = await data_manager.alternative_me.collect()
        return data["index"]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch Fear & Greed Index: {str(e)}"
        )


@router.get("/prices")
async def get_current_prices():
    """
    Get current cryptocurrency prices (BTC and ETH)

    Returns price, volume, and 24h change for each asset.
    """
    try:
        data = await data_manager.binance.collect()
        return {
            "btc": data["btc"].dict(),
            "eth": data["eth"].dict(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch prices: {str(e)}"
        )


@router.get("/ohlcv")
async def get_ohlcv_data(
    symbol: str = Query("BTCUSDT", description="Trading pair symbol"),
    interval: str = Query("1h", description="Candle interval (1m, 5m, 15m, 1h, 4h, 1d)"),
    limit: int = Query(100, description="Number of candles", ge=1, le=1000)
):
    """
    Get OHLCV (candlestick) data from Binance

    Args:
        symbol: Trading pair (e.g., BTCUSDT, ETHUSDT)
        interval: Time interval (1m, 5m, 15m, 1h, 4h, 1d, 1w, 1M)
        limit: Number of candles (1-1000)

    Returns list of candles with open, high, low, close, volume data.
    """
    try:
        data = await data_manager.binance.get_ohlcv(
            symbol=symbol,
            interval=interval,
            limit=limit
        )
        return {"symbol": symbol, "interval": interval, "data": [candle.dict() for candle in data]}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch OHLCV data: {str(e)}"
        )


@router.get("/macro")
async def get_macroeconomic_data():
    """
    Get macroeconomic data from FRED (Federal Reserve Economic Data)

    Includes:
    - Federal Funds Rate (DFF)
    - M2 Money Supply Growth (M2SL)
    - US Dollar Index - DXY (DTWEXBGS)
    - 10-Year Treasury Rate (DGS10)

    Data is cached for 1 hour to respect API limits.
    """
    try:
        data = await data_manager.fred.collect()
        return data["data"]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch macroeconomic data: {str(e)}"
        )


@router.get("/indicators", response_model=TechnicalIndicators)
async def get_technical_indicators(
    symbol: str = Query("BTC/USDT", description="Trading pair symbol"),
    timeframe: str = Query("1h", description="Chart timeframe")
):
    """
    Get calculated technical indicators for a symbol

    Includes:
    - EMA (9, 21, 50, 200)
    - RSI (14 period)
    - MACD (12, 26, 9)
    - Bollinger Bands (20 period, 2 std)
    - Trading signals

    Data is calculated from recent 7-day OHLCV data.
    """
    try:
        indicators = await data_manager.get_technical_analysis(
            symbol=symbol,
            timeframe=timeframe
        )
        return indicators
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate indicators: {str(e)}"
        )


@router.get("/status")
async def get_collector_status():
    """
    Get status of all data collectors

    Shows which collectors are configured and when they last fetched data.
    Useful for debugging and monitoring.
    """
    try:
        status = data_manager.get_collector_status()
        return status
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get collector status: {str(e)}"
        )


@router.post("/cache/clear")
async def clear_cache():
    """
    Clear all cached data from all collectors

    Forces fresh data fetch on next request.
    Useful for testing and debugging.
    """
    try:
        data_manager.clear_all_caches()
        return {"message": "All caches cleared successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear caches: {str(e)}"
        )
