#!/bin/bash
# Cuscli 安装验证脚本
# 用于验证安装是否成功，版本是否正确

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

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_step() {
    echo -e "${CYAN}🔧 $1${NC}"
}

# 检测可用的 Python 命令
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    print_error "未找到 Python 命令！"
    exit 1
fi

# 显示 banner
echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     ${GREEN}Cuscli 安装验证工具${CYAN}                 ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════╝${NC}"
echo ""

PASS_COUNT=0
FAIL_COUNT=0
TOTAL_TESTS=7

# 测试1: 检查 pip show
print_step "测试 1/$TOTAL_TESTS: 检查 pip 包信息"
if pip show cuscli &> /dev/null; then
    INSTALLED_VERSION=$(pip show cuscli 2>/dev/null | grep "^Version:" | awk '{print $2}')
    INSTALLED_LOCATION=$(pip show cuscli 2>/dev/null | grep "^Location:" | awk '{print $2}')

    echo "  包名: ${GREEN}cuscli${NC}"
    echo "  版本: ${GREEN}$INSTALLED_VERSION${NC}"
    echo "  位置: ${BLUE}$INSTALLED_LOCATION${NC}"
    print_success "  测试通过"
    ((PASS_COUNT++))
else
    print_error "  cuscli 未安装"
    ((FAIL_COUNT++))
fi
echo ""

# 测试2: 检查 Python 版本导入
print_step "测试 2/$TOTAL_TESTS: 检查 Python 版本导入"
PYTHON_VERSION=$($PYTHON_CMD -c "from autocoder.version import __version__; print(__version__)" 2>/dev/null || echo "")
if [ -n "$PYTHON_VERSION" ]; then
    echo "  autocoder.version.__version__ = ${GREEN}$PYTHON_VERSION${NC}"

    # 验证版本号一致性
    if [ "$PYTHON_VERSION" = "$INSTALLED_VERSION" ]; then
        print_success "  版本号一致"
    else
        print_error "  版本号不一致！pip: $INSTALLED_VERSION vs Python: $PYTHON_VERSION"
    fi
    print_success "  测试通过"
    ((PASS_COUNT++))
else
    print_error "  无法导入 autocoder.version"
    ((FAIL_COUNT++))
fi
echo ""

# 测试3: 检查主入口点
print_step "测试 3/$TOTAL_TESTS: 检查主入口点"
if command -v cuscli &> /dev/null; then
    CUSCLI_PATH=$(which cuscli)
    echo "  cuscli 命令路径: ${BLUE}$CUSCLI_PATH${NC}"
    print_success "  测试通过"
    ((PASS_COUNT++))
else
    print_error "  cuscli 命令未找到"
    ((FAIL_COUNT++))
fi
echo ""

