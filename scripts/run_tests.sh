#!/bin/bash
# 代码检查器测试运行脚本

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# 显示使用帮助
show_help() {
    cat << EOF
代码检查器测试脚本

用法:
    ./scripts/run_tests.sh [选项]

选项:
    -h, --help              显示帮助信息
    -u, --unit              只运行单元测试
    -i, --integration       只运行集成测试
    -a, --all               运行所有测试（默认）
    -c, --coverage          生成覆盖率报告
    -v, --verbose           详细输出
    --html                  生成 HTML 覆盖率报告
    --no-cache              清除 pytest 缓存

示例:
    ./scripts/run_tests.sh                  # 运行所有测试
    ./scripts/run_tests.sh -u -c            # 运行单元测试并生成覆盖率
    ./scripts/run_tests.sh -i -v            # 运行集成测试（详细输出）
    ./scripts/run_tests.sh --html           # 生成 HTML 覆盖率报告
EOF
}

# 默认参数
RUN_UNIT=false
RUN_INTEGRATION=false
RUN_ALL=true
COVERAGE=false
VERBOSE=false
HTML_COVERAGE=false
NO_CACHE=false

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -u|--unit)
            RUN_UNIT=true
            RUN_ALL=false
            shift
            ;;
        -i|--integration)
            RUN_INTEGRATION=true
            RUN_ALL=false
            shift
            ;;
        -a|--all)
            RUN_ALL=true
            shift
            ;;
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --html)
            HTML_COVERAGE=true
            COVERAGE=true
            shift
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        *)
            print_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 检查 pytest 是否安装
if ! command -v pytest &> /dev/null; then
    print_error "pytest 未安装，请先安装: pip install pytest pytest-cov"
    exit 1
fi

# 清除缓存
if [ "$NO_CACHE" = true ]; then
    print_info "清除 pytest 缓存..."
    rm -rf .pytest_cache
    rm -rf htmlcov
    rm -f .coverage
    rm -f coverage.xml
    print_success "缓存已清除"
fi

# 构建 pytest 命令
PYTEST_CMD="pytest tests/checker/"

# 添加标记过滤
if [ "$RUN_ALL" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -m 'unit or integration'"
elif [ "$RUN_UNIT" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -m unit"
elif [ "$RUN_INTEGRATION" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -m integration"
fi

# 添加覆盖率选项
if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=autocoder/checker --cov-report=term-missing"

    if [ "$HTML_COVERAGE" = true ]; then
        PYTEST_CMD="$PYTEST_CMD --cov-report=html"
    fi
fi

# 添加详细输出选项
if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -vv"
else
    PYTEST_CMD="$PYTEST_CMD -v"
fi

# 添加其他选项
PYTEST_CMD="$PYTEST_CMD --tb=short --color=yes"

# 显示执行信息
print_info "开始运行测试..."
echo ""
print_info "执行命令: $PYTEST_CMD"
echo ""

# 运行测试
if eval $PYTEST_CMD; then
    echo ""
    print_success "所有测试通过！"

    if [ "$HTML_COVERAGE" = true ]; then
        echo ""
        print_info "HTML 覆盖率报告已生成: htmlcov/index.html"
        print_info "使用浏览器打开: file://$(pwd)/htmlcov/index.html"
    fi

    exit 0
else
    echo ""
    print_error "测试失败！"
    exit 1
fi
