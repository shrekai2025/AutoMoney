"""Agent Execution Monitor API - Agent执行监控

提供实时查看所有Agent执行状态的API
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from pydantic import BaseModel

from app.core.deps import get_db, get_optional_user
from app.models import AgentExecution, User

logger = logging.getLogger(__name__)

router = APIRouter(redirect_slashes=False)


class AgentExecutionItem(BaseModel):
    """Agent执行项"""
    id: str
    agent_name: str
    agent_display_name: str
    executed_at: datetime
    execution_duration_ms: int
    status: str
    signal: str
    confidence: float
    score: float
    reasoning: str
    strategy_execution_id: Optional[str]
    user_id: Optional[int]

    class Config:
        from_attributes = True


class AgentStats(BaseModel):
    """Agent统计"""
    agent_name: str
    agent_display_name: str
    total_executions: int
    recent_signal: str
    recent_score: float
    last_executed: datetime
    avg_duration_ms: int


@router.get("/executions")
async def get_agent_executions(
    limit: int = Query(50, ge=1, le=200, description="返回数量"),
    agent_name: Optional[str] = Query(None, description="筛选特定Agent"),
    hours: int = Query(24, ge=1, le=168, description="查询最近N小时"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    获取Agent执行记录列表

    - 未登录用户也可访问（查看所有）
    - 支持按agent_name筛选
    - 支持时间范围筛选
    """
    try:
        # 计算时间范围
        since = datetime.utcnow() - timedelta(hours=hours)

        # 构建查询
        query = select(AgentExecution).where(
            AgentExecution.executed_at >= since
        )

        if agent_name:
            query = query.where(AgentExecution.agent_name == agent_name)

        query = query.order_by(desc(AgentExecution.executed_at)).limit(limit)

        result = await db.execute(query)
        executions = result.scalars().all()

        return {
            "executions": [
                {
                    "id": str(ex.id),
                    "agent_name": ex.agent_name,
                    "agent_display_name": ex.agent_display_name,
                    "executed_at": ex.executed_at.isoformat() + "Z" if not ex.executed_at.isoformat().endswith('Z') else ex.executed_at.isoformat(),
                    "execution_duration_ms": ex.execution_duration_ms,
                    "status": ex.status,
                    "signal": ex.signal,
                    "confidence": float(ex.confidence),
                    "score": float(ex.score),
                    "reasoning": ex.reasoning[:200] if ex.reasoning else "",  # 截断
                    "strategy_execution_id": str(ex.strategy_execution_id) if ex.strategy_execution_id else None,
                    "user_id": ex.user_id,
                }
                for ex in executions
            ],
            "total": len(executions),
            "time_range_hours": hours,
        }

    except Exception as e:
        logger.error(f"获取Agent执行记录失败: {e}", exc_info=True)
        return {"error": str(e), "executions": [], "total": 0}


@router.get("/stats")
async def get_agent_stats(
    hours: int = Query(24, ge=1, le=168, description="统计最近N小时"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    获取各Agent的统计信息

    - 每个Agent的执行次数、最新信号、平均耗时等
    - 未登录用户也可访问
    """
    try:
        since = datetime.utcnow() - timedelta(hours=hours)

        # 查询所有agent的最新执行
        query = select(AgentExecution).where(
            AgentExecution.executed_at >= since
        )
        result = await db.execute(query)
        all_executions = result.scalars().all()

        # 按agent_name分组统计
        from collections import defaultdict
        agent_groups = defaultdict(list)
        for ex in all_executions:
            agent_groups[ex.agent_name].append(ex)

        stats = []
        for agent_name, execs in agent_groups.items():
            # 按执行时间排序，最新的在前
            execs_sorted = sorted(execs, key=lambda x: x.executed_at, reverse=True)
            latest = execs_sorted[0]

            stats.append({
                "agent_name": agent_name,
                "agent_display_name": latest.agent_display_name,
                "total_executions": len(execs),
                "recent_signal": latest.signal,
                "recent_score": float(latest.score),
                "last_executed": latest.executed_at.isoformat() + "Z" if not latest.executed_at.isoformat().endswith('Z') else latest.executed_at.isoformat(),
                "avg_duration_ms": int(sum(e.execution_duration_ms for e in execs) / len(execs)),
            })

        # 按最后执行时间倒序排列
        stats.sort(key=lambda x: x["last_executed"], reverse=True)

        return {
            "stats": stats,
            "time_range_hours": hours,
            "total_agents": len(stats),
        }

    except Exception as e:
        logger.error(f"获取Agent统计失败: {e}", exc_info=True)
        return {"error": str(e), "stats": [], "total_agents": 0}
