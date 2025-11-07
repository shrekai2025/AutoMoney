import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { ArrowUpRight, ArrowDownRight, TrendingUp, Plus, Minus, Shield, Zap } from "lucide-react";
import { LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { Checkbox } from "./ui/checkbox";
import { Badge } from "./ui/badge";

// Mock data
const portfolioHistory = [
  { date: "10-23", total: 95000, strategy1: 44000, strategy2: 28500, strategy3: 19500 },
  { date: "10-24", total: 98000, strategy1: 44800, strategy2: 28800, strategy3: 19900 },
  { date: "10-25", total: 96500, strategy1: 44200, strategy2: 28200, strategy3: 19600 },
  { date: "10-26", total: 101000, strategy1: 45500, strategy2: 29000, strategy3: 20500 },
  { date: "10-27", total: 103500, strategy1: 46200, strategy2: 29200, strategy3: 21100 },
  { date: "10-28", total: 102000, strategy1: 45800, strategy2: 28800, strategy3: 20900 },
  { date: "10-29", total: 106500, strategy1: 47200, strategy2: 29500, strategy3: 21800 },
  { date: "10-30", total: 108420, strategy1: 45000, strategy2: 28000, strategy3: 20420 },
];

const strategyAllocation = [
  { name: "HODL-Wave Squad", value: 45000, color: "#3B82F6" },
  { name: "ArbitrageX Squad", value: 28000, color: "#8B5CF6" },
  { name: "MomentumPro Squad", value: 20420, color: "#10B981" },
  { name: "Available", value: 15000, color: "#64748B" },
];

const myInvestments = [
  { 
    name: "HODL-Wave Squad", 
    subtitle: "Macro Swing Strategy",
    value: 45000, 
    todayPnl: 850, 
    todayPnlPercent: 1.93, 
    key: "strategy1",
    status: "accelerate",
    color: "blue"
  },
  { 
    name: "ArbitrageX Squad", 
    subtitle: "High-Frequency Trading",
    value: 28000, 
    todayPnl: -320, 
    todayPnlPercent: -1.13, 
    key: "strategy2",
    status: "defensive",
    color: "purple"
  },
  { 
    name: "MomentumPro Squad", 
    subtitle: "Trend Following",
    value: 20420, 
    todayPnl: 590, 
    todayPnlPercent: 2.97, 
    key: "strategy3",
    status: "hold",
    color: "emerald"
  },
];

export function Dashboard() {
  const totalValue = 108420;
  const totalPnl = 8420;
  const totalPnlPercent = 8.42;
  const availableBalance = 15000;

  const [showTotal, setShowTotal] = useState(true);
  const [showStrategy1, setShowStrategy1] = useState(true);
  const [showStrategy2, setShowStrategy2] = useState(true);
  const [showStrategy3, setShowStrategy3] = useState(true);

  const getStatusBadge = (status: string) => {
    switch(status) {
      case "accelerate":
        return <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/50 text-xs px-2 py-0">🔥 Accelerating</Badge>;
      case "defensive":
        return <Badge className="bg-red-500/20 text-red-400 border-red-500/50 text-xs px-2 py-0">🛡️ Defensive</Badge>;
      case "hold":
        return <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/50 text-xs px-2 py-0">⚖️ Holding</Badge>;
      default:
        return null;
    }
  };

  return (
    <div className="space-y-3">
      {/* Page Header */}
      <div className="flex items-center justify-between mb-2">
        <div>
          <h1 className="text-white mb-0.5 text-xl flex items-center gap-2">
            <Shield className="w-5 h-5 text-blue-400" />
            My Portfolio
          </h1>
          <p className="text-slate-400 text-xs">Your AI Squad Command Center</p>
        </div>
      </div>

      {/* Asset Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
        <Card className="bg-gradient-to-br from-slate-900 to-slate-800 border-slate-700/50 shadow-xl overflow-hidden relative group hover:scale-[1.02] transition-transform">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-transparent"></div>
          <div className="absolute top-0 right-0 w-20 h-20 bg-blue-500/20 rounded-full blur-2xl"></div>
          <CardHeader className="pb-1 pt-3 px-3 relative">
            <CardTitle className="text-slate-400 text-xs">Total Assets</CardTitle>
          </CardHeader>
          <CardContent className="relative px-3 pb-3">
            <div className="text-white text-xl mb-0.5">${totalValue.toLocaleString()}</div>
            <div className="flex items-center gap-1 text-emerald-400">
              <ArrowUpRight className="w-3 h-3" />
              <span className="text-xs">+{totalPnlPercent}% Today</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-slate-900 to-slate-800 border-slate-700/50 shadow-xl overflow-hidden relative group hover:scale-[1.02] transition-transform">
          <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/10 to-transparent"></div>
          <div className="absolute top-0 right-0 w-20 h-20 bg-emerald-500/20 rounded-full blur-2xl"></div>
          <CardHeader className="pb-1 pt-3 px-3 relative">
            <CardTitle className="text-slate-400 text-xs">Total P&L</CardTitle>
          </CardHeader>
          <CardContent className="relative px-3 pb-3">
            <div className="text-emerald-400 text-xl mb-0.5">${totalPnl.toLocaleString()}</div>
            <div className="flex items-center gap-1 text-emerald-400">
              <Zap className="w-3 h-3" />
              <span className="text-xs">+{totalPnlPercent}%</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-slate-900 to-slate-800 border-slate-700/50 shadow-xl overflow-hidden relative group hover:scale-[1.02] transition-transform">
          <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 to-transparent"></div>
          <div className="absolute top-0 right-0 w-20 h-20 bg-purple-500/20 rounded-full blur-2xl"></div>
          <CardHeader className="pb-1 pt-3 px-3 relative">
            <CardTitle className="text-slate-400 text-xs">Available Balance</CardTitle>
          </CardHeader>
          <CardContent className="relative px-3 pb-3">
            <div className="text-white text-xl mb-0.5">${availableBalance.toLocaleString()}</div>
            <div className="text-xs text-slate-500">Ready to Deploy</div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card className="bg-slate-900/50 border-slate-700/50 backdrop-blur-sm">
        <CardHeader className="pb-2 pt-3 px-3">
          <CardTitle className="text-white text-sm">Quick Actions</CardTitle>
        </CardHeader>
        <CardContent className="px-3 pb-3">
          <div className="flex gap-2 flex-wrap">
            <Button className="gap-2 bg-gradient-to-r from-purple-600 to-pink-500 hover:from-purple-700 hover:to-pink-600 border-0 shadow-lg shadow-purple-500/50 h-8 text-xs px-3">
              <TrendingUp className="w-3 h-3" />
              Recruit New Squad
            </Button>
            <Button variant="outline" className="gap-2 border-slate-600 text-slate-200 hover:bg-slate-700 hover:text-white hover:border-slate-500 h-8 text-xs px-3">
              <Plus className="w-3 h-3" />
              Deposit Funds
            </Button>
            <Button variant="outline" className="gap-2 border-slate-600 text-slate-200 hover:bg-slate-700 hover:text-white hover:border-slate-500 h-8 text-xs px-3">
              <Minus className="w-3 h-3" />
              Withdraw
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* My Squad Deployments */}
      <Card className="bg-slate-900/50 border-slate-700/50 backdrop-blur-sm">
        <CardHeader className="pb-2 pt-3 px-3">
          <CardTitle className="text-white text-sm">My Squad Deployments</CardTitle>
        </CardHeader>
        <CardContent className="px-3 pb-3">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
            {/* Pie Chart */}
            <div className="flex items-center justify-center bg-slate-800/30 rounded-lg p-2">
              <ResponsiveContainer width="100%" height={240}>
                <PieChart>
                  <Pie
                    data={strategyAllocation}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    {strategyAllocation.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value: number) => `$${value.toLocaleString()}`}
                    contentStyle={{ 
                      backgroundColor: "#1e293b", 
                      border: "1px solid #334155", 
                      borderRadius: "6px",
                      color: "#fff",
                      fontSize: "12px"
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Squad List */}
            <div className="space-y-1.5">
              {myInvestments.map((investment, index) => (
                <div key={index} className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-2.5 hover:bg-slate-800/70 transition-all hover:scale-[1.01] relative overflow-hidden group">
                  <div className={`absolute inset-0 bg-gradient-to-r from-${investment.color}-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity`}></div>
                  <div className="flex justify-between items-start mb-1 relative">
                    <div className="flex-1">
                      <div className="text-white text-xs mb-0.5 flex items-center gap-2">
                        {investment.name}
                        {getStatusBadge(investment.status)}
                      </div>
                      <div className="text-xs text-slate-500">{investment.subtitle}</div>
                      <div className="text-xs text-slate-400 mt-0.5">${investment.value.toLocaleString()}</div>
                    </div>
                    <div
                      className={`flex items-center gap-0.5 ${
                        investment.todayPnl >= 0 ? "text-emerald-400" : "text-red-400"
                      }`}
                    >
                      {investment.todayPnl >= 0 ? (
                        <ArrowUpRight className="w-3 h-3" />
                      ) : (
                        <ArrowDownRight className="w-3 h-3" />
                      )}
                      <span className="text-xs">
                        {investment.todayPnl >= 0 ? "+" : ""}
                        {investment.todayPnlPercent}%
                      </span>
                    </div>
                  </div>
                  <div className="text-xs text-slate-500 relative">
                    Today: {investment.todayPnl >= 0 ? "+" : ""}${Math.abs(investment.todayPnl).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Base Performance Chart */}
      <Card className="bg-slate-900/50 border-slate-700/50 backdrop-blur-sm">
        <CardHeader className="pb-2 pt-3 px-3">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <CardTitle className="text-white text-sm">Base Performance Monitor</CardTitle>
            <div className="flex gap-2 flex-wrap">
              <Button variant="outline" size="sm" className="h-6 text-xs px-2 border-slate-600 text-slate-200 hover:bg-slate-700 hover:text-white">7D</Button>
              <Button size="sm" className="h-6 text-xs px-2 bg-blue-600 hover:bg-blue-700 text-white">30D</Button>
              <Button variant="outline" size="sm" className="h-6 text-xs px-2 border-slate-600 text-slate-200 hover:bg-slate-700 hover:text-white">90D</Button>
              <Button variant="outline" size="sm" className="h-6 text-xs px-2 border-slate-600 text-slate-200 hover:bg-slate-700 hover:text-white">All</Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="px-3 pb-3">
          <div className="mb-2 flex flex-wrap gap-3 text-xs">
            <label className="flex items-center gap-1.5 cursor-pointer">
              <Checkbox checked={showTotal} onCheckedChange={setShowTotal} className="h-3 w-3" />
              <span className="text-slate-300">Total Base</span>
            </label>
            <label className="flex items-center gap-1.5 cursor-pointer">
              <Checkbox checked={showStrategy1} onCheckedChange={setShowStrategy1} className="h-3 w-3" />
              <span className="text-slate-300">HODL-Wave</span>
            </label>
            <label className="flex items-center gap-1.5 cursor-pointer">
              <Checkbox checked={showStrategy2} onCheckedChange={setShowStrategy2} className="h-3 w-3" />
              <span className="text-slate-300">ArbitrageX</span>
            </label>
            <label className="flex items-center gap-1.5 cursor-pointer">
              <Checkbox checked={showStrategy3} onCheckedChange={setShowStrategy3} className="h-3 w-3" />
              <span className="text-slate-300">MomentumPro</span>
            </label>
          </div>
          <div className="bg-slate-800/30 rounded-lg p-3">
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={portfolioHistory}>
                <defs>
                  <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="date" stroke="#64748b" style={{ fontSize: '11px' }} />
                <YAxis stroke="#64748b" style={{ fontSize: '11px' }} />
                <Tooltip
                  formatter={(value: number) => `$${value.toLocaleString()}`}
                  contentStyle={{ 
                    backgroundColor: "#1e293b", 
                    border: "1px solid #334155", 
                    borderRadius: "6px",
                    color: "#fff",
                    fontSize: "11px"
                  }}
                />
                <Legend wrapperStyle={{ fontSize: '11px' }} />
                {showTotal && (
                  <Line 
                    type="monotone" 
                    dataKey="total" 
                    stroke="#3B82F6" 
                    strokeWidth={3} 
                    dot={false}
                    name="Total Base"
                    fill="url(#colorTotal)"
                  />
                )}
                {showStrategy1 && (
                  <Line 
                    type="monotone" 
                    dataKey="strategy1" 
                    stroke="#10B981" 
                    strokeWidth={2} 
                    dot={false}
                    name="HODL-Wave"
                    strokeDasharray="3 3"
                  />
                )}
                {showStrategy2 && (
                  <Line 
                    type="monotone" 
                    dataKey="strategy2" 
                    stroke="#8B5CF6" 
                    strokeWidth={2} 
                    dot={false}
                    name="ArbitrageX"
                    strokeDasharray="3 3"
                  />
                )}
                {showStrategy3 && (
                  <Line 
                    type="monotone" 
                    dataKey="strategy3" 
                    stroke="#F59E0B" 
                    strokeWidth={2} 
                    dot={false}
                    name="MomentumPro"
                    strokeDasharray="3 3"
                  />
                )}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
