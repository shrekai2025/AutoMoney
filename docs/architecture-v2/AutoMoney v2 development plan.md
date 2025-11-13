AutoMoney v2.0 开发计划
基于Python + FastAPI + LangGraph架构
项目目录：AMfrontend（前端）+ AMbackend（后端）
LLM供应商：OpenRouter.ai + Tuzi（支持多模型切换）
📋 总体时间线
阶段	周期	核心目标	交付物
Phase 1	Week 1-6	MVP核心功能	完整策略执行闭环
Phase 2	Week 7-9	用户体验优化	Dashboard + SuperAgent
Phase 3	Week 10-11	生产就绪	测试 + 监控 + 文档
🎯 Phase 1: MVP核心功能（Week 1-6）
Week 1-2: 基础设施搭建
🔴 P0 - 必须完成（3天）
Task 1.1: 后端项目初始化
# 工作目录：AMbackend/
- [ ] 创建FastAPI项目结构
- [ ] 配置Poetry依赖管理
- [ ] 创建.env配置模板
- [ ] 设置Python代码规范（black + isort + flake8）
交付物：
AMbackend/pyproject.toml
AMbackend/app/main.py
AMbackend/.env.example
AMbackend/app/core/config.py
验收标准：
cd AMbackend
poetry install
poetry run uvicorn app.main:app --reload
# 访问 http://localhost:8000/docs 看到Swagger文档
Task 1.2: Docker开发环境
# 工作目录：AMbackend/
- [ ] 编写docker-compose.yml（PostgreSQL + TimescaleDB + Redis）
- [ ] 创建init.sql初始化脚本
- [ ] 配置本地开发网络
交付物：
AMbackend/docker-compose.yml
AMbackend/scripts/init_timescaledb.sql
AMbackend/Dockerfile.dev
验收标准：
docker-compose up -d
# PostgreSQL可访问：localhost:5432
# Redis可访问：localhost:6379
# 数据持久化到本地volume
Task 1.3: 数据库ORM配置
# 工作目录：AMbackend/app/models/
- [ ] 配置SQLAlchemy异步引擎
- [ ] 创建Base模型类
- [ ] 配置Alembic迁移工具
- [ ] 创建首个迁移（users表）
交付物：
AMbackend/app/db/session.py
AMbackend/app/models/base.py
AMbackend/alembic/versions/001_create_users.py
验收标准：
alembic upgrade head
# 数据库中成功创建users表
Task 1.4: Google OAuth集成
# 工作目录：AMbackend/app/api/auth/
- [ ] 安装authlib库
- [ ] 实现Google OAuth回调
- [ ] 生成JWT Token
- [ ] 创建登录/登出API
交付物：
AMbackend/app/api/auth/google.py
AMbackend/app/core/security.py（JWT工具）
POST /api/auth/google
POST /api/auth/logout
验收标准：
# Postman测试Google登录流程
# 返回JWT Token
# Token能正确解析user_id
🟡 P1 - 重要（2天）
Task 1.5: 前端状态管理重构
# 工作目录：AMfrontend/src/store/
- [ ] 安装Zustand
- [ ] 创建userStore（用户状态）
- [ ] 创建agentStore（Agent Score状态）
- [ ] 创建portfolioStore（投资组合状态）
交付物：
AMfrontend/src/store/userStore.ts
AMfrontend/src/store/agentStore.ts
AMfrontend/src/store/portfolioStore.ts
验收标准：
// 在组件中使用
const { user, login, logout } = useUserStore()
const { scores, updateScores } = useAgentStore()
Task 1.6: API Client封装
# 工作目录：AMfrontend/src/api/
- [ ] 安装axios
- [ ] 创建API client（带JWT拦截器）
- [ ] 创建auth API模块
- [ ] 创建agent API模块
交付物：
AMfrontend/src/api/client.ts
AMfrontend/src/api/auth.ts
AMfrontend/src/api/agents.ts
🟢 P2 - 可选（1天）
Task 1.7: 开发工具配置
# 工作目录：AMbackend/
- [ ] 配置VS Code调试
- [ ] 配置pytest测试框架
- [ ] 创建Makefile快捷命令
交付物：
AMbackend/.vscode/launch.json
AMbackend/Makefile
Week 3-4: LLM集成 + Agent核心
🔴 P0 - 必须完成（4天）
Task 2.1: LLM多供应商抽象层
# 工作目录：AMbackend/app/services/llm/
- [ ] 创建LLMProvider抽象基类
- [ ] 实现OpenRouterProvider
- [ ] 实现TuziProvider
- [ ] 实现模型切换逻辑
交付物：
# AMbackend/app/services/llm/base.py
class LLMProvider(ABC):
    @abstractmethod
    async def chat(self, messages, model, **kwargs) -> LLMResponse:
        pass

