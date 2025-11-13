# AutoMoney 架构文档 v2.0

> 🚀 基于Python + FastAPI + LangGraph的AI驱动加密货币投资平台  
> 📅 最后更新: 2025-11-05  
> 👨‍💻 架构设计: AI Assistant  
> 📝 状态: 架构设计完成，待开发实施

---

## 📚 文档导航

本架构方案分为8个模块，建议按以下顺序阅读：

### 🎯 第一阶段：理解项目（所有人必读）

| 文档 | 阅读时间 | 内容概要 | 适合人群 |
|-----|---------|---------|---------|
| [00-项目总览](./00-项目总览.md) | 15分钟 | 产品定位、功能地图、技术栈、成本估算 | 所有人 |
| [01-技术选型详解](./01-技术选型详解.md) | 20分钟 | 为什么选Python、FastAPI、LangGraph？ | 技术决策者 |

### 🏗️ 第二阶段：核心架构（开发者必读）

| 文档 | 阅读时间 | 内容概要 | 适合人群 |
|-----|---------|---------|---------|
| [02-Multi-Agent架构设计](./02-Multi-Agent架构设计.md) | 30分钟 | 三层Agent架构、LangGraph工作流 | 后端开发者 |
| [03-数据流与调度机制](./03-数据流与调度机制.md) | 25分钟 | 数据采集、处理、APScheduler调度 | 后端开发者 |

### 📊 第三阶段：实现细节（开发实施）

| 文档 | 阅读时间 | 内容概要 | 适合人群 |
|-----|---------|---------|---------|
| [04-数据库设计方案](./04-数据库设计方案.md) | ⏳ 待完善 | PostgreSQL+TimescaleDB表结构 | 后端/DBA |
| [05-API与接口设计](./05-API与接口设计.md) | 20分钟 | REST API + WebSocket通信协议 | 前后端开发者 |
| [06-部署与运维方案](./06-部署与运维方案.md) | 25分钟 | Docker、Railway部署、监控告警 | DevOps |

### 🎓 第四阶段：规范与优化（长期参考）

| 文档 | 阅读时间 | 内容概要 | 适合人群 |
|-----|---------|---------|---------|
| [07-开发规范与最佳实践](./07-开发规范与最佳实践.md) | 25分钟 | 代码规范、测试策略、Git工作流 | 全体开发者 |
| [08-成本优化与扩展路线](./08-成本优化与扩展路线.md) | 30分钟 | LLM成本优化、商业化路径、GMV预测 | 技术负责人/产品 |

---

## 🎯 架构亮点

### 1. 技术选型优势

| 选择 | 理由 | 收益 |
|-----|------|------|
| **Python + FastAPI** | AI生态强大，开发效率高 | 节省30%开发时间 |
| **LangGraph** | 专为Multi-Agent设计 | 节省60-90小时自研时间 |
| **混合LLM方案** | 成本与质量平衡 | 节省25-40% LLM成本 |
| **TimescaleDB** | 时序数据优化 | 查询性能提升100倍 |
| **Railway部署** | 零运维PaaS | 节省DevOps人力 |

### 2. Multi-Agent架构

```
用户触发
  ↓
System Layer (SuperAgent + Planning)
  ↓
Analysis Layer (Macro 40% + OnChain 40% + TA 20%)  ← 并行执行
  ↓
Decision Layer (Conviction Calculator + Signal Generator)
  ↓
Paper Trading + WebSocket推送
```

**核心优势**:
- 🚀 **并行优化**: 3个Agent同时分析，提速3倍
- 🎯 **职责清晰**: 每个Agent专注单一领域
- 🔄 **易于扩展**: 新增Agent无需改动现有代码
- 📊 **可追溯**: 每步决策可回溯和解释

### 3. 成本控制策略

| 策略 | 节省 | 实施难度 |
|-----|------|---------|
| 混合LLM方案 | 33% | 🟢 低 |
| 智能缓存 | 30-40% | 🟢 低 |
| Prompt优化 | 20% | 🟡 中 |
| 动态调整周期 | 20% | 🟢 低 |

**盈亏平衡点**: 仅需18个付费用户（@$10/月）

---

## 📊 成本与收益分析

### 初期成本（10用户）

| 项目 | 成本 |
|-----|------|
| LLM API | $50/月 |
| Glassnode | $29/月 |
| Railway | $20/月 |
| **合计** | **$99/月** |

### 6个月目标

| 指标 | 目标 |
|-----|------|
| 注册用户 | 500 |
| 付费用户 | 50 |
| MRR | $800 |
| 净利润 | $150/月 |

### 12个月目标

| 指标 | 目标 |
|-----|------|
| 注册用户 | 2000 |
| 付费用户 | 300 |
| MRR | $4,500 |
| 净利润 | $1,500/月 |

---

## 🚦 实施路线图

### Phase 1: MVP基础（Week 1-6）

**目标**: 完成第一个策略的完整闭环

**里程碑**:
- [ ] Week 1-2: 基础设施（FastAPI + PostgreSQL + Redis + OAuth）
- [ ] Week 3-4: Agent核心（LangGraph + 3个分析Agent）
- [ ] Week 5-6: 决策与交易（Conviction + Signal + Paper Trading）

**交付物**: 用户可登录、看到实时Agent Score、模拟交易、查看P&L

### Phase 2: 用户体验（Week 7-9）

**目标**: 提升用户体验，增加留存

**功能**:
- [ ] Dashboard优化
- [ ] 策略性能图表
- [ ] SuperAgent对话
- [ ] API性能优化

### Phase 3: 生产就绪（Week 10-11）

**目标**: 准备上线

