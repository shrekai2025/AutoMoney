"""Glassnode on-chain data collector"""

from typing import Dict, Any
from datetime import datetime

from app.services.data_collectors.base import DataCollector
from app.schemas.market_data import OnChainMetrics


class GlassnodeCollector(DataCollector):
    """
    Glassnode API collector for on-chain metrics

    NOTE: Glassnode requires a paid subscription ($29-$799/month)
    This collector is disabled until a valid API key is provided.

    Documentation: https://docs.glassnode.com/api/
    """

    def __init__(self, api_key: str = ""):
        """
        Initialize Glassnode collector

        Args:
            api_key: Glassnode API key (required)
        """
        super().__init__(api_key=api_key, base_url="https://api.glassnode.com/v1")

    async def collect(self) -> Dict[str, Any]:
        """
        Collect on-chain metrics from Glassnode

        Returns:
            Dictionary with on-chain metrics

        Raises:
            NotImplementedError: Glassnode requires paid subscription

        Example endpoints:
        - GET /v1/metrics/market/mvrv_z_score
        - GET /v1/metrics/indicators/nvt
        - GET /v1/metrics/addresses/active_count
        - GET /v1/metrics/transactions/transfers_volume_sum
        - GET /v1/metrics/distribution/balance_1pct_holders
        """
        raise NotImplementedError(
            "Glassnode on-chain data requires a paid subscription. "
            "Please subscribe at https://glassnode.com/pricing or use a free alternative. "
            "Recommended free alternatives: Blockchain.com API, CryptoCompare, or CoinGecko."
        )

    async def get_mvrv_z_score(self) -> float:
        """
        Get MVRV Z-Score (Market Value to Realized Value)

        Returns:
            MVRV Z-Score value

        Raises:
            NotImplementedError: Glassnode requires paid subscription
        """
        raise NotImplementedError("Glassnode requires paid subscription")

    async def get_nvt_ratio(self) -> float:
        """
        Get NVT Ratio (Network Value to Transactions)

        Returns:
            NVT Ratio value

        Raises:
            NotImplementedError: Glassnode requires paid subscription
        """
        raise NotImplementedError("Glassnode requires paid subscription")

    @property
    def is_configured(self) -> bool:
        """Check if Glassnode collector is configured"""
        # Always return False unless valid API key is provided
        return bool(self.api_key and self.api_key != "your-glassnode-api-key")
