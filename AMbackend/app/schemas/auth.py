"""Authentication schemas"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict
from app.schemas.base import UTCAwareBaseModel


class FirebaseConfig(BaseModel):
    """Firebase client configuration"""

    apiKey: str
    authDomain: str
    projectId: str
    storageBucket: str
    messagingSenderId: str
    appId: str
    measurementId: str


class UserBase(BaseModel):
    """Base user schema"""

    email: EmailStr
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: bool = True
    role: str = "user"


class UserCreate(UserBase):
    """User creation schema"""

    google_id: str  # Firebase UID


class UserUpdate(BaseModel):
    """User update schema"""

    full_name: Optional[str] = None
    avatar_url: Optional[str] = None


class UserInDB(UserBase):
    """User schema as stored in database"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    google_id: Optional[str] = None  # Firebase UID
    is_superuser: bool = False
    created_at: datetime
    updated_at: datetime


class User(UserInDB):
    """User schema for API responses"""

    pass
