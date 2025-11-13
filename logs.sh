#!/bin/bash

# 日志查看脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$PROJECT_ROOT/.pids"

# 日志文件路径
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"

echo -e "${BLUE}==================================="
echo -e "  AutoMoney 日志查看"
echo -e "===================================${NC}"
echo ""

# 显示帮助
show_help() {
    echo -e "${BLUE}用法:${NC}"
    echo -e "  ${GREEN}./logs.sh${NC}              # 查看所有日志"
    echo -e "  ${GREEN}./logs.sh backend${NC}      # 只查看后端日志"
    echo -e "  ${GREEN}./logs.sh frontend${NC}     # 只查看前端日志"
    echo -e "  ${GREEN}./logs.sh -f${NC}           # 实时跟踪所有日志"
    echo -e "  ${GREEN}./logs.sh backend -f${NC}   # 实时跟踪后端日志"
    echo -e "  ${GREEN}./logs.sh clean${NC}        # 清理所有日志"
    echo ""
}

# 清理日志
clean_logs() {
    echo -e "${YELLOW}🗑️  清理日志文件...${NC}"
    
    if [ -f "$BACKEND_LOG" ]; then
        > "$BACKEND_LOG"
        echo -e "${GREEN}✓ 后端日志已清理${NC}"
    fi
    
    if [ -f "$FRONTEND_LOG" ]; then
        > "$FRONTEND_LOG"
        echo -e "${GREEN}✓ 前端日志已清理${NC}"
    fi
    
    echo -e "${GREEN}✓ 日志清理完成${NC}"
}

# 查看日志
view_logs() {
    local target=$1
    local follow=$2
    
    if [ "$target" = "backend" ]; then
        if [ ! -f "$BACKEND_LOG" ]; then
            echo -e "${RED}❌ 后端日志文件不存在${NC}"
            return 1
        fi
        
        echo -e "${BLUE}后端日志 (${BACKEND_LOG}):${NC}"
        echo -e "${YELLOW}----------------------------------------${NC}"
        
        if [ "$follow" = "-f" ]; then
            tail -f "$BACKEND_LOG"
        else
            tail -50 "$BACKEND_LOG"
        fi
        
    elif [ "$target" = "frontend" ]; then
        if [ ! -f "$FRONTEND_LOG" ]; then
            echo -e "${RED}❌ 前端日志文件不存在${NC}"
            return 1
        fi
        
        echo -e "${BLUE}前端日志 (${FRONTEND_LOG}):${NC}"
        echo -e "${YELLOW}----------------------------------------${NC}"
        
        if [ "$follow" = "-f" ]; then
            tail -f "$FRONTEND_LOG"
        else
            tail -50 "$FRONTEND_LOG"
        fi
        
    else
        # 查看所有日志
        if [ -f "$BACKEND_LOG" ]; then
            echo -e "${BLUE}📋 后端日志 (最后50行):${NC}"
            echo -e "${YELLOW}----------------------------------------${NC}"
            tail -50 "$BACKEND_LOG"
            echo ""
        fi
        
        if [ -f "$FRONTEND_LOG" ]; then
            echo -e "${BLUE}📋 前端日志 (最后50行):${NC}"
            echo -e "${YELLOW}----------------------------------------${NC}"
            tail -50 "$FRONTEND_LOG"
            echo ""
        fi
        
        if [ "$follow" = "-f" ]; then
            echo -e "${GREEN}实时跟踪所有日志...${NC}"
            tail -f "$BACKEND_LOG" "$FRONTEND_LOG"
        fi
    fi
}

# 处理命令
case "$1" in
    help|-h|--help)
        show_help
        ;;
    clean)
        clean_logs
        ;;
    backend)
        view_logs "backend" "$2"
        ;;
    frontend)
        view_logs "frontend" "$2"
        ;;
    -f)
        view_logs "all" "-f"
        ;;
    "")
        view_logs "all" ""
        ;;
    *)
        echo -e "${RED}❌ 未知命令: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
