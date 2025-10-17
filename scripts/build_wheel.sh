#!/bin/bash
# Cuscli Wheel 打包脚本
# 用于快速构建和测试 whl 包
# 支持 Linux 和 Windows (Git Bash) 环境

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_step() {
    echo -e "${CYAN}🔧 $1${NC}"
}

# 显示使用帮助
show_help() {
    cat << EOF
${GREEN}Cuscli Wheel 打包脚本${NC}

${YELLOW}用法:${NC}
    ./scripts/build_wheel.sh [选项]

${YELLOW}选项:${NC}
    -h, --help              显示帮助信息
    -c, --clean-only        只清理临时文件，不构建
    -i, --install           构建后自动安装到当前环境
    -l, --list              显示 whl 包内容列表
    -v, --verbose           详细输出
    --no-clean              构建前不清理临时文件
    --no-bump               跳过版本号自动递增（默认每次build自动递增）

${YELLOW}示例:${NC}
    ./scripts/build_wheel.sh                    # 构建 whl 包（自动递增版本号）
    ./scripts/build_wheel.sh -i                 # 构建并安装（自动递增版本号）
    ./scripts/build_wheel.sh -l                 # 构建并查看包内容
    ./scripts/build_wheel.sh -c                 # 只清理临时文件
    ./scripts/build_wheel.sh --no-bump -i       # 不递增版本号，构建并安装

${YELLOW}构建流程:${NC}
    1. (默认) 自动递增版本号（满10进1）
    2. 清理旧的构建文件 (build/, dist/, *.egg-info)
    3. 从 autocoder/version.py 读取版本号
    4. 使用 python setup.py bdist_wheel 构建
    5. 验证生成的 whl 文件
    6. (可选) 安装到当前环境
    7. (可选) 显示包内容列表

EOF
}

# 默认参数
CLEAN_ONLY=false
INSTALL=false
LIST_CONTENTS=false
BUMP_VERSION=true     # 默认自动递增版本号
NO_BUMP=false         # 默认不跳过版本递增
VERBOSE=false
NO_CLEAN=false

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -c|--clean-only)
            CLEAN_ONLY=true
            shift
            ;;
        -i|--install)
            INSTALL=true
            shift
            ;;
        -l|--list)
            LIST_CONTENTS=true
            shift
            ;;
        --no-bump)
            NO_BUMP=true
            BUMP_VERSION=false
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --no-clean)
            NO_CLEAN=true
            shift
            ;;
        *)
            print_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 获取项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# 检测可用的 Python 命令 (支持 python3 和 python)
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    print_error "未找到 Python 命令！请确保已安装 Python 3.10+"
    exit 1
fi

# 检查 setup.py 是否存在
if [ ! -f "setup.py" ]; then
    print_error "setup.py 文件不存在！"
    exit 1
fi

# 获取当前版本号（从 autocoder/version.py 读取）
get_version() {
    $PYTHON_CMD -c '
import re
with open("autocoder/version.py", "r", encoding="utf-8") as f:
    content = f.read()
    match = re.search(r"^__version__\s*=\s*[\"'"'"']([^\"'"'"']+)[\"'"'"']", content, re.MULTILINE)
    if match:
        print(match.group(1))
    else:
        print("unknown")
'
}

# 升级版本号（满10进1规则）
bump_version() {
    local current_version="$1"
    $PYTHON_CMD -c '
import re

# 读取当前版本
version = "'$current_version'"
parts = version.split(".")
if len(parts) == 3:
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    
    # 实现满10进1逻辑
    patch += 1
    if patch >= 10:
        patch = 0
        minor += 1
        if minor >= 10:
            minor = 0
            major += 1
    
    new_version = f"{major}.{minor}.{patch}"
    
    # 更新 autocoder/version.py
    with open("autocoder/version.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # 替换版本号
    content = re.sub(
        r"^__version__\s*=\s*[\"'"'"']([^\"'"'"']+)[\"'"'"']",
        f"__version__ = \"'"'"'{new_version}'"'"'\"",
        content,
        flags=re.MULTILINE
    )
    
    with open("autocoder/version.py", "w", encoding="utf-8") as f:
        f.write(content)
    
    print(new_version)
else:
    print("'$current_version'")
'
}


# 清理临时文件
clean_build() {
    print_step "清理旧的构建文件..."

    # 清理构建目录
    if [ -d "build" ]; then
        rm -rf build
        [ "$VERBOSE" = true ] && echo "  - 已删除 build/"
    fi

    if [ -d "dist" ]; then
        rm -rf dist
        [ "$VERBOSE" = true ] && echo "  - 已删除 dist/"
    fi

    # 清理 egg-info 目录
    for egg_info in *.egg-info; do
        if [ -d "$egg_info" ]; then
            rm -rf "$egg_info"
            [ "$VERBOSE" = true ] && echo "  - 已删除 $egg_info"
        fi
    done

    # 清理 Python 缓存
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type f -name "*.pyo" -delete 2>/dev/null || true

    print_success "清理完成"
}

# 显示 banner
echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     ${GREEN}Cuscli Wheel 打包工具${CYAN}                   ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════╝${NC}"
echo ""