# AMbackend/app/services/llm/openrouter.py
class OpenRouterProvider(LLMProvider):
    async def chat(self, messages, model, **kwargs):
        # 调用OpenRouter API
        pass

# AMbackend/app/services/llm/tuzi.py
class TuziProvider(LLMProvider):
    async def chat(self, messages, model, **kwargs):
        # 调用Tuzi API
        pass

# AMbackend/app/services/llm/manager.py
class LLMManager:
    """管理多个LLM供应商，支持动态切换"""
    def __init__(self):
        self.providers = {
            'openrouter': OpenRouterProvider(),
            'tuzi': TuziProvider(),
        }
    
    async def chat(self, provider: str, model: str, messages, **kwargs):
        return await self.providers[provider].chat(messages, model, **kwargs)
配置文件：
# AMbackend/app/core/llm_config.yaml
llm_providers:
  openrouter:
    api_key: ${OPENROUTER_API_KEY}
    base_url: https://openrouter.ai/api/v1
    models:
      claude-3.5-sonnet: anthropic/claude-3.5-sonnet
      gpt-4o: openai/gpt-4o
      gpt-4o-mini: openai/gpt-4o-mini
  
  tuzi:
    api_key: ${TUZI_API_KEY}
    base_url: https://api.tuzi.ai/v1
    models:
      claude-3.5-sonnet: claude-3-5-sonnet-20241022
      claude-haiku: claude-3-haiku-20240307

# 策略配置：为不同Agent指定模型
agent_llm_config:
  system_layer:
    provider: openrouter
    model: gpt-4o-mini  # 便宜模型
  
  macro_agent:
    provider: tuzi
    model: claude-3.5-sonnet  # 质量优先
    fallback:
      provider: openrouter
      model: claude-3.5-sonnet
  
  onchain_agent:
    provider: tuzi
    model: claude-3.5-sonnet
  
  ta_agent:
    provider: openrouter
    model: gpt-4o
验收标准：
# 测试多供应商切换
llm = LLMManager()
result1 = await llm.chat('openrouter', 'gpt-4o-mini', messages)
result2 = await llm.chat('tuzi', 'claude-3.5-sonnet', messages)
# 两者都能正常返回
Task 2.2: 数据采集模块
# 工作目录：AMbackend/app/services/data_collectors/
- [ ] 创建DataCollector抽象基类
- [ ] 实现BinanceCollector（价格数据）
- [ ] 实现GlassnodeCollector（链上数据）
- [ ] 实现FREDCollector（宏观数据）
- [ ] 实现AlternativeMeCollector（Fear & Greed）
交付物：
# AMbackend/app/services/data_collectors/binance.py
class BinanceCollector(DataCollector):
    async def collect(self) -> dict:
        # 获取BTC/ETH价格
        # 获取K线数据
        return {
            'BTC': {'price': 45000, 'ohlcv': [...]}
        }

# AMbackend/app/services/data_collectors/glassnode.py
class GlassnodeCollector(DataCollector):
    async def collect(self) -> dict:
        # 获取MVRV, NVT等指标
        return {
            'mvrv_z_score': 2.5,
            'nvt_ratio': 60.0,
            ...
        }
