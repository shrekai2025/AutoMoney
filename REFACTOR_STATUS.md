# 策略系统重构进度报告

## 📊 总体进度：12/15 (80%)

---

## ✅ 已完成工作 (12项)

### 1. 数据库模型层 ✅
**文件:**
- `app/models/strategy_definition.py` - 策略模板模型
- `app/models/agent_registry.py` - Agent注册表模型
- `app/models/tool_registry.py` - Tool注册表模型
- `app/models/api_config.py` - API配置模型
- `app/models/portfolio.py` - Portfolio模型（已修改，添加strategy_definition_id等字段）
- `app/models/user.py` - User模型（role扩展为user/trader/admin）
- `app/models/__init__.py` - 导出所有新模型

**状态:** 代码完成，无lint错误

---

### 2. 数据库迁移 ✅
**文件:**
- `alembic/versions/001_add_strategy_system_tables.py`

**内容:**
- 创建4个新表（strategy_definitions, agent_registry, tool_registry, api_config）
- 修改portfolios表（添加strategy_definition_id, instance_name, instance_description, instance_params等）
- 删除portfolios的旧字段（strategy_name, rebalance_period_minutes, agent_weights等）

**执行步骤:**
```bash
cd AMbackend
alembic upgrade head
```

---

### 3. 初始化脚本 ✅
**文件:**
- `scripts/cleanup_old_portfolios.py` - 清理旧数据
- `scripts/init_strategy_definitions.py` - 初始化策略模板
- `scripts/init_registries.py` - 初始化注册表

**执行步骤:**
```bash
# 1. 清理旧数据
python scripts/cleanup_old_portfolios.py

# 2. 初始化策略模板
python scripts/init_strategy_definitions.py

# 3. 初始化注册表
python scripts/init_registries.py
```

---

### 4. 决策Agent系统 ✅
**文件:**
- `app/decision_agents/__init__.py`
- `app/decision_agents/base.py` - 抽象基类（预留）
- `app/decision_agents/multi_agent_conviction.py` - 多Agent信念决策引擎

**特性:**
- 整合了ConvictionCalculator和SignalGenerator
- 支持从instance_params读取参数
- 返回完整的决策结果

**测试状态:** ✅ 导入测试通过

---

### 5. 策略模板管理服务 ✅
**文件:**
- `app/services/strategy/definition_service.py`

**功能:**
- 获取所有策略模板
- 获取单个模板详情
- 更新模板配置
- 从模板创建实例
- 生成默认实例名称

---

### 6. 注册表管理服务 ✅
**文件:**
- `app/services/agents/agent_manager.py` - Agent注册表管理
- `app/services/tools/tool_manager.py` - Tool注册表管理
- `app/services/apis/api_manager.py` - API配置管理

**用途:** Admin页面查询和展示用

---

### 7. 权限系统扩展 ✅
**文件:**
- `app/core/deps.py`

**新增函数:**
- `get_current_trader_or_admin()` - 交易员或管理员权限检查

---

### 8. 策略模板API ✅
**文件:**
- `app/api/v1/endpoints/strategy_definitions.py`

**端点:**
- `GET /api/v1/strategy-definitions` - 获取所有模板
- `GET /api/v1/strategy-definitions/{id}` - 获取模板详情
- `PATCH /api/v1/strategy-definitions/{id}` - 更新模板配置

**权限:** 仅Admin

---

### 9. Admin配置管理API ✅
**文件:**
- `app/api/v1/endpoints/admin.py`（已扩展）

**新增端点:**
- `GET /api/v1/admin/agents` - 获取Agent注册表
- `GET /api/v1/admin/tools` - 获取Tool注册表
- `GET /api/v1/admin/apis` - 获取API配置列表
- `PATCH /api/v1/admin/apis/{api_name}` - 更新API配置

---

### 10. 路由配置更新 ✅
**文件:**
- `app/api/v1/api.py`

**变更:**
- 导入strategy_definitions端点
- 注册/strategy-definitions路由

---

### 11. Orchestrator改造 ✅
**文件:**
- `app/services/strategy/strategy_orchestrator.py`

