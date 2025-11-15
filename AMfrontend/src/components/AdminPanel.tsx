/**
 * Admin Panel - 管理员面板主组件
 *
 * 使用标签页整合所有管理功能：
 * - 策略管理
 * - Agent注册表
 * - Tool注册表
 * - API配置
 * - Agent监控
 */

import { Shield } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { AdminStrategies } from "./admin/AdminStrategies";
import { AdminStrategyTemplates } from "./admin/AdminStrategyTemplates";
import { AdminAgentRegistry } from "./admin/AdminAgentRegistry";
import { AdminToolRegistry } from "./admin/AdminToolRegistry";
import { AdminAPIConfig } from "./admin/AdminAPIConfig";
import { AgentMonitor } from "./AgentMonitor";

export function AdminPanel() {
  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <Shield className="w-8 h-8 text-purple-400" />
          <h1 className="text-3xl font-bold text-white">Admin Panel</h1>
        </div>
        <p className="text-slate-400">
          Manage strategies, agents, tools, API configurations, and monitor agent execution
        </p>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="strategies" className="space-y-6">
        <div className="overflow-x-auto -mx-4 px-4">
          <TabsList className="inline-flex w-auto bg-slate-900/50 border border-slate-800">
            <TabsTrigger
              value="strategies"
              className="data-[state=active]:bg-purple-600 data-[state=active]:text-white whitespace-nowrap px-6"
            >
              Strategy Instances
            </TabsTrigger>
            <TabsTrigger
              value="templates"
              className="data-[state=active]:bg-purple-600 data-[state=active]:text-white whitespace-nowrap px-6"
            >
              Strategy Templates
            </TabsTrigger>
            <TabsTrigger
              value="agents"
              className="data-[state=active]:bg-purple-600 data-[state=active]:text-white whitespace-nowrap px-6"
            >
              Agent Registry
            </TabsTrigger>
            <TabsTrigger
              value="tools"
              className="data-[state=active]:bg-purple-600 data-[state=active]:text-white whitespace-nowrap px-6"
            >
              Tool Registry
            </TabsTrigger>
            <TabsTrigger
              value="apis"
              className="data-[state=active]:bg-purple-600 data-[state=active]:text-white whitespace-nowrap px-6"
            >
              API Config
            </TabsTrigger>
            <TabsTrigger
              value="monitor"
              className="data-[state=active]:bg-purple-600 data-[state=active]:text-white whitespace-nowrap px-6"
            >
              Agent Monitor
            </TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="strategies" className="space-y-4">
          <AdminStrategies />
        </TabsContent>

        <TabsContent value="templates" className="space-y-4">
          <AdminStrategyTemplates />
        </TabsContent>

        <TabsContent value="agents" className="space-y-4">
          <AdminAgentRegistry />
        </TabsContent>

        <TabsContent value="tools" className="space-y-4">
          <AdminToolRegistry />
        </TabsContent>

        <TabsContent value="apis" className="space-y-4">
          <AdminAPIConfig />
        </TabsContent>

        <TabsContent value="monitor" className="space-y-4">
          <AgentMonitor />
        </TabsContent>
      </Tabs>
    </div>
  );
}
