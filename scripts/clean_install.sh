#!/bin/bash
# Cuscli 清理安装脚本
# 用于完全清理旧版本并安装新版本
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
${GREEN}Cuscli 清理安装脚本${NC}

${YELLOW}用法:${NC}
    ./scripts/clean_install.sh [选项]

${YELLOW}选项:${NC}
    -w, --wheel <file>      指定 whl 文件路径（必需）
    -v, --verbose           详细输出清理过程
    --dry-run               模拟运行，不实际执行
    --skip-verify           跳过安装后验证
    -h, --help              显示帮助信息

${YELLOW}示例:${NC}
    ./scripts/clean_install.sh -w dist/cuscli-1.0.4-py3-none-any.whl
    ./scripts/clean_install.sh -w cuscli-1.0.4-py3-none-any.whl -v
    ./scripts/clean_install.sh --wheel ./cuscli-1.0.4-py3-none-any.whl --dry-run

${YELLOW}清理流程:${NC}
    1. 卸载旧版本 cuscli
    2. 清理 pip 缓存
    3. 清理 site-packages 中的残留文件
    4. 清理 Python 字节码缓存 (.pyc, __pycache__)
    5. 安装新版本（使用 --no-cache-dir --force-reinstall）
    6. 验证安装结果

EOF
}

# 默认参数
WHEEL_FILE=""
VERBOSE=false
DRY_RUN=false
SKIP_VERIFY=false

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -w|--wheel)
            WHEEL_FILE="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --skip-verify)
            SKIP_VERIFY=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            print_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 检查必需参数
if [ -z "$WHEEL_FILE" ]; then
    print_error "缺少 whl 文件路径参数"
    echo ""
    show_help
    exit 1
fi

# 检查 whl 文件是否存在
if [ ! -f "$WHEEL_FILE" ]; then
    print_error "whl 文件不存在: $WHEEL_FILE"
    exit 1
fi

# 获取 whl 文件的绝对路径
WHEEL_FILE=$(realpath "$WHEEL_FILE" 2>/dev/null || readlink -f "$WHEEL_FILE" 2>/dev/null || echo "$WHEEL_FILE")

# 检测可用的 Python 命令
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    print_error "未找到 Python 命令！请确保已安装 Python 3.10+"
    exit 1
fi

# 显示 banner
echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     ${GREEN}Cuscli 清理安装工具${CYAN}                 ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════╝${NC}"
echo ""

if [ "$DRY_RUN" = true ]; then
    print_warning "模拟运行模式 (--dry-run)，不会实际执行操作"
    echo ""
fi

print_info "Python 版本: $($PYTHON_CMD --version 2>&1)"
print_info "whl 文件: $WHEEL_FILE"
echo ""

# 执行命令的包装函数
run_cmd() {
    local cmd="$1"
    local desc="$2"

    if [ "$VERBOSE" = true ]; then
        echo "  → 执行: $cmd"
    fi

    if [ "$DRY_RUN" = false ]; then
        eval "$cmd"
        return $?
    else
        echo "  [DRY RUN] $cmd"
        return 0
    fi
}

# 步骤1: 卸载旧版本
print_step "步骤 1/5: 卸载旧版本 cuscli..."
if run_cmd "pip uninstall -y cuscli 2>&1" "卸载 cuscli"; then
    print_success "已卸载旧版本"
else
    print_info "未找到已安装的 cuscli（可能是首次安装）"
fi
echo ""

# 步骤2: 清理 pip 缓存
print_step "步骤 2/5: 清理 pip 缓存..."
if command -v pip &> /dev/null; then
    # 尝试清理特定包的缓存
    if run_cmd "pip cache remove cuscli 2>&1" "清理 cuscli 缓存"; then
        print_success "已清理 cuscli pip 缓存"
    else
        [ "$VERBOSE" = true ] && print_info "pip cache remove 失败，尝试 purge..."
        if run_cmd "pip cache purge 2>&1" "清理所有 pip 缓存"; then
            print_success "已清理所有 pip 缓存"
        else
            print_warning "无法清理 pip 缓存（可能不支持此功能）"
        fi
    fi
else
    print_warning "未找到 pip 命令"
fi
echo ""

# 步骤3: 清理 site-packages 残留
print_step "步骤 3/5: 清理 site-packages 残留文件..."

# 获取 site-packages 路径列表
SITE_PACKAGES_DIRS=$($PYTHON_CMD -c "import site; print('\n'.join(site.getsitepackages()))" 2>/dev/null)
if [ -z "$SITE_PACKAGES_DIRS" ]; then
    # 备用方法
    SITE_PACKAGES_DIRS=$($PYTHON_CMD -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())" 2>/dev/null)
fi

# 添加用户 site-packages
USER_SITE=$($PYTHON_CMD -m site --user-site 2>/dev/null || true)
if [ -n "$USER_SITE" ]; then
    SITE_PACKAGES_DIRS="$SITE_PACKAGES_DIRS"$'\n'"$USER_SITE"
fi

CLEANED_COUNT=0

# 清理每个 site-packages 目录
while IFS= read -r site_dir; do
    if [ -z "$site_dir" ]; then
        continue
    fi

    [ "$VERBOSE" = true ] && echo "  → 检查目录: $site_dir"

    # 清理 autocoder 目录
    if [ -d "$site_dir/autocoder" ]; then
        [ "$VERBOSE" = true ] && echo "    → 发现 autocoder/ 目录"
        if run_cmd "rm -rf '$site_dir/autocoder'" "删除 autocoder"; then
            print_success "  已删除: $site_dir/autocoder"
            ((CLEANED_COUNT++))
        fi
    fi

    # 清理 cuscli*.dist-info 目录
    for dist_info in "$site_dir"/cuscli*.dist-info; do
        if [ -d "$dist_info" ]; then
            [ "$VERBOSE" = true ] && echo "    → 发现 $(basename "$dist_info")"
            if run_cmd "rm -rf '$dist_info'" "删除 dist-info"; then
                print_success "  已删除: $dist_info"
                ((CLEANED_COUNT++))
            fi
        fi
    done
