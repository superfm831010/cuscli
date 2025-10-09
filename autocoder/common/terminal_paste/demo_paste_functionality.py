#!/usr/bin/env python3
"""
演示新的粘贴功能

这个脚本展示了如何使用新的粘贴处理功能:
1. Ctrl+P 粘贴多行内容并自动保存为文件
2. 占位符自动解析为实际内容
"""

import os
import tempfile
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.clipboard import ClipboardData
from autocoder.common.terminal_paste import register_paste_handler, resolve_paste_placeholders


def demo_paste_functionality():
    """演示粘贴功能的完整流程"""
    print("🎯 Terminal Paste 功能演示")
    print("=" * 50)
    
    # 创建键绑定
    kb = KeyBindings()
    register_paste_handler(kb)
    
    print("✅ 粘贴处理器已注册")
    print("📋 使用说明:")
    print("   - 复制多行文本到剪贴板")
    print("   - 按 Ctrl+P 粘贴 (多行内容会保存为文件)")
    print("   - 按 Ctrl+V 正常粘贴 (单行内容)")
    print("   - 输入 'quit' 退出演示")
    print()
    
    # 创建 PromptSession
    session = PromptSession(
        key_bindings=kb
        # 注意：bracketed paste 通过 Keys.BracketedPaste 绑定处理
    )
    
    while True:
        try:
            # 获取用户输入
            user_input = session.prompt("📝 请输入命令 (或按 Ctrl+P 粘贴): ")
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 演示结束")
                break
            
            # 解析占位符
            resolved_input = resolve_paste_placeholders(user_input)
            
            # 显示结果
            if resolved_input != user_input:
                print("🔄 占位符已解析:")
                print(f"   原始输入: {user_input}")
                print(f"   解析后: {resolved_input}")
            else:
                print(f"📤 您输入了: {resolved_input}")
            
            print()
            
        except KeyboardInterrupt:
            print("\n👋 演示结束")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")


def create_sample_clipboard_content():
    """创建示例剪贴板内容用于测试"""
    sample_content = """def hello_world():
    print("Hello, World!")
    return "success"

if __name__ == "__main__":
    result = hello_world()
    print(f"Result: {result}")"""
    
    print("📋 示例多行内容:")
    print(sample_content)
    print()
    print("💡 提示: 复制上面的代码，然后在演示中按 Ctrl+P 粘贴")
    print()


if __name__ == "__main__":
    print("🚀 开始 Terminal Paste 功能演示")
    print()
    
    # 显示示例内容
    create_sample_clipboard_content()
    
    # 运行演示
    demo_paste_functionality() 