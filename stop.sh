#!/bin/bash

# AutoMoney 停止脚本
# 停止前端和后端服务

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
PID_DIR="$PROJECT_ROOT/.pids"

echo -e "${BLUE}==================================="
echo -e "  AutoMoney 停止服务"
echo -e "===================================${NC}"
echo ""

# 停止后端
if [ -f "$PID_DIR/backend.pid" ]; then
    BACKEND_PID=$(cat "$PID_DIR/backend.pid")
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}🛑 停止后端服务 (PID: $BACKEND_PID)...${NC}"
        kill $BACKEND_PID 2>/dev/null || kill -9 $BACKEND_PID 2>/dev/null
        rm "$PID_DIR/backend.pid"
        echo -e "${GREEN}✓ 后端服务已停止${NC}"
    else
        echo -e "${YELLOW}⚠️  后端服务未运行 (PID文件存在但进程不存在)${NC}"
        rm "$PID_DIR/backend.pid"
    fi
else
    echo -e "${YELLOW}⚠️  未找到后端PID文件${NC}"
fi

# 强力清理：通过端口杀死所有进程（包括子进程）
BACKEND_PORT_PIDS=$(lsof -ti:8000 2>/dev/null)
if [ ! -z "$BACKEND_PORT_PIDS" ]; then
    echo -e "${YELLOW}⚠️  发现端口8000被占用，正在清理...${NC}"
    for pid in $BACKEND_PORT_PIDS; do
        echo -e "${YELLOW}   停止进程 PID: $pid${NC}"
        kill -9 $pid 2>/dev/null
    done
    sleep 1
    # 再次检查
    if lsof -ti:8000 >/dev/null 2>&1; then
        echo -e "${RED}⚠️  端口8000仍被占用，执行强制清理${NC}"
        lsof -ti:8000 | xargs kill -9 2>/dev/null
    fi
    echo -e "${GREEN}✓ 已清理端口8000${NC}"
fi

echo ""

# 停止前端
if [ -f "$PID_DIR/frontend.pid" ]; then
    FRONTEND_PID=$(cat "$PID_DIR/frontend.pid")
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}🛑 停止前端服务 (PID: $FRONTEND_PID)...${NC}"
        kill $FRONTEND_PID 2>/dev/null || kill -9 $FRONTEND_PID 2>/dev/null
        rm "$PID_DIR/frontend.pid"
        echo -e "${GREEN}✓ 前端服务已停止${NC}"
    else
        echo -e "${YELLOW}⚠️  前端服务未运行 (PID文件存在但进程不存在)${NC}"
        rm "$PID_DIR/frontend.pid"
    fi
else
    echo -e "${YELLOW}⚠️  未找到前端PID文件${NC}"
fi

# 强力清理：通过端口杀死所有进程（包括子进程）
FRONTEND_PORT_PIDS=$(lsof -ti:3010 2>/dev/null)
if [ ! -z "$FRONTEND_PORT_PIDS" ]; then
    echo -e "${YELLOW}⚠️  发现端口3010被占用，正在清理...${NC}"
    for pid in $FRONTEND_PORT_PIDS; do
        echo -e "${YELLOW}   停止进程 PID: $pid${NC}"
        kill -9 $pid 2>/dev/null
    done
    sleep 1
    # 再次检查
    if lsof -ti:3010 >/dev/null 2>&1; then
        echo -e "${RED}⚠️  端口3010仍被占用，执行强制清理${NC}"
        lsof -ti:3010 | xargs kill -9 2>/dev/null
    fi
    echo -e "${GREEN}✓ 已清理端口3010${NC}"
fi

echo ""

# 清理日志（可选）
if [ "$1" == "--clean-logs" ]; then
    echo -e "${YELLOW}🧹 清理日志文件...${NC}"
    rm -f "$PID_DIR/backend.log"
    rm -f "$PID_DIR/frontend.log"
    echo -e "${GREEN}✓ 日志已清理${NC}"
    echo ""
fi

echo -e "${GREEN}==================================="
echo -e "  ✅ 服务已停止"
echo -e "===================================${NC}"
echo ""
echo -e "${BLUE}提示:${NC}"
echo -e "  重新启动: ${YELLOW}./start.sh${NC}"
echo -e "  查看状态: ${YELLOW}./status.sh${NC}"
echo -e "  清理日志: ${YELLOW}./stop.sh --clean-logs${NC}"
echo ""
