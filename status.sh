#!/bin/bash

# AutoMoney 状态查看脚本
# 查看前端和后端服务状态

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
echo -e "  AutoMoney 服务状态"
echo -e "===================================${NC}"
echo ""

# 检查后端状态
echo -e "${BLUE}🖥️  后端服务 (端口 8000):${NC}"
BACKEND_RUNNING=false

if [ -f "$PID_DIR/backend.pid" ]; then
    BACKEND_PID=$(cat "$PID_DIR/backend.pid")
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo -e "  状态: ${GREEN}运行中 ✓${NC}"
        echo -e "  PID: ${BACKEND_PID}"

        # 检查服务是否响应
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "  健康: ${GREEN}正常 ✓${NC}"
            BACKEND_RUNNING=true
        else
            echo -e "  健康: ${RED}无响应 ✗${NC}"
        fi
    else
        echo -e "  状态: ${RED}未运行 ✗${NC}"
        echo -e "  ${YELLOW}(PID文件存在但进程不存在)${NC}"
    fi
else
    # 检查端口是否被占用
    BACKEND_PORT_PID=$(lsof -ti:8000 2>/dev/null)
    if [ ! -z "$BACKEND_PORT_PID" ]; then
        echo -e "  状态: ${YELLOW}端口8000被占用${NC}"
        echo -e "  PID: ${BACKEND_PORT_PID}"
        echo -e "  ${YELLOW}(可能是手动启动或其他进程)${NC}"
        BACKEND_RUNNING=true
    else
        echo -e "  状态: ${RED}未运行 ✗${NC}"
    fi
fi

if [ "$BACKEND_RUNNING" = true ]; then
    echo -e "  地址: ${GREEN}http://localhost:8000${NC}"
    echo -e "  文档: ${GREEN}http://localhost:8000/docs${NC}"
fi

echo ""

# 检查前端状态
echo -e "${BLUE}🎨 前端服务 (端口 3010):${NC}"
FRONTEND_RUNNING=false

if [ -f "$PID_DIR/frontend.pid" ]; then
    FRONTEND_PID=$(cat "$PID_DIR/frontend.pid")
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo -e "  状态: ${GREEN}运行中 ✓${NC}"
        echo -e "  PID: ${FRONTEND_PID}"

        # 检查服务是否响应
        if curl -s http://localhost:3010 > /dev/null 2>&1; then
            echo -e "  健康: ${GREEN}正常 ✓${NC}"
            FRONTEND_RUNNING=true
        else
            echo -e "  健康: ${YELLOW}启动中...${NC}"
        fi
    else
        echo -e "  状态: ${RED}未运行 ✗${NC}"
        echo -e "  ${YELLOW}(PID文件存在但进程不存在)${NC}"
    fi
else
    # 检查端口是否被占用
    FRONTEND_PORT_PID=$(lsof -ti:3010 2>/dev/null)
    if [ ! -z "$FRONTEND_PORT_PID" ]; then
        echo -e "  状态: ${YELLOW}端口3010被占用${NC}"
        echo -e "  PID: ${FRONTEND_PORT_PID}"
        echo -e "  ${YELLOW}(可能是手动启动或其他进程)${NC}"
        FRONTEND_RUNNING=true
    else
        echo -e "  状态: ${RED}未运行 ✗${NC}"
    fi
fi

if [ "$FRONTEND_RUNNING" = true ]; then
    echo -e "  地址: ${GREEN}http://localhost:3010${NC}"
fi

echo ""

# 日志文件状态
echo -e "${BLUE}📄 日志文件:${NC}"
if [ -f "$PID_DIR/backend.log" ]; then
    BACKEND_LOG_SIZE=$(du -h "$PID_DIR/backend.log" | cut -f1)
    echo -e "  后端日志: ${GREEN}存在${NC} ($BACKEND_LOG_SIZE)"
    echo -e "    查看: ${YELLOW}tail -f $PID_DIR/backend.log${NC}"
else
    echo -e "  后端日志: ${YELLOW}不存在${NC}"
fi

if [ -f "$PID_DIR/frontend.log" ]; then
    FRONTEND_LOG_SIZE=$(du -h "$PID_DIR/frontend.log" | cut -f1)
    echo -e "  前端日志: ${GREEN}存在${NC} ($FRONTEND_LOG_SIZE)"
    echo -e "    查看: ${YELLOW}tail -f $PID_DIR/frontend.log${NC}"
else
    echo -e "  前端日志: ${YELLOW}不存在${NC}"
fi

echo ""
echo -e "${BLUE}==================================="
echo -e "  操作命令"
echo -e "===================================${NC}"
echo ""

if [ "$BACKEND_RUNNING" = false ] || [ "$FRONTEND_RUNNING" = false ]; then
    echo -e "${YELLOW}启动服务:${NC} ./start.sh"
fi

if [ "$BACKEND_RUNNING" = true ] || [ "$FRONTEND_RUNNING" = true ]; then
    echo -e "${YELLOW}停止服务:${NC} ./stop.sh"
    echo -e "${YELLOW}重启服务:${NC} ./stop.sh && ./start.sh"
fi

echo ""
