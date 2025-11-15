"""API Test Endpoint - API连接测试

测试所有外部API的连接状态和数据返回
"""

import logging
import asyncio
from typing import Dict, Any, List
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_optional_user
from app.models import User

logger = logging.getLogger(__name__)

router = APIRouter(redirect_slashes=False)


@router.get("/test-all-apis")
async def test_all_apis(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_optional_user),
):
    """
    测试所有外部API连接

    返回每个API的测试结果，包括：
    - 连接状态
    - 响应时间
    - 返回的数据
    - 错误信息（如果有）
    """
    results = []

    # 1. 测试 Binance API
    binance_result = await _test_binance_api()
    results.append(binance_result)

    # 2. 测试 FRED API
    fred_result = await _test_fred_api()
    results.append(fred_result)

    # 3. 测试 Fear & Greed API
    fear_greed_result = await _test_fear_greed_api()
    results.append(fear_greed_result)

    # 4. 测试 Glassnode API
    glassnode_result = await _test_glassnode_api()
    results.append(glassnode_result)

    # 5. 测试完整市场数据采集
    market_data_result = await _test_market_data_collection()
    results.append(market_data_result)

    # 统计
    total = len(results)
    success = sum(1 for r in results if r["status"] == "success")
    failed = total - success

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "summary": {
            "total": total,
            "success": success,
            "failed": failed,
            "success_rate": f"{(success/total*100):.1f}%" if total > 0 else "0%",
        },
        "results": results,
    }


async def _test_binance_api() -> Dict[str, Any]:
    """测试Binance API"""
    start_time = datetime.utcnow()

    try:
        from app.services.data_collectors.binance import BinanceCollector

        collector = BinanceCollector()

        # 测试获取价格数据
        data = await collector.collect()

        duration = (datetime.utcnow() - start_time).total_seconds()

        return {
            "api_name": "Binance API",
            "status": "success",
            "duration_seconds": round(duration, 3),
            "data": data,
            "error": None,
        }

    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.error(f"Binance API test failed: {e}")

        return {
            "api_name": "Binance API",
            "status": "failed",
            "duration_seconds": round(duration, 3),
            "data": None,
            "error": {
                "type": type(e).__name__,
                "message": str(e),
            },
        }


async def _test_fred_api() -> Dict[str, Any]:
    """测试FRED API"""
    start_time = datetime.utcnow()

    try:
        from app.services.data_collectors.fred import FREDCollector
        from app.core.config import settings

        # 使用配置中的API key
        collector = FREDCollector(api_key=settings.FRED_API_KEY)

        # 测试获取宏观经济数据
        data = await collector.collect()

        duration = (datetime.utcnow() - start_time).total_seconds()

        return {
            "api_name": "FRED API (Federal Reserve)",
            "status": "success",
            "duration_seconds": round(duration, 3),
            "data": data,
            "error": None,
        }

    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.error(f"FRED API test failed: {e}")

        return {
            "api_name": "FRED API (Federal Reserve)",
            "status": "failed",
            "duration_seconds": round(duration, 3),
            "data": None,
            "error": {
                "type": type(e).__name__,
                "message": str(e),
            },
        }


async def _test_fear_greed_api() -> Dict[str, Any]:
    """测试Fear & Greed Index API"""
    start_time = datetime.utcnow()

    try:
        from app.services.data_collectors.alternative_me import AlternativeMeCollector

        collector = AlternativeMeCollector()
        data = await collector.collect()

        duration = (datetime.utcnow() - start_time).total_seconds()

        return {
            "api_name": "Fear & Greed Index API",
            "status": "success",
            "duration_seconds": round(duration, 3),
            "data": data,
            "error": None,
        }

    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.error(f"Fear & Greed API test failed: {e}")

        return {
            "api_name": "Fear & Greed Index API",
            "status": "failed",
            "duration_seconds": round(duration, 3),
            "data": None,
            "error": {
                "type": type(e).__name__,
                "message": str(e),
            },
        }


async def _test_glassnode_api() -> Dict[str, Any]:
    """测试Glassnode API"""
    start_time = datetime.utcnow()

    try:
        from app.services.data_collectors.glassnode import GlassnodeCollector
        from app.core.config import settings

        collector = GlassnodeCollector(api_key=settings.GLASSNODE_API_KEY if hasattr(settings, 'GLASSNODE_API_KEY') else "")

        # 测试获取链上数据
        data = await collector.collect()

        duration = (datetime.utcnow() - start_time).total_seconds()

        return {
            "api_name": "Glassnode API",
            "status": "success",
            "duration_seconds": round(duration, 3),
            "data": data,
            "error": None,
        }

    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.error(f"Glassnode API test failed: {e}")

        return {
            "api_name": "Glassnode API",
            "status": "failed",
            "duration_seconds": round(duration, 3),
            "data": None,
            "error": {
                "type": type(e).__name__,
                "message": str(e),
            },
        }


async def _test_market_data_collection() -> Dict[str, Any]:
    """测试完整市场数据采集"""
    start_time = datetime.utcnow()

    try:
        from app.services.data_collectors.manager import data_manager

        # 使用data_manager采集所有数据
        snapshot = await data_manager.collect_all()

        duration = (datetime.utcnow() - start_time).total_seconds()

        return {
            "api_name": "Complete Market Data Collection",
            "status": "success",
            "duration_seconds": round(duration, 3),
            "data": {
                "btc_price": snapshot.btc_price.price if snapshot.btc_price else None,
                "eth_price": snapshot.eth_price.price if snapshot.eth_price else None,
                "fear_greed": snapshot.fear_greed.value if snapshot.fear_greed else None,
                "macro_data_available": snapshot.macro is not None,
                "onchain_data_available": snapshot.onchain is not None,
                "timestamp": snapshot.timestamp.isoformat() if snapshot.timestamp else None,
            },
            "error": None,
        }

    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds()
        logger.error(f"Market data collection test failed: {e}")

        return {
            "api_name": "Complete Market Data Collection",
            "status": "failed",
            "duration_seconds": round(duration, 3),
            "data": None,
            "error": {
                "type": type(e).__name__,
                "message": str(e),
            },
        }