验收标准：
# 运行数据采集测试
poetry run python -m app.services.data_collectors.test
# 成功获取所有数据源数据
Task 2.3: 技术指标计算
# 工作目录：AMbackend/app/services/indicators/
- [ ] 安装TA-Lib或pandas-ta
- [ ] 实现EMA计算
- [ ] 实现RSI计算
- [ ] 实现MACD计算
- [ ] 实现Bollinger Bands计算
交付物：
# AMbackend/app/services/indicators/calculator.py
class IndicatorCalculator:
    def calculate_ema(self, prices: list, period: int) -> float:
        pass
    
    def calculate_rsi(self, prices: list, period: int) -> float:
        pass
    
    def calculate_all(self, ohlcv_data: pd.DataFrame) -> dict:
        return {
            'ema_21': ...,
            'ema_55': ...,
            'rsi_14': ...,
            'macd': ...,
        }
Task 2.4: MacroAgent实现
# 工作目录：AMbackend/app/agents/macro_agent.py
- [ ] 设计MacroAgent Prompt
- [ ] 实现数据预处理（规则引擎）
- [ ] 调用LLM分析
- [ ] 解析LLM输出（Pydantic验证）
- [ ] 存储结果到TimescaleDB
交付物：
# AMbackend/app/agents/macro_agent.py
class MacroAgent:
    def __init__(self, llm_manager: LLMManager):
        self.llm = llm_manager
        self.prompt_template = """
你是专业的宏观经济分析师，评估加密市场宏观环境。

输入数据：
- ETF净流入: {etf_flow} USD
- CME期货多头占比: {futures_position}%
- 美联储降息概率: {fed_rate_prob}%
- 全球M2增长: {m2_growth}%

规则引擎已计算初步score: {preliminary_score}

请你：
1. 验证这个score是否合理
2. 考虑规则未覆盖的因素（地缘政治、突发事件等）
3. 给出最终score（可微调±0.2）
4. 用3-5句话解释reasoning

输出JSON格式：
{{
  "score": 0.8,  // -1.0 ~ +1.0
  "confidence": 0.9,  // 0 ~ 1
  "reasoning": "...",
  "signals": {{
    "etf": "bullish",
    "futures": "neutral",
    "fed": "bullish",
    "liquidity": "bullish"
  }}
}}
"""
    
    async def analyze(self, data: dict) -> MacroAgentOutput:
        # 1. 规则引擎预处理
        preliminary_score = self._calculate_preliminary_score(data)
        
        # 2. 调用LLM
        messages = [
            {"role": "system", "content": "You are a macro economist."},
            {"role": "user", "content": self.prompt_template.format(
                etf_flow=data['etf_flow'],
                futures_position=data['futures_position'],
                fed_rate_prob=data['fed_rate_prob'],
                m2_growth=data['m2_growth'],
                preliminary_score=preliminary_score
            )}
        ]
        
        response = await self.llm.chat(
            provider='tuzi',
            model='claude-3.5-sonnet',
            messages=messages
        )
        
        # 3. 解析输出
        result = MacroAgentOutput.parse_raw(response.content)
        
        # 4. 存储到数据库
        await self._save_to_db(result)
        
        return result
    
    def _calculate_preliminary_score(self, data: dict) -> float:
        """规则引擎：预计算score"""
        score = 0.0
        
        # 规则1: ETF流量
        if data['etf_flow'] > 100_000_000:
            score += 0.35
        elif data['etf_flow'] < -100_000_000:
            score -= 0.35
        
        # 规则2: 降息预期
        if data['fed_rate_prob'] > 70:
            score += 0.30
        elif data['fed_rate_prob'] < 30:
            score -= 0.30
        
        # 规则3: M2增长
        if data['m2_growth'] > 5:
            score += 0.15
        
        # 规则4: 期货持仓
        if data['futures_position'] > 60:
            score += 0.20
        elif data['futures_position'] < 40:
            score -= 0.20
        
        return max(-1.0, min(1.0, score))
