"""Alternative.me Fear & Greed Index collector"""

from typing import Dict, Any
from datetime import datetime

from app.services.data_collectors.base import DataCollector
from app.schemas.market_data import FearGreedIndex


class AlternativeMeCollector(DataCollector):
    """
    Alternative.me API collector for Fear & Greed Index

    Documentation: https://alternative.me/crypto/fear-and-greed-index/
    API: https://api.alternative.me/fng/
    Note: This API is free and doesn't require authentication
    """

    def __init__(self):
        """Initialize Alternative.me collector"""
        super().__init__(base_url="https://api.alternative.me")

    async def collect(self) -> Dict[str, Any]:
        """
        Collect Fear & Greed Index

        Returns:
            Dictionary with fear & greed index data

        Raises:
            Exception: If API fetch fails (no mock data fallback)

        API Endpoint: GET https://api.alternative.me/fng/?limit=1
        """
        # Check cache (10 minute cache)
        cached = await self.get_cached_data("fear_greed", max_age_seconds=600)
        if cached:
            return cached

        # Call real API (no fallback)
        response = await self.get("/fng/", params={"limit": "1"})

        if response and "data" in response and len(response["data"]) > 0:
            api_data = response["data"][0]

            # Convert API response to our schema
            fear_greed = FearGreedIndex(
                timestamp=datetime.fromtimestamp(int(api_data["timestamp"])),
                value=int(api_data["value"]),
                classification=api_data["value_classification"],
                components={}  # API doesn't return component breakdown in free tier
            )

            result = {"index": fear_greed.dict()}
            self.set_cache("fear_greed", result)
            self.last_fetch_time = datetime.utcnow()

            return result
        else:
            raise ValueError("Invalid response from Alternative.me API")

    async def get_current_index(self) -> int:
        """
        Get current Fear & Greed Index value

        Returns:
            Index value (0-100)
        """
        data = await self.collect()
        return data["index"]["value"]

    async def get_classification(self) -> str:
        """
        Get current Fear & Greed classification

        Returns:
            Classification string
        """
        data = await self.collect()
        return data["index"]["classification"]

    @property
    def is_configured(self) -> bool:
        """Alternative.me doesn't require configuration"""
        return True
