import { useState } from "react";
import { Dashboard } from "./components/Dashboard";
import { StrategyMarketplace } from "./components/StrategyMarketplace";
import { StrategyDetails } from "./components/StrategyDetails";
import { Exploration } from "./components/Exploration";
import { Research } from "./components/Research";
import { WalletConnect } from "./components/WalletConnect";
import { Button } from "./components/ui/button";
import { LayoutDashboard, TrendingUp, Sparkles, Activity, Brain } from "lucide-react";
import { Toaster } from "./components/ui/sonner";

type View = "dashboard" | "exploration" | "marketplace" | "strategy-details" | "research";

export default function App() {
  const [currentView, setCurrentView] = useState<View>("exploration");
  const [selectedStrategyId, setSelectedStrategyId] = useState<number | null>(null);

  const handleSelectStrategy = (strategyId: number) => {
    setSelectedStrategyId(strategyId);
    setCurrentView("strategy-details");
  };

  const handleBackToMarketplace = () => {
    setCurrentView("marketplace");
    setSelectedStrategyId(null);
  };

  return (
    <div className="dark min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      {/* Animated background elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 -left-4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl"></div>
        <div className="absolute top-1/2 left-1/2 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl"></div>
      </div>

      {/* Top Navigation */}
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
                <Button
                  variant={currentView === "exploration" ? "default" : "ghost"}
                  onClick={() => setCurrentView("exploration")}
                  className={`gap-1.5 h-7 px-3 text-xs ${
                    currentView === "exploration"
                      ? "bg-gradient-to-r from-purple-600 to-pink-500 text-white shadow-lg shadow-purple-500/50"
                      : "text-slate-300 hover:text-white hover:bg-slate-800"
                  }`}
                  size="sm"
                >
                  <Activity className="w-3.5 h-3.5" />
                  Mind Hub
                </Button>
                <Button
                  variant={
                    currentView === "marketplace" || currentView === "strategy-details"
                      ? "default"
                      : "ghost"
                  }
                  onClick={() => setCurrentView("marketplace")}
                  className={`gap-1.5 h-7 px-3 text-xs ${
                    currentView === "marketplace" || currentView === "strategy-details"
                      ? "bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-lg shadow-blue-500/50"
                      : "text-slate-300 hover:text-white hover:bg-slate-800"
                  }`}
                  size="sm"
                >
                  <TrendingUp className="w-3.5 h-3.5" />
                  Strategy
                </Button>
                <Button
                  variant={currentView === "research" ? "default" : "ghost"}
                  onClick={() => setCurrentView("research")}
                  className={`gap-1.5 h-7 px-3 text-xs ${
                    currentView === "research"
                      ? "bg-gradient-to-r from-cyan-600 to-cyan-500 text-white shadow-lg shadow-cyan-500/50"
                      : "text-slate-300 hover:text-white hover:bg-slate-800"
                  }`}
                  size="sm"
                >
                  <Brain className="w-3.5 h-3.5" />
                  Research
                </Button>
                <Button
                  variant={currentView === "dashboard" ? "default" : "ghost"}
                  onClick={() => setCurrentView("dashboard")}
                  className={`gap-1.5 h-7 px-3 text-xs ${
                    currentView === "dashboard"
                      ? "bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-lg shadow-blue-500/50"
                      : "text-slate-300 hover:text-white hover:bg-slate-800"
                  }`}
                  size="sm"
                >
                  <LayoutDashboard className="w-3.5 h-3.5" />
                  Portfolio
                </Button>
              </div>
            </div>

            <WalletConnect />
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="relative max-w-7xl mx-auto px-3 sm:px-4 lg:px-6 py-4">
        {currentView === "dashboard" && <Dashboard />}
        {currentView === "exploration" && <Exploration />}
        {currentView === "marketplace" && (
          <StrategyMarketplace onSelectStrategy={handleSelectStrategy} />
        )}
        {currentView === "strategy-details" && selectedStrategyId && (
          <StrategyDetails
            strategyId={selectedStrategyId}
            onBack={handleBackToMarketplace}
          />
        )}
        {currentView === "research" && <Research />}
      </main>

      {/* Mobile Bottom Navigation */}
      <div className="md:hidden fixed bottom-0 left-0 right-0 backdrop-blur-xl bg-slate-900/80 border-t border-slate-800/50 px-3 py-2">
        <div className="flex gap-2">
          <Button
            variant={currentView === "exploration" ? "default" : "outline"}
            onClick={() => setCurrentView("exploration")}
            className={`flex-1 gap-1.5 h-9 text-xs ${
              currentView === "exploration"
                ? "bg-gradient-to-r from-purple-600 to-pink-500 text-white border-0"
                : "border-slate-700 text-slate-200 hover:text-white hover:bg-slate-800"
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Mind Hub</span>
          </Button>
          <Button
            variant={
              currentView === "marketplace" || currentView === "strategy-details"
                ? "default"
                : "outline"
            }
            onClick={() => setCurrentView("marketplace")}
            className={`flex-1 gap-1.5 h-9 text-xs ${
              currentView === "marketplace" || currentView === "strategy-details"
                ? "bg-gradient-to-r from-blue-600 to-blue-500 text-white border-0"
                : "border-slate-700 text-slate-200 hover:text-white hover:bg-slate-800"
            }`}
          >
            <TrendingUp className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Strategy</span>
          </Button>
          <Button
            variant={currentView === "research" ? "default" : "outline"}
            onClick={() => setCurrentView("research")}
            className={`flex-1 gap-1.5 h-9 text-xs ${
              currentView === "research"
                ? "bg-gradient-to-r from-cyan-600 to-cyan-500 text-white border-0"
                : "border-slate-700 text-slate-200 hover:text-white hover:bg-slate-800"
            }`}
          >
            <Brain className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Research</span>
          </Button>
          <Button
            variant={currentView === "dashboard" ? "default" : "outline"}
            onClick={() => setCurrentView("dashboard")}
            className={`flex-1 gap-1.5 h-9 text-xs ${
              currentView === "dashboard"
                ? "bg-gradient-to-r from-blue-600 to-blue-500 text-white border-0"
                : "border-slate-700 text-slate-200 hover:text-white hover:bg-slate-800"
            }`}
          >
            <LayoutDashboard className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Portfolio</span>
          </Button>
        </div>
      </div>

      {/* Toast Notifications */}
      <Toaster position="top-right" />
    </div>
  );
}
