"""Mempool.space on-chain data collector - Free API"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import httpx

from app.services.data_collectors.base import DataCollector


class MempoolSpaceCollector(DataCollector):
    """
    Mempool.space API collector for on-chain metrics

    This is a FREE API with no authentication required.

    Documentation: https://mempool.space/docs/api/rest
    """

    def __init__(self):
        """Initialize Mempool.space collector (no API key needed)"""
        super().__init__(api_key="", base_url="https://mempool.space/api")

    async def collect(self) -> Dict[str, Any]:
        """
        Collect on-chain metrics from Mempool.space

        Returns:
            Dictionary with on-chain metrics
        """
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                # Get recommended fees
                fees = await self._get_recommended_fees(client)

                # Get mempool stats
                mempool_stats = await self._get_mempool_stats(client)

                # Get blockchain tip height
                tip_height = await self._get_tip_height(client)

                # Get difficulty adjustment
                difficulty_adj = await self._get_difficulty_adjustment(client)

                return {
                    "recommended_fees": fees,
                    "mempool_stats": mempool_stats,
                    "tip_height": tip_height,
                    "difficulty_adjustment": difficulty_adj,
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "mempool.space",
                }
        except Exception as e:
            print(f"Error collecting mempool.space data: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "source": "mempool.space",
            }

    async def _get_recommended_fees(self, client: httpx.AsyncClient) -> Optional[Dict[str, Any]]:
        """
        Get recommended transaction fees

        Endpoint: GET /v1/fees/recommended

        Returns:
            Recommended fees for different priority levels (sat/vB)
        """
        try:
            response = await client.get(f"{self.base_url}/v1/fees/recommended")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching recommended fees: {e}")
            return None

    async def _get_mempool_stats(self, client: httpx.AsyncClient) -> Optional[Dict[str, Any]]:
        """
        Get mempool statistics

        Endpoint: GET /mempool

        Returns:
            Mempool statistics including size, tx count, etc.
        """
        try:
            response = await client.get(f"{self.base_url}/mempool")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching mempool stats: {e}")
            return None

    async def _get_tip_height(self, client: httpx.AsyncClient) -> Optional[int]:
        """
        Get current blockchain tip height

        Endpoint: GET /blocks/tip/height

        Returns:
            Current block height
        """
        try:
            response = await client.get(f"{self.base_url}/blocks/tip/height")
            response.raise_for_status()
            return int(response.text)
        except Exception as e:
            print(f"Error fetching tip height: {e}")
            return None

    async def _get_difficulty_adjustment(self, client: httpx.AsyncClient) -> Optional[Dict[str, Any]]:
        """
        Get difficulty adjustment info

        Endpoint: GET /v1/difficulty-adjustment

        Returns:
            Difficulty adjustment information
        """
        try:
            response = await client.get(f"{self.base_url}/v1/difficulty-adjustment")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching difficulty adjustment: {e}")
            return None

    async def get_address_transactions(
        self, client: httpx.AsyncClient, address: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get transaction history for an address
        Useful for tracking exchange wallet flows

        Endpoint: GET /address/{address}/txs

        Args:
            address: Bitcoin address to query

        Returns:
            List of transactions
        """
        try:
            response = await client.get(f"{self.base_url}/address/{address}/txs")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching address transactions: {e}")
            return None

    @property
    def is_configured(self) -> bool:
        """Mempool.space API is always available (no key required)"""
        return True
