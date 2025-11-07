# AutoMoney v2.0

AI驱动的加密货币投资分析系统

---

## 🚀 快速开始

### 一键启动

```bash
cd /Users/uniteyoo/Documents/AutoMoney

# 启动前后端服务
./start.sh

# 查看状态
./status.sh

# 停止服务
./stop.sh
```

### 访问地址

启动后访问：
- **前端界面**: http://localhost:3010
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

---

## 📦 项目结构

```
AutoMoney/
├── AMbackend/          # FastAPI后端
│   ├── app/           # 应用代码
│   ├── tests/         # 测试
│   └── .env           # 环境配置
│
├── AMfrontend/        # React前端
│   ├── src/          # 源代码
│   └── package.json  # 依赖配置
│
├── start.sh          # 启动脚本
├── stop.sh           # 停止脚本
├── status.sh         # 状态查看
└── .pids/            # 进程和日志
```

---

## ✅ 已完成功能

### 后端
- [x] FastAPI应用框架
- [x] Firebase Authentication
- [x] 数据库ORM（SQLAlchemy）
- [x] LLM多供应商支持（OpenRouter + Tuzi）
- [x] 数据采集框架（Binance, FRED, Glassnode, Alternative.me）
- [x] 技术指标计算（EMA, RSI, MACD, Bollinger Bands）
- [x] 测试框架

### 前端
- [x] React + Vite环境
- [x] UI组件库（Radix UI）
- [x] Firebase SDK集成
- [x] Axios HTTP客户端

---

## 📚 文档

- **[SETUP.md](SETUP.md)** - 环境配置与 API 密钥设置指南
- **[QUICKSTART.md](QUICKSTART.md)** - 详细启动指南
- **[COMMANDS.md](COMMANDS.md)** - 命令速查表
- **[FRONTEND_INTEGRATION.md](AMbackend/FRONTEND_INTEGRATION.md)** - 前端登录实现
- **[DATA_API_TODO.md](AMbackend/DATA_API_TODO.md)** - 数据API对接计划
- **[PROGRESS.md](AMbackend/PROGRESS.md)** - 开发进度追踪
- **[TECHNICAL_INDICATORS.md](AMbackend/TECHNICAL_INDICATORS.md)** - 技术指标文档

---

## 🎯 下一步

### 待实现功能

1. **前端登录** - 参考 `FRONTEND_INTEGRATION.md`
2. **数据API对接** - 参考 `DATA_API_TODO.md`
   - Alternative.me（免费，10分钟）
   - Binance公开API（免费，20分钟）
   - FRED API（需注册，30分钟）
3. **Agent实现**
   - MacroAgent - 宏观分析
   - OnChainAgent - 链上分析
   - TAAgent - 技术分析
4. **LangGraph工作流** - 多Agent协作

---

## 🛠️ 技术栈

### 后端
- **框架**: FastAPI
- **数据库**: PostgreSQL + TimescaleDB
- **ORM**: SQLAlchemy 2.0
- **认证**: Firebase Admin SDK
- **AI**: LangChain + LangGraph
- **LLM**: OpenRouter + Tuzi
- **数据分析**: Pandas + Numpy

### 前端
- **框架**: React 18
- **构建工具**: Vite
- **UI**: Radix UI + Tailwind CSS
- **图表**: Recharts
- **认证**: Firebase SDK
- **HTTP**: Axios

---

## 🔧 环境要求

- Python 3.9+
- Node.js 20+
- Docker Desktop（可选，用于PostgreSQL）

---

## 📝 配置

### 环境变量配置

**重要：请勿将 API 密钥提交到 Git！**

1. 复制环境变量模板：
```bash
cd AMbackend
cp .env.example .env
```

2. 编辑 `.env` 文件，填入你的配置：
```bash
nano AMbackend/.env
```

3. 最低配置要求：
- PostgreSQL 数据库连接
- Firebase 认证配置（7 个变量）
- JWT 密钥（生产环境必须修改默认值）
- 至少一个 LLM 服务（OpenRouter 或 Tuzi）

详细配置指南请查看 **[SETUP.md](SETUP.md)**

---

## 🆘 故障排除

### 服务启动失败

```bash
# 1. 查看状态
./status.sh

# 2. 查看日志
tail -f .pids/backend.log
tail -f .pids/frontend.log

# 3. 重启服务
./stop.sh && ./start.sh
```

### 端口被占用

```bash
# 停止所有服务
./stop.sh

# 强制清理端口
kill -9 $(lsof -ti:8000)
kill -9 $(lsof -ti:3010)

# 重新启动
./start.sh
```

---

## 📊 开发进度

- **Week 1-2**: 基础设施搭建 ✅ 83%
- **Week 3-4**: Agent核心开发 🔄 43%
  - LLM抽象层 ✅
  - 数据采集 ✅
  - 技术指标 ✅
  - Agent实现 ⏳
  - LangGraph工作流 ⏳

详见 [PROGRESS.md](AMbackend/PROGRESS.md)

---

## 👥 贡献

欢迎提交Issue和Pull Request！

---

## 📄 许可

MIT License

---

最后更新: 2025-11-07
