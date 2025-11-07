#!/bin/bash

# 快速安全检查脚本
# 在 git push 之前运行此脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  AutoMoney 安全检查${NC}"
echo -e "${BLUE}========================================${NC}\n"

# 计数器
PASSED=0
FAILED=0

# 检查函数
check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ $1${NC}"
        ((FAILED++))
    fi
}

# 1. 检查 .gitignore 是否存在
echo -e "${YELLOW}[1/8] 检查 .gitignore...${NC}"
test -f .gitignore
check ".gitignore 文件存在"

# 2. 检查 .env 是否被忽略
echo -e "\n${YELLOW}[2/8] 检查 .env 文件...${NC}"
git check-ignore AMbackend/.env > /dev/null 2>&1
check "AMbackend/.env 已被忽略"

# 3. 检查 API keys 文件
echo -e "\n${YELLOW}[3/8] 检查 API keys 文件...${NC}"
git check-ignore "AMbackend/API_docs/api keys.md" > /dev/null 2>&1
check "API keys 文件已被忽略"

# 4. 检查 venv
echo -e "\n${YELLOW}[4/8] 检查虚拟环境...${NC}"
git check-ignore AMbackend/venv > /dev/null 2>&1
check "venv 已被忽略"

# 5. 检查 node_modules
echo -e "\n${YELLOW}[5/8] 检查 node_modules...${NC}"
git check-ignore AMfrontend/node_modules > /dev/null 2>&1
check "node_modules 已被忽略"

# 6. 检查 Firebase 配置文件
echo -e "\n${YELLOW}[6/8] 检查 Firebase 服务账号...${NC}"
git check-ignore AMbackend/firebase-service-account.json > /dev/null 2>&1
check "Firebase 服务账号 JSON 已被忽略"

# 7. 搜索代码中的密钥
echo -e "\n${YELLOW}[7/8] 扫描代码中的密钥泄露...${NC}"
FOUND_KEYS=$(grep -r "sk-or-v1\|sk-AUswv\|PvLfdoqm\|9QLajKWv\|AIzaSyA7liJBv1D6eED\|882d0feaf0151dbe" \
    AMbackend/app AMfrontend/src 2>/dev/null | grep -v ".pyc" | wc -l)

if [ "$FOUND_KEYS" -eq 0 ]; then
    echo -e "${GREEN}✅ 未在代码中发现密钥${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ 警告：在代码中发现 $FOUND_KEYS 处密钥泄露！${NC}"
    echo -e "${RED}   请运行以下命令查看详情：${NC}"
    echo -e "${RED}   grep -rn 'sk-or-v1\\|PvLfdoqm' AMbackend/app AMfrontend/src${NC}"
    ((FAILED++))
fi

# 8. 检查 .pids 目录
echo -e "\n${YELLOW}[8/8] 检查日志和 PID 文件...${NC}"
git check-ignore .pids > /dev/null 2>&1
check ".pids 目录已被忽略"

# 总结
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}  检查结果${NC}"
echo -e "${BLUE}========================================${NC}\n"

echo -e "通过: ${GREEN}$PASSED${NC}"
echo -e "失败: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ 所有检查通过！可以安全推送到 GitHub${NC}\n"
    echo -e "运行以下命令推送："
    echo -e "${BLUE}./git-first-push.sh your-github-username${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}❌ 检查失败！请修复以上问题后再推送${NC}\n"
    echo -e "查看安全检查清单："
    echo -e "${BLUE}cat SECURITY_CHECKLIST.md${NC}"
    echo ""
    exit 1
fi
