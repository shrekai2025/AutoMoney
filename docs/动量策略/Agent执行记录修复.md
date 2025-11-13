# Agent执行记录修复 - Bug修复报告

## 🐛 问题描述

用户反馈: 在策略执行详情页面,动量策略仍然显示旧的3个Agent("The Oracle", "Momentum Scout", "Data Warden"),而不是应该调用的`RegimeFilterAgent`和`TAMomentumAgent`。

---

## 🔍 问题分析

### 症状
- UI显示的Agent列表不正确
- 显示: "The Oracle", "Momentum Scout", "Data Warden" (旧策略)
- 应该显示: "Regime Filter", "Momentum TA" (动量策略)

### 根本原因

经过逐步排查,发现了三个关联问题:

#### 1. Agent执行未记录到数据库 ❌

**问题代码** (`DynamicAgentExecutor._run_agent`):
```python
# 执行Agent
output = await agent.analyze(market_data=market_data)

# ❌ 缺少: 没有调用 agent_execution_recorder 保存执行记录
return output
```

**对比** (`RealAgentExecutor._run_onchain_agent`):
```python
# 执行Agent
output = await self.onchain_agent.analyze(...)

# ✅ 正确: 调用recorder保存
await agent_execution_recorder.record_onchain_agent(
    db=db,
    output=output,
    market_data=market_data,
    llm_info=llm_info,
    strategy_execution_id=strategy_execution_id,
    ...
)
```

#### 2. 缺少通用记录方法 ❌

`AgentExecutionRecorder`只有针对旧3个Agent的特定方法:
- `record_macro_agent()`
- `record_ta_agent()`
- `record_onchain_agent()`

**缺少**:
- 没有`record_regime_filter()`
- 没有`record_ta_momentum()`
- 没有通用的`record_generic_agent()`方法

#### 3. DecisionOutput返回类型不匹配 ❌

**MomentumRegimeDecision**:
```python
def decide(...) -> DecisionOutput:  # 返回对象
    return DecisionOutput(
        signal="LONG",
        signal_strength=0.8,
        ...
    )
```

**StrategyOrchestrator期待**:
```python
decision_result = decision_agent.decide(...)
conviction_score = decision_result["conviction_score"]  # ❌ 对象不能用[]访问
```

**错误信息**:
```
'DecisionOutput' object is not subscriptable
```

---

## ✅ 解决方案

### 1. 添加通用Agent记录方法

**文件**: `AMbackend/app/services/agents/execution_recorder.py`

```python
class AgentExecutionRecorder:
    # 更新显示名称映射
    DISPLAY_NAMES = {
        'macro_agent': 'The Oracle',
        'ta_agent': 'Momentum Scout',
        'onchain_agent': 'Data Warden',
        'regime_filter': 'Regime Filter',  # 🆕
        'ta_momentum': 'Momentum TA',      # 🆕
    }
    
    async def record_generic_agent(
        self,
        db: AsyncSession,
        agent_name: str,
        output: Dict[str, Any],
        market_data: Dict[str, Any],
        llm_info: Optional[Dict[str, Any]] = None,
        caller_type: Optional[str] = None,
        caller_id: Optional[str] = None,
        strategy_execution_id: Optional[str] = None,
        user_id: Optional[int] = None,
        execution_duration_ms: Optional[int] = None,
        template_execution_batch_id: Optional[Any] = None,
    ) -> AgentExecution:
        """通用Agent执行记录方法（用于新的Agent类型）"""
        
        # 序列化数据
        serialized_market_data = self._serialize_for_json(market_data)
        serialized_output = self._serialize_for_json(output)
        
        # 获取显示名称
        display_name = self.DISPLAY_NAMES.get(agent_name, agent_name)
        
        # 智能提取标准字段
        signal = serialized_output.get('signal', 'NEUTRAL')
        confidence = serialized_output.get('confidence', 0.0)
        
        # score字段(RegimeFilterAgent有regime_score)
        score = serialized_output.get('score')
        if score is None and 'regime_score' in serialized_output:
            score = float(serialized_output['regime_score'])
        
        reasoning = serialized_output.get('reasoning', '')
        
        # 创建执行记录
        execution = AgentExecution(
            agent_name=agent_name,
            agent_display_name=display_name,
            executed_at=datetime.utcnow(),
            execution_duration_ms=execution_duration_ms or 0,
            status='success',
            signal=signal,
            confidence=confidence,
            score=score,
            reasoning=reasoning,
            agent_specific_data=serialized_output,
            market_data_snapshot=serialized_market_data,
            llm_provider=llm_info.get('provider') if llm_info else None,
            llm_model=llm_info.get('model') if llm_info else None,
            llm_prompt=llm_info.get('prompt') if llm_info else None,
            llm_response=llm_info.get('response') if llm_info else None,
            tokens_used=llm_info.get('tokens_used') if llm_info else None,
            llm_cost=llm_info.get('cost') if llm_info else None,
            caller_type=caller_type,
            caller_id=caller_id,
            strategy_execution_id=strategy_execution_id,
            user_id=user_id,
            template_execution_batch_id=template_execution_batch_id,
        )
        
        db.add(execution)
        await db.commit()
        await db.refresh(execution)
        
        return execution
```

### 2. 在DynamicAgentExecutor中记录执行

**文件**: `AMbackend/app/services/strategy/dynamic_agent_executor.py`