验收标准：
# 单元测试
test_data = {
    'etf_flow': 250_000_000,
    'futures_position': 65,
    'fed_rate_prob': 80,
    'm2_growth': 5.5
}
result = await macro_agent.analyze(test_data)
assert -1.0 <= result.score <= 1.0
assert 0 <= result.confidence <= 1
assert len(result.reasoning) > 0
Task 2.5: OnChainAgent实现
# 工作目录：AMbackend/app/agents/onchain_agent.py
- [ ] 设计OnChainAgent Prompt
- [ ] 实现MVRV/NVT阈值规则
- [ ] 调用LLM分析
- [ ] 输出标准化结果
Prompt模板：
ONCHAIN_AGENT_PROMPT = """
你是专业的链上数据分析师，评估比特币健康度。

输入数据：
- MVRV Z-Score: {mvrv} (>7=泡沫, <1=低估)
- NVT Ratio: {nvt} (>100=高估, <50=低估)
- 交易所净流量: {exchange_flow} BTC
- 长期持有者变化: {lth_change}%
- 活跃地址: {active_addresses}

规则引擎初步score: {preliminary_score}

请输出JSON格式：
{{
  "score": 0.7,  // -1.0 ~ +1.0
  "confidence": 0.85,
  "reasoning": "链上数据健康...",
  "signals": {{
    "valuation": "fair",
    "accumulation": "whales_buying",
    "activity": "increasing"
  }}
}}

规则：
- 交易所流出>10000 BTC → bullish（囤币）
- LTH增长>2% → bullish
- MVRV<3 → bullish; MVRV>7 → bearish
"""
Task 2.6: TAAgent实现
# 工作目录：AMbackend/app/agents/ta_agent.py
- [ ] 设计TAAgent Prompt
- [ ] 集成技术指标计算结果
- [ ] 调用LLM分析
Prompt模板：
TA_AGENT_PROMPT = """
你是专业的技术分析师，评估趋势。

技术指标：
- EMA21: {ema21}, EMA55: {ema55}
- 周RSI(14): {rsi}
- MACD柱状图: {macd}
- 布林带宽度: {bb_width}

规则引擎初步score: {preliminary_score}

输出JSON：
{{
  "score": 0.5,
  "confidence": 0.75,
  "reasoning": "中期看多：EMA金叉...",
  "signals": {{
    "trend": "uptrend",
    "momentum": "neutral",
    "volatility": "normal"
  }}
}}

规则：
- EMA21>EMA55 → bullish（金叉）
- RSI>70 → overbought; RSI<30 → oversold
- MACD>0 → bullish
"""
🟡 P1 - 重要（2天）
Task 2.7: LangGraph工作流搭建
# 工作目录：AMbackend/app/workflows/strategy_workflow.py
- [ ] 安装langgraph
- [ ] 定义StrategyState
- [ ] 创建工作流图
- [ ] 配置并行节点
- [ ] 测试工作流执行
交付物：
# AMbackend/app/workflows/strategy_workflow.py
from langgraph.graph import StateGraph
from typing import TypedDict, Annotated
import operator

class StrategyState(TypedDict):
    # 输入
    strategy_id: str
    market_data: dict
    
    # 分析层输出
    macro_score: Annotated[float, operator.add]
    macro_reasoning: str
    onchain_score: Annotated[float, operator.add]
    onchain_reasoning: str
    ta_score: Annotated[float, operator.add]
    ta_reasoning: str
    
    # 决策层输出
    conviction_score: float
    signal: str
    reasoning: str
    
    # 元数据
    errors: list[str]

# 创建工作流
workflow = StateGraph(StrategyState)

# 添加节点
workflow.add_node("macro", macro_agent_node)
workflow.add_node("onchain", onchain_agent_node)
workflow.add_node("ta", ta_agent_node)
workflow.add_node("conviction", conviction_calculator_node)
workflow.add_node("signal", signal_generator_node)

# 设置并行入口点
workflow.set_entry_point("macro")
workflow.set_entry_point("onchain")
workflow.set_entry_point("ta")

# 添加边
workflow.add_edge("macro", "conviction")
workflow.add_edge("onchain", "conviction")
workflow.add_edge("ta", "conviction")
workflow.add_edge("conviction", "signal")
workflow.set_finish_point("signal")

