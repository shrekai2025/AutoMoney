"""Base class for data collectors"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime
import httpx


class DataCollector(ABC):
    """Abstract base class for all data collectors"""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize data collector

        Args:
            api_key: API key for authentication (if required)
            base_url: Base URL for API endpoint (if applicable)
        """
        self.api_key = api_key
        self.base_url = base_url
        self.last_fetch_time: Optional[datetime] = None
        self.cache: Dict[str, Any] = {}
        self._client: Optional[httpx.AsyncClient] = None

    @abstractmethod
    async def collect(self) -> Dict[str, Any]:
        """
        Collect data from the source

        Returns:
            Dictionary containing collected data

        Raises:
            Exception: If data collection fails
        """
        pass

    async def get_cached_data(self, cache_key: str, max_age_seconds: int = 60) -> Optional[Any]:
        """
        Get cached data if available and not expired

        Args:
            cache_key: Key for cached data
            max_age_seconds: Maximum age of cached data in seconds

        Returns:
            Cached data or None if not available/expired
        """
        if cache_key not in self.cache:
            return None

        cached_item = self.cache[cache_key]
        cache_time = cached_item.get("timestamp")

        if cache_time is None:
            return None

        age = (datetime.utcnow() - cache_time).total_seconds()
        if age > max_age_seconds:
            return None

        return cached_item.get("data")

    def set_cache(self, cache_key: str, data: Any):
        """
        Set cached data with current timestamp

        Args:
            cache_key: Key for cached data
            data: Data to cache
        """
        self.cache[cache_key] = {"timestamp": datetime.utcnow(), "data": data}

    def clear_cache(self):
        """Clear all cached data"""
        self.cache.clear()

    async def get_client(self) -> httpx.AsyncClient:
        """
        Get or create HTTP client

        Returns:
            HTTP client instance
        """
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close_client(self):
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Make GET request to API

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            JSON response data

        Raises:
            httpx.HTTPError: If request fails
        """
        if not self.base_url:
            raise ValueError("base_url is not set for this collector")

        url = f"{self.base_url}{endpoint}"
        client = await self.get_client()

        response = await client.get(url, params=params)
        response.raise_for_status()

        return response.json()

    @property
    def is_configured(self) -> bool:
        """
        Check if collector is properly configured

        Returns:
            True if configured, False otherwise
        """
        if self.api_key:
            return bool(self.api_key)
        return True  # Some collectors don't need API keys
