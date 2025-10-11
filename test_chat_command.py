#!/usr/bin/env python3
"""
测试 /chat 命令功能
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, '/projects/cuscli')

# 设置环境变量，避免某些检查
os.environ['autocoder_auto_init'] = 'false'

print("=" * 60)
print("测试 /chat 命令")
print("=" * 60)

# 导入所需模块
from autocoder.auto_coder_runner import chat
from autocoder.common.core_config import get_memory_manager

# 确保有默认模型配置
memory_manager = get_memory_manager()
current_model = memory_manager.get_config("model", None)
print(f"\n当前配置的模型: {current_model}")

if not current_model:
    print("警告: 未找到默认模型配置，正在设置...")
    from autocoder.auto_coder_runner import configure
    configure("model:DSV3", skip_print=True)
    configure("product_mode:lite", skip_print=True)
    print("已设置默认模型: DSV3")

# 测试简单的聊天
print("\n" + "=" * 60)
print("发送测试消息: '你好，请简单回复收到'")
print("=" * 60 + "\n")

try:
    chat("你好，请简单回复收到")
    print("\n" + "=" * 60)
    print("✓ 聊天功能测试完成")
    print("=" * 60)
except Exception as e:
    print(f"\n✗ 聊天功能测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