# 编译
app = workflow.compile()
验收标准：
# 测试工作流
state = {
    'strategy_id': 'hodl-wave',
    'market_data': {...}
}
result = await app.ainvoke(state)
assert result['conviction_score'] is not None
assert result['signal'] in ['BUY', 'SELL', 'HOLD']
Week 5-6: 决策层 + Paper Trading
🔴 P0 - 必须完成（4天）
Task 3.1: ConvictionCalculator实现
# 工作目录：AMbackend/app/services/decision/conviction.py
- [ ] 实现加权公式
- [ ] 实现风险调整逻辑
- [ ] 单元测试
交付物：
class ConvictionCalculator:
    def calculate(
        self, 
        macro_score: float, 
        onchain_score: float, 
        ta_score: float,
        volatility: float,
        fear_index: int,
        mvrv: float
    ) -> ConvictionScore:
        # 1. 加权汇总
        base_score = (
            macro_score * 0.4 +
            onchain_score * 0.4 +
            ta_score * 0.2
        )
        
        # 2. 归一化到0-100
        conviction = (base_score + 1) * 50
        
        # 3. 风险调整
        if volatility > 0.06:
            conviction *= 0.8
        if fear_index < 20:
            conviction *= 0.7
        if mvrv > 7:
            conviction *= 0.5
        
        # 4. 截断
        conviction = max(0, min(100, conviction))
        
        return ConvictionScore(
            score=conviction,
            breakdown={
                'macro': macro_score,
                'onchain': onchain_score,
                'ta': ta_score
            },
            adjustments={
                'volatility': volatility,
                'fear_index': fear_index,
                'mvrv': mvrv
            }
        )
Task 3.2: SignalGenerator实现
# 工作目录：AMbackend/app/services/decision/signal.py
- [ ] 实现信号规则
- [ ] 实现熔断规则
- [ ] 实现仓位计算
交付物：
class SignalGenerator:
    def generate(
        self, 
        conviction: ConvictionScore,
        current_portfolio: Portfolio
    ) -> TradingSignal:
        # 熔断规则（优先级最高）
        if conviction.adjustments['fear_index'] < 20:
            return TradingSignal(
                action='SELL',
                reason='CIRCUIT_BREAKER: Extreme Fear',
                urgency='HIGH'
            )
        
        if conviction.adjustments['mvrv'] > 7:
            return TradingSignal(
                action='SELL',
                reason='CIRCUIT_BREAKER: Bubble Territory',
                urgency='HIGH'
            )
        
        # 正常决策
        if conviction.score > 70:
            action = 'BUY'
            position_size = self._calculate_position(conviction, current_portfolio)
        elif conviction.score < 40:
            action = 'SELL'
            position_size = 0.5  # 减仓50%
        else:
            action = 'HOLD'
            position_size = 0
        
        return TradingSignal(
            action=action,
            conviction_score=conviction.score,
            position_size=position_size,
            reasoning=self._generate_reasoning(conviction)
        )
    
    def _calculate_position(self, conviction, portfolio):
        """动态仓位计算"""
        if conviction.score > 80:
            base_ratio = 0.0075  # 0.75%
        elif conviction.score > 70:
            base_ratio = 0.005   # 0.5%
        else:
            base_ratio = 0.0025
        
        # 风险调整
        if conviction.adjustments['volatility'] > 0.06:
            base_ratio *= 0.5
        
        return portfolio.total_value * base_ratio
Task 3.3: Paper Trading引擎
# 工作目录：AMbackend/app/services/trading/paper_engine.py
- [ ] 实现模拟订单执行
- [ ] 实现持仓更新
- [ ] 实现盈亏计算
- [ ] 实现交易历史记录
交付物：
class PaperTradingEngine:
    async def execute(
        self, 
        signal: TradingSignal,
        user_id: str,
        strategy_id: str
    ) -> TradeExecution:
        # 1. 获取当前价格
        current_price = await self.get_current_price(signal.asset)
        
        # 2. 计算交易数量
        if signal.action == 'BUY':
            quantity = signal.position_size / current_price
        elif signal.action == 'SELL':
            quantity = await self.get_holding_quantity(user_id, signal.asset)
            quantity *= signal.position_size  # 减仓比例
        else:
            return None  # HOLD不执行
        
        # 3. 创建交易记录
        trade = Trade(
            user_id=user_id,
            strategy_id=strategy_id,
            asset=signal.asset,
            action=signal.action,
            quantity=quantity,
            price=current_price,
            total_value=quantity * current_price,
            fee=quantity * current_price * 0.001,  # 0.1%手续费
            conviction_score=signal.conviction_score,
            signal_reasoning=signal.reasoning,
            status='EXECUTED'
        )
        
        # 4. 更新持仓
        await self.update_portfolio(user_id, trade)
        
        # 5. 计算盈亏（如果是SELL）
        if signal.action == 'SELL':
            pnl = await self.calculate_realized_pnl(user_id, trade)
            trade.realized_pnl = pnl
        
        # 6. 保存到数据库
        await self.save_trade(trade)
        
        return TradeExecution(
            trade_id=trade.id,
            executed_at=datetime.utcnow(),
            executed_price=current_price,
            executed_quantity=quantity
        )
