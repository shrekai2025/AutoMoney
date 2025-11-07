"""Blockchain.com (blockchain.info) on-chain data collector - Free API"""

from typing import Dict, Any, Optional
from datetime import datetime
import httpx

from app.services.data_collectors.base import DataCollector


class BlockchainInfoCollector(DataCollector):
    """
    Blockchain.com (blockchain.info) API collector for on-chain metrics

    This is a FREE API with no authentication required.

    Documentation: https://www.blockchain.com/api
    """

    def __init__(self):
        """Initialize Blockchain.info collector (no API key needed)"""
        super().__init__(api_key="", base_url="https://api.blockchain.info")

    async def collect(self) -> Dict[str, Any]:
        """
        Collect on-chain metrics from Blockchain.info

        Returns:
            Dictionary with on-chain metrics
        """
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                # Get network statistics
                stats = await self._get_network_stats(client)

                # Get active addresses (24h)
                active_addresses = await self._get_active_addresses(client)

                # Get transaction count (30 days)
                transaction_count = await self._get_transaction_count(client)

                # Get market cap
                market_cap = await self._get_market_cap(client)

                return {
                    "network_stats": stats,
                    "active_addresses_24h": active_addresses,
                    "transaction_count_30d": transaction_count,
                    "market_cap": market_cap,
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "blockchain.info",
                }
        except Exception as e:
            print(f"Error collecting blockchain.info data: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "source": "blockchain.info",
            }

    async def _get_network_stats(self, client: httpx.AsyncClient) -> Dict[str, Any]:
        """
        Get network statistics

        Endpoint: GET /stats

        Returns:
            Network statistics including difficulty, hash rate, etc.
        """
        try:
            response = await client.get(f"{self.base_url}/stats")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching network stats: {e}")
            return {}

    async def _get_active_addresses(self, client: httpx.AsyncClient) -> Optional[int]:
        """
        Get active addresses count (24 hours)

        Endpoint: GET /charts/n-unique-addresses?timespan=7days&format=json

        Returns:
            Number of active addresses in last 24h
        """
        try:
            response = await client.get(
                f"{self.base_url}/charts/n-unique-addresses",
                params={"timespan": "7days", "format": "json"}
            )
            response.raise_for_status()
            data = response.json()

            # Get the latest value
            if data.get("values") and len(data["values"]) > 0:
                return int(data["values"][-1]["y"])
            return None
        except Exception as e:
            print(f"Error fetching active addresses: {e}")
            return None

    async def _get_transaction_count(self, client: httpx.AsyncClient) -> Optional[Dict[str, Any]]:
        """
        Get transaction count (30 days)

        Endpoint: GET /charts/n-transactions?timespan=30days&format=json

        Returns:
            Transaction count data for past 30 days
        """
        try:
            response = await client.get(
                f"{self.base_url}/charts/n-transactions",
                params={"timespan": "30days", "format": "json"}
            )
            response.raise_for_status()
            data = response.json()

            if data.get("values") and len(data["values"]) > 0:
                # Calculate average daily transactions
                values = [v["y"] for v in data["values"]]
                avg_daily = sum(values) / len(values)
                latest = values[-1]

                return {
                    "latest_daily": int(latest),
                    "avg_30d": int(avg_daily),
                    "total_30d": int(sum(values)),
                }
            return None
        except Exception as e:
            print(f"Error fetching transaction count: {e}")
            return None

    async def _get_market_cap(self, client: httpx.AsyncClient) -> Optional[float]:
        """
        Get Bitcoin market cap

        Endpoint: GET /charts/market-cap?timespan=7days&format=json

        Returns:
            Market cap in USD
        """
        try:
            response = await client.get(
                f"{self.base_url}/charts/market-cap",
                params={"timespan": "7days", "format": "json"}
            )
            response.raise_for_status()
            data = response.json()

            # Get the latest value
            if data.get("values") and len(data["values"]) > 0:
                return float(data["values"][-1]["y"])
            return None
        except Exception as e:
            print(f"Error fetching market cap: {e}")
            return None

    @property
    def is_configured(self) -> bool:
        """Blockchain.info API is always available (no key required)"""
        return True