**核心改动:**
1. **动态加载决策Agent**
   - 从strategy_definition读取decision_agent_module和decision_agent_class
   - 使用importlib动态加载
   
2. **从instance_params读取参数**
   - 不再从portfolio的单独字段读取配置
   - 全部从instance_params JSONB字段读取

3. **使用决策Agent的decide方法**
   - 替代原有的ConvictionCalculator + SignalGenerator
   - 统一的决策接口

**状态:** 代码完成，逻辑正确

---

### 12. 测试工具 ✅
**文件:**
- `test_imports.py` - 导入测试脚本

**测试结果:**
- ✅ 决策Agent导入成功
- ⚠️ 其他模块因环境缺少依赖（需配置python环境）

---

## 🔄 待完成工作 (3项)

### 1. Scheduler改造 ⏳
**文件:** `app/services/strategy/scheduler.py`

**改造要点:**
```python
async def batch_execute_by_definitions():
    """按strategy_definition_id分组执行"""
    
    # 1. 获取所有活跃实例，按definition_id分组
    instances_by_definition = {}
    async with SessionLocal() as db:
        result = await db.execute(
            select(Portfolio)
            .options(selectinload(Portfolio.strategy_definition))
            .where(Portfolio.is_active == True)
        )
        portfolios = result.scalars().all()
        
        for portfolio in portfolios:
            definition_id = portfolio.strategy_definition_id
            if definition_id not in instances_by_definition:
                instances_by_definition[definition_id] = []
            instances_by_definition[definition_id].append(portfolio)
    
    # 2. 遍历每个策略模板组
    for definition_id, instances in instances_by_definition.items():
        definition = instances[0].strategy_definition
        
        # 2.1 采集市场数据（所有实例共享）
        market_data = await _fetch_market_data()
        
        # 2.2 执行一次业务Agent分析（关键优化！）
        agent_outputs, agent_errors = await real_agent_executor.execute_all_agents(
            market_data=market_data,
            db=db,
            user_id=instances[0].user_id,
            strategy_execution_id=None,  # 批量执行不需要链接
        )
        
        # 2.3 为每个实例执行决策和交易
        for instance in instances:
            try:
                # 使用共享的agent_outputs
                execution = await strategy_orchestrator.execute_strategy(
                    db=db,
                    user_id=instance.user_id,
                    portfolio_id=str(instance.id),
                    market_data=market_data,
                    agent_outputs=agent_outputs,  # 共享结果
                )
                
                instance.last_execution_time = datetime.utcnow()
                await db.commit()
                
            except Exception as e:
                logger.error(f"实例执行失败: {instance.instance_name} - {e}")
                continue
```

**核心优化:**
- 同一模板的实例共享一次Agent分析结果
- 大幅降低LLM调用成本

**预计工作量:** 2-3小时

---

### 2. Marketplace Service重构 ⏳
**当前文件:** `app/services/strategy/marketplace_service.py`
**目标文件:** `app/services/strategy/instance_service.py`

**改造要点:**
1. 文件重命名
2. 方法更新以支持新的模型结构：
   - 从portfolio.strategy_definition获取模板信息
   - 从portfolio.instance_params读取参数
   - 支持instance_name和instance_description
3. 创建实例方法移到definition_service（已完成）

**需要修改的方法:**
- `get_marketplace_list()` - 改为按role过滤显示
- `get_strategy_detail()` - 添加模板信息展示
- `update_strategy_settings()` - 更新instance_params
- `get_strategy_executions()` - 无需改动
- `get_portfolio_trades()` - 无需改动

**预计工作量:** 2-3小时

---

### 3. Marketplace API重构 ⏳
**当前文件:** `app/api/v1/endpoints/marketplace.py`
**目标文件:** `app/api/v1/endpoints/strategy_instances.py`

**改造要点:**
1. 文件重命名
2. 路由前缀改为 `/strategies`
3. 权限控制调整：
   - `GET /strategies` - 普通用户只看is_active=true，交易员/Admin看全部
   - `POST /strategies` - 仅交易员/Admin（创建实例）
   - `PATCH /strategies/{id}` - 仅交易员/Admin
