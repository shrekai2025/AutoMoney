"""Admin API Schemas"""

from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.base import UTCAwareBaseModel


class AdminStrategyItem(BaseModel):
    """管理员视图的策略项"""

    id: str = Field(..., description="策略ID (UUID)")
    user_id: int = Field(..., description="用户ID")
    name: str = Field(..., description="策略名称")
    strategy_name: str = Field(..., description="策略类型")
    is_active: bool = Field(..., description="是否激活")
    total_value: float = Field(..., description="总价值")
    total_pnl: float = Field(..., description="总盈亏")
    total_pnl_percent: float = Field(..., description="总盈亏百分比")
    rebalance_period_minutes: int = Field(..., description="策略执行周期（分钟）")
    created_at: str = Field(..., description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")

    class Config:
        from_attributes = True


class AdminStrategyListResponse(BaseModel):
    """管理员策略列表响应"""

    total: int = Field(..., description="策略总数")
    strategies: List[AdminStrategyItem] = Field(..., description="策略列表")


class StrategyToggleRequest(BaseModel):
    """策略开关请求"""

    is_active: bool = Field(..., description="目标状态")


class StrategyToggleResponse(BaseModel):
    """策略开关响应"""

    success: bool = Field(..., description="操作是否成功")
    portfolio_id: str = Field(..., description="策略ID")
    is_active: bool = Field(..., description="当前状态")
    message: str = Field(..., description="消息")
