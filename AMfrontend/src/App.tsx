import { BrowserRouter, Routes, Route, Link, useNavigate, useParams, useLocation } from "react-router-dom";
import { Dashboard } from "./components/Dashboard";
import { StrategyMarketplace } from "./components/StrategyMarketplace";
import { StrategyDetails } from "./components/StrategyDetails";
import { Exploration } from "./components/Exploration";
import ResearchChat from "./components/ResearchChat";
import { AdminPanel } from "./components/AdminPanel";
import { GoogleAuth } from "./components/GoogleAuth";
import { Button } from "./components/ui/button";
import { LayoutDashboard, TrendingUp, Sparkles, Activity, MessageSquare, Shield } from "lucide-react";
import { Toaster } from "./components/ui/sonner";
import { AuthProvider, useAuth } from "./contexts/AuthContext";

// Wrapper component for StrategyMarketplace to handle navigation
function StrategyMarketplaceWrapper() {
  const navigate = useNavigate();

  const handleSelectStrategy = (strategyId: string) => {
    navigate(`/strategy/${strategyId}`);
  };

  return <StrategyMarketplace onSelectStrategy={handleSelectStrategy} />;
}

// Wrapper component for StrategyDetails to handle navigation
function StrategyDetailsWrapper() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();

  const handleBack = () => {
    navigate("/marketplace");
  };

  if (!id) {
    navigate("/marketplace");
    return null;
  }

  return <StrategyDetails strategyId={id} onBack={handleBack} />;
}

// Navigation component - now uses AuthContext
function Navigation() {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  return (
    <nav className="sticky top-0 z-50 backdrop-blur-xl bg-slate-900/80 border-b border-slate-800/50">
      <div className="max-w-7xl mx-auto px-3 sm:px-4 lg:px-6">
        <div className="flex items-center justify-between h-12">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center shadow-lg shadow-blue-500/50">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              <span className="text-white text-sm">CryptoAI</span>
            </div>

            <div className="hidden md:flex gap-1">
              <NavButton to="/exploration" icon={Activity}>Mind Hub</NavButton>
              <NavButton to="/research" icon={MessageSquare}>Research</NavButton>
              <NavButton to="/marketplace" icon={TrendingUp}>Strategy</NavButton>
              <NavButton to="/dashboard" icon={LayoutDashboard}>Portfolio</NavButton>
              {isAdmin && <NavButton to="/admin" icon={Shield} color="purple">Admin</NavButton>}
            </div>
          </div>

          <GoogleAuth />
        </div>
      </div>
    </nav>
  );
}

// Navigation button component
function NavButton({ to, icon: Icon, children, color = "blue" }: {
  to: string;
  icon: any;
  children: React.ReactNode;
  color?: "blue" | "emerald" | "purple";
}) {
  const location = useLocation();
  const isActive = location.pathname === to || (to === "/exploration" && location.pathname === "/");

  const colorClasses = {
    blue: "bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-lg shadow-blue-500/50",
    emerald: "bg-gradient-to-r from-emerald-600 to-teal-500 text-white shadow-lg shadow-emerald-500/50",
    purple: "bg-gradient-to-r from-purple-600 to-purple-500 text-white shadow-lg shadow-purple-500/50",
  };

  return (
    <Link to={to} className="no-underline">
      <Button
        variant="ghost"
        className={`gap-1.5 h-7 px-3 text-xs transition-all ${
          isActive
            ? `${colorClasses[color]} hover:opacity-90`
            : "text-slate-300 hover:text-white hover:bg-slate-800"
        }`}
        size="sm"
      >
        <Icon className="w-3.5 h-3.5" />
        {children}
      </Button>
    </Link>
  );
}

// Mobile Navigation component
function MobileNav() {
  const location = useLocation();

  const navItems = [
    { to: "/exploration", icon: Activity, label: "Mind Hub", gradient: "from-purple-600 to-pink-500" },
    { to: "/marketplace", icon: TrendingUp, label: "Strategy", gradient: "from-blue-600 to-blue-500" },
    { to: "/dashboard", icon: LayoutDashboard, label: "Portfolio", gradient: "from-blue-600 to-blue-500" },
  ];

  return (
    <div className="md:hidden fixed bottom-0 left-0 right-0 backdrop-blur-xl bg-slate-900/80 border-t border-slate-800/50 px-3 py-2">
      <div className="flex gap-2">
        {navItems.map(({ to, icon: Icon, label, gradient }) => {
          const isActive = location.pathname === to || (to === "/exploration" && location.pathname === "/");

          return (
            <Link key={to} to={to} className="flex-1 no-underline">
              <Button
                variant={isActive ? "default" : "outline"}
                className={`w-full gap-1.5 h-9 text-xs ${
                  isActive
                    ? `bg-gradient-to-r ${gradient} text-white border-0`
                    : "border-slate-700 text-slate-200 hover:text-white hover:bg-slate-800"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {label}
              </Button>
            </Link>
          );
        })}
      </div>
    </div>
  );
}

// Main app content component
function AppContent() {
  const { isLoading } = useAuth();

  // Global loading screen - wait for auth to complete
  if (isLoading) {
    return (
      <div className="dark min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center">
        {/* Animated background elements */}
        <div className="fixed inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-0 -left-4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 right-0 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl"></div>
          <div className="absolute top-1/2 left-1/2 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl"></div>
        </div>

        {/* Loading spinner */}
        <div className="relative text-center">
          <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center shadow-lg shadow-blue-500/50 mx-auto mb-4 animate-pulse">
            <Sparkles className="w-8 h-8 text-white" />
          </div>
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-t-2 border-purple-500 mx-auto mb-4"></div>
          <p className="text-white text-lg font-medium">Initializing CryptoAI...</p>
          <p className="text-slate-400 text-sm mt-2">Authenticating and loading your environment</p>
        </div>
      </div>
    );
  }

  return (
    <div className="dark min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Animated background elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 -left-4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl"></div>
        <div className="absolute top-1/2 left-1/2 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl"></div>
      </div>

      {/* Top Navigation */}
      <Navigation />

      {/* Main Content */}
      <main className="relative max-w-7xl mx-auto px-3 sm:px-4 lg:px-6 py-4">
        <Routes>
          <Route path="/" element={<Exploration />} />
          <Route path="/exploration" element={<Exploration />} />
          <Route path="/research" element={<ResearchChat />} />
          <Route path="/marketplace" element={<StrategyMarketplaceWrapper />} />
          <Route path="/strategy/:id" element={<StrategyDetailsWrapper />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/admin" element={<AdminPanel />} />
        </Routes>
      </main>

      {/* Mobile Bottom Navigation */}
      <MobileNav />

      {/* Toast Notifications */}
      <Toaster position="top-right" />
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </AuthProvider>
  );
}