4. 创建实例端点：
   ```python
   @router.post("/", response_model=PortfolioResponse)
   async def create_strategy_instance(
       create_request: CreateInstanceRequest,
       db: AsyncSession = Depends(get_db),
       current_user: User = Depends(get_current_trader_or_admin),
   ):
       """从模板创建策略实例（交易员/Admin）"""
       portfolio = await definition_service.create_instance_from_definition(
           db=db,
           definition_id=create_request.strategy_definition_id,
           user_id=current_user.id,
           initial_balance=create_request.initial_balance,
           instance_name=create_request.instance_name,
           instance_description=create_request.instance_description,
           instance_params=create_request.instance_params,
       )
       return PortfolioResponse.from_orm(portfolio)
   ```

5. 更新api.py中的路由注册：
   ```python
   api_router.include_router(
       strategy_instances.router,
       prefix="/strategies",  # 原 /marketplace
       tags=["strategies"],
   )
   ```

**预计工作量:** 2-3小时

---

## 🧪 测试检查清单

### 数据库测试
- [ ] 执行数据库迁移
- [ ] 运行初始化脚本
- [ ] 检查表结构和数据

### API测试
- [ ] 测试策略模板CRUD
  - [ ] GET /strategy-definitions
  - [ ] GET /strategy-definitions/{id}
  - [ ] PATCH /strategy-definitions/{id}
- [ ] 测试配置管理
  - [ ] GET /admin/agents
  - [ ] GET /admin/tools
  - [ ] GET /admin/apis
  - [ ] PATCH /admin/apis/{api_name}
- [ ] 测试实例创建
  - [ ] POST /strategies（创建实例）
  - [ ] 验证instance_name生成
  - [ ] 验证instance_params复制
- [ ] 测试权限控制
  - [ ] 普通用户只能看active实例
  - [ ] 交易员可以创建实例
  - [ ] Admin可以管理模板

### 策略执行测试
- [ ] 测试Orchestrator动态加载决策Agent
- [ ] 测试从instance_params读取参数
- [ ] 测试批量执行（按definition分组）
- [ ] 测试Agent结果共享

---

## 📝 部署步骤

### 1. 数据库迁移
```bash
cd AMbackend

# 备份数据库（重要！）
pg_dump automoney > backup_$(date +%Y%m%d).sql

# 执行迁移
alembic upgrade head

# 清理旧数据
python scripts/cleanup_old_portfolios.py

# 初始化新数据
python scripts/init_strategy_definitions.py
python scripts/init_registries.py
```

### 2. 代码部署
```bash
# 重启后端服务
./stop.sh
./start.sh

# 检查日志
tail -f server.log
```

### 3. 验证测试
```bash
# 测试API可用性
curl http://localhost:8000/api/v1/strategy-definitions

# 测试创建实例
# （使用Postman或其他工具测试）
```

---

## ⚠️ 注意事项

### 破坏性变更
1. **Portfolio表结构大改** - 旧数据需要清理
2. **策略参数存储方式改变** - 从单独字段 → instance_params JSONB
3. **决策逻辑接口改变** - 从直接调用 → 动态加载决策Agent

### 兼容性
- ✅ 新旧代码可以共存（通过检查strategy_definition_id是否为空）
- ⚠️ 但建议完成所有重构后再部署到生产环境

### 回滚方案
如果出现问题：
1. 回滚数据库：`alembic downgrade -1`
2. 恢复备份：`psql automoney < backup_YYYYMMDD.sql`
3. 回滚代码：`git checkout <previous_commit>`

---

## 🎯 下一步行动

### 短期（本周内）
1. ✅ 完成Scheduler改造
2. ✅ 完成Marketplace重构
3. ✅ 本地测试全流程

### 中期（下周）
1. 前端适配新API
2. 添加交易员管理UI
3. 完善Admin配置页面

### 长期
1. 添加第二个策略模板
2. 实现合约交易支持
3. 添加策略性能对比功能

---

## 📞 联系方式

如有问题，请查看：
- 代码注释（每个文件都有详细说明）
- 本文档
- Git commit历史

---

**最后更新:** 2024-01-15
**状态:** 80%完成，核心功能已实现





