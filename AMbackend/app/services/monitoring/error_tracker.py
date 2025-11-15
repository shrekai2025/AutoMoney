"""System error tracking service"""

import logging
import traceback
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.system_error import SystemError

logger = logging.getLogger(__name__)


class ErrorTracker:
    """系统错误追踪器"""
    
    @staticmethod
    async def track_error(
        db: AsyncSession,
        error_type: str,
        error_category: str,
        severity: str,
        component: str,
        error_message: str,
        error_details: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        portfolio_id: Optional[str] = None,
        strategy_name: Optional[str] = None,
    ) -> SystemError:
        """
        记录系统错误
        
        Args:
            error_type: 错误类型 ('data_collection', 'agent_execution', 'strategy_execution')
            error_category: 错误分类 ('network', 'api', 'logic', 'timeout')
            severity: 严重程度 ('critical', 'error', 'warning', 'info')
            component: 出错组件
            error_message: 错误信息
            error_details: 详细堆栈
            context: 上下文数据
            user_id: 用户ID
            portfolio_id: Portfolio ID
            strategy_name: 策略名称
        
        Returns:
            SystemError对象
        """
        try:
            # 检查是否是重复错误(同一组件的同一错误消息)
            result = await db.execute(
                select(SystemError).where(
                    and_(
                        SystemError.component == component,
                        SystemError.error_message == error_message,
                        SystemError.is_resolved == False,
                    )
                ).order_by(SystemError.last_occurred_at.desc()).limit(1)
            )
            existing_error = result.scalar_one_or_none()
            
            if existing_error:
                # 更新重复错误
                existing_error.occurrence_count += 1
                existing_error.last_occurred_at = datetime.utcnow()
                existing_error.error_details = error_details  # 更新最新的堆栈
                existing_error.context = context  # 更新最新的上下文
                await db.commit()
                
                logger.info(f"更新重复错误: {component} - {error_message} (第{existing_error.occurrence_count}次)")
                return existing_error
            else:
                # 创建新错误记录
                error_record = SystemError(
                    error_type=error_type,
                    error_category=error_category,
                    severity=severity,
                    component=component,
                    error_message=error_message,
                    error_details=error_details,
                    context=context,
                    user_id=user_id,
                    portfolio_id=portfolio_id,
                    strategy_name=strategy_name,
                )
                
                db.add(error_record)
                await db.commit()
                await db.refresh(error_record)
                
                logger.info(f"记录新错误: {component} - {error_message}")
                return error_record
                
        except Exception as e:
            logger.error(f"记录错误失败: {e}", exc_info=True)
            await db.rollback()
            # 即使记录失败也不影响主流程
            return None
    
    @staticmethod
    async def track_exception(
        db: AsyncSession,
        exception: Exception,
        error_type: str,
        component: str,
        severity: str = "error",
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> SystemError:
        """
        从异常对象记录错误
        
        Args:
            db: 数据库会话
            exception: 异常对象
            error_type: 错误类型
            component: 组件名称
            severity: 严重程度
            context: 上下文
            **kwargs: 其他参数(user_id, portfolio_id等)
        """
        error_message = str(exception)
        error_details = traceback.format_exc()
        
        # 根据异常类型确定错误分类
        error_category = "unknown"
        if "connect" in error_message.lower() or "network" in error_message.lower():
            error_category = "network"
        elif "timeout" in error_message.lower():
            error_category = "timeout"
        elif "api" in error_message.lower() or "http" in error_message.lower():
            error_category = "api"
        else:
            error_category = "logic"
        
        return await ErrorTracker.track_error(
            db=db,
            error_type=error_type,
            error_category=error_category,
            severity=severity,
            component=component,
            error_message=error_message,
            error_details=error_details,
            context=context,
            **kwargs
        )
    
    @staticmethod
    async def get_recent_errors(
        db: AsyncSession,
        limit: int = 50,
        severity: Optional[str] = None,
        error_type: Optional[str] = None,
        unresolved_only: bool = False,
    ):
        """
        获取最近的错误记录
        
        Args:
            db: 数据库会话
            limit: 返回数量
            severity: 筛选严重程度
            error_type: 筛选错误类型
            unresolved_only: 只返回未解决的错误
        """
        query = select(SystemError).order_by(SystemError.last_occurred_at.desc())
        
        filters = []
        if severity:
            filters.append(SystemError.severity == severity)
        if error_type:
            filters.append(SystemError.error_type == error_type)
        if unresolved_only:
            filters.append(SystemError.is_resolved == False)
        
        if filters:
            query = query.where(and_(*filters))
        
        query = query.limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def mark_resolved(
        db: AsyncSession,
        error_id: int,
        resolution_note: Optional[str] = None,
    ):
        """标记错误为已解决"""
        result = await db.execute(
            select(SystemError).where(SystemError.id == error_id)
        )
        error = result.scalar_one_or_none()
        
        if error:
            error.is_resolved = True
            error.resolved_at = datetime.utcnow()
            error.resolution_note = resolution_note
            await db.commit()
            logger.info(f"标记错误 {error_id} 为已解决")
    
    @staticmethod
    async def get_error_summary(db: AsyncSession) -> Dict[str, Any]:
        """获取错误摘要统计"""
        from sqlalchemy import func
        
        # 总错误数
        total_result = await db.execute(
            select(func.count(SystemError.id))
        )
        total_errors = total_result.scalar()
        
        # 未解决错误数
        unresolved_result = await db.execute(
            select(func.count(SystemError.id)).where(SystemError.is_resolved == False)
        )
        unresolved_errors = unresolved_result.scalar()
        
        # 按严重程度统计
        severity_result = await db.execute(
            select(
                SystemError.severity,
                func.count(SystemError.id)
            ).where(
                SystemError.is_resolved == False
            ).group_by(SystemError.severity)
        )
        severity_stats = {row[0]: row[1] for row in severity_result.all()}
        
        # 按错误类型统计
        type_result = await db.execute(
            select(
                SystemError.error_type,
                func.count(SystemError.id)
            ).where(
                SystemError.is_resolved == False
            ).group_by(SystemError.error_type)
        )
        type_stats = {row[0]: row[1] for row in type_result.all()}
        
        return {
            "total_errors": total_errors,
            "unresolved_errors": unresolved_errors,
            "critical_count": severity_stats.get("critical", 0),
            "error_count": severity_stats.get("error", 0),
            "warning_count": severity_stats.get("warning", 0),
            "by_severity": severity_stats,
            "by_type": type_stats,
        }


# 全局实例
error_tracker = ErrorTracker()

