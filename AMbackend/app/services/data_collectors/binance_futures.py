"""Binance Futures data collector for derivatives metrics"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from app.services.data_collectors.base import DataCollector


class BinanceFuturesCollector(DataCollector):
    """
    Binance Futures API collector for derivatives data
    
    Documentation: https://binance-docs.github.io/apidocs/futures/en/
    
    Provides:
    - Funding rate (资金费率)
    - Open interest (持仓量)
    - Futures premium rate (期货溢价率)
    """
    
    def __init__(self, api_key: str = "", api_secret: str = ""):
        """
        Initialize Binance Futures collector
        
        Args:
            api_key: Binance API key (optional for public endpoints)
            api_secret: Binance API secret
        """
        super().__init__(
            api_key=api_key, 
            base_url="https://fapi.binance.com"  # Futures base URL
        )
        self.api_secret = api_secret
    
    async def collect(self) -> Dict[str, Any]:
        """
        Implement abstract collect method - collects all futures data
        
        Returns:
            Dict containing futures data for all supported symbols
        """
        symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        result = {}
        
        for symbol in symbols:
            try:
                coin = symbol.replace("USDT", "")
                result[coin] = {
                    "funding_rate": await self.get_funding_rate(symbol),
                    "open_interest": await self.get_open_interest(symbol),
                    "futures_premium": await self.get_futures_premium(symbol)
                }
            except Exception as e:
                # Log error but continue with other symbols
                result[coin] = {
                    "funding_rate": {"error": str(e)},
                    "open_interest": {"error": str(e)},
                    "futures_premium": {"error": str(e)}
                }
        
        return result
    
    async def get_funding_rate(self, symbol: str = "BTCUSDT") -> Dict[str, Any]:
        """
        Get current and historical funding rate
        
        Args:
            symbol: Futures symbol (e.g., 'BTCUSDT')
        
        Returns:
            {
                "symbol": "BTCUSDT",
                "current_funding_rate": 0.0001,
                "next_funding_time": "2025-11-13T16:00:00",
                "avg_funding_rate_8h": 0.00012
            }
        
        API Endpoint: GET /fapi/v1/fundingRate
        """
        cache_key = f"funding_rate_{symbol}"
        cached = await self.get_cached_data(cache_key, max_age_seconds=3600)  # 1 hour cache
        if cached:
            return cached
        
        # Get latest funding rate
        response = await self.get(
            "/fapi/v1/fundingRate",
            params={"symbol": symbol, "limit": 8}  # Last 8 funding rates (24 hours)
        )
        
        if not response:
            raise ValueError(f"No funding rate data for {symbol}")
        
        # Calculate average funding rate over last 8 hours (8 periods × 1 hour each)
        funding_rates = [float(r["fundingRate"]) for r in response]
        avg_funding_rate = sum(funding_rates) / len(funding_rates) if funding_rates else 0.0
        
        result = {
            "symbol": symbol,
            "current_funding_rate": float(response[0]["fundingRate"]),
            "next_funding_time": datetime.fromtimestamp(response[0]["fundingTime"] / 1000).isoformat(),
            "avg_funding_rate_8h": avg_funding_rate,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.set_cache(cache_key, result)
        return result
    
    async def get_open_interest(self, symbol: str = "BTCUSDT") -> Dict[str, Any]:
        """
        Get current open interest and 24h change
        
        Args:
            symbol: Futures symbol
        
        Returns:
            {
                "symbol": "BTCUSDT",
                "open_interest": 123456.78,  // Current open interest
                "open_interest_value_usd": 12345678900.0,
                "open_interest_change_24h_pct": 5.2  // Percentage change
            }
        
        API Endpoint: GET /fapi/v1/openInterest
        """
        cache_key = f"open_interest_{symbol}"
        cached = await self.get_cached_data(cache_key, max_age_seconds=600)  # 10 min cache
        if cached:
            return cached
        
        # Get current open interest
        response = await self.get(
            "/fapi/v1/openInterest",
            params={"symbol": symbol}
        )
        
        if not response:
            raise ValueError(f"No open interest data for {symbol}")
        
        # Get historical open interest for 24h change calculation
        hist_response = await self.get(
            "/futures/data/openInterestHist",
            params={
                "symbol": symbol,
                "period": "1h",
                "limit": 24  # Last 24 hours
            }
        )
        
        # Calculate 24h change
        open_interest_change_24h_pct = 0.0
        if hist_response and len(hist_response) >= 2:
            try:
                current_oi = float(hist_response[0]["sumOpenInterest"])
                oi_24h_ago = float(hist_response[-1]["sumOpenInterest"])
                open_interest_change_24h_pct = ((current_oi - oi_24h_ago) / oi_24h_ago) * 100
            except (ValueError, KeyError, ZeroDivisionError):
                pass
        
        result = {
            "symbol": symbol,
            "open_interest": float(response["openInterest"]),
            "open_interest_value_usd": float(response["openInterest"]) * float(response.get("price", 0)),
            "open_interest_change_24h_pct": round(open_interest_change_24h_pct, 2),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.set_cache(cache_key, result)
        return result
    
    async def get_futures_premium(
        self, 
        symbol: str = "BTCUSDT",
        spot_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculate futures premium rate
        
        Premium = (Futures Price - Spot Price) / Spot Price × 100%
        
        Args:
            symbol: Futures symbol
            spot_price: Current spot price (if not provided, will fetch from API)
        
        Returns:
            {
                "symbol": "BTCUSDT",
                "futures_price": 95300.0,
                "spot_price": 95250.0,
                "premium_rate_pct": 0.05  // Percentage premium
            }
        
        API Endpoint: GET /fapi/v1/ticker/price (futures)
                      GET /api/v3/ticker/price (spot)
        """
        cache_key = f"futures_premium_{symbol}"
        cached = await self.get_cached_data(cache_key, max_age_seconds=60)  # 1 min cache
        if cached:
            return cached
        
        # Get futures price
        futures_response = await self.get(
            "/fapi/v1/ticker/price",
            params={"symbol": symbol}
        )
        
        if not futures_response:
            raise ValueError(f"No futures price data for {symbol}")
        
        futures_price = float(futures_response["price"])
        
        # Get spot price if not provided
        if spot_price is None:
            # Use spot API
            spot_response = await self.get(
                "/api/v3/ticker/price",
                params={"symbol": symbol},
                base_url="https://api.binance.com"  # Override to spot API
            )
            spot_price = float(spot_response["price"])
        
        # Calculate premium
        premium_rate_pct = ((futures_price - spot_price) / spot_price) * 100 if spot_price > 0 else 0.0
        
        result = {
            "symbol": symbol,
            "futures_price": futures_price,
            "spot_price": spot_price,
            "premium_rate_pct": round(premium_rate_pct, 4),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.set_cache(cache_key, result)
        return result
    
    async def collect_all_derivatives(
        self, 
        symbols: List[str] = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Collect all derivatives data for multiple symbols
        
        Args:
            symbols: List of futures symbols
        
        Returns:
            {
                "BTCUSDT": {
                    "funding_rate": {...},
                    "open_interest": {...},
                    "futures_premium": {...}
                },
                "ETHUSDT": {...},
                "SOLUSDT": {...}
            }
        """
        results = {}
        
        for symbol in symbols:
            try:
                funding = await self.get_funding_rate(symbol)
                oi = await self.get_open_interest(symbol)
                premium = await self.get_futures_premium(symbol)
                
                results[symbol] = {
                    "funding_rate": funding,
                    "open_interest": oi,
                    "futures_premium": premium
                }
            except Exception as e:
                print(f"Error collecting derivatives data for {symbol}: {e}")
                # Partial failure is acceptable
                results[symbol] = {
                    "error": str(e)
                }
        
        return results
    
    @property
    def is_configured(self) -> bool:
        """Check if Binance Futures collector is configured"""
        # Public endpoints don't require authentication
        return True

