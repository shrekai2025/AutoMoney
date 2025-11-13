/**
 * Authentication Context
 * 管理全局用户认证状态，确保所有组件在用户加载完成后再渲染
 * 使用Firebase onAuthStateChanged监听器自动响应认证状态变化
 */

import { createContext, useContext, useState, useEffect, ReactNode, useRef } from 'react';
import { initializeFirebase } from '../lib/firebase';
import { getCurrentUser } from '../lib/api';
import { getAuth, User as FirebaseUser, onAuthStateChanged } from 'firebase/auth';

interface User {
  id: number;
  email: string;
  full_name?: string;
  avatar_url?: string;
  role: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const authListenerUnsubscribeRef = useRef<(() => void) | null>(null);
  const isInitializedRef = useRef(false);

  /**
   * 从后端加载用户数据
   */
  const loadUserFromBackend = async (firebaseUser: FirebaseUser | null) => {
    if (!firebaseUser) {
      setUser(null);
      setIsLoading(false);
      setError(null);
      return;
    }

    try {
      // 获取后端用户数据
      const userData = await getCurrentUser();
      setUser(userData);
      setError(null);
      console.log('[AuthContext] User loaded successfully:', userData.email);
    } catch (userError: any) {
      console.error('[AuthContext] Error fetching user from backend:', userError);
      
      // 如果是401错误，说明token无效或用户未在后端注册
      if (userError.response?.status === 401) {
        console.warn('[AuthContext] User not found in backend, clearing state');
        setUser(null);
        setError('User not registered in backend');
      } else {
        // 其他错误，保留Firebase用户但标记错误
        setError(userError.message || 'Failed to load user data');
      }
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * 初始化Firebase并设置认证状态监听器
   */
  useEffect(() => {
    let mounted = true;

    const initializeAuth = async () => {
      try {
        setIsLoading(true);
        setError(null);

        // Step 1: Initialize Firebase
        await initializeFirebase();

        // Step 2: Get auth instance
        const auth = getAuth();

        // Step 3: Set up Firebase auth state listener
        // 这个监听器会在认证状态变化时自动触发（登录、登出、token刷新等）
        const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
          if (!mounted) return;

          console.log('[AuthContext] Firebase auth state changed:', firebaseUser?.email || 'signed out');

          if (firebaseUser) {
            // 用户已登录，从后端加载用户数据
            await loadUserFromBackend(firebaseUser);
          } else {
            // 用户已登出
            setUser(null);
            setError(null);
            setIsLoading(false);
          }
        });

        authListenerUnsubscribeRef.current = unsubscribe;
        isInitializedRef.current = true;

        console.log('[AuthContext] Auth listener initialized');
      } catch (err: any) {
        if (!mounted) return;

        const errorMessage = err.message || 'Failed to initialize authentication';
        console.error('[AuthContext] Authentication initialization error:', err);
        setError(errorMessage);
        setUser(null);
        setIsLoading(false);
      }
    };

    initializeAuth();

    // Cleanup function
    return () => {
      mounted = false;
      if (authListenerUnsubscribeRef.current) {
        authListenerUnsubscribeRef.current();
        authListenerUnsubscribeRef.current = null;
      }
    };
  }, []);

  /**
   * 手动刷新用户数据（用于登录后立即更新）
   */
  const refreshUser = async () => {
    try {
      const auth = getAuth();
      const firebaseUser = auth.currentUser;

      if (firebaseUser) {
        // 如果Firebase用户存在，重新加载后端数据
        await loadUserFromBackend(firebaseUser);
      } else {
        // 如果没有Firebase用户，清除状态
        setUser(null);
        setIsLoading(false);
      }
    } catch (err: any) {
      console.error('[AuthContext] Error refreshing user:', err);
      setError(err.message || 'Failed to refresh user');
    }
  };

  const contextValue: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    error,
    refreshUser,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * Hook to access auth context
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

/**
 * Hook to require authentication
 * Returns loading/error states for components that need auth
 */
export function useRequireAuth() {
  const { user, isLoading, error } = useAuth();

  return {
    user,
    isLoading,
    error,
    isAuthenticated: !!user,
  };
}
