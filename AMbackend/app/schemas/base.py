"""Base schemas with custom serialization"""

from pydantic import BaseModel
from datetime import datetime
from typing import Any
from app.utils.datetime_utils import ensure_utc


class UTCAwareBaseModel(BaseModel):
    """
    Base model with UTC-aware datetime serialization.

    All datetime fields will be serialized with UTC timezone.
    """

    class Config:
        json_encoders = {
            datetime: lambda dt: ensure_utc(dt).isoformat() if dt else None
        }
        orm_mode = True