```python
import time
from app.services.agents.execution_recorder import agent_execution_recorder

class DynamicAgentExecutor:
    async def _run_agent(self, agent_name: str, agent: Any, ...) -> Any:
        start_time = time.time()
        
        try:
            # 执行Agent
            if agent_name == "regime_filter":
                output = await agent.analyze(market_data=market_data, use_llm=False)
            elif agent_name == "ta_momentum":
                output = await agent.analyze(market_data=market_data)
            
            # 计算执行时长
            execution_duration_ms = int((time.time() - start_time) * 1000)
            
            # 🆕 记录新Agent的执行
            if agent_name in ["regime_filter", "ta_momentum"] and db:
                try:
                    # 转换Pydantic模型为dict
                    if hasattr(output, 'dict'):
                        output_dict = output.dict()
                    elif hasattr(output, 'model_dump'):
                        output_dict = output.model_dump()
                    else:
                        output_dict = output
                    
                    await agent_execution_recorder.record_generic_agent(
                        db=db,
                        agent_name=agent_name,
                        output=output_dict,
                        market_data=market_data,
                        llm_info=None,
                        caller_type="strategy_execution",
                        strategy_execution_id=strategy_execution_id,
                        user_id=user_id,
                        execution_duration_ms=execution_duration_ms,
                        template_execution_batch_id=template_execution_batch_id,
                    )
                    logger.info(f"✅ {agent_name} 执行记录已保存")
                except Exception as record_error:
                    logger.warning(f"⚠️  {agent_name} 执行记录保存失败: {record_error}")
            
            return output
        except Exception as e:
            logger.error(f"❌ {agent_name} 执行异常: {e}", exc_info=True)
            raise
```

### 3. 修复DecisionOutput返回类型

**文件**: `AMbackend/app/decision_agents/base.py`

```python
@dataclass
class DecisionOutput:
    """决策输出"""
    signal: str
    signal_strength: float
    position_size: float
    conviction_score: float
    risk_level: str
    should_execute: bool
    reasons: list
    warnings: list
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典(用于兼容旧的决策Agent)"""
        return {
            "signal": self.signal,
            "signal_strength": self.signal_strength,
            "position_size": self.position_size,
            "conviction_score": self.conviction_score,
            "risk_level": self.risk_level,
            "should_execute": self.should_execute,
            "reasons": self.reasons,
            "warnings": self.warnings,
            **self.metadata  # 展开metadata到顶层
        }
```

**文件**: `AMbackend/app/services/strategy/strategy_orchestrator.py`

```python
# Step 6: 使用决策Agent生成决策
decision_result = decision_agent.decide(
    agent_outputs=agent_outputs,
    market_data=market_data,
    instance_params=portfolio.instance_params,
    portfolio_state=portfolio_state,
    current_position=current_position,
)

# 🆕 兼容两种返回格式
if hasattr(decision_result, 'to_dict'):
    # 新的DecisionOutput对象
    decision_dict = decision_result.to_dict()
else:
    # 旧的字典格式
    decision_dict = decision_result

conviction_score = decision_dict["conviction_score"]
signal = decision_dict["signal"]
# ...
```

---

## 🧪 测试验证

### 数据库检查
```bash
# 查询Agent执行记录
SELECT agent_name, agent_display_name, executed_at, strategy_execution_id
FROM agent_executions
WHERE strategy_execution_id = 'xxx'
ORDER BY executed_at;

# 预期结果:
# agent_name       | agent_display_name | ...
# -----------------|-------------------|----
# regime_filter    | Regime Filter     | ...
# ta_momentum      | Momentum TA       | ...
```

### UI验证
访问策略执行详情页,应该看到:
- **Agent Executions (2)** ← 而不是(3)
- "Regime Filter" ← 而不是"The Oracle"
- "Momentum TA" ← 而不是"Momentum Scout"
- (没有"Data Warden")

---

## 📊 修复影响

### 修改的文件
1. `AMbackend/app/services/agents/execution_recorder.py`
   - 添加`DISPLAY_NAMES`映射
   - 添加`record_generic_agent()`方法

2. `AMbackend/app/services/strategy/dynamic_agent_executor.py`
   - 导入`agent_execution_recorder`
   - 在`_run_agent()`中添加记录逻辑

3. `AMbackend/app/decision_agents/base.py`
   - 添加`DecisionOutput.to_dict()`方法

4. `AMbackend/app/services/strategy/strategy_orchestrator.py`
   - 添加返回格式兼容处理

### 向后兼容性
- ✅ 旧策略(macro/ta/onchain)继续使用原有记录方法
- ✅ 新策略(regime_filter/ta_momentum)使用通用记录方法
- ✅ 旧的字典返回格式仍然支持
- ✅ 新的DecisionOutput对象也支持

---

## 🎯 相关问题修复

这次修复同时解决了以下关联问题:

1. ✅ Agent执行记录缺失
2. ✅ UI显示错误的Agent列表
3. ✅ DecisionOutput类型错误导致的crash
4. ✅ 动量策略Agent执行状态无法追踪

---

## 📝 经验教训

### 1. 新功能开发要考虑记录和可观测性
- 每个Agent执行都应该记录到数据库
- 便于追溯和调试
- 提供用户可见的执行历史

### 2. 接口兼容性很重要
- 新的返回类型要考虑向后兼容
- 提供`to_dict()`等转换方法
- 避免破坏现有调用方

### 3. 通用方法优于特化方法
- `record_generic_agent()`比为每个新Agent写一个方法更可扩展
- 智能提取字段(`score` vs `regime_score`)
- 易于添加新的Agent类型

---

**修复状态**: ✅ 已完成  
**测试状态**: ⏳ 待验证  
**部署**: 需要重启后端服务

