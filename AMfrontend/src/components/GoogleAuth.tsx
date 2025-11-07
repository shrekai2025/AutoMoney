import { useState, useEffect } from "react";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { LogIn, LogOut, Copy, Check, User } from "lucide-react";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "./ui/popover";
import { toast } from "sonner";
import { getAuth, signInWithPopup, GoogleAuthProvider, signOut, User as FirebaseUser } from "firebase/auth";
import { useAuth } from "../contexts/AuthContext";

export function GoogleAuth() {
  const [user, setUser] = useState<FirebaseUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSigningIn, setIsSigningIn] = useState(false);
  const [copied, setCopied] = useState(false);
  const { refreshUser } = useAuth();

  // Listen for Firebase auth state changes (Firebase already initialized by AuthContext)
  useEffect(() => {
    const setupAuthListener = async () => {
      try {
        // Firebase is already initialized by AuthContext, just get the instance
        const auth = getAuth();

        // Listen for auth state changes
        const unsubscribe = auth.onAuthStateChanged((firebaseUser) => {
          setUser(firebaseUser);
          setIsLoading(false);
        });

        return () => {
          unsubscribe();
        };
      } catch (error) {
        console.error("[GoogleAuth] Error setting up auth listener:", error);
        setIsLoading(false);
      }
    };

    setupAuthListener();
  }, []);

  const signInWithGoogle = async () => {
    setIsSigningIn(true);
    try {
      const auth = getAuth();
      const provider = new GoogleAuthProvider();

      // Add prompt to force account selection
      provider.setCustomParameters({
        prompt: 'select_account'
      });

      const result = await signInWithPopup(auth, provider);
      const user = result.user;

      toast.success("Sign In Successful", {
        description: `Welcome, ${user.displayName || user.email}!`,
      });

      // Refresh AuthContext to load user data from backend
      await refreshUser();
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
      } else {
        toast.error("Sign In Failed", {
          description: error.message || "Failed to sign in with Google.",
        });
      }
    } finally {
      setIsSigningIn(false);
    }
  };

  const handleSignOut = async () => {
    try {
      const auth = getAuth();
      await signOut(auth);

      // Refresh AuthContext to clear user data
      await refreshUser();

      toast.success("Signed Out", {
        description: "You have been signed out successfully.",
      });
    } catch (error) {
      console.error("Error signing out:", error);
      toast.error("Sign Out Failed", {
        description: "Failed to sign out.",
      });
    }
  };

  const copyEmail = () => {
    if (user?.email) {
      navigator.clipboard.writeText(user.email);
      setCopied(true);
      toast.success("Email Copied");
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const getDisplayName = () => {
    if (user?.displayName) {
      return user.displayName;
    }
    if (user?.email) {
      return user.email.split('@')[0];
    }
    return 'User';
  };

  // Loading state
  if (isLoading) {
    return (
      <Button
        disabled
        className="h-7 px-3 text-xs bg-gradient-to-r from-blue-600 to-purple-600 text-white border-0"
      >
        <User className="w-3.5 h-3.5 mr-1.5" />
        Loading...
      </Button>
    );
  }

  // Not signed in
  if (!user) {
    return (
      <Button
        onClick={signInWithGoogle}
        disabled={isSigningIn}
        className="h-7 px-3 text-xs bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white border-0 shadow-lg shadow-blue-500/30"
      >
        <LogIn className="w-3.5 h-3.5 mr-1.5" />
        {isSigningIn ? "Signing In..." : "Sign In with Google"}
      </Button>
    );
  }

  // Signed in - show user info in popover
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          className="h-7 px-2 text-xs bg-slate-800/50 border-slate-700 text-white hover:bg-slate-700 hover:border-slate-600"
        >
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
            {user.photoURL ? (
              <img
                src={user.photoURL}
                alt="Profile"
                className="w-4 h-4 rounded-full"
              />
            ) : (
              <User className="w-3.5 h-3.5" />
            )}
            <span className="hidden sm:inline font-medium max-w-[100px] truncate">
              {getDisplayName()}
            </span>
          </div>
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-64 bg-slate-900 border-slate-700" align="end">
        <div className="space-y-3">
          {/* Header */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-white">Signed In</span>
            <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/50 text-xs px-2 py-0">
              Active
            </Badge>
          </div>

          {/* User Profile */}
          <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/50">
            <div className="flex items-center gap-3 mb-3">
              {user.photoURL ? (
                <img
                  src={user.photoURL}
                  alt="Profile"
                  className="w-12 h-12 rounded-full border-2 border-slate-700"
                />
              ) : (
                <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center">
                  <User className="w-6 h-6 text-white" />
                </div>
              )}
              <div className="flex-1 min-w-0">
                <div className="text-sm text-white font-medium truncate">
                  {user.displayName || 'User'}
                </div>
                <div className="text-xs text-slate-400 truncate">
                  {user.email}
                </div>
              </div>
            </div>
          </div>

          {/* Email */}
          {user.email && (
            <div className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/50">
              <div className="text-xs text-slate-400 mb-2">Email</div>
              <div className="flex items-center gap-2">
                <code className="text-xs text-slate-300 flex-1 truncate">
                  {user.email}
                </code>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="space-y-2">
            {user.email && (
              <Button
                onClick={copyEmail}
                variant="outline"
                className="w-full h-8 text-xs bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700 hover:text-white"
              >
                {copied ? (
                  <>
                    <Check className="w-3 h-3 mr-1.5" />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy className="w-3 h-3 mr-1.5" />
                    Copy Email
                  </>
                )}
              </Button>
            )}
            <Button
              onClick={handleSignOut}
              variant="outline"
              className="w-full h-8 text-xs bg-red-900/20 border-red-500/50 text-red-400 hover:bg-red-900/30 hover:text-red-300"
            >
              <LogOut className="w-3 h-3 mr-1.5" />
              Sign Out
            </Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}
