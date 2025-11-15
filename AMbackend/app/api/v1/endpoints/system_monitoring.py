"""System monitoring and error tracking endpoints"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.services.monitoring.error_tracker import error_tracker
from app.models.user import User

router = APIRouter()


@router.get("/errors/recent")
async def get_recent_errors(
    limit: int = Query(50, ge=1, le=200),
    severity: Optional[str] = Query(None, regex="^(critical|error|warning|info)$"),
    error_type: Optional[str] = None,
    unresolved_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取最近的系统错误
    
    Args:
        limit: 返回数量 (1-200)
        severity: 筛选严重程度 (critical/error/warning/info)
        error_type: 筛选错误类型
        unresolved_only: 只返回未解决的错误
    """
    try:
        errors = await error_tracker.get_recent_errors(
            db=db,
            limit=limit,
            severity=severity,
            error_type=error_type,
            unresolved_only=unresolved_only,
        )
        
        return {
            "count": len(errors),
            "errors": [
                {
                    "id": error.id,
                    "error_type": error.error_type,
                    "error_category": error.error_category,
                    "severity": error.severity,
                    "component": error.component,
                    "error_message": error.error_message,
                    "error_details": error.error_details[:500] if error.error_details else None,  # 截断长错误
                    "context": error.context,
                    "occurrence_count": error.occurrence_count,
                    "first_occurred_at": error.first_occurred_at.isoformat(),
                    "last_occurred_at": error.last_occurred_at.isoformat(),
                    "is_resolved": error.is_resolved,
                    "strategy_name": error.strategy_name,
                    "portfolio_id": error.portfolio_id,
                }
                for error in errors
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取错误记录失败: {str(e)}")


@router.get("/errors/summary")
async def get_error_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取错误统计摘要"""
    try:
        summary = await error_tracker.get_error_summary(db)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取错误摘要失败: {str(e)}")


@router.post("/errors/{error_id}/resolve")
async def resolve_error(
    error_id: int,
    resolution_note: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """标记错误为已解决"""
    try:
        await error_tracker.mark_resolved(
            db=db,
            error_id=error_id,
            resolution_note=resolution_note,
        )
        return {"message": "错误已标记为已解决", "error_id": error_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"标记错误失败: {str(e)}")


@router.get("/system/health")
async def system_health(
    db: AsyncSession = Depends(get_db),
):
    """系统健康检查"""
    try:
        summary = await error_tracker.get_error_summary(db)
        
        # 判断系统健康状态
        status = "healthy"
        if summary["critical_count"] > 0:
            status = "critical"
        elif summary["error_count"] > 5:
            status = "degraded"
        elif summary["warning_count"] > 10:
            status = "warning"
        
        return {
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "error_summary": summary,
            "message": _get_health_message(status, summary),
        }
    except Exception as e:
        return {
            "status": "unknown",
            "message": f"无法获取系统状态: {str(e)}",
        }


def _get_health_message(status: str, summary: dict) -> str:
    """生成健康状态消息"""
    if status == "critical":
        return f"系统有 {summary['critical_count']} 个严重错误需要立即处理"
    elif status == "degraded":
        return f"系统有 {summary['error_count']} 个错误,部分功能可能受影响"
    elif status == "warning":
        return f"系统有 {summary['warning_count']} 个警告"
    else:
        return "系统运行正常"


from datetime import datetime