Task 3.4: APScheduler调度器
# 工作目录：AMbackend/app/services/scheduler/strategy_scheduler.py
- [ ] 配置APScheduler
- [ ] 创建策略执行任务
- [ ] 创建数据采集任务
- [ ] 实现任务锁（防止重复执行）
交付物：
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.redis import RedisJobStore

class StrategyScheduler:
    def __init__(self):
        jobstores = {
            'default': RedisJobStore(host='localhost', port=6379)
        }
        
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            job_defaults={
                'coalesce': True,
                'max_instances': 1
            }
        )
    
    def start(self):
        # 策略执行任务
        self.scheduler.add_job(
            self.execute_hodl_wave,
            'cron',
            hour='*/4',  # 每4小时
            id='hodl_wave_strategy',
            replace_existing=True
        )
        
        # 数据采集任务
        self.scheduler.add_job(
            self.collect_market_data,
            'cron',
            minute='*/5',  # 每5分钟
            id='collect_binance_data',
            replace_existing=True
        )
        
        self.scheduler.start()
    
    async def execute_hodl_wave(self):
        """执行宏观波段HODL策略"""
        lock_key = 'lock:strategy:hodl-wave'
        
        # 获取分布式锁
        if not await redis.set(lock_key, '1', nx=True, ex=3600):
            logger.info('Strategy already running')
            return
        
        try:
            # 1. 收集数据
            data = await self.collect_all_data()
            
            # 2. 执行LangGraph工作流
            result = await strategy_workflow.ainvoke({
                'strategy_id': 'hodl-wave',
                'market_data': data
            })
            
            # 3. 执行交易
            if result['signal'] != 'HOLD':
                await paper_trading_engine.execute(
                    signal=result['signal'],
                    user_id=...,
                    strategy_id='hodl-wave'
                )
            
            # 4. 推送WebSocket
            await ws_gateway.broadcast_agent_scores(result)
            
        finally:
            await redis.delete(lock_key)
Task 3.5: WebSocket实时推送
# 工作目录：AMbackend/app/api/websocket/gateway.py
- [ ] 安装python-socketio
- [ ] 创建WebSocket Gateway
- [ ] 实现订阅机制
- [ ] 实现广播功能
交付物：
import socketio

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')

class WebSocketGateway:
    @sio.event
    async def connect(sid, environ, auth):
        # 验证JWT
        token = auth.get('token')
        user = await verify_jwt(token)
        await sio.save_session(sid, {'user_id': user.id})
        await sio.enter_room(sid, f'user_{user.id}')
    
    @sio.event
    async def subscribe_agent_scores(sid, data):
        strategy_id = data['strategyId']
        await sio.enter_room(sid, f'strategy_{strategy_id}')
    
    async def broadcast_agent_scores(self, strategy_id, scores):
        await sio.emit(
            'agent:scores',
            scores,
            room=f'strategy_{strategy_id}'
        )
前端集成：
// AMfrontend/src/hooks/useWebSocket.ts
import { io } from 'socket.io-client'

