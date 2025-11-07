/**
 * Authentication Context
 * 管理全局用户认证状态，确保所有组件在用户加载完成后再渲染
 */

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { initializeFirebase } from '../lib/firebase';
import { getCurrentUser } from '../lib/api';

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

  const loadUser = async (showLoading = true) => {
    try {
      if (showLoading) {
        setIsLoading(true);
      }
      setError(null);

      // Step 1: Initialize Firebase first (critical!)
      await initializeFirebase();

      // Step 2: Wait a bit to ensure Firebase auth state is fully settled
      await new Promise(resolve => setTimeout(resolve, 500));

      // Step 3: Check if user is logged in with Firebase
      const { getAuth } = await import('firebase/auth');
      const auth = getAuth();
      const firebaseUser = auth.currentUser;

      if (!firebaseUser) {
        setUser(null);
        if (showLoading) {
          setIsLoading(false);
        }
        return;
      }

      // Step 4: Try to get current user from backend (only if Firebase user exists)
      try {
        const userData = await getCurrentUser();
        setUser(userData);
      } catch (userError: any) {
        console.error('[AuthContext] Error fetching user from backend:', userError);
        setUser(null);
      }
    } catch (err: any) {
      const errorMessage = err.message || 'Failed to initialize authentication';
      console.error('[AuthContext] Authentication initialization error:', err);
      setError(errorMessage);
      setUser(null);
    } finally {
      if (showLoading) {
        setIsLoading(false);
      }
    }
  };

  // Initial load
  useEffect(() => {
    loadUser(true);  // Show loading on initial load
  }, []);

  const refreshUser = async () => {
    await loadUser(false);  // Don't show loading spinner on refresh
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
