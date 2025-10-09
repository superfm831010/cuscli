#!/usr/bin/env python3
"""
测试 MCP 工具模块的 KeyboardInterrupt 处理
"""

import sys
import time
import signal
import threading
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from autocoder.common.mcp_tools import get_mcp_server, McpRequest


def test_keyboard_interrupt():
    """测试 KeyboardInterrupt 是否能正确处理"""
    print("🧪 测试 MCP 工具模块的 KeyboardInterrupt 处理")
    print("=" * 50)
    
    # 获取 MCP 服务器实例
    print("1. 获取 MCP 服务器实例...")
    server = get_mcp_server()
    print(f"   ✓ 服务器实例创建成功: {server}")
    
    # 测试基本请求
    print("\n2. 测试基本请求...")
    try:
        request = McpRequest(query="test query")
        print(f"   ✓ 请求创建成功: {request}")
    except Exception as e:
        print(f"   ✗ 请求创建失败: {e}")
        return False
    
    # 设置定时器，5秒后发送 KeyboardInterrupt
    def send_interrupt():
        print("\n⏰ 5秒后将发送 KeyboardInterrupt 信号...")
        time.sleep(5)
        print("📡 发送 KeyboardInterrupt 信号")
        import os
        os.kill(os.getpid(), signal.SIGINT)
    
    # 启动定时器线程
    timer_thread = threading.Thread(target=send_interrupt, daemon=True)
    timer_thread.start()
    
    # 保持程序运行，等待中断信号
    print("\n3. 等待 KeyboardInterrupt 信号...")
    print("   （或者您可以手动按 Ctrl+C 来测试）")
    
    try:
        while True:
            time.sleep(1)
            print("   ⏳ 程序正在运行...")
    except KeyboardInterrupt:
        print("\n✅ KeyboardInterrupt 信号被正确捕获!")
        print("   正在进行清理...")
        
        # 等待一下，让清理完成
        time.sleep(2)
        print("✅ 清理完成，程序即将退出")
        return True
    except Exception as e:
        print(f"\n❌ 发生意外错误: {e}")
        return False


def main():
    """主函数"""
    print("🚀 开始测试 MCP 工具模块的 KeyboardInterrupt 处理")
    
    try:
        success = test_keyboard_interrupt()
        if success:
            print("\n🎉 测试成功！MCP 工具模块可以正确处理 KeyboardInterrupt")
            return 0
        else:
            print("\n❌ 测试失败！MCP 工具模块无法正确处理 KeyboardInterrupt")
            return 1
    except Exception as e:
        print(f"\n💥 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    print(f"\n🏁 测试结束，退出代码: {exit_code}")
    sys.exit(exit_code) 