#!/bin/bash

# AutoMoney 端口清理脚本
# 强制杀死占用8000和5173端口的所有进程

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================="
echo -e "  强制清理端口"
echo -e "===================================${NC}"
echo ""

# 清理函数
kill_port() {
    local port=$1
    local port_name=$2

    echo -e "${YELLOW}检查端口 ${port} (${port_name})...${NC}"

    # 获取所有占用该端口的进程
    PIDS=$(lsof -ti:$port 2>/dev/null)

    if [ -z "$PIDS" ]; then
        echo -e "${GREEN}✓ 端口 ${port} 未被占用${NC}"
        return 0
    fi

    echo -e "${RED}发现 ${port} 端口被占用，进程:${NC}"

    # 显示进程信息
    for pid in $PIDS; do
        PROC_INFO=$(ps -p $pid -o pid,command 2>/dev/null)
        if [ ! -z "$PROC_INFO" ]; then
            echo -e "${YELLOW}  $PROC_INFO${NC}"
        fi
    done

    echo ""
    echo -e "${YELLOW}正在强制终止这些进程...${NC}"

    # 强制杀死所有进程
    for pid in $PIDS; do
        echo -e "${YELLOW}  杀死 PID: $pid${NC}"
        kill -9 $pid 2>/dev/null
    done

    # 等待一下
    sleep 1

    # 再次检查
    REMAINING=$(lsof -ti:$port 2>/dev/null)
    if [ -z "$REMAINING" ]; then
        echo -e "${GREEN}✓ 端口 ${port} 已清理${NC}"
        return 0
    else
        echo -e "${RED}⚠️  端口 ${port} 仍有残留进程，执行二次清理${NC}"
        lsof -ti:$port | xargs kill -9 2>/dev/null
        sleep 1

        # 最终检查
        FINAL_CHECK=$(lsof -ti:$port 2>/dev/null)
        if [ -z "$FINAL_CHECK" ]; then
            echo -e "${GREEN}✓ 端口 ${port} 清理成功${NC}"
        else
            echo -e "${RED}✗ 端口 ${port} 清理失败，可能需要管理员权限${NC}"
            return 1
        fi
    fi
}

# 清理后端端口 8000
kill_port 8000 "后端"
echo ""

# 清理前端端口 3010
kill_port 3010 "前端"
echo ""

echo -e "${GREEN}==================================="
echo -e "  ✅ 端口清理完成"
echo -e "===================================${NC}"
echo ""
echo -e "${BLUE}验证端口状态:${NC}"
echo -e "  后端(8000): ${YELLOW}lsof -i:8000${NC}"
echo -e "  前端(3010): ${YELLOW}lsof -i:3010${NC}"
echo ""
echo -e "${BLUE}启动服务:${NC}"
echo -e "  运行: ${YELLOW}./start.sh${NC}"
echo ""
