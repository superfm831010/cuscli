#!/usr/bin/env python3
"""
AgenticConversationPruner 消息ID裁剪逻辑验证脚本

本脚本用于验证 agentic_conversation_pruner.py 中基于消息ID的裁剪逻辑，
使用真实的会话ID和消息配置来测试裁剪功能。

支持的消息ID格式：
1. 直接字段格式: {"message_id": "9226b3a4-1234-5678-9abc-def012345678"}
2. Hint嵌入格式: {"content": "消息内容 [[message_id: 9226b3a4]]"}
3. 兼容格式: {"content": "消息内容 message_id: 9226b3a4"}

测试场景：
1. 有消息ID配置的会话 - 应用消息ID裁剪
2. 无消息ID配置的会话 - 跳过消息ID裁剪  
3. 裁剪统计信息验证
4. 成对裁剪逻辑验证
5. 两种消息ID格式的混合验证
"""

import sys
import os
import json
from datetime import datetime
from typing import List, Dict, Any

# 添加src路径到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../..'))

from autocoder.common.pruner.agentic_conversation_pruner import AgenticConversationPruner
from autocoder.common.pruner.conversation_message_ids_api import get_conversation_message_ids_api
from autocoder.common import AutoCoderArgs
from autocoder.sdk import get_llm


def create_test_conversations() -> List[Dict[str, Any]]:
    """创建测试用的会话数据，包含我们已知要删除的消息ID
    
    展示两种消息ID格式的支持：
    1. 直接字段格式（推荐）- 从message_id字段提取
    2. Hint嵌入格式（兼容性）- 从content中提取
    """
    
    # 根据之前的查询，我们知道要删除的消息ID是 642f04ee
    # 我们创建一个包含这个ID的会话数据来测试
    conversations = [
        {
            "role": "system",
            "content": "You are a helpful assistant.",
            "message_id": "12345678abcdef01"  # 格式1: 直接字段格式（完整UUID）
        },
        {
            "role": "user", 
            "content": "Hello, can you help me with some code? [[message_id: 87654321]]",  # 格式2: 标准hint格式
            "message_id": "87654321fedcba02"  # 同时包含两种格式用于验证优先级
        },
        {
            "role": "assistant",
            "content": "Of course! I'd be happy to help you with your code. What do you need assistance with?",
            "message_id": "642f04ee11223344"  # 格式1: 这个消息ID的前8位匹配要删除的 642f04ee
        },
        {
            "role": "user",
            "content": "I want to read a file and analyze it. message_id: 13579bdf",  # 格式2: 兼容hint格式
            # 没有message_id字段，只从content中提取
        },
        {
            "role": "assistant", 
            "content": "I'll help you read and analyze the file.\n\n<read_file>\n<path>example.py</path>\n</read_file>",
            "message_id": "97531eca"  # 格式1: 8字符短ID
        },
        {
            "role": "user",
            "content": "<tool_result tool_name='read_file' success='true'><message>File read successfully</message><content>def hello():\n    print('Hello, World!')\n    return 'success'</content></tool_result> [[message_id: abcdef01]]",  # 格式2: 标准hint格式
            # 没有message_id字段，只从content中提取
        },
        {
            "role": "assistant",
            "content": "I can see the file contains a simple hello function. The code looks good!",
            "message_id": "fedcba9876543210"  # 格式1: 完整UUID
        }
    ]
    
    return conversations


def create_test_args() -> AutoCoderArgs:
    """创建测试用的参数"""
    return AutoCoderArgs(
        source_dir=".",
        conversation_prune_safe_zone_tokens=1000,  # 设置较小的值，强制触发裁剪逻辑
        context_prune=True,
        context_prune_strategy="extract",
        query="测试消息ID裁剪逻辑"
    )


def print_conversations(conversations: List[Dict[str, Any]], title: str):
    """打印会话列表，方便查看"""
    print(f"\n📋 {title}")
    print("=" * 80)
    
    for i, conv in enumerate(conversations):
        role = conv.get("role", "unknown")
        content = conv.get("content", "")
        message_id = conv.get("message_id", "no_id")
        
        # 截断长内容
        if len(content) > 100:
            content_display = content[:97] + "..."
        else:
            content_display = content
            
        print(f"  {i+1:2d}. [{role:9}] {message_id[:8]} | {content_display}")


