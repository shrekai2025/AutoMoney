import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "./ui/button";
import { Sparkles, TrendingUp, Shield, Zap, ChevronRight, AlertCircle } from "lucide-react";
import { getAuth, signInWithPopup, GoogleAuthProvider } from "firebase/auth";
import { toast } from "sonner";
import { useAuth } from "../contexts/AuthContext";

export function Login() {
  const navigate = useNavigate();
  const { user, isLoading, refreshUser } = useAuth();
  const [isSigningIn, setIsSigningIn] = useState(false);

  // Redirect to home if already authenticated
  useEffect(() => {
    if (user && !isLoading) {
      navigate("/");
    }
  }, [user, isLoading, navigate]);

  const handleGoogleSignIn = async () => {
    setIsSigningIn(true);
    try {
      const auth = getAuth();
      const provider = new GoogleAuthProvider();

      // Force account selection
      provider.setCustomParameters({
        prompt: 'select_account'
      });

      const result = await signInWithPopup(auth, provider);
      const firebaseUser = result.user;

      // Refresh user data
      await refreshUser();

      toast.success("Welcome to CryptoAI!", {
        description: `Signed in as ${firebaseUser.displayName || firebaseUser.email}`,
      });

      // Navigate to home
      navigate("/");
    } catch (error: any) {
      console.error("Error signing in with Google:", error);

      if (error.code === 'auth/popup-closed-by-user') {
        toast.error("Sign In Cancelled", {
          description: "You closed the sign-in popup.",
        });
      } else if (error.code === 'auth/popup-blocked') {
        toast.error("Popup Blocked", {
          description: "Please allow popups for this site.",
        });
      } else if (error.code === 'auth/internal-error') {
        toast.error("Configuration Error", {
          description: "Firebase configuration issue. Please contact support.",
        });
      } else if (error.code === 'auth/network-request-failed') {
        toast.error("Network Error", {
          description: "Please check your internet connection.",
        });
      } else {
        toast.error("Sign In Failed", {
          description: error.message || "Failed to sign in with Google.",
        });
      }
    } finally {
      setIsSigningIn(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center shadow-lg shadow-blue-500/50 mx-auto mb-4 animate-pulse">
            <Sparkles className="w-8 h-8 text-white" />
          </div>
          <p className="text-white text-lg font-medium">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center relative overflow-hidden">
      {/* Animated background elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 -left-4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }}></div>
        <div className="absolute top-1/2 left-1/2 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '2s' }}></div>
      </div>

      {/* Login Card */}
      <div className="relative z-10 w-full max-w-md mx-4">
        <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-800/50 rounded-2xl shadow-2xl p-8 sm:p-10">
          {/* Logo and Title */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl shadow-lg shadow-blue-500/50 mb-6">
              <Sparkles className="w-10 h-10 text-white" />
            </div>
            <h1 className="text-3xl sm:text-4xl font-bold text-white mb-3 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              Welcome to CryptoAI
            </h1>
            <p className="text-slate-400 text-sm sm:text-base">
              AI-Powered Cryptocurrency Trading Platform
            </p>
          </div>

          {/* Features */}
          <div className="space-y-3 mb-8">
            <div className="flex items-center gap-3 text-slate-300 text-sm">
              <div className="w-8 h-8 bg-blue-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                <TrendingUp className="w-4 h-4 text-blue-400" />
              </div>
              <span>Advanced AI Trading Strategies</span>
            </div>
            <div className="flex items-center gap-3 text-slate-300 text-sm">
              <div className="w-8 h-8 bg-purple-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                <Zap className="w-4 h-4 text-purple-400" />
              </div>
              <span>Real-time Market Analysis</span>
            </div>
            <div className="flex items-center gap-3 text-slate-300 text-sm">
              <div className="w-8 h-8 bg-emerald-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
                <Shield className="w-4 h-4 text-emerald-400" />
              </div>
              <span>Secure & Reliable Trading</span>
            </div>
          </div>

          {/* Google Sign In Button */}
          <Button
            onClick={handleGoogleSignIn}
            disabled={isSigningIn}
            className="w-full h-12 text-base font-medium bg-white hover:bg-gray-50 text-gray-900 border-0 shadow-lg hover:shadow-xl transition-all duration-200 group disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSigningIn ? (
              <>
                <div className="w-5 h-5 mr-3 border-2 border-gray-300 border-t-blue-600 rounded-full animate-spin"></div>
                Signing in...
              </>
            ) : (
              <>
                <svg className="w-5 h-5 mr-3" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                  <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                  <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                  <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                </svg>
                Sign in with Google
                <ChevronRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
              </>
            )}
          </Button>

          {/* Divider */}
          <div className="relative my-8">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-800"></div>
            </div>
            <div className="relative flex justify-center text-xs">
              <span className="px-4 bg-slate-900/50 text-slate-500">
                Secure authentication powered by Google
              </span>
            </div>
          </div>

          {/* Footer */}
          <div className="text-center text-xs text-slate-500">
            By signing in, you agree to our{" "}
            <a href="#" className="text-blue-400 hover:text-blue-300 transition-colors">
              Terms of Service
            </a>{" "}
            and{" "}
            <a href="#" className="text-blue-400 hover:text-blue-300 transition-colors">
              Privacy Policy
            </a>
          </div>
        </div>

        {/* Bottom gradient glow */}
        <div className="absolute -bottom-8 left-1/2 -translate-x-1/2 w-3/4 h-24 bg-gradient-to-t from-blue-500/20 to-transparent blur-3xl rounded-full"></div>
      </div>
    </div>
  );
}