**任务**:
- [ ] 单元测试覆盖率>80%
- [ ] 压力测试
- [ ] 监控告警（Sentry）
- [ ] 生产环境部署

**总计**: 11周（约2.5个月）

---

## 💡 关键设计决策

### 1. 为什么选Python而不是NestJS？

✅ **Python优势**:
- AI/ML生态强大（pandas、TA-Lib）
- 开发效率高30%
- 团队学习成本低

❌ **Trade-off**:
- 前后端类型不共享（可接受）

### 2. 为什么选LangGraph而不是自研？

✅ **LangGraph优势**:
- 节省60-90小时开发时间
- 内置可视化调试
- 社区活跃

❌ **Trade-off**:
- 依赖外部库（但很稳定）

### 3. 为什么混合LLM而不是单一模型？

✅ **混合优势**:
- 节省33% LLM成本
- 多提供商备份（可靠性）
- 灵活A/B测试

❌ **Trade-off**:
- 配置复杂度略高（可接受）

---

## 🔥 与旧版方案对比

| 维度 | v1.0 (NestJS) | v2.0 (FastAPI) | 优势 |
|-----|--------------|---------------|------|
| **开发周期** | 340-500h | 250-340h | 节省90-160h |
| **LLM成本** | $7.5/用户 | $5/用户 | 节省33% |
| **AI生态** | ⭐⭐ | ⭐⭐⭐⭐⭐ | 更适合AI项目 |
| **学习曲线** | ⭐⭐ | ⭐⭐⭐⭐ | 更易上手 |
| **运营成本** | $125/月(10用户) | $99/月(10用户) | 节省$26/月 |

**结论**: v2.0方案在开发效率、成本、AI生态上全面优于v1.0

---

## 📝 待完善文档

- [ ] **04-数据库设计方案.md**: 完整的表结构定义（已有旧版，待更新到v2.0）

该文档在Phase 1实施阶段可根据实际需求调整。

---

## 🙋 常见问题

### Q1: 为什么不用MongoDB？

**A**: PostgreSQL + TimescaleDB更适合：
- 强事务支持（交易记录需要ACID）
- 关系查询性能好（用户-策略-交易关联）
- 时序数据优化（TimescaleDB扩展）

### Q2: APScheduler能支撑多少用户？

**A**: 
- <100用户: 完全够用
- 100-500用户: 需监控任务队列
- >500用户: 迁移到Celery分布式

### Q3: LLM成本会失控吗？

**A**: 有4层防护：
1. 混合方案（节省33%）
2. 智能缓存（节省30%）
3. 用户配额限制
4. 成本实时监控告警

### Q4: 如何保证策略效果？

**A**:
1. Paper Trading模拟验证
2. 历史回测（Sharpe Ratio、Max Drawdown）
3. 透明化推理过程
4. 免责声明（仅供参考）

---

## 👥 团队分工建议

| 角色 | 职责 | 技能要求 |
|-----|------|---------|
| **后端Leader** | Agent开发、API设计 | Python、FastAPI、LangGraph |
| **后端开发** | 数据采集、调度、交易 | Python、PostgreSQL |
| **前端Leader** | UI实现、状态管理 | React、TypeScript、Zustand |
| **DevOps** | 部署、监控、成本优化 | Docker、Railway、监控 |

**最小团队**: 2后端 + 1前端 + 0.5DevOps = 3.5人

---

## 📞 联系方式

| 角色 | 姓名 | 联系方式 |
|-----|------|---------|
| **产品负责人** | TBD | - |
| **技术负责人** | TBD | - |
| **架构师** | AI Assistant | 本文档 |

---

## 📜 版本历史

| 版本 | 日期 | 变更内容 | 作者 |
|-----|------|---------|------|
| **v2.0** | 2025-11-05 | 优化版架构（Python+FastAPI+LangGraph） | AI Assistant |
| v1.0 | 2025-11-05 | 初版架构（NestJS方案） | - |

---

## 🎓 学习资源

### 推荐阅读

**FastAPI**:
- [官方文档](https://fastapi.tiangolo.com/)
- [FastAPI最佳实践](https://github.com/zhanymkanov/fastapi-best-practices)

**LangGraph**:
- [官方文档](https://langchain-ai.github.io/langgraph/)
- [Multi-Agent教程](https://blog.langchain.dev/langgraph-multi-agent-workflows/)

**加密货币分析**:
- [Glassnode Academy](https://academy.glassnode.com/)
- [链上数据分析入门](https://www.chaincatcher.com/)

---

## 🚀 快速开始

### 1. 阅读架构文档

按照上面的导航顺序阅读，预计3-4小时完整理解。

### 2. 环境准备

```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 前端
cd frontend
npm install
```

### 3. 本地开发

```bash
# 启动Redis（Docker）
docker run -d -p 6379:6379 redis:7

# 启动后端
cd backend
uvicorn app.main:app --reload

# 启动前端
cd frontend
npm run dev
```

### 4. 开始开发

从Phase 1 Week 1开始实施！

---

## ⚠️ 重要提醒

1. **成本控制**: 每天检查LLM成本，设置告警
2. **法律合规**: 仅Paper Trading，咨询律师
3. **风险提示**: 明确告知用户投资风险
4. **数据安全**: 用户数据加密存储
5. **监控告警**: 生产环境必须接入Sentry

---

## 📌 快速链接

- [项目总览](./00-项目总览.md) - 15分钟了解全貌
- [技术选型](./01-技术选型详解.md) - 理解为什么这样选
- [Agent架构](./02-Multi-Agent架构设计.md) - 核心逻辑详解
- [成本优化](./08-成本优化与扩展路线.md) - 商业可行性分析

---

**🎉 架构设计完成！接下来开始Phase 1开发实施！**

**💪 Let's build something amazing!**

