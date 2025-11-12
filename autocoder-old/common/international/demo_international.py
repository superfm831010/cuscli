#!/usr/bin/env python3
"""
国际化模块功能演示脚本
International module functionality demo
"""

from autocoder.common.international import (
    register_messages,
    get_message,
    get_message_with_format,
    get_system_language,
    get_message_manager
)


def main():
    """演示国际化模块的主要功能"""
    print("=== 国际化模块功能演示 ===")
    print("=== International Module Demo ===\n")
    
    # 1. 显示系统语言
    print("1. 系统语言检测 / System Language Detection:")
    lang = get_system_language()
    print(f"   当前系统语言 / Current system language: {lang}\n")
    
    # 2. 注册自定义消息
    print("2. 注册自定义消息 / Register Custom Messages:")
    custom_messages = {
        "demo_greeting": {
            "en": "Hello from International Module!",
            "zh": "来自国际化模块的问候！"
        },
        "demo_user_info": {
            "en": "User {{name}} has {{count}} messages",
            "zh": "用户{{name}}有{{count}}条消息"
        },
        "demo_status": {
            "en": "Status: {{status}}",
            "zh": "状态：{{status}}"
        }
    }
    
    register_messages(custom_messages)
    print("   自定义消息已注册 / Custom messages registered\n")
    
    # 3. 获取简单消息
    print("3. 获取简单消息 / Get Simple Messages:")
    greeting = get_message("demo_greeting")
    print(f"   问候消息 / Greeting: {greeting}\n")
    
    # 4. 获取格式化消息
    print("4. 获取格式化消息 / Get Formatted Messages:")
    user_info = get_message_with_format("demo_user_info", name="张三", count=5)
    print(f"   用户信息 / User info: {user_info}")
    
    status_msg = get_message_with_format("demo_status", status="正常")
    print(f"   状态消息 / Status: {status_msg}\n")
    
    # 5. 显示自动注册的消息
    print("5. 自动注册的消息 / Auto-registered Messages:")
    manager = get_message_manager()
    total_messages = len(manager._messages)
    print(f"   总消息数量 / Total messages: {total_messages}")
    
    # 尝试获取一些已知的自动注册消息
    known_keys = ["file_scored_message", "config_delete_success", "config_invalid_format"]
    for key in known_keys:
        if key in manager._messages:
            msg = get_message(key)
            if msg:
                print(f"   {key}: {msg}")
            break
    
    print("\n6. 消息覆盖演示 / Message Override Demo:")
    # 覆盖现有消息
    override_messages = {
        "demo_greeting": {
            "en": "Updated Hello from International Module!",
            "zh": "来自国际化模块的更新问候！"
        }
    }
    
    register_messages(override_messages)
    updated_greeting = get_message("demo_greeting")
    print(f"   更新后的问候 / Updated greeting: {updated_greeting}\n")
    
    print("=== 演示完成 ===")
    print("=== Demo Complete ===")


if __name__ == "__main__":
    main() 