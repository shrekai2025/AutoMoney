"""DateTime utilities for consistent timezone handling"""

from datetime import datetime, timezone
from typing import Optional


def ensure_utc(dt: datetime) -> datetime:
    """
    Ensure datetime has UTC timezone information.

    Args:
        dt: datetime object (with or without timezone)

    Returns:
        datetime with UTC timezone
    """
    if dt is None:
        return None

    if dt.tzinfo is None:
        # Naive datetime, assume UTC
        return dt.replace(tzinfo=timezone.utc)

    # Already has timezone
    return dt.astimezone(timezone.utc)


def to_iso_string(dt: Optional[datetime]) -> Optional[str]:
    """
    Convert datetime to ISO 8601 string with UTC timezone.

    Args:
        dt: datetime object

    Returns:
        ISO 8601 formatted string with timezone (e.g., "2025-11-07T02:10:59+00:00")
        or None if input is None
    """
    if dt is None:
        return None

    # Ensure UTC timezone
    dt_utc = ensure_utc(dt)

    # Return ISO format with timezone
    return dt_utc.isoformat()
