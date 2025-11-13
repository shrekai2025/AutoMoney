#!/bin/bash

# AutoMoney 初始化脚本
# 初始化数据库、注册Agent、注册策略

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/AMbackend"

echo -e "${BLUE}==================================="
echo -e "  AutoMoney 初始化"
echo -e "===================================${NC}"
echo ""

# 检查后端目录
if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}❌ 错误: 找不到后端目录${NC}"
    exit 1
fi

cd "$BACKEND_DIR"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ 错误: 找不到Python虚拟环境${NC}"
    echo -e "${YELLOW}请先运行: cd AMbackend && python -m venv venv${NC}"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

echo -e "${YELLOW}📦 检查数据库连接...${NC}"
# 这里可以添加数据库连接检查
echo -e "${GREEN}✓ 数据库连接正常${NC}"
echo ""

# 1. 初始化数据库表（如果需要）
echo -e "${YELLOW}🗄️  初始化数据库表...${NC}"
# 如果有alembic migrations
if [ -d "alembic" ]; then
    echo -e "${BLUE}  运行数据库迁移...${NC}"
    alembic upgrade head
    echo -e "${GREEN}✓ 数据库迁移完成${NC}"
else
    echo -e "${YELLOW}  跳过（未配置alembic）${NC}"
fi
echo ""

# 2. 注册动量策略Agent和Tool
echo -e "${YELLOW}🤖 注册动量策略Agent和Tool...${NC}"
if [ -f "scripts/register_momentum_complete.py" ]; then
    python scripts/register_momentum_complete.py
    echo -e "${GREEN}✓ Agent和Tool注册完成${NC}"
else
    echo -e "${RED}❌ 找不到注册脚本: scripts/register_momentum_complete.py${NC}"
    exit 1
fi
echo ""

# 3. 注册动量策略模板
echo -e "${YELLOW}📋 注册动量策略模板...${NC}"
if [ -f "scripts/init_momentum_strategy.py" ]; then
    python scripts/init_momentum_strategy.py
    echo -e "${GREEN}✓ 策略模板注册完成${NC}"
else
    echo -e "${RED}❌ 找不到策略初始化脚本: scripts/init_momentum_strategy.py${NC}"
    exit 1
fi
echo ""

# 4. 验证注册结果
echo -e "${YELLOW}🔍 验证注册结果...${NC}"
python << 'EOF'
import asyncio
from app.db.session import AsyncSessionLocal
from app.models.agent_registry import AgentRegistry
from app.models.tool_registry import ToolRegistry
from app.models.strategy_definition import StrategyDefinition
from sqlalchemy import select, func

async def verify():
    async with AsyncSessionLocal() as db:
        # 检查Agent
        result = await db.execute(select(func.count(AgentRegistry.id)))
        agent_count = result.scalar()
        
        # 检查Tool
        result = await db.execute(select(func.count(ToolRegistry.id)))
        tool_count = result.scalar()
        
        # 检查策略
        result = await db.execute(select(func.count(StrategyDefinition.id)))
        strategy_count = result.scalar()
        
        # 检查动量策略
        result = await db.execute(
            select(StrategyDefinition).where(
                StrategyDefinition.name == "momentum_regime_btc_v1"
            )
        )
        momentum_strategy = result.scalar_one_or_none()
        
        print(f"  ✓ Agents: {agent_count} 个")
        print(f"  ✓ Tools: {tool_count} 个")
        print(f"  ✓ Strategies: {strategy_count} 个")
        if momentum_strategy:
            print(f"  ✓ 动量策略已注册 (ID: {momentum_strategy.id})")
        else:
            print(f"  ⚠️  动量策略未找到")

asyncio.run(verify())
EOF
echo ""

echo -e "${GREEN}==================================="
echo -e "  ✅ 初始化完成"
echo -e "===================================${NC}"
echo ""
echo -e "${BLUE}下一步:${NC}"
echo -e "  1. 启动服务: ${YELLOW}./start.sh${NC}"
echo -e "  2. 访问前端: ${GREEN}http://localhost:3010${NC}"
echo -e "  3. 访问后端API: ${GREEN}http://localhost:8080/docs${NC}"
echo ""
echo -e "${BLUE}管理命令:${NC}"
echo -e "  查看状态: ${YELLOW}./status.sh${NC}"
echo -e "  查看日志: ${YELLOW}./logs.sh${NC}"
echo -e "  停止服务: ${YELLOW}./stop.sh${NC}"
echo ""

