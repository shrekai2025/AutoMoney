# AutoMoney 环境配置指南

本文档详细说明如何配置 AutoMoney 项目的环境变量和 API 密钥。

**⚠️ 重要：所有敏感信息都不应提交到 Git 仓库！**

---

## 📋 目录

1. [快速开始](#快速开始)
2. [后端配置](#后端配置)
3. [前端配置](#前端配置)
4. [API 密钥获取](#api-密钥获取)
5. [安全最佳实践](#安全最佳实践)

---

## 🚀 快速开始

### 1. 复制环境变量模板

```bash
# 后端
cd AMbackend
cp .env.example .env
```

### 2. 编辑 .env 文件

使用你喜欢的编辑器打开 `AMbackend/.env` 并填入你的 API 密钥：

```bash
nano AMbackend/.env
# 或
code AMbackend/.env
```

### 3. 必需的配置项

以下配置项是项目运行的**最低要求**：

- `DATABASE_URL` - PostgreSQL 数据库连接
- `FIREBASE_*` - Firebase 认证配置（7个变量）
- `SECRET_KEY` - JWT 签名密钥（生产环境必须修改）

### 4. 可选的配置项

以下配置项可在需要时配置：

- `OPENROUTER_API_KEY` / `TUZI_API_KEY` - LLM 服务（至少配置一个）
- `BINANCE_API_KEY` - Binance 交易数据
- `FRED_API_KEY` - 美联储经济数据
- `GLASSNODE_API_KEY` - 链上数据分析

---

## 🔧 后端配置

### 数据库配置

```env
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/automoney
```

**说明**：
- 将 `username` 和 `password` 替换为你的 PostgreSQL 凭据
- 确保数据库 `automoney` 已创建

**创建数据库**：
```bash
# 使用 psql
psql -U postgres -c "CREATE DATABASE automoney;"

# 或使用 createdb
createdb -U postgres automoney
```

### Firebase 配置

前往 [Firebase Console](https://console.firebase.google.com/)：

1. 选择你的项目（或创建新项目）
2. 进入 **Project Settings** → **General**
3. 在 "Your apps" 部分，找到 Web 应用配置
4. 复制配置信息到 `.env`：

```env
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_API_KEY=AIzaSy...
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_STORAGE_BUCKET=your-project.firebasestorage.app
FIREBASE_MESSAGING_SENDER_ID=123456789
FIREBASE_APP_ID=1:123456789:web:abc123...
FIREBASE_MEASUREMENT_ID=G-ABC123...
```

**（可选）Firebase Admin SDK**：

如果需要后端服务器直接操作 Firebase：

1. 进入 **Project Settings** → **Service Accounts**
2. 点击 "Generate new private key"
3. 下载 JSON 文件并保存到安全位置
4. 配置路径：

```env
FIREBASE_SERVICE_ACCOUNT_PATH=/path/to/serviceAccountKey.json
```

### JWT 配置

```env
SECRET_KEY=your-super-secret-key-change-this-in-production
```

**生成安全的密钥**：
```bash
# 使用 Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 使用 OpenSSL
openssl rand -base64 32
```

### LLM 服务配置

#### OpenRouter

1. 访问 [OpenRouter](https://openrouter.ai/)
2. 注册并生成 API Key
3. 配置：

```env
OPENROUTER_API_KEY=sk-or-v1-...
```

#### Tuzi (兔子)

1. 访问 [Tuzi](https://tu-zi.com/)
2. 注册并生成 API Key
3. 配置：

```env
TUZI_API_KEY=sk-...
```

### 数据源配置

#### Binance API

1. 登录 [Binance](https://www.binance.com/)
2. 进入 **账户** → **API Management**
3. 创建新的 API Key（只需要 **读取** 权限）
4. 配置：

```env
BINANCE_API_KEY=your-api-key
BINANCE_API_SECRET=your-api-secret
```

**安全提示**：
- ✅ 只启用 "读取" 权限
- ✅ 启用 IP 白名单限制
- ❌ 不要启用 "交易" 或 "提现" 权限

#### FRED API（美联储经济数据）

1. 访问 [FRED](https://fred.stlouisfed.org/)
2. 注册账户
3. 前往 [My Account](https://fredaccount.stlouisfed.org/apikeys) 生成 API Key
4. 配置：

```env
FRED_API_KEY=your-fred-api-key
```

#### Glassnode API

1. 访问 [Glassnode](https://glassnode.com/)
2. 注册并订阅（有免费套餐）
3. 进入 Settings → API
4. 配置：

```env
GLASSNODE_API_KEY=your-glassnode-api-key
```

---

## 🎨 前端配置

前端**不需要**单独的 `.env` 文件！

所有 Firebase 配置都从后端 API 动态获取（`/api/v1/auth/config`），这样更安全。

如果需要修改前端配置，请编辑：

```typescript
// AMfrontend/src/lib/firebase.ts
const response = await fetch('http://localhost:8000/api/v1/auth/config');
```

在生产环境中，将 URL 改为你的后端域名。

---

## 🔑 API 密钥获取

### 免费 API

以下服务提供免费套餐：

| 服务 | 免费额度 | 注册链接 |
|------|---------|---------|
| **Alternative.me** | 完全免费 | 无需注册 |
| **Binance Public API** | 有限制但充足 | [binance.com](https://www.binance.com/) |
| **FRED** | 完全免费 | [fred.stlouisfed.org](https://fred.stlouisfed.org/) |

### 付费 API

以下服务需要付费订阅：

| 服务 | 起步价格 | 推荐等级 |
|------|---------|---------|
| **OpenRouter** | Pay-as-you-go | ⭐⭐⭐⭐⭐ |
| **Tuzi** | 按量计费 | ⭐⭐⭐⭐ |
| **Glassnode** | $39/月 | ⭐⭐⭐ |

---

## 🔒 安全最佳实践

### ✅ 应该做的

1. **使用环境变量**
   - 所有敏感信息存储在 `.env` 文件中
   - 永远不要在代码中硬编码密钥

2. **保护 .env 文件**
   - `.env` 文件已被 `.gitignore` 排除
   - 定期检查没有意外提交敏感信息

3. **生产环境配置**
   - 修改默认的 `SECRET_KEY`
   - 使用强密码
   - 启用 HTTPS
   - 限制 CORS 域名

4. **API 权限最小化**
   - Binance API 只启用"读取"权限
   - 使用 IP 白名单
   - 定期轮换密钥

5. **备份配置**
   - 在安全的地方（如密码管理器）备份配置
   - 不要通过邮件或聊天发送密钥

### ❌ 不应该做的

1. ❌ 提交 `.env` 文件到 Git
2. ❌ 在代码中硬编码 API 密钥
3. ❌ 在日志中打印敏感信息
4. ❌ 在 Discord/Slack 等公开渠道分享密钥
5. ❌ 使用生产密钥进行测试

---

## 🔍 验证配置

启动项目后，检查配置是否正确：

```bash
# 1. 启动服务
./start.sh

# 2. 检查后端健康状态
curl http://localhost:8000/api/v1/health

# 3. 检查 Firebase 配置
curl http://localhost:8000/api/v1/auth/config

# 4. 查看日志
tail -f .pids/backend.log
```

---

## 🆘 常见问题

### Q: 为什么 .env 文件不存在？

A: `.env` 文件被 `.gitignore` 排除了。你需要手动复制 `.env.example`：
```bash
cp AMbackend/.env.example AMbackend/.env
```

### Q: Firebase 配置在哪里？

A: 访问 [Firebase Console](https://console.firebase.google.com/) → Project Settings → General

### Q: 我需要所有的 API 密钥吗？

A: 不需要。最低要求是：
- 数据库连接
- Firebase 配置
- 至少一个 LLM 服务（OpenRouter 或 Tuzi）

其他 API 可以在需要时配置。

### Q: 如何在生产环境部署？

A: 生产环境配置：
1. 修改 `SECRET_KEY` 为强密钥
2. 设置 `ENVIRONMENT=production`
3. 设置 `DEBUG=False`
4. 配置正确的 `CORS_ORIGINS`
5. 使用环境变量注入（而非 .env 文件）

---

## 📞 获取帮助

如果遇到配置问题：

1. 检查 [QUICKSTART.md](QUICKSTART.md) 快速启动指南
2. 查看 `.pids/backend.log` 后端日志
3. 确认所有必需的配置项都已填写
4. 验证 API 密钥是否有效

---

**最后更新**: 2025-11-07
