#!/bin/bash
# Auto-Coder 中文界面启动脚本

# 设置中文 locale
export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8

# 激活虚拟环境（如果存在）
if [ -f ".venv/bin/activate" ]; then
    . .venv/bin/activate
fi

# 启动 auto-coder.chat（中文界面）
auto-coder.chat "$@"
