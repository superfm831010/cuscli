#!/bin/bash
# Auto-Coder 二次开发环境设置脚本
# 用于快速搭建开发环境

set -e  # 遇到错误立即退出

echo "========================================"
echo "Auto-Coder 二次开发环境设置"
echo "========================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查 Python 版本
printf "${YELLOW}步骤 1/5: 检查 Python 版本...${NC}\n"

# 检测 python 或 python3 命令
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    printf "${RED}✗ 未找到 Python 命令${NC}\n"
    echo "请先安装 Python 3.10-3.12"
    exit 1
fi

python_version=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
python_major=$(echo "$python_version" | cut -d. -f1)
python_minor=$(echo "$python_version" | cut -d. -f2)

if [ "$python_major" -eq 3 ] && [ "$python_minor" -ge 10 ] && [ "$python_minor" -le 12 ]; then
    printf "${GREEN}✓ Python 版本符合要求: $python_version (使用 $PYTHON_CMD)${NC}\n"
else
    printf "${RED}✗ Python 版本不符合要求 (需要 3.10-3.12)，当前版本: $python_version${NC}\n"
    exit 1
fi
echo ""

# 检查是否在虚拟环境中
printf "${YELLOW}步骤 2/5: 检查/创建虚拟环境...${NC}\n"
if [ -z "$VIRTUAL_ENV" ] && [ -z "$CONDA_DEFAULT_ENV" ]; then
    printf "${YELLOW}未检测到虚拟环境，将自动创建...${NC}\n"

    # 定义虚拟环境目录
    VENV_DIR=".venv"

    # 检查是否已存在虚拟环境目录
    if [ -d "$VENV_DIR" ]; then
        echo "发现已存在的虚拟环境目录: $VENV_DIR"
    else
        echo "正在创建虚拟环境..."
        $PYTHON_CMD -m venv "$VENV_DIR"
        printf "${GREEN}✓ 虚拟环境创建成功${NC}\n"
    fi

    # 激活虚拟环境
    echo "正在激活虚拟环境..."
    # shellcheck source=/dev/null
    . "$VENV_DIR/bin/activate"

    if [ -n "$VIRTUAL_ENV" ]; then
        printf "${GREEN}✓ 虚拟环境已激活: $VENV_DIR${NC}\n"
    else
        printf "${RED}✗ 虚拟环境激活失败${NC}\n"
        echo "请手动激活虚拟环境："
        echo "  source $VENV_DIR/bin/activate"
        exit 1
    fi
else
    if [ -n "$CONDA_DEFAULT_ENV" ]; then
        printf "${GREEN}✓ 检测到 Conda 环境: $CONDA_DEFAULT_ENV${NC}\n"
    else
        printf "${GREEN}✓ 检测到虚拟环境: $VIRTUAL_ENV${NC}\n"
    fi
fi
echo ""

# 卸载已安装的 auto-coder（如果存在）
printf "${YELLOW}步骤 3/5: 检查并卸载现有安装...${NC}\n"
if pip show auto-coder &> /dev/null; then
    echo "检测到已安装的 auto-coder，正在卸载..."
    pip uninstall -y auto-coder
    printf "${GREEN}✓ 已卸载现有版本${NC}\n"
else
    echo "未检测到已安装的 auto-coder"
fi
echo ""

# 安装开发模式
printf "${YELLOW}步骤 4/5: 安装开发模式（editable install）...${NC}\n"
echo "这将以可编辑模式安装项目，修改代码后无需重新安装"
pip install -e .
printf "${GREEN}✓ 开发模式安装完成${NC}\n"
echo ""

# 验证安装
printf "${YELLOW}步骤 5/5: 验证安装...${NC}\n"
if command -v auto-coder &> /dev/null; then
    printf "${GREEN}✓ auto-coder 命令可用${NC}\n"
    auto-coder --version 2>&1 | head -1 || echo "版本信息获取失败（这可能是正常的）"
else
    printf "${RED}✗ auto-coder 命令不可用${NC}\n"
    echo "请检查 PATH 环境变量或重新激活虚拟环境"
    exit 1
fi
echo ""

# 完成提示
echo "========================================"
printf "${GREEN}开发环境设置完成！${NC}\n"
echo "========================================"
echo ""

# 检查是否创建了新的虚拟环境
if [ -d ".venv" ] && [ -z "$CONDA_DEFAULT_ENV" ]; then
    printf "${YELLOW}重要提示：${NC}\n"
    echo "虚拟环境已创建在 .venv/ 目录下"
    echo ""
    echo "下次使用前，请先激活虚拟环境："
    printf "${GREEN}  source .venv/bin/activate${NC}\n"
    echo ""
    echo "或者将以下内容添加到您的 ~/.bashrc 或 ~/.zshrc："
    echo "  alias autocoder-dev='cd /projects/cuscli && source .venv/bin/activate'"
    echo ""
fi

echo "现在您可以："
echo "  1. 直接修改 autocoder/ 目录下的源代码"
echo "  2. 修改后无需重新安装，直接运行命令测试"
echo "  3. 使用以下命令进行测试："
echo ""
echo "     auto-coder --help           # 查看帮助"
echo "     auto-coder.chat            # 启动聊天模式"
echo "     auto-coder.run -p \"测试\"   # 运行测试"
echo ""
echo "  4. 查看日志："
echo "     tail -f .auto-coder/logs/auto-coder.log"
echo ""
echo "开发建议："
echo "  - 每次修改后建议先运行简单测试确保基本功能正常"
echo "  - 重要修改请记录到 docs/development.md"
echo "  - 提交代码前请运行测试（如果有的话）"
echo ""
