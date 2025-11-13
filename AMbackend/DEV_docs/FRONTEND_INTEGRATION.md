# 前端集成指南

## ✅ 后端服务状态

**后端已成功启动！**
- URL: http://localhost:8000
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health
- 状态: 运行中 ✓

---

## 步骤2: 前端登录集成

### 1. 获取Firebase配置

后端提供Firebase配置接口，前端可以直接调用：

```javascript
// 获取Firebase配置
const response = await fetch('http://localhost:8000/api/v1/auth/config');
const firebaseConfig = await response.json();

// firebaseConfig 结构:
{
  "apiKey": "AIzaSyA7liJBv1D6eED-kwNquX95JgQH1ZU8O5g",
  "authDomain": "lingocontext.firebaseapp.com",
  "projectId": "lingocontext",
  "storageBucket": "lingocontext.firebasestorage.app",
  "messagingSenderId": "411097463678",
  "appId": "1:411097463678:web:be5b33640f70a98312912f",
  "measurementId": "G-NL67MZQ00C"
}
```

### 2. 前端Firebase初始化

```javascript
// 安装依赖
// npm install firebase

import { initializeApp } from 'firebase/app';
import { getAuth, signInWithPopup, GoogleAuthProvider } from 'firebase/auth';

// 获取配置并初始化
const configResponse = await fetch('http://localhost:8000/api/v1/auth/config');
const firebaseConfig = await configResponse.json();

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();
```

### 3. 实现Google登录

```javascript
// Google登录函数
async function loginWithGoogle() {
  try {
    // 1. Firebase Google登录
    const result = await signInWithPopup(auth, provider);
    const user = result.user;

    // 2. 获取Firebase ID Token
    const idToken = await user.getIdToken();

    // 3. 调用后端验证并获取用户信息
    const response = await fetch('http://localhost:8000/api/v1/auth/me', {
      headers: {
        'Authorization': `Bearer ${idToken}`
      }
    });

    const userData = await response.json();
    console.log('登录成功:', userData);

    // 4. 保存token供后续API调用使用
    localStorage.setItem('firebaseToken', idToken);

    return userData;
  } catch (error) {
    console.error('登录失败:', error);
    throw error;
  }
}
```

### 4. API调用示例

登录后，所有API调用都需要带上Firebase Token：

```javascript
// 通用API调用函数
async function callAPI(endpoint, options = {}) {
  const token = localStorage.getItem('firebaseToken');

  const response = await fetch(`http://localhost:8000${endpoint}`, {
    ...options,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
      ...options.headers
    }
  });

  if (!response.ok) {
    throw new Error(`API call failed: ${response.statusText}`);
  }

  return response.json();
}

// 使用示例
const userInfo = await callAPI('/api/v1/auth/me');
console.log(userInfo);
```

### 5. 完整的React示例

```jsx
import { useState, useEffect } from 'react';
import { initializeApp } from 'firebase/app';
import { getAuth, signInWithPopup, GoogleAuthProvider } from 'firebase/auth';

function App() {
  const [user, setUser] = useState(null);
  const [auth, setAuth] = useState(null);

  // 初始化Firebase
  useEffect(() => {
    async function initFirebase() {
      const response = await fetch('http://localhost:8000/api/v1/auth/config');
      const firebaseConfig = await response.json();

      const app = initializeApp(firebaseConfig);
      const firebaseAuth = getAuth(app);
      setAuth(firebaseAuth);
    }

    initFirebase();
  }, []);

  // Google登录
  const handleGoogleLogin = async () => {
    if (!auth) return;

    try {
      const provider = new GoogleAuthProvider();
      const result = await signInWithPopup(auth, provider);
      const idToken = await result.user.getIdToken();

      // 验证token并获取用户信息
      const response = await fetch('http://localhost:8000/api/v1/auth/me', {
        headers: { 'Authorization': `Bearer ${idToken}` }
      });

      const userData = await response.json();
      setUser(userData);
      localStorage.setItem('firebaseToken', idToken);

      console.log('登录成功:', userData);
    } catch (error) {
      console.error('登录失败:', error);
    }
  };

  // 登出
  const handleLogout = async () => {
    await auth.signOut();
    localStorage.removeItem('firebaseToken');
    setUser(null);
  };

  return (
    <div>
      {!user ? (
        <button onClick={handleGoogleLogin}>
          使用Google登录
        </button>
      ) : (
        <div>
          <p>欢迎, {user.email}</p>
          <button onClick={handleLogout}>登出</button>
        </div>
      )}
    </div>
  );
}

