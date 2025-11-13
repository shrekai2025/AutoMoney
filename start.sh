#!/bin/bash

# AutoMoney 一键启动脚本
# 同时启动前端和后端服务

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
FRONTEND_DIR="$PROJECT_ROOT/AMfrontend"
PID_DIR="$PROJECT_ROOT/.pids"

# 创建PID目录
mkdir -p "$PID_DIR"

echo -e "${BLUE}==================================="
echo -e "  AutoMoney 一键启动"
echo -e "===================================${NC}"
echo ""

# 检查目录
if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}❌ 错误: 找不到后端目录${NC}"
    exit 1
fi

if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}❌ 错误: 找不到前端目录${NC}"
    exit 1
fi

# 检查端口占用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# 启动后端
echo -e "${YELLOW}🚀 启动后端服务...${NC}"
cd "$BACKEND_DIR"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ 错误: 找不到Python虚拟环境${NC}"
    echo -e "${YELLOW}请先运行: python -m venv venv${NC}"
    exit 1
fi

# 检查后端端口
if check_port 8000; then
    echo -e "${YELLOW}⚠️  警告: 端口8000已被占用${NC}"
    echo -e "${YELLOW}可能后端已经在运行，或者需要先执行 ./stop.sh${NC}"
else
    # 启动后端（后台运行）
    # 注意: 不使用--reload,因为调度器需要完全重启才能更新
    source venv/bin/activate
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > "$PID_DIR/backend.log" 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > "$PID_DIR/backend.pid"
    echo -e "${GREEN}✓ 后端服务已启动 (PID: $BACKEND_PID)${NC}"
    echo -e "${BLUE}  访问: http://localhost:8000${NC}"
    echo -e "${BLUE}  文档: http://localhost:8000/docs${NC}"
    echo -e "${BLUE}  日志: $PID_DIR/backend.log${NC}"
    echo -e "${YELLOW}  注意: 修改代码后需要 ./stop.sh && ./start.sh 重启${NC}"
fi

echo ""

# 等待后端启动
echo -e "${YELLOW}⏳ 等待后端服务就绪...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 后端服务就绪${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ 后端启动超时${NC}"
        echo -e "${YELLOW}查看日志: tail -f $PID_DIR/backend.log${NC}"
        exit 1
    fi
    sleep 1
done

echo ""

# 启动前端
echo -e "${YELLOW}🎨 启动前端服务...${NC}"
cd "$FRONTEND_DIR"

# 检查node_modules
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠️  检测到node_modules不存在，正在安装依赖...${NC}"
    npm install
fi

# 检查前端端口
if check_port 3010; then
    echo -e "${YELLOW}⚠️  警告: 端口3010已被占用${NC}"
    echo -e "${YELLOW}可能前端已经在运行，或者需要先执行 ./stop.sh${NC}"
else
    # 启动前端（后台运行）
    nohup npm run dev > "$PID_DIR/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "$PID_DIR/frontend.pid"
    echo -e "${GREEN}✓ 前端服务已启动 (PID: $FRONTEND_PID)${NC}"
    echo -e "${BLUE}  访问: http://localhost:3010${NC}"
    echo -e "${BLUE}  日志: $PID_DIR/frontend.log${NC}"
fi

echo ""
echo -e "${GREEN}==================================="
echo -e "  ✅ 启动完成"
echo -e "===================================${NC}"
echo ""
echo -e "${BLUE}服务地址:${NC}"
echo -e "  前端: ${GREEN}http://localhost:3010${NC}"
echo -e "  后端: ${GREEN}http://localhost:8000${NC}"
echo -e "  API文档: ${GREEN}http://localhost:8000/docs${NC}"
echo ""
echo -e "${BLUE}查看日志:${NC}"
echo -e "  所有日志: ${YELLOW}./logs.sh${NC}"
echo -e "  后端日志: ${YELLOW}./logs.sh backend${NC}"
echo -e "  前端日志: ${YELLOW}./logs.sh frontend${NC}"
echo -e "  实时跟踪: ${YELLOW}./logs.sh -f${NC}"
echo ""
echo -e "${BLUE}停止服务:${NC}"
echo -e "  运行: ${YELLOW}./stop.sh${NC}"
echo ""
echo -e "${BLUE}查看状态:${NC}"
echo -e "  运行: ${YELLOW}./status.sh${NC}"
echo ""