# 测试4: 检查 checker 模块
print_step "测试 4/$TOTAL_TESTS: 检查 checker 模块"
CHECKER_RESULT=$($PYTHON_CMD -c "
try:
    from autocoder.checker import core, rules_loader, file_processor
    print('OK')
except Exception as e:
    print(f'FAIL: {e}')
" 2>&1)

if [ "$CHECKER_RESULT" = "OK" ]; then
    echo "  autocoder.checker.core: ${GREEN}✓${NC}"
    echo "  autocoder.checker.rules_loader: ${GREEN}✓${NC}"
    echo "  autocoder.checker.file_processor: ${GREEN}✓${NC}"
    print_success "  测试通过"
    ((PASS_COUNT++))
else
    echo "  ${RED}$CHECKER_RESULT${NC}"
    print_error "  checker 模块导入失败"
    ((FAIL_COUNT++))
fi
echo ""

# 测试5: 检查 checker 插件
print_step "测试 5/$TOTAL_TESTS: 检查 code_checker_plugin"
PLUGIN_RESULT=$($PYTHON_CMD -c "
try:
    from autocoder.plugins.code_checker_plugin import CodeCheckerPlugin
    plugin = CodeCheckerPlugin()
    print(f'OK:{plugin.plugin_name()}:{plugin.version}')
except Exception as e:
    print(f'FAIL:{e}')
" 2>&1)

if [[ "$PLUGIN_RESULT" == OK:* ]]; then
    PLUGIN_NAME=$(echo "$PLUGIN_RESULT" | cut -d: -f2)
    PLUGIN_VERSION=$(echo "$PLUGIN_RESULT" | cut -d: -f3)
    echo "  插件名称: ${GREEN}$PLUGIN_NAME${NC}"
    echo "  插件版本: ${GREEN}$PLUGIN_VERSION${NC}"
    print_success "  测试通过"
    ((PASS_COUNT++))
else
    echo "  ${RED}$PLUGIN_RESULT${NC}"
    print_error "  插件加载失败"
    ((FAIL_COUNT++))
fi
echo ""

# 测试6: 检查 checker 命令注册
print_step "测试 6/$TOTAL_TESTS: 检查 /check 命令注册"
COMMANDS_RESULT=$($PYTHON_CMD -c "
try:
    from autocoder.plugins.code_checker_plugin import CodeCheckerPlugin
    plugin = CodeCheckerPlugin()
    commands = plugin.register_commands()
    if commands:
        for cmd, info in commands.items():
            print(f'{cmd}')
        print('OK')
    else:
        print('FAIL:No commands registered')
except Exception as e:
    print(f'FAIL:{e}')
" 2>&1)

if [[ "$COMMANDS_RESULT" == *"OK"* ]]; then
    echo "  注册的命令："
    while IFS= read -r line; do
        if [ "$line" != "OK" ] && [ -n "$line" ]; then
            echo "    - ${GREEN}$line${NC}"
        fi
    done <<< "$COMMANDS_RESULT"
    print_success "  测试通过"
    ((PASS_COUNT++))
else
    echo "  ${RED}$COMMANDS_RESULT${NC}"
    print_error "  命令注册失败"
    ((FAIL_COUNT++))
fi
echo ""

# 测试7: 检查数据文件
print_step "测试 7/$TOTAL_TESTS: 检查规则数据文件"
DATA_RESULT=$($PYTHON_CMD -c "
import os
try:
    from autocoder import checker
    checker_dir = os.path.dirname(checker.__file__)
    parent_dir = os.path.dirname(checker_dir)
    rules_dir = os.path.join(parent_dir, 'data', 'rules')

    if os.path.exists(rules_dir):
        rules_config = os.path.join(rules_dir, 'rules_config.json')
        frontend_rules = os.path.join(rules_dir, 'frontend_rules.md')
        backend_rules = os.path.join(rules_dir, 'backend_rules.md')

        files_found = []
        if os.path.exists(rules_config):
            files_found.append('rules_config.json')
        if os.path.exists(frontend_rules):
            files_found.append('frontend_rules.md')
        if os.path.exists(backend_rules):
            files_found.append('backend_rules.md')

        if files_found:
            print('OK:' + ','.join(files_found))
        else:
            print('FAIL:Rules directory exists but no rule files found')
    else:
        print(f'FAIL:Rules directory not found: {rules_dir}')
except Exception as e:
    print(f'FAIL:{e}')
" 2>&1)

if [[ "$DATA_RESULT" == OK:* ]]; then
    FILES=$(echo "$DATA_RESULT" | cut -d: -f2)
    echo "  规则文件："
    IFS=',' read -ra FILE_ARRAY <<< "$FILES"
    for file in "${FILE_ARRAY[@]}"; do
        echo "    - ${GREEN}$file${NC}"
    done
    print_success "  测试通过"
    ((PASS_COUNT++))
else
    echo "  ${RED}$DATA_RESULT${NC}"
    print_error "  规则文件检查失败"
    ((FAIL_COUNT++))
fi
echo ""

# 显示测试汇总
echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     ${GREEN}测试汇总${CYAN}                                ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════╝${NC}"
echo ""

echo "  总测试数: $TOTAL_TESTS"
echo "  ${GREEN}通过: $PASS_COUNT${NC}"

if [ $FAIL_COUNT -gt 0 ]; then
    echo "  ${RED}失败: $FAIL_COUNT${NC}"
    echo ""
    print_error "验证失败！"
    echo ""
    print_info "建议操作："
    echo "  1. 重新运行清理安装脚本："
    echo "     ${CYAN}./scripts/clean_install.sh -w <whl文件>${NC}"
    echo ""
    echo "  2. 检查 Python 环境："
    echo "     ${CYAN}$PYTHON_CMD --version${NC}"
    echo "     ${CYAN}pip list | grep cuscli${NC}"
    echo ""
    exit 1
else
    echo ""
    print_success "所有测试通过！安装验证成功！"
    echo ""
    print_info "可以开始使用 cuscli 了："
    echo "  ${CYAN}cuscli${NC}"
    echo ""
    print_info "尝试以下命令："
    echo "  ${CYAN}/help${NC}          - 查看帮助"
    echo "  ${CYAN}/check /help${NC}   - 查看 checker 帮助"
    echo "  ${CYAN}/plugins${NC}       - 查看已加载的插件"
    echo ""
    exit 0
fi