export default App;
```

### 6. Token自动刷新

Firebase会自动刷新token，但建议实现token刷新逻辑：

```javascript
import { getAuth } from 'firebase/auth';

// 获取新token
async function refreshToken() {
  const auth = getAuth();
  const user = auth.currentUser;

  if (user) {
    const newToken = await user.getIdToken(true); // force refresh
    localStorage.setItem('firebaseToken', newToken);
    return newToken;
  }
  return null;
}

// API拦截器（自动重试）
async function callAPIWithRetry(endpoint, options = {}) {
  try {
    return await callAPI(endpoint, options);
  } catch (error) {
    if (error.message.includes('401')) {
      // Token过期，刷新后重试
      await refreshToken();
      return await callAPI(endpoint, options);
    }
    throw error;
  }
}
```

---

## 可用的API端点

### 认证相关

1. **获取Firebase配置**
   ```
   GET /api/v1/auth/config
   无需认证
   ```

2. **获取当前用户**
   ```
   GET /api/v1/auth/me
   需要: Authorization: Bearer <firebase-token>

   返回:
   {
     "id": 1,
     "email": "user@example.com",
     "display_name": "User Name",
     "firebase_uid": "...",
     "is_active": true,
     "created_at": "2024-01-01T00:00:00",
     "last_login": "2024-01-01T00:00:00"
   }
   ```

3. **登出**
   ```
   POST /api/v1/auth/logout
   需要: Authorization: Bearer <firebase-token>

   注意: 登出主要在客户端处理（清除token）
   ```

### 其他端点

其他API端点正在开发中，完成后会更新此文档。

---

## 前端CORS配置

后端已配置CORS允许以下源：
- http://localhost:3000 (React默认)
- http://localhost:3010 (Vite默认)

如果你的前端运行在其他端口，需要在 `.env` 中添加：

```env
CORS_ORIGINS=["http://localhost:3000", "http://localhost:3010", "http://localhost:YOUR_PORT"]
```

---

## 测试登录流程

### 使用curl测试（需要真实Firebase token）

```bash
# 1. 获取Firebase配置
curl http://localhost:8000/api/v1/auth/config

# 2. 前端登录后获取token，然后测试
curl -H "Authorization: Bearer YOUR_FIREBASE_TOKEN" \
     http://localhost:8000/api/v1/auth/me
```

### 使用Postman测试

1. 在前端完成Google登录
2. 从浏览器console复制Firebase token
3. 在Postman中设置Header: `Authorization: Bearer <token>`
4. 测试 `/api/v1/auth/me` 端点

---

## 常见问题

### Q: 401 Unauthorized错误
**A:** 检查：
1. Token是否正确传递
2. Token是否过期（调用 `user.getIdToken(true)` 强制刷新）
3. Firebase项目ID是否匹配

### Q: CORS错误
**A:** 确保：
1. 后端 `.env` 中 `CORS_ORIGINS` 包含你的前端地址
2. 前端使用正确的API地址 `http://localhost:8000`

### Q: Firebase初始化失败
**A:** 检查：
1. Firebase配置是否正确
2. 网络是否正常
3. Firebase项目是否启用了Authentication

---

## 下一步

登录成功后，可以开始开发其他功能：
- Agent分析API
- 市场数据查询
- 投资组合管理

这些API正在开发中，完成后会更新文档。

---

## 需要帮助？

如果遇到问题：
1. 查看后端日志
2. 查看浏览器console
3. 检查 http://localhost:8000/docs 中的API文档