export function useAgentScores() {
  const [scores, setScores] = useState(null)
  
  useEffect(() => {
    const socket = io('http://localhost:8000', {
      auth: { token: localStorage.getItem('jwt') }
    })
    
    socket.emit('subscribe:agent_scores', { strategyId: 'hodl-wave' })
    
    socket.on('agent:scores', (data) => {
      setScores(data)
    })
    
    return () => socket.disconnect()
  }, [])
  
  return scores
}
🟡 P1 - 重要（2天）
Task 3.6: 数据库完整Schema
# 工作目录：AMbackend/alembic/versions/
- [ ] 创建所有核心表迁移
- [ ] 配置TimescaleDB Hypertable
- [ ] 创建索引
- [ ] 插入种子数据（策略模板）
交付物：
002_create_strategies.py
003_create_portfolios.py
004_create_trades.py
005_create_timescale_tables.py
006_seed_strategies.py
Task 3.7: 端到端测试
- [ ] 测试完整策略执行流程
- [ ] 验证数据流转正确性
- [ ] 检查WebSocket推送
验收标准：
# 1. 启动服务
docker-compose up -d
poetry run uvicorn app.main:app

# 2. 触发策略执行
curl -X POST http://localhost:8000/api/strategies/hodl-wave/execute

# 3. 验证结果
# - PostgreSQL中有agent_analysis_results记录
# - 前端收到WebSocket推送
# - trades表有新交易记录
🎨 Phase 2: 用户体验优化（Week 7-9）
Week 7-8: Dashboard增强
🔴 P0 - 必须完成（3天）
Task 4.1: 投资组合API
# 工作目录：AMbackend/app/api/portfolio/
- [ ] GET /api/portfolio （获取总览）
- [ ] GET /api/portfolio/history （历史曲线）
- [ ] GET /api/portfolio/holdings （持仓明细）
Task 4.2: 交易历史API
- [ ] GET /api/trades （分页查询）
- [ ] GET /api/trades/:id （单个详情）
- [ ] 支持筛选（按策略、资产、时间范围）
Task 4.3: 前端Dashboard重构
# 工作目录：AMfrontend/src/components/Dashboard.tsx
- [ ] 集成TanStack Query获取数据
- [ ] 实时P&L计算
- [ ] 历史收益曲线图
- [ ] 策略性能对比
🟡 P1 - 重要（2天）
Task 4.4: Mind Hub完善
# 工作目录：AMfrontend/src/components/Exploration.tsx
- [ ] Agent Score历史趋势图
- [ ] 实时数据Feed（WebSocket）
- [ ] 决策推理可视化
- [ ] 下次更新倒计时
Task 4.5: 策略市场优化
# 工作目录：AMfrontend/src/components/StrategyMarketplace.tsx
- [ ] 策略订阅功能
- [ ] 策略性能图表
- [ ] 风险评级展示
Week 9: SuperAgent对话
🔴 P0 - 必须完成（3天）
Task 5.1: SuperAgent实现
# 工作目录：AMbackend/app/agents/super_agent.py
- [ ] 意图识别Prompt
- [ ] 调用LLM分类用户意图
- [ ] 返回结构化Intent对象
Task 5.2: PlanningAgent实现
# 工作目录：AMbackend/app/agents/planning_agent.py
- [ ] 根据意图选择Agent组合
- [ ] 协调Agent执行
- [ ] 汇总结果返回
Task 5.3: 对话API
- [ ] POST /api/chat （用户发送消息）
- [ ] GET /api/chat/history （对话历史）
- [ ] WebSocket支持流式响应
Task 5.4: 前端对话组件
# 工作目录：AMfrontend/src/components/ChatWidget.tsx
- [ ] 创建聊天窗口
- [ ] 支持Markdown渲染
- [ ] 显示Agent调用过程
🚀 Phase 3: 生产就绪（Week 10-11）
Week 10: 测试 + 优化
🔴 P0 - 必须完成（3天）
Task 6.1: 单元测试
# 工作目录：AMbackend/tests/
- [ ] Agent测试（Mock LLM）
- [ ] ConvictionCalculator测试
- [ ] SignalGenerator测试
- [ ] PaperTradingEngine测试
目标：覆盖率 > 80%
Task 6.2: 集成测试
- [ ] 完整工作流测试
- [ ] API端到端测试
- [ ] WebSocket测试
Task 6.3: 性能优化
- [ ] 数据库查询优化（EXPLAIN ANALYZE）
- [ ] Redis缓存策略调整
- [ ] LLM调用并发优化
目标：
Agent分析 < 10秒
API响应 P95 < 500ms
WebSocket延迟 < 100ms
🟡 P1 - 重要（2天）
Task 6.4: 错误处理完善
- [ ] 全局异常处理器
- [ ] LLM API降级逻辑
- [ ] 数据采集失败重试
Task 6.5: 日志系统
- [ ] 配置结构化日志（JSON格式）
- [ ] 按模块分级（DEBUG/INFO/WARNING/ERROR）
- [ ] 日志轮转配置
Week 11: 监控 + 文档
🔴 P0 - 必须完成（2天）
Task 7.1: 成本监控
# 工作目录：AMbackend/app/services/monitoring/cost_tracker.py
- [ ] 记录每次LLM调用成本
- [ ] 按用户/策略/Agent聚合
- [ ] 成本告警（日成本>$50）
交付物：
class CostTracker:
    async def track_llm_call(
        self, 
        provider: str,
        model: str,
        tokens: int,
        cost: float,
        context: dict
    ):
        await db.execute(
            insert(llm_cost_log).values(
                provider=provider,
                model=model,
                tokens=tokens,
                cost=cost,
                user_id=context['user_id'],
                agent_type=context['agent_type'],
                timestamp=datetime.utcnow()
            )
        )
        
        # 检查日成本
        daily_cost = await self.get_daily_cost()
        if daily_cost > 50:
            await self.send_alert(f'Daily cost exceeded: ${daily_cost}')
