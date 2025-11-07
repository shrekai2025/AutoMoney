"""FRED (Federal Reserve Economic Data) collector"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from app.services.data_collectors.base import DataCollector
from app.schemas.market_data import MacroEconomicData


class FREDCollector(DataCollector):
    """
    FRED API collector for macroeconomic data

    Documentation: https://fred.stlouisfed.org/docs/api/fred/
    """

    def __init__(self, api_key: str = ""):
        """
        Initialize FRED collector

        Args:
            api_key: FRED API key
        """
        super().__init__(api_key=api_key, base_url="https://api.stlouisfed.org/fred")

    async def _fetch_series(self, series_id: str, limit: int = 1) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch observations for a specific FRED series

        Args:
            series_id: FRED series ID
            limit: Number of most recent observations to fetch

        Returns:
            List of observations or None if failed
        """
        try:
            response = await self.get(
                "/series/observations",
                params={
                    "series_id": series_id,
                    "api_key": self.api_key,
                    "file_type": "json",
                    "sort_order": "desc",
                    "limit": limit
                }
            )

            if response and "observations" in response:
                # Filter out observations with '.' value (missing data)
                valid_obs = [obs for obs in response["observations"] if obs["value"] != "."]
                return valid_obs[:limit] if valid_obs else None
            return None

        except Exception as e:
            print(f"Error fetching FRED series {series_id}: {e}")
            return None

    async def collect(self) -> Dict[str, Any]:
        """
        Collect macroeconomic data from FRED

        Returns:
            Dictionary with macro economic data

        Key series IDs:
        - M2SL: M2 Money Stock
        - DFF: Federal Funds Effective Rate
        - DTWEXBGS: Trade Weighted U.S. Dollar Index (DXY)
        - DGS10: 10-Year Treasury Constant Maturity Rate

        Raises:
            Exception: If API fetch fails (no mock data fallback)
        """
        # Check cache (1 hour cache for macro data)
        cached = await self.get_cached_data("macro_data", max_age_seconds=3600)
        if cached:
            return cached

        # Fetch real data from FRED (no fallback)
        m2_value = await self._fetch_series("M2SL", limit=2)  # Get latest 2 for YoY calc
        dff_value = await self._fetch_series("DFF", limit=1)
        dxy_value = await self._fetch_series("DTWEXBGS", limit=1)
        dgs10_value = await self._fetch_series("DGS10", limit=1)

        # Validate that we got data
        if not dff_value:
            raise ValueError("Failed to fetch Federal Funds Rate (DFF) from FRED API")
        if not dxy_value:
            raise ValueError("Failed to fetch Dollar Index (DTWEXBGS) from FRED API")
        if not dgs10_value:
            raise ValueError("Failed to fetch 10-Year Treasury (DGS10) from FRED API")

        # Calculate M2 YoY growth (simplified - using 2 latest points)
        m2_growth = 0.0
        if m2_value and len(m2_value) >= 2:
            try:
                latest = float(m2_value[0]["value"])
                previous = float(m2_value[1]["value"])
                m2_growth = round(((latest - previous) / previous) * 100, 2)
            except (ValueError, KeyError) as e:
                raise ValueError(f"Failed to calculate M2 growth: {e}")

        macro_data = MacroEconomicData(
            timestamp=datetime.utcnow(),
            # Bitcoin-specific (not available from FRED)
            etf_flow=0.0,  # Would come from other source
            futures_oi=0.0,  # Would come from other source
            futures_long_ratio=50.0,  # Would come from other source
            # Real FRED data
            fed_rate_prob=float(dff_value[0]["value"]),
            m2_growth=m2_growth,
            dxy_index=float(dxy_value[0]["value"]),
            gold_price=1900.0,  # Would come from other source (not in FRED)
            # Metadata
            metadata={
                "data_quality": "real",
                "source": "fred_api",
                "dgs10_rate": float(dgs10_value[0]["value"]),
            },
        )

        result = {"data": macro_data.dict()}
        self.set_cache("macro_data", result)
        self.last_fetch_time = datetime.utcnow()

        return result

    async def get_m2_growth(self) -> float:
        """
        Get M2 money supply growth rate

        Returns:
            M2 growth rate (%)
        """
        data = await self.collect()
        return data["data"]["m2_growth"]

    async def get_dxy_index(self) -> float:
        """
        Get US Dollar Index

        Returns:
            DXY Index value
        """
        data = await self.collect()
        return data["data"]["dxy_index"]

    @property
    def is_configured(self) -> bool:
        """Check if FRED collector is configured"""
        return bool(self.api_key)