# 获取当前版本
CURRENT_VERSION=$(get_version)
print_info "当前版本: ${GREEN}${CURRENT_VERSION}${NC}"
echo ""

# 升级版本号（默认执行，除非指定 --no-bump）
if [ "$NO_BUMP" = false ]; then
    print_step "自动递增版本号（满10进1规则）..."
    NEW_VERSION=$(bump_version "$CURRENT_VERSION")
    print_success "版本号已递增: ${CURRENT_VERSION} → ${GREEN}${NEW_VERSION}${NC}"
    CURRENT_VERSION="$NEW_VERSION"
    echo ""
else
    print_info "跳过版本号递增（--no-bump）"
    echo ""
fi

# 清理构建文件
if [ "$NO_CLEAN" = false ]; then
    clean_build
    echo ""
fi

# 如果只是清理，则退出
if [ "$CLEAN_ONLY" = true ]; then
    print_success "清理完成，退出"
    exit 0
fi

# 检查 Python 环境
print_step "检查 Python 环境..."
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
print_info "Python 版本: ${PYTHON_VERSION}"

# 检查必需的包
if ! $PYTHON_CMD -c "import setuptools" 2>/dev/null; then
    print_error "setuptools 未安装，请先安装: pip install setuptools wheel"
    exit 1
fi

if ! $PYTHON_CMD -c "import wheel" 2>/dev/null; then
    print_error "wheel 未安装，请先安装: pip install setuptools wheel"
    exit 1
fi

print_success "环境检查通过"
echo ""

# 构建 wheel 包
print_step "开始构建 wheel 包..."
echo ""

if [ "$VERBOSE" = true ]; then
    $PYTHON_CMD setup.py bdist_wheel
else
    $PYTHON_CMD setup.py bdist_wheel > /dev/null 2>&1
fi

if [ $? -ne 0 ]; then
    print_error "构建失败！"
    exit 1
fi

echo ""
print_success "构建完成！"
echo ""

# 验证 whl 文件
print_step "验证生成的 whl 文件..."

if [ ! -d "dist" ]; then
    print_error "dist 目录不存在！"
    exit 1
fi

WHL_FILE=$(ls dist/*.whl 2>/dev/null | head -n 1)

if [ -z "$WHL_FILE" ]; then
    print_error "未找到生成的 whl 文件！"
    exit 1
fi

WHL_FILENAME=$(basename "$WHL_FILE")
WHL_SIZE=$(du -h "$WHL_FILE" | cut -f1)

print_success "找到 whl 文件:"
echo ""
echo -e "  ${GREEN}文件名:${NC} ${WHL_FILENAME}"
echo -e "  ${GREEN}大小:${NC}   ${WHL_SIZE}"
echo -e "  ${GREEN}路径:${NC}   ${WHL_FILE}"
echo ""

# 显示包内容
if [ "$LIST_CONTENTS" = true ]; then
    print_step "查看包内容..."
    echo ""

    if command -v unzip &> /dev/null; then
        unzip -l "$WHL_FILE" | head -n 50
        echo ""
        print_info "完整内容请使用: unzip -l $WHL_FILE"
    else
        print_warning "unzip 命令未找到，无法显示包内容"
    fi

    echo ""
fi

# 安装到当前环境
if [ "$INSTALL" = true ]; then
    print_step "安装到当前环境..."
    echo ""

    # 先卸载旧版本
    print_info "卸载旧版本 cuscli..."
    pip uninstall -y cuscli > /dev/null 2>&1 || true

    # 安装新版本
    print_info "安装新版本: ${WHL_FILENAME}"
    pip install "$WHL_FILE"

    if [ $? -eq 0 ]; then
        echo ""
        print_success "安装成功！"
        echo ""

        # 验证安装
        print_info "验证安装..."
        INSTALLED_VERSION=$(pip show cuscli 2>/dev/null | grep "^Version:" | cut -d' ' -f2)

        if [ "$INSTALLED_VERSION" = "$CURRENT_VERSION" ]; then
            print_success "版本验证通过: ${INSTALLED_VERSION}"
        else
            print_warning "版本不匹配: 预期 ${CURRENT_VERSION}, 实际 ${INSTALLED_VERSION}"
        fi
    else
        echo ""
        print_error "安装失败！"
        exit 1
    fi

    echo ""
fi

# 显示完成信息
echo -e "${CYAN}╔════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     ${GREEN}✨ 打包完成！${CYAN}                            ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════╝${NC}"
echo ""

print_info "下一步操作:"
echo ""
echo "  ${GREEN}1.${NC} 查看包内容:"
echo "     ${CYAN}unzip -l ${WHL_FILE}${NC}"
echo ""
echo "  ${GREEN}2.${NC} 安装到其他环境:"
echo "     ${CYAN}pip install ${WHL_FILE}${NC}"
echo ""
echo "  ${GREEN}3.${NC} 卸载:"
echo "     ${CYAN}pip uninstall cuscli${NC}"
echo ""
echo "  ${GREEN}4.${NC} 发布到 PyPI (如果需要):"
echo "     ${CYAN}twine upload ${WHL_FILE}${NC}"
echo ""

exit 0