Task 7.2: Sentry错误追踪
# 工作目录：AMbackend/app/core/monitoring.py
- [ ] 集成Sentry SDK
- [ ] 配置错误捕获
- [ ] 自定义错误上下文
🟡 P1 - 重要（2天）
Task 7.3: API文档完善
- [ ] 完善Swagger注释
- [ ] 添加请求/响应示例
- [ ] 创建Postman Collection
Task 7.4: 开发文档
# 工作目录：AMbackend/docs/
- [ ] 环境搭建指南
- [ ] API使用手册
- [ ] Agent Prompt库
- [ ] 故障排查手册
📊 进度追踪表
Week	P0任务数	P1任务数	P2任务数	预估工时	累计工时
1-2	4	2	1	40h	40h
3-4	6	1	0	48h	88h
5-6	5	1	0	48h	136h
7-8	3	2	0	40h	176h
9	4	0	0	24h	200h
10	3	2	0	40h	240h
11	2	2	0	32h	272h
总计	27	10	1	272h	-
🎯 关键里程碑
里程碑	时间	验收标准
M1: 基础设施	Week 2结束	✅ 后端可启动 ✅ 数据库迁移成功 ✅ OAuth可登录
M2: Agent核心	Week 4结束	✅ 3个Agent可独立执行 ✅ LangGraph工作流运行
M3: MVP闭环	Week 6结束	✅ 策略自动执行 ✅ 模拟交易 ✅ WebSocket推送
M4: 用户体验	Week 9结束	✅ Dashboard完善 ✅ SuperAgent可对话
M5: 生产就绪	Week 11结束	✅ 测试覆盖>80% ✅ 监控系统 ✅ 文档完整
🚦 每日站会检查清单
每日回答3个问题：
昨天完成了什么？
今天计划做什么？
有什么阻塞？
每周回顾：
完成的P0任务数
累计工时
下周优先级调整
📝 下一步立即行动
🔥 现在就开始（30分钟内）
# 1. 创建后端项目结构
cd AMbackend
poetry init --name automoney-backend --python "^3.11"

# 2. 安装核心依赖
poetry add fastapi uvicorn sqlalchemy alembic redis python-jose[cryptography]
poetry add --group dev pytest pytest-asyncio black isort flake8

# 3. 创建目录结构
mkdir -p app/{api,agents,services,models,db,core,workflows}
mkdir -p tests/{unit,integration}
mkdir -p scripts

# 4. 创建docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: timescale/timescaledb:latest-pg16
    environment:
      POSTGRES_DB: automoney
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init_timescaledb.sql:/docker-entrypoint-initdb.d/init.sql

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
EOF

# 5. 启动开发环境
docker-compose up -d

# 6. 验证
docker-compose ps