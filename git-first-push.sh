#!/bin/bash

# GitHub 首次推送脚本
# 用法: ./git-first-push.sh <your-github-username>

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查参数
if [ $# -eq 0 ]; then
    echo -e "${RED}错误：请提供 GitHub 用户名${NC}"
    echo "用法: ./git-first-push.sh <your-github-username>"
    exit 1
fi

GITHUB_USERNAME=$1
REPO_NAME="AutoMoney"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  AutoMoney - GitHub 上传准备${NC}"
echo -e "${BLUE}========================================${NC}\n"

# 1. 安全检查
echo -e "${YELLOW}[1/6] 运行安全检查...${NC}"

echo -e "\n检查敏感文件是否被忽略..."
if git check-ignore AMbackend/.env > /dev/null 2>&1; then
    echo -e "${GREEN}✅ .env 文件已被忽略${NC}"
else
    echo -e "${RED}❌ 警告：.env 文件未被忽略！${NC}"
    exit 1
fi

if git check-ignore "AMbackend/API_docs/api keys.md" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API keys 文件已被忽略${NC}"
else
    echo -e "${RED}❌ 警告：API keys 文件未被忽略！${NC}"
    exit 1
fi

if git check-ignore AMfrontend/node_modules > /dev/null 2>&1; then
    echo -e "${GREEN}✅ node_modules 已被忽略${NC}"
else
    echo -e "${RED}❌ 警告：node_modules 未被忽略！${NC}"
    exit 1
fi

# 搜索密钥泄露
echo -e "\n检查代码中的密钥泄露..."
if grep -r "sk-or-v1\|sk-AUswv\|PvLfdoqm\|9QLajKWv\|AIzaSyA7liJBv1D6eED\|882d0feaf0151dbe" AMbackend/app AMfrontend/src 2>/dev/null | grep -v ".pyc"; then
    echo -e "${RED}❌ 警告：在代码中发现密钥！请检查并移除${NC}"
    exit 1
else
    echo -e "${GREEN}✅ 未在代码中发现密钥${NC}"
fi

# 2. 查看将要提交的文件
echo -e "\n${YELLOW}[2/6] 查看将要提交的文件...${NC}"
git status --short | head -20
echo ""
read -p "以上文件将被添加，是否继续？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}已取消${NC}"
    exit 1
fi

# 3. 添加文件到暂存区
echo -e "\n${YELLOW}[3/6] 添加文件到 Git...${NC}"
git add .gitignore
git add README.md SETUP.md SECURITY_CHECKLIST.md
git add QUICKSTART.md COMMANDS.md FRONTEND_BACKEND_INTEGRATION_COMPLETE.md research功能实现.md 2>/dev/null || true
git add start.sh stop.sh status.sh kill-ports.sh
git add AMbackend --dry-run

echo -e "\n即将添加 AMbackend 目录，最后确认..."
git status AMbackend --short | head -30
echo ""
read -p "确认添加 AMbackend？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}已取消${NC}"
    exit 1
fi

git add AMbackend
git add AMfrontend
git add app docs 2>/dev/null || true

# 4. 最终确认
echo -e "\n${YELLOW}[4/6] 最终确认...${NC}"
echo -e "\n将要提交的文件："
git status --short | head -30
echo ""
echo -e "${YELLOW}⚠️  最后机会检查！确认以上文件不包含敏感信息？${NC}"
read -p "继续提交？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}已取消${NC}"
    echo "您可以使用 'git reset' 撤销暂存的文件"
    exit 1
fi

# 5. 提交
echo -e "\n${YELLOW}[5/6] 创建提交...${NC}"
git commit -m "Initial commit: AutoMoney v2.0

- FastAPI backend with Firebase authentication
- React frontend with Vite
- LLM integration (OpenRouter + Tuzi)
- Data collection framework (Binance, FRED, Alternative.me)
- Technical indicators (EMA, RSI, MACD, Bollinger Bands)
- Docker and PostgreSQL support
- Comprehensive documentation

Security:
- All API keys properly excluded via .gitignore
- Environment variables using .env (not tracked)
- Security checklist included
"

echo -e "${GREEN}✅ 提交成功${NC}"

# 6. 推送到 GitHub
echo -e "\n${YELLOW}[6/6] 准备推送到 GitHub...${NC}"
echo -e "\n请确保你已经在 GitHub 上创建了仓库："
echo -e "${BLUE}https://github.com/${GITHUB_USERNAME}/${REPO_NAME}${NC}"
echo ""
read -p "仓库已创建？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}请先在 GitHub 上创建仓库，然后运行：${NC}"
    echo -e "git remote add origin https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"
    echo -e "git branch -M main"
    echo -e "git push -u origin main"
    exit 0
fi

# 添加远程仓库
echo -e "\n添加远程仓库..."
if git remote get-url origin > /dev/null 2>&1; then
    echo -e "${YELLOW}远程仓库已存在，跳过添加${NC}"
else
    git remote add origin "https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"
    echo -e "${GREEN}✅ 远程仓库已添加${NC}"
fi

# 重命名分支为 main
git branch -M main

# 推送
echo -e "\n开始推送..."
if git push -u origin main; then
    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}  ✅ 成功推送到 GitHub！${NC}"
    echo -e "${GREEN}========================================${NC}\n"
    echo -e "仓库地址："
    echo -e "${BLUE}https://github.com/${GITHUB_USERNAME}/${REPO_NAME}${NC}\n"
    echo -e "建议后续操作："
    echo -e "1. 在 GitHub 上添加仓库描述和话题标签"
    echo -e "2. 启用 Secret Scanning（Settings → Security）"
    echo -e "3. 设置分支保护规则"
    echo -e "4. 添加 GitHub Actions（可选）"
else
    echo -e "\n${RED}推送失败，请检查：${NC}"
    echo -e "1. GitHub 仓库是否已创建"
    echo -e "2. 是否有推送权限"
    echo -e "3. 网络连接是否正常"
    exit 1
fi