done <<< "$SITE_PACKAGES_DIRS"

if [ $CLEANED_COUNT -eq 0 ]; then
    print_info "未发现需要清理的残留文件"
else
    print_success "共清理 $CLEANED_COUNT 个目录"
fi
echo ""

# 步骤4: 清理 Python 字节码缓存
print_step "步骤 4/5: 清理 Python 字节码缓存..."

CACHE_CLEANED=0

while IFS= read -r site_dir; do
    if [ -z "$site_dir" ] || [ ! -d "$site_dir" ]; then
        continue
    fi

    # 清理 .pyc 文件
    if [ "$VERBOSE" = true ]; then
        PYC_COUNT=$(find "$site_dir" -name "*.pyc" 2>/dev/null | wc -l)
        if [ "$PYC_COUNT" -gt 0 ]; then
            echo "  → 发现 $PYC_COUNT 个 .pyc 文件"
        fi
    fi

    if run_cmd "find '$site_dir' -name '*.pyc' -delete 2>/dev/null || true" "删除 .pyc"; then
        ((CACHE_CLEANED++))
    fi

    # 清理 __pycache__ 目录
    if [ "$VERBOSE" = true ]; then
        PYCACHE_COUNT=$(find "$site_dir" -type d -name "__pycache__" 2>/dev/null | wc -l)
        if [ "$PYCACHE_COUNT" -gt 0 ]; then
            echo "  → 发现 $PYCACHE_COUNT 个 __pycache__ 目录"
        fi
    fi

    if run_cmd "find '$site_dir' -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true" "删除 __pycache__"; then
        ((CACHE_CLEANED++))
    fi
done <<< "$SITE_PACKAGES_DIRS"

if [ $CACHE_CLEANED -gt 0 ]; then
    print_success "已清理字节码缓存"
else
    print_info "未发现需要清理的字节码缓存"
fi
echo ""

# 步骤5: 安装新版本
print_step "步骤 5/5: 安装新版本..."
echo ""

if [ "$DRY_RUN" = false ]; then
    print_info "使用参数: --no-cache-dir --force-reinstall"
    if pip install --no-cache-dir --force-reinstall "$WHEEL_FILE"; then
        echo ""
        print_success "安装成功！"
    else
        echo ""
        print_error "安装失败！"
        exit 1
    fi
else
    echo "  [DRY RUN] pip install --no-cache-dir --force-reinstall $WHEEL_FILE"
    print_info "模拟运行完成"
fi
echo ""

# 验证安装
if [ "$SKIP_VERIFY" = false ] && [ "$DRY_RUN" = false ]; then
    print_step "验证安装结果..."
    echo ""

    # 检查 pip show
    print_info "检查安装的包信息："
    INSTALLED_VERSION=$(pip show cuscli 2>/dev/null | grep "^Version:" | awk '{print $2}')
    if [ -n "$INSTALLED_VERSION" ]; then
        echo "  版本: ${GREEN}$INSTALLED_VERSION${NC}"
    else
        print_error "  无法获取版本信息"
    fi

    # 检查 Python 导入
    echo ""
    print_info "检查 Python 导入："
    PYTHON_VERSION=$($PYTHON_CMD -c "from autocoder.version import __version__; print(__version__)" 2>/dev/null || echo "")
    if [ -n "$PYTHON_VERSION" ]; then
        echo "  autocoder.version.__version__ = ${GREEN}$PYTHON_VERSION${NC}"
        print_success "  ✓ 版本导入正常"
    else
        print_error "  ✗ 无法导入版本号"
    fi

    # 检查 checker 插件
    echo ""
    print_info "检查 checker 插件："
    CHECKER_RESULT=$($PYTHON_CMD -c "from autocoder.plugins.code_checker_plugin import CodeCheckerPlugin; print('OK')" 2>/dev/null || echo "FAIL")
    if [ "$CHECKER_RESULT" = "OK" ]; then
        print_success "  ✓ CodeCheckerPlugin 加载成功"
    else
        print_error "  ✗ CodeCheckerPlugin 加载失败"
    fi

    echo ""
fi

# 显示完成信息
echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     ${GREEN}✨ 清理安装完成！${CYAN}                    ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════╝${NC}"
echo ""

if [ "$DRY_RUN" = false ]; then
    print_info "下一步："
    echo ""
    echo "  ${GREEN}1.${NC} 启动 cuscli："
    echo "     ${CYAN}cuscli${NC}"
    echo ""
    echo "  ${GREEN}2.${NC} 验证 /check 命令："
    echo "     ${CYAN}输入 /check 然后按 Tab 查看补全${NC}"
    echo ""
    echo "  ${GREEN}3.${NC} 如需详细验证："
    echo "     ${CYAN}./scripts/verify_install.sh${NC}"
    echo ""
else
    print_warning "这是模拟运行，实际操作未执行"
    echo ""
    print_info "如需实际执行，请去掉 --dry-run 参数："
    echo "  ${CYAN}./scripts/clean_install.sh -w $WHEEL_FILE${NC}"
    echo ""
fi

exit 0
