"""User model"""

from sqlalchemy import Boolean, Column, Integer, String, Index
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """User model for authentication and profile"""

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    google_id = Column(String(255), unique=True, index=True, nullable=True)
    full_name = Column(String(255), nullable=True)
    avatar_url = Column(String(512), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    role = Column(String(20), default="user", nullable=False, index=True)  # 'user' or 'admin'

    # Relationships
    agent_executions = relationship("AgentExecution", back_populates="user", cascade="all, delete-orphan")
    strategy_executions = relationship("StrategyExecution", back_populates="user", cascade="all, delete-orphan")
    portfolios = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")

    # Indexes for faster queries
    __table_args__ = (
        Index("idx_user_email_active", "email", "is_active"),
        Index("idx_user_google_id", "google_id"),
    )

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"
