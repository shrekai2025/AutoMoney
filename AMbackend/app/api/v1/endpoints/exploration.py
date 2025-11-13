"""Exploration (Mind Hub) API endpoints

提供Exploration页面所需的所有数据API
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from sqlalchemy.orm import selectinload

from app.core.deps import get_db, get_current_user
from app.models import User, AgentExecution, StrategyExecution, StrategyDefinition, Portfolio
from app.services.agents.execution_recorder import agent_execution_recorder

router = APIRouter()
logger = logging.getLogger(__name__)


def normalize_score(score: float) -> float:
    """将score从-100~+100转换为-1.0~+1.0（保留此函数以兼容现有代码，但前端会转换回-100~+100）"""
    return score / 100.0 if score else 0.0


def format_relative_time(timestamp: datetime) -> str:
    """将时间戳转换为相对时间格式（如 '2d 5h ago'）"""
    if not timestamp:
        return "N/A"
    
    now = datetime.utcnow()
    delta = now - timestamp
    
    days = delta.days
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    
    if days > 0:
        return f"{days}d {hours}h ago"
    elif hours > 0:
        return f"{hours}h {minutes}m ago"
    elif minutes > 0:
        return f"{minutes}m ago"
    else:
        return "Just Now"


def get_conviction_level(score: float) -> str:
    """根据Conviction Score返回等级"""
    if score >= 70:
        return "Strong"
    elif score >= 40:
        return "Moderate"
    else:
        return "Weak"


def get_status_text(signal: str, conviction_score: float) -> str:
    """根据Signal和Conviction Score生成状态文本"""
    if signal == "BUY":
        if conviction_score > 70:
            return "Accelerate Accumulation"
        elif conviction_score >= 40:
            return "Gradual Accumulation"
        else:
            return "Cautious Accumulation"
    elif signal == "SELL":
        return "Reduce Exposure"
    elif signal == "HOLD":
        return "Hold Position"
    elif signal == "PAUSE":
        return "Defensive Mode"
    else:
        return "Monitoring"


def calculate_countdown(execution_time: datetime, period_minutes: int = 10) -> Dict[str, Any]:
    """计算倒计时（默认10分钟，实际值从策略定义获取）"""
    if not execution_time:
        return {"remaining_seconds": 0, "formatted": "00:00:00", "progress": 0}
    
    now = datetime.utcnow()
    elapsed = (now - execution_time).total_seconds()
    period_seconds = period_minutes * 60
    remaining = max(0, period_seconds - elapsed)
    
    hours = int(remaining // 3600)
    minutes = int((remaining % 3600) // 60)
    seconds = int(remaining % 60)
    
    formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    progress = min(100, (elapsed / period_seconds) * 100) if period_seconds > 0 else 0
    
    return {
        "remaining_seconds": int(remaining),
        "formatted": formatted,
        "progress": progress
    }


def get_trend_status(ema_data: Dict[str, Any]) -> str:
    """从EMA数据判断趋势状态"""
    if not ema_data:
        return "Unknown"
    
    ema_9 = ema_data.get("ema_9", {}).get("value")
    ema_20 = ema_data.get("ema_20", {}).get("value")
    ema_50 = ema_data.get("ema_50", {}).get("value")
    
    if ema_9 and ema_20 and ema_50:
        if ema_9 > ema_20 > ema_50:
            return "Golden Cross"
        elif ema_9 < ema_20 < ema_50:
            return "Death Cross"
        else:
            return "Mixed"
    
    trend = ema_data.get("trend", "")
    if trend == "bullish":
        return "Bullish"
    elif trend == "bearish":
        return "Bearish"
    else:
        return "Neutral"


@router.get("/squad-decision-core")
async def get_squad_decision_core(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取Squad Decision Core数据（三个Agent的最新执行结果）
    
    返回三个业务Agent的最新工作成果，用于Exploration页面左侧显示
    所有用户都可以看到所有数据，不进行权限过滤
    """
    try:
        latest_executions = await agent_execution_recorder.get_latest_executions(db, user_id=None)
        
        # 调试信息：检查查询结果
        logger.info(f"[Exploration] Querying agent executions (all users), found {len(latest_executions)} agents")
        for agent_name, execution in latest_executions.items():
            if execution:
                logger.info(f"[Exploration] {agent_name}: score={execution.score}, executed_at={execution.executed_at}")
        
        squad = []
        last_updated = None
        
        agent_configs = [
            {
                "name": "macro_agent",
                "display_name": "The Oracle",
                "weight": "40%",
                "color": "blue"
            },
            {
                "name": "onchain_agent",
                "display_name": "Data Warden",
                "weight": "40%",
                "color": "emerald"
            },
            {
                "name": "ta_agent",
                "display_name": "Momentum Scout",
                "weight": "20%",
                "color": "amber"
            }
        ]
        
        for config in agent_configs:
            execution = latest_executions.get(config["name"])
            
            if execution:
                agent_data = execution.agent_specific_data or {}
                
                # MacroAgent特定处理
                if config["name"] == "macro_agent":
                    macro_indicators = agent_data.get("macro_indicators", {})
                    
                    # ETF Net Flow - 可能不存在，使用0或N/A
                    etf_flow = None
                    if isinstance(macro_indicators, dict):
                        etf_flow = macro_indicators.get("etf_flow")
                        if etf_flow is None:
                            # 尝试从market_data_snapshot获取
                            market_data = execution.market_data_snapshot or {}
                            macro = market_data.get("macro", {})
                            etf_flow = macro.get("etf_flow")
                    
                    # Fed Rate - 从macro_indicators获取
                    fed_rate_data = macro_indicators.get("fed_funds_rate", {})
                    fed_rate_prob = None
                    if isinstance(fed_rate_data, dict):
                        fed_rate_prob = fed_rate_data.get("value")
                    if not fed_rate_prob:
                        # 尝试从market_data_snapshot获取
                        market_data = execution.market_data_snapshot or {}
                        macro = market_data.get("macro", {})
                        fed_rate_prob = macro.get("fed_rate_prob")
                    
                    core_inputs = []
                    if etf_flow is not None and etf_flow != 0:
                        core_inputs.append({
                            "label": "ETF Net Flow",
                            "value": f"+${etf_flow/1e6:.0f}M" if etf_flow > 0 else f"${etf_flow/1e6:.0f}M",
                            "progress": min(100, abs(etf_flow / 1e6) * 0.3)
                        })
                    else:
                        core_inputs.append({
                            "label": "ETF Net Flow",
                            "value": "N/A",
                            "progress": 0
                        })
                    
                    if fed_rate_prob:
                        core_inputs.append({
                            "label": "Fed Rate",
                            "value": f"{fed_rate_prob:.2f}%",
                            "progress": min(100, abs(fed_rate_prob) * 1.25)
                        })
                    else:
                        core_inputs.append({
                            "label": "Fed Rate",
                            "value": "N/A",
                            "progress": 0
                        })
                
                # OnChainAgent特定处理
                elif config["name"] == "onchain_agent":
                    onchain_metrics = agent_data.get("onchain_metrics", {})
                    mvrv = onchain_metrics.get("mvrv_z_score")
                    nvt_ratio = onchain_metrics.get("nvt_ratio")
                    exchange_flow = onchain_metrics.get("exchange_netflow")
                    
                    # 使用NVT比率替代MVRV（如果MVRV不存在）
                    if mvrv is None and nvt_ratio:
                        # 简化的MVRV近似值（NVT比率/10）
                        mvrv = nvt_ratio / 10.0
                    
                    core_inputs = []
                    
                    # MVRV Z-Score
                    if mvrv is not None:
                        core_inputs.append({
                            "label": "MVRV Z-Score",
                            "value": f"{mvrv:.2f}",
                            "progress": min(100, abs(mvrv) * 20)
                        })
                    else:
                        core_inputs.append({
                            "label": "MVRV Z-Score",
                            "value": "N/A",
                            "progress": 0
                        })
                    
                    # Exchange Flow (负值表示流出，看涨)
                    if exchange_flow is not None and exchange_flow != 0:
                        abs_flow = abs(exchange_flow)
                        if abs_flow >= 1000:
                            # 负值显示为"-10K BTC"（流出，看涨）
                            value_str = f"{exchange_flow/1000:.0f}K BTC"
                        else:
                            value_str = f"{exchange_flow:.0f} BTC"
                        core_inputs.append({
                            "label": "Exchange Flow",
                            "value": value_str,
                            "progress": min(100, abs(exchange_flow / 1000) * 0.1)
                        })
                    else:
                        core_inputs.append({
                            "label": "Exchange Flow",
                            "value": "N/A",
                            "progress": 0
                        })
                
                # TAAgent特定处理
                else:  # ta_agent
                    technical_indicators = agent_data.get("technical_indicators", {})
                    rsi_data = technical_indicators.get("rsi", {})
                    ema_data = technical_indicators.get("ema", {})
                    
                    rsi_value = None
                    if isinstance(rsi_data, dict):
                        rsi_value = rsi_data.get("value")
                    elif isinstance(rsi_data, (int, float)):
                        rsi_value = rsi_data
                    
                    trend_status = get_trend_status(ema_data)
                    
                    core_inputs = []
                    
                    # RSI
                    if rsi_value is not None:
                        core_inputs.append({
                            "label": "RSI(14)",
                            "value": f"{rsi_value:.0f}",
                            "progress": min(100, max(0, rsi_value))
                        })
                    else:
                        core_inputs.append({
                            "label": "RSI(14)",
                            "value": "N/A",
                            "progress": 0
                        })
                    
                    # Trend Status
                    core_inputs.append({
                        "label": "Trend Status",
                        "value": trend_status,
                        "progress": 0  # Badge显示，不需要进度条
                    })
                
                # 确保score正确转换（NUMERIC类型可能需要特殊处理）
                score_value = float(execution.score) if execution.score is not None else 0.0
                logger.info(f"[Exploration] Processing {config['name']}: raw_score={execution.score}, converted_score={score_value}, type={type(execution.score)}")
                
                squad.append({
                    "agent_name": config["name"],
                    "display_name": config["display_name"],
                    "weight": config["weight"],
                    "color": config["color"],
                    "score": score_value,  # 直接返回原始score (-100~+100)，前端负责显示转换
                    "confidence": float(execution.confidence) if execution.confidence is not None else 0.0,
                    "signal": execution.signal,
                    "reasoning": execution.reasoning[:200] if execution.reasoning else "No reasoning available",
                    "core_inputs": core_inputs,
                    "executed_at": execution.executed_at.isoformat() if execution.executed_at else None
                })
                
                if execution.executed_at and (not last_updated or execution.executed_at > last_updated):
                    last_updated = execution.executed_at
            
            else:
                # Agent还未执行过或查询不到记录
                # 注意：如果查询不到记录，可能是user_id过滤导致，需要检查数据是否正确关联
                squad.append({
                    "agent_name": config["name"],
                    "display_name": config["display_name"],
                    "weight": config["weight"],
                    "color": config["color"],
                    "score": 0.0,
                    "confidence": 0.0,
                    "signal": None,
                    "reasoning": "No execution record found for this user",
                    "core_inputs": [],
                    "executed_at": None
                })
        
        return {
            "squad": squad,
            "last_updated": last_updated.isoformat() if last_updated else None
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch squad decision core: {str(e)}")


@router.get("/commander-analysis")
async def get_commander_analysis(
    strategy_id: Optional[int] = Query(None, description="策略定义ID，可选"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取AI Commander的综合分析
    
    返回最新的策略执行记录，包含Conviction Score和LLM总结
    """
    try:
        # 查询最新的策略执行记录（所有用户的数据）
        query = select(StrategyExecution)
        
        if strategy_id:
            # 如果指定了策略ID，查询该策略的实例
            query = query.join(Portfolio).where(
                Portfolio.strategy_definition_id == strategy_id
            )
        
        query = query.order_by(desc(StrategyExecution.execution_time)).limit(1)
        
        result = await db.execute(query)
        execution = result.scalar_one_or_none()
        
        if not execution:
            return {
                "commander_name": "Commander Nova",
                "status": "OFFLINE",
                "conviction_score": 0,
                "conviction_level": "Unknown",
                "market_analysis": "No execution records",
                "signal": None,
                "signal_strength": 0,
                "risk_level": None,
                "last_updated": None
            }
        
        conviction_score = execution.conviction_score or 0
        conviction_level = get_conviction_level(conviction_score)
        
        return {
            "commander_name": "Commander Nova",
            "status": "ONLINE",
            "conviction_score": conviction_score,
            "conviction_level": conviction_level,
            "market_analysis": execution.llm_summary or "No analysis summary",
            "signal": execution.signal,
            "signal_strength": execution.signal_strength or 0,
            "risk_level": execution.risk_level,
            "last_updated": execution.execution_time.isoformat() if execution.execution_time else None
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch commander analysis: {str(e)}")


@router.get("/active-directive")
async def get_active_directive(
    strategy_id: Optional[int] = Query(None, description="策略定义ID，可选"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取当前活跃的指令
    
    返回最新的策略执行记录，包含策略信息、Signal、Position Size和倒计时
    """
    try:
        # 查询最新的策略执行记录（所有用户的数据）
        query = select(StrategyExecution).options(
            selectinload(StrategyExecution.user)
        )
        
        if strategy_id:
            query = query.join(Portfolio).where(
                Portfolio.strategy_definition_id == strategy_id
            )
        
        query = query.order_by(desc(StrategyExecution.execution_time)).limit(1)
        
        result = await db.execute(query)
        execution = result.scalar_one_or_none()
        
        if not execution:
            return {
                "strategy_name": None,
                "strategy_subtitle": None,
                "countdown": {"remaining_seconds": 0, "formatted": "00:00:00", "progress": 0},
                "status": "No Active Directive",
                "action": {"type": "NONE", "amount": "0%", "asset": "BTC"},
                "description": "No active directive",
                "execution_time": None
            }
        
        # 获取策略定义信息
        portfolio_query = select(Portfolio).where(
            Portfolio.id == execution.portfolio_id
        ).options(selectinload(Portfolio.strategy_definition))
        
        portfolio_result = await db.execute(portfolio_query)
        portfolio = portfolio_result.scalar_one_or_none()
        
        strategy_name = "Unknown Strategy"
        strategy_subtitle = ""
        period_minutes = 10  # 默认10分钟（与StrategyDefinition默认值一致）
        
        if portfolio and portfolio.strategy_definition:
            strategy_name = portfolio.strategy_definition.display_name
            strategy_subtitle = portfolio.strategy_definition.description or ""
            # 优先从default_params获取，如果没有则从字段获取，最后使用默认值10分钟
            definition = portfolio.strategy_definition
            if definition.default_params and definition.default_params.get("rebalance_period_minutes"):
                period_minutes = definition.default_params.get("rebalance_period_minutes")
            elif definition.rebalance_period_minutes:
                period_minutes = definition.rebalance_period_minutes
            else:
                period_minutes = 10
        
        # 计算倒计时
        countdown = calculate_countdown(execution.execution_time, period_minutes)
        
        # 生成状态文本
        conviction_score = execution.conviction_score or 0
        status = get_status_text(execution.signal or "HOLD", conviction_score)
        
        # 格式化交易指令
        position_size = execution.position_size or 0
        action_type = execution.signal or "HOLD"
        asset = portfolio.strategy_definition.trade_symbol if portfolio and portfolio.strategy_definition else "BTC"
        
        action = {
            "type": action_type,
            "amount": f"{position_size * 100:.2f}%" if position_size else "0%",
            "asset": asset
        }
        
        # 生成说明
        description = "All agents aligned • Maximum confidence deployment" if conviction_score > 70 else "Monitoring market conditions"
        
        return {
            "strategy_name": strategy_name,
            "strategy_subtitle": strategy_subtitle,
            "countdown": countdown,
            "status": status,
            "action": action,
            "description": description,
            "execution_time": execution.execution_time.isoformat() if execution.execution_time else None
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch active directive: {str(e)}")


@router.get("/directive-history")
async def get_directive_history(
    strategy_id: Optional[int] = Query(None, description="策略定义ID，可选"),
    limit: int = Query(100, ge=1, le=200, description="返回数量限制"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取指令历史
    
    返回最近100条策略执行记录，包含策略信息、执行结果和收益百分比
    """
    try:
        query = select(StrategyExecution).options(
            selectinload(StrategyExecution.user)
        )
        
        if strategy_id:
            query = query.join(Portfolio).where(
                Portfolio.strategy_definition_id == strategy_id
            )
        
        query = query.order_by(desc(StrategyExecution.execution_time)).limit(limit)
        
        result = await db.execute(query)
        executions = result.scalars().all()
        
        # 批量查询策略定义
        portfolio_ids = [e.portfolio_id for e in executions if e.portfolio_id]
        portfolios_query = select(Portfolio).where(
            Portfolio.id.in_(portfolio_ids)
        ).options(selectinload(Portfolio.strategy_definition))
        
        portfolios_result = await db.execute(portfolios_query)
        portfolios = {p.id: p for p in portfolios_result.scalars().all()}
        
        directives = []
        for execution in executions:
            portfolio = portfolios.get(execution.portfolio_id) if execution.portfolio_id else None
            
            strategy_name = "Unknown Strategy"
            strategy_subtitle = ""
            
            if portfolio and portfolio.strategy_definition:
                strategy_name = portfolio.strategy_definition.display_name
                strategy_subtitle = portfolio.strategy_definition.description or ""
            
            conviction_score = execution.conviction_score or 0
            status = get_status_text(execution.signal or "HOLD", conviction_score)
            
            position_size = execution.position_size or 0
            action_type = execution.signal or "HOLD"
            asset = portfolio.strategy_definition.trade_symbol if portfolio and portfolio.strategy_definition else "BTC"
            
            action = {
                "type": action_type,
                "amount": f"{position_size * 100:.2f}%" if position_size else "-",
                "asset": asset,
                "sentiment": "bullish" if action_type == "BUY" else "bearish" if action_type == "SELL" else "neutral"
            }
            
            # TODO: 计算收益百分比（需要关联trades表）
            result_pct = 0.0  # 暂时返回0，后续实现
            
            directives.append({
                "id": str(execution.id),
                "timestamp": format_relative_time(execution.execution_time),
                "execution_time": execution.execution_time.isoformat() if execution.execution_time else None,
                "strategy": strategy_name,
                "strategy_subtitle": strategy_subtitle,
                "status": status,
                "action": action,
                "conviction": conviction_score,
                "result": result_pct
            })
        
        return {
            "directives": directives,
            "total": len(directives),
            "last_updated": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch directive history: {str(e)}")


@router.get("/data-stream")
async def get_data_stream(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取格式化的数据流数组
    
    返回Macro, OnChain, TA, Risk, Sentiment数据，用于Exploration页面右侧显示
    """
    try:
        latest_executions = await agent_execution_recorder.get_latest_executions(db, user_id=None)
        
        stream_items = []
        
        # Macro数据
        macro_execution = latest_executions.get("macro_agent")
        if macro_execution:
            macro_data = macro_execution.agent_specific_data or {}
            macro_indicators = macro_data.get("macro_indicators", {})
            
            fed_rate = macro_indicators.get("fed_funds_rate", {}).get("value")
            if fed_rate:
                stream_items.append({
                    "type": "Macro",
                    "text": f"Fed Rate: {fed_rate:.2f}%",
                    "trend": "neutral"
                })
            
            etf_flow = macro_indicators.get("etf_flow", 0)
            if etf_flow:
                stream_items.append({
                    "type": "Macro",
                    "text": f"ETF Net Flow: +${etf_flow/1e6:.0f}M" if etf_flow > 0 else f"ETF Net Flow: ${etf_flow/1e6:.0f}M",
                    "trend": "up" if etf_flow > 0 else "down"
                })
        
        # OnChain数据
        onchain_execution = latest_executions.get("onchain_agent")
        if onchain_execution:
            onchain_data = onchain_execution.agent_specific_data or {}
            onchain_metrics = onchain_data.get("onchain_metrics", {})
            
            active_addresses = onchain_metrics.get("active_addresses")
            if active_addresses:
                stream_items.append({
                    "type": "OnChain",
                    "text": f"Active Addresses: {active_addresses/1000:.0f}K",
                    "trend": "up" if onchain_execution.signal == "BULLISH" else "down" if onchain_execution.signal == "BEARISH" else "neutral"
                })
            
            exchange_flow = onchain_metrics.get("exchange_netflow", 0)
            if exchange_flow:
                stream_items.append({
                    "type": "OnChain",
                    "text": f"Exchange Flow: {exchange_flow/1000:.0f}K BTC" if exchange_flow > 0 else f"Exchange Flow: {abs(exchange_flow)/1000:.0f}K BTC",
                    "trend": "up" if exchange_flow < 0 else "down"  # 流出是看涨
                })
        
        # TA数据
        ta_execution = latest_executions.get("ta_agent")
        if ta_execution:
            ta_data = ta_execution.agent_specific_data or {}
            technical_indicators = ta_data.get("technical_indicators", {})
            
            rsi_data = technical_indicators.get("rsi", {})
            rsi_value = rsi_data.get("value") if isinstance(rsi_data, dict) else None
            if rsi_value:
                stream_items.append({
                    "type": "TA",
                    "text": f"BTC RSI(14): {rsi_value:.2f}",
                    "trend": "up" if rsi_value > 70 else "down" if rsi_value < 30 else "neutral"
                })
            
            ema_data = technical_indicators.get("ema", {})
            trend_status = get_trend_status(ema_data)
            if trend_status != "Unknown":
                stream_items.append({
                    "type": "TA",
                    "text": f"{trend_status} Active",
                    "trend": "up" if "Golden" in trend_status or "Bullish" in trend_status else "down" if "Death" in trend_status or "Bearish" in trend_status else "neutral"
                })
        
        # Fear & Greed Index（需要从market_data API获取，这里暂时跳过）
        # TODO: 集成Fear & Greed Index到数据流
        
        return {
            "stream": stream_items,
            "last_updated": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch data stream: {str(e)}")


@router.get("/available-strategies")
async def get_available_strategies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取所有已激活的策略列表
    
    不判断权限，所有用户都可见所有已激活的策略
    """
    try:
        query = select(StrategyDefinition).where(
            StrategyDefinition.is_active == True
        ).order_by(StrategyDefinition.display_name)
        
        result = await db.execute(query)
        strategies = result.scalars().all()
        
        return {
            "strategies": [
                {
                    "id": s.id,
                    "name": s.name,
                    "display_name": s.display_name,
                    "description": s.description or "",
                    "is_active": s.is_active,
                    "is_locked": False  # 所有已激活的策略都可见
                }
                for s in strategies
            ],
            "total": len(strategies)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch available strategies: {str(e)}")