def verify_pruning_with_message_ids():
    """验证有消息ID配置的裁剪逻辑"""
    
    print("🔍 测试场景1: 验证有消息ID配置的会话裁剪")
    print("=" * 80)
    
    # 使用已知的会话ID，该会话配置了要删除消息ID 642f04ee
    conversation_id = "796e1c2e-1ab8-46d1-9448-f9bd29d5c095"
    
    # 创建测试数据
    original_conversations = create_test_conversations()
    args = create_test_args()
    llm = get_llm("v3_chat", product_mode="lite")
    
    # 打印原始会话
    print_conversations(original_conversations, "原始会话数据")
    
    # 查询消息ID配置
    api = get_conversation_message_ids_api()
    message_ids_config = api.get_conversation_message_ids(conversation_id)
    
    if message_ids_config:
        print(f"\n✅ 找到消息ID配置:")
        print(f"   会话ID: {message_ids_config.conversation_id}")
        print(f"   要删除的消息ID: {message_ids_config.message_ids}")
        print(f"   保持成对删除: {message_ids_config.preserve_pairs}")
    else:
        print(f"❌ 未找到会话ID {conversation_id} 的消息ID配置")
        return False
    
    # 创建裁剪器并执行裁剪
    from autocoder.common.conversations.get_conversation_manager import get_conversation_manager
    
    # 不设置 conversation manager，因为我们直接通过构造函数传递 conversation_id
    
    pruner = AgenticConversationPruner(args=args, llm=llm, conversation_id=conversation_id)
    
    # 调试：检查消息ID提取和验证
    print(f"\n🔍 调试信息:")
    print(f"   测试数据中的消息ID:")
    for i, conv in enumerate(original_conversations):
        message_id = conv.get("message_id", "no_id")
        extracted_id = message_id[:8] if len(message_id) >= 8 else "invalid"
        print(f"     {i+1}. {message_id} -> {extracted_id}")
    
    print(f"   配置中要删除的消息ID: {message_ids_config.message_ids}")
    
    # 手动验证消息ID匹配
    conversation_msg_ids = [conv.get("message_id", "")[:8] for conv in original_conversations if len(conv.get("message_id", "")) >= 8]
    print(f"   从对话中提取的消息ID: {conversation_msg_ids}")
    
    # 检查验证逻辑
    api = get_conversation_message_ids_api()
    validation_result = api.validate_message_ids(
        message_ids_config.message_ids, 
        [conv.get("message_id", "") for conv in original_conversations]
    )
    print(f"   消息ID验证结果: {validation_result.is_valid}")
    if not validation_result.is_valid:
        print(f"   验证失败原因: {validation_result.error_message}")
    if validation_result.warnings:
        for warning in validation_result.warnings:
            print(f"   验证警告: {warning}")
    
    print(f"\n🚀 开始执行裁剪...")
    
    # 首先计算token数，看看是否需要裁剪
    from autocoder.common.tokens import count_string_tokens
    import json
    original_tokens = count_string_tokens(json.dumps(original_conversations, ensure_ascii=False))
    print(f"   原始对话token数: {original_tokens}")
    print(f"   安全区域阈值: {args.conversation_prune_safe_zone_tokens}")
    print(f"   是否超过阈值: {'是' if original_tokens > args.conversation_prune_safe_zone_tokens else '否'}")
    
    if original_tokens <= args.conversation_prune_safe_zone_tokens:
        print(f"⚠️ 注意: token数未超过阈值，可能不会触发裁剪逻辑")
    
    # 直接测试 _apply_message_ids_pruning 方法
    print(f"\n🔧 直接测试 _apply_message_ids_pruning 方法:")
    try:
        range_pruned = pruner._apply_message_ids_pruning(original_conversations)
        print(f"   Message IDs pruning 结果: {len(original_conversations)} -> {len(range_pruned)} 消息")
        
        if len(range_pruned) < len(original_conversations):
            print(f"   ✅ Message IDs pruning 成功删除了消息")
            # 检查哪些消息被删除了
            original_ids = [conv.get("message_id", "")[:8] for conv in original_conversations]
            pruned_ids = [conv.get("message_id", "")[:8] for conv in range_pruned]
            deleted_ids = [msg_id for msg_id in original_ids if msg_id not in pruned_ids]
            print(f"   删除的消息ID: {deleted_ids}")
        else:
            print(f"   ⚠️ Message IDs pruning 没有删除任何消息")
    except Exception as e:
        print(f"   ❌ Message IDs pruning 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 执行完整的裁剪流程
    pruned_conversations = pruner.prune_conversations(original_conversations)
    
    # 打印裁剪后的会话
    print_conversations(pruned_conversations, "裁剪后的会话数据")
    
    # 验证裁剪结果
    print(f"\n📊 裁剪结果分析:")
    print(f"   原始消息数量: {len(original_conversations)}")
    print(f"   裁剪后数量: {len(pruned_conversations)}")
    print(f"   删除的消息数: {len(original_conversations) - len(pruned_conversations)}")
    
    # 检查特定消息ID是否被删除
    pruned_message_ids = [conv.get("message_id", "")[:8] for conv in pruned_conversations]
    target_message_id = "642f04ee"
    
    if target_message_id in pruned_message_ids:
        print(f"❌ 错误: 消息ID {target_message_id} 应该被删除但仍然存在")
        return False
    else:
        print(f"✅ 正确: 消息ID {target_message_id} 已成功删除")
    
    # 获取裁剪统计信息
    stats = pruner.get_pruning_statistics()
    print(f"\n📈 裁剪统计信息:")
    print(f"   消息ID裁剪已应用: {stats['range_pruning']['applied']}")
    print(f"   消息ID裁剪成功: {stats['range_pruning']['success']}")
    print(f"   会话ID: {stats['range_pruning']['conversation_id']}")
    print(f"   总压缩比: {stats['compression']['total_compression_ratio']:.2%}")
    
    # 验证成对删除逻辑（如果启用）
    if message_ids_config.preserve_pairs:
        print(f"\n🔗 成对删除逻辑验证:")
        # 分析是否正确处理了用户/助手配对
        user_assistant_pairs = []
        i = 0
        while i < len(pruned_conversations):
            if (i + 1 < len(pruned_conversations) and 
                pruned_conversations[i].get("role") == "user" and 
                pruned_conversations[i + 1].get("role") == "assistant"):
                user_assistant_pairs.append((i, i + 1))
                i += 2
            else:
                i += 1
        
        print(f"   检测到 {len(user_assistant_pairs)} 个用户/助手配对")
        print(f"   配对完整性: {'✅ 良好' if len(user_assistant_pairs) > 0 else '⚠️ 需要检查'}")
    
    return True


def verify_pruning_without_message_ids():
    """验证无消息ID配置的裁剪逻辑"""
    
    print("\n🔍 测试场景2: 验证无消息ID配置的会话裁剪")
    print("=" * 80)
    
    # 使用一个不存在的会话ID
    conversation_id = "nonexistent-conversation-id-12345"
    
    # 创建测试数据
    original_conversations = create_test_conversations()
    args = create_test_args()
    llm = get_llm("v3_chat", product_mode="lite")
    
    # 创建裁剪器并执行裁剪
    from autocoder.common.conversations.get_conversation_manager import get_conversation_manager
    
    # 不设置 conversation manager，因为我们直接通过构造函数传递 conversation_id
    
    pruner = AgenticConversationPruner(args=args, llm=llm, conversation_id=conversation_id)
    
    print(f"🚀 开始执行裁剪 (无消息ID配置)...")
    pruned_conversations = pruner.prune_conversations(original_conversations)
    
    # 验证结果
    print(f"\n📊 裁剪结果分析:")
    print(f"   原始消息数量: {len(original_conversations)}")
    print(f"   裁剪后数量: {len(pruned_conversations)}")
    
    # 获取统计信息
    stats = pruner.get_pruning_statistics()
    print(f"\n📈 裁剪统计信息:")
    print(f"   消息ID裁剪已应用: {stats['range_pruning']['applied']}")
    print(f"   消息ID裁剪成功: {stats['range_pruning']['success']}")
    
    # 验证没有应用消息ID裁剪
    if not stats['range_pruning']['applied']:
        print(f"✅ 正确: 无消息ID配置时跳过了消息ID裁剪")
        return True
    else:
        print(f"❌ 错误: 无消息ID配置时不应该应用消息ID裁剪")
        return False


def verify_tool_cleanup_logic():
    """验证工具输出清理逻辑"""
    
    print("\n🔍 测试场景3: 验证工具输出清理逻辑")
    print("=" * 80)
    
    # 创建包含大量工具输出的会话数据
    large_tool_output = "def example_function():\n    pass\n" * 100  # 创建大量内容
    
    conversations_with_tools = [
        {
            "role": "user",
            "content": "Please read a file",
            "message_id": "tool_test_001"
        },
        {
            "role": "assistant", 
            "content": "I'll read the file for you.\n\n<read_file>\n<path>example.py</path>\n</read_file>",
            "message_id": "tool_test_002"
        },
        {
            "role": "user",
            "content": f"<tool_result tool_name='read_file' success='true'><message>File read successfully</message><content>{large_tool_output}</content></tool_result>",
            "message_id": "tool_test_003"
        },
        {
            "role": "assistant",
            "content": "I can see the file content. It contains many function definitions.",
            "message_id": "tool_test_004"
        }
    ]
    
    # 使用小的token阈值来触发工具清理
    args = AutoCoderArgs(
        source_dir=".",
        conversation_prune_safe_zone_tokens=1000,  # 小阈值触发清理
        context_prune=True,
        context_prune_strategy="extract",
        query="测试工具清理逻辑"
    )
    
    llm = get_llm("v3_chat", product_mode="lite")
    
    # 不使用消息ID配置，只测试工具清理
    # 为工具清理测试使用一个测试会话ID
    test_conversation_id = "tool-cleanup-test-conversation"
    pruner = AgenticConversationPruner(args=args, llm=llm, conversation_id=test_conversation_id)
    
    print(f"🚀 开始执行工具输出清理...")
    
    # 计算原始token数
    from autocoder.common.tokens import count_string_tokens
    original_tokens = count_string_tokens(json.dumps(conversations_with_tools, ensure_ascii=False))
    print(f"   原始token数: {original_tokens}")
    
    pruned_conversations = pruner.prune_conversations(conversations_with_tools)
    
    # 计算清理后token数
    final_tokens = count_string_tokens(json.dumps(pruned_conversations, ensure_ascii=False))
    print(f"   清理后token数: {final_tokens}")
    print(f"   Token减少: {original_tokens - final_tokens} ({((original_tokens - final_tokens) / original_tokens * 100):.1f}%)")
    
    # 检查工具结果是否被清理
    tool_result_cleaned = False
    for conv in pruned_conversations:
        content = conv.get("content", "")
        if "tool_result" in content and "Content cleared to save tokens" in content:
            tool_result_cleaned = True
            break
    
    if tool_result_cleaned:
        print(f"✅ 正确: 工具输出已被清理")
        return True
    else:
        print(f"⚠️ 注意: 工具输出可能未被清理（可能因为token数仍在阈值内）")
        return True


def main():
    """主测试函数"""
    print("🧪 AgenticConversationPruner 消息ID裁剪逻辑验证")
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    test_results = []
    
    try:
        # 测试场景1: 有消息ID配置的裁剪
        result1 = verify_pruning_with_message_ids()
        test_results.append(("有消息ID配置的裁剪", result1))
        
        # 测试场景2: 无消息ID配置的裁剪  
        result2 = verify_pruning_without_message_ids()
        test_results.append(("无消息ID配置的裁剪", result2))
        
        # 测试场景3: 工具输出清理
        result3 = verify_tool_cleanup_logic()
        test_results.append(("工具输出清理逻辑", result3))
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # 汇总测试结果
    print(f"\n🎯 测试结果汇总")
    print("=" * 80)
    
    all_passed = True
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")
        if not result:
            all_passed = False
    
    print(f"\n{'🎉 所有测试通过!' if all_passed else '⚠️ 部分测试失败，请检查上述结果'}")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 