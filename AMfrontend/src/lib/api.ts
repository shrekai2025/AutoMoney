/**
 * API调用工具函数
 */

import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { getAuth } from 'firebase/auth';
import { initializeFirebase } from './firebase';

const API_BASE_URL = 'http://localhost:8000';

// Firebase 初始化状态
let firebaseInitialized = false;
let firebaseInitPromise: Promise<void> | null = null;

/**
 * 确保 Firebase 已初始化
 */
async function ensureFirebaseInitialized(): Promise<void> {
  if (firebaseInitialized) {
    return;
  }

  if (firebaseInitPromise) {
    return firebaseInitPromise;
  }

  firebaseInitPromise = (async () => {
    try {
      await initializeFirebase();
      firebaseInitialized = true;
      console.log('✅ Firebase ready for API requests');
    } catch (error) {
      console.error('❌ Firebase initialization failed:', error);
      firebaseInitPromise = null; // 允许重试
      throw error;
    }
  })();

  return firebaseInitPromise;
}

// 创建axios实例
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30秒超时
});

// 请求拦截器：确保Firebase初始化并自动添加Token
apiClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    try {
      // 等待 Firebase 初始化完成
      await ensureFirebaseInitialized();

      const auth = getAuth();
      const user = auth.currentUser;

      if (user) {
        try {
          // 获取 Firebase ID Token（Access Token）
          // forceRefresh=false: 使用缓存的 token（最长1小时有效）
          // Firebase SDK 会在 token 过期前5分钟自动刷新
          const token = await user.getIdToken(false);
          config.headers.Authorization = `Bearer ${token}`;
          console.log('🔑 Request with auth token');
        } catch (tokenError) {
          console.error('❌ Error getting Firebase token:', tokenError);
          // Token 获取失败，继续请求（可能是公开端点）
        }
      } else {
        console.log('👤 Request without auth (no user)');
      }

      return config;
    } catch (initError) {
      console.error('❌ Firebase initialization error in request interceptor:', initError);
      // Firebase 初始化失败，但仍尝试发送请求（可能是公开端点）
      return config;
    }
  },
  (error) => {
    console.error('❌ Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器：处理401错误（token过期或无效）
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // 如果是401错误且未重试过
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        console.log('🔄 Received 401, attempting token refresh...');

        // 确保 Firebase 已初始化
        await ensureFirebaseInitialized();

        const auth = getAuth();
        const user = auth.currentUser;

        if (user) {
          try {
            // 强制刷新 token
            const newToken = await user.getIdToken(true); // force refresh
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            console.log('✅ Token refreshed, retrying request');
            return apiClient(originalRequest);
          } catch (refreshError) {
            console.error('❌ Failed to refresh token:', refreshError);
            // Token 刷新失败，可能是 Refresh Token 也过期了
            // 清除本地状态并重定向到登录页
            console.log('🚪 Redirecting to login...');
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        } else {
          console.log('❌ No user found, redirecting to login...');
          window.location.href = '/login';
          return Promise.reject(new Error('User not authenticated'));
        }
      } catch (error) {
        console.error('❌ Error in 401 handler:', error);
        return Promise.reject(error);
      }
    }

    // 其他错误直接返回
    return Promise.reject(error);
  }
);

/**
 * 获取当前用户信息
 */
export async function getCurrentUser() {
  try {
    const response = await apiClient.get('/api/v1/auth/me');
    return response.data;
  } catch (error) {
    console.error('Error fetching current user:', error);
    throw error;
  }
}

/**
 * 登出
 */
export async function logout() {
  try {
    await apiClient.post('/api/v1/auth/logout');
  } catch (error) {
    console.error('Error logging out:', error);
    // 即使后端登出失败，也继续本地登出
  }
}

export default apiClient;
