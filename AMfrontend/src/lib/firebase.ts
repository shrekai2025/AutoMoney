/**
 * Firebase配置和初始化
 */

import { initializeApp, FirebaseApp } from 'firebase/app';
import {
  getAuth,
  Auth,
  setPersistence,
  browserLocalPersistence,
  inMemoryPersistence
} from 'firebase/auth';

// Firebase配置（从后端API获取）
let firebaseApp: FirebaseApp | null = null;
let auth: Auth | null = null;
let initializationPromise: Promise<{ app: FirebaseApp; auth: Auth }> | null = null;

/**
 * 从后端获取Firebase配置并初始化
 */
export async function initializeFirebase(): Promise<{ app: FirebaseApp; auth: Auth }> {
  // 如果已经初始化，直接返回
  if (firebaseApp && auth) {
    return { app: firebaseApp, auth };
  }

  // 如果正在初始化，返回现有的Promise
  if (initializationPromise) {
    return initializationPromise;
  }

  // 创建初始化Promise
  initializationPromise = (async () => {
    try {
      // 从后端API获取Firebase配置
      const response = await fetch('http://localhost:8000/api/v1/auth/config');
      if (!response.ok) {
        throw new Error('Failed to fetch Firebase config');
      }

      const firebaseConfig = await response.json();

      // 初始化Firebase
      firebaseApp = initializeApp(firebaseConfig);
      auth = getAuth(firebaseApp);

      // 配置持久化策略：使用 localStorage 存储 Refresh Token (30天有效)
      // Access Token 会自动配置为最长有效时间（1小时），并在过期前自动刷新
      try {
        await setPersistence(auth, browserLocalPersistence);
        console.log('✅ Firebase persistence set to LOCAL (30 days)');
      } catch (persistenceError) {
        console.warn('⚠️  Failed to set persistence, falling back to memory:', persistenceError);
        // 如果设置失败，使用内存持久化
        await setPersistence(auth, inMemoryPersistence);
      }

      console.log('✅ Firebase initialized successfully');
      return { app: firebaseApp, auth };
    } catch (error) {
      console.error('❌ Error initializing Firebase:', error);
      initializationPromise = null; // 重置以允许重试
      throw error;
    }
  })();

  return initializationPromise;
}

/**
 * 获取Auth实例（确保已初始化）
 */
export async function getAuthInstance(): Promise<Auth> {
  if (!auth) {
    const { auth: authInstance } = await initializeFirebase();
    return authInstance;
  }
  return auth;
}
