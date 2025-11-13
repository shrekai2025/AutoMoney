/**
 * Registry API Service - Agent/Tool/API Configuration Management
 * 注册表 API 调用服务
 */

import apiClient from './api';

// ========== Types ==========

export interface AgentRegistry {
  id: number;
  agent_name: string;
  display_name: string;
  description?: string;
  agent_module: string;
  agent_class: string;
  available_tools: string[];
  is_active: boolean;
}

export interface ToolRegistry {
  id: number;
  tool_name: string;
  display_name: string;
  description?: string;
  tool_module: string;
  tool_function: string;
  required_apis: string[];
  is_active: boolean;
}

export interface APIConfig {
  id: number;
  api_name: string;
  display_name: string;
  description?: string;
  base_url?: string;
  api_key_masked?: string;
  rate_limit?: number;
  is_active: boolean;
}

export interface APIConfigUpdate {
  display_name?: string;
  description?: string;
  base_url?: string;
  api_key_encrypted?: string;
  api_secret_encrypted?: string;
  rate_limit?: number;
  is_active?: boolean;
}

// ========== Agent Registry API ==========

/**
 * 获取所有注册的Agent
 * @param activeOnly - 是否只返回活跃的Agent
 */
export async function fetchAllAgents(activeOnly: boolean = true): Promise<AgentRegistry[]> {
  const response = await apiClient.get<AgentRegistry[]>(
    `/api/v1/admin/agents`,
    {
      params: { active_only: activeOnly },
    }
  );
  return response.data;
}

// ========== Tool Registry API ==========

/**
 * 获取所有注册的Tool
 * @param activeOnly - 是否只返回活跃的Tool
 */
export async function fetchAllTools(activeOnly: boolean = true): Promise<ToolRegistry[]> {
  const response = await apiClient.get<ToolRegistry[]>(
    `/api/v1/admin/tools`,
    {
      params: { active_only: activeOnly },
    }
  );
  return response.data;
}

// ========== API Config API ==========

/**
 * 获取所有API配置
 * @param activeOnly - 是否只返回活跃的API
 */
export async function fetchAllAPIs(activeOnly: boolean = true): Promise<APIConfig[]> {
  const response = await apiClient.get<APIConfig[]>(
    `/api/v1/admin/apis`,
    {
      params: { active_only: activeOnly },
    }
  );
  return response.data;
}

/**
 * 更新API配置
 * @param apiName - API名称
 * @param updateData - 更新数据
 */
export async function updateAPIConfig(
  apiName: string,
  updateData: APIConfigUpdate
): Promise<APIConfig> {
  const response = await apiClient.patch<APIConfig>(
    `/api/v1/admin/apis/${apiName}`,
    updateData
  );
  return response.data;
}
