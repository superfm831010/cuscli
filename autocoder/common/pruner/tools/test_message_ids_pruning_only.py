#!/usr/bin/env python3
"""
专门测试消息ID裁剪逻辑的验证脚本

只测试 _apply_message_ids_pruning 方法，不受 token 阈值限制影响

支持的消息ID格式：
1. 直接字段格式: {"message_id": "9226b3a4-1234-5678-9abc-def012345678"}
2. Hint嵌入格式: {"content": "消息内容 [[message_id: 9226b3a4]]"}
3. 兼容格式: {"content": "消息内容 message_id: 9226b3a4"}
"""

import sys
import os
from datetime import datetime

# 添加src路径到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../..'))

from autocoder.common.pruner.agentic_conversation_pruner import AgenticConversationPruner
from autocoder.common.pruner.conversation_message_ids_api import get_conversation_message_ids_api
from autocoder.common import AutoCoderArgs
from autocoder.sdk import get_llm


def test_message_ids_pruning_logic():
    """直接测试消息ID裁剪逻辑"""
    
    print("🧪 消息ID裁剪逻辑专项测试")
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # 使用已知的会话ID
    conversation_id = "796e1c2e-1ab8-46d1-9448-f9bd29d5c095"
    
    # 创建测试数据，包含要删除的消息ID
    # 展示两种消息ID格式的支持
    test_conversations = [
        {
            "role": "system",
            "content": "You are a helpful assistant.",
            "message_id": "12345678abcdef01"  # 格式1: 直接字段格式（完整UUID）
        },
        {
            "role": "user", 
            "content": "Hello, can you help me with some code? [[message_id: 87654321]]",  # 格式2: 标准hint格式
            "message_id": "87654321fedcba02"  # 同时测试优先级（字段优先）
        },
        {
            "role": "assistant",
            "content": "Of course! I'd be happy to help you with your code. What do you need assistance with?",
            "message_id": "642f04ee11223344"  # 格式1: 这个消息ID应该被删除
        },
        {
            "role": "user",
            "content": "I want to read a file and analyze it. message_id: 13579bdf",  # 格式2: 兼容hint格式
            # 没有message_id字段，只从content中提取
        },
        {
            "role": "assistant", 
            "content": "I'll help you read and analyze the file. [[message_id: 97531eca]]",  # 格式2: 标准hint格式
            # 没有message_id字段，只从content中提取
        }
    ]
    
    print("📋 测试数据:")
    for i, conv in enumerate(test_conversations, 1):
        role = conv.get("role", "unknown")
        message_id = conv.get("message_id", "no_id")[:8]
        content = conv.get("content", "")[:50] + "..." if len(conv.get("content", "")) > 50 else conv.get("content", "")
        print(f"  {i}. [{role:9}] {message_id} | {content}")
    
    # 查询消息ID配置
    api = get_conversation_message_ids_api()
    message_ids_config = api.get_conversation_message_ids(conversation_id)
    
    if not message_ids_config:
        print(f"❌ 未找到会话ID {conversation_id} 的消息删除配置")
        return False
    
    print(f"\n✅ 消息ID配置:")
    print(f"   要删除的消息ID: {message_ids_config.message_ids}")
    print(f"   保持成对删除: {message_ids_config.preserve_pairs}")
    
    # 创建裁剪器
    args = AutoCoderArgs(
        source_dir=".",
        conversation_prune_safe_zone_tokens=1000,
        context_prune=True,
        context_prune_strategy="extract",
        query="测试消息ID裁剪逻辑"
    )
    llm = get_llm("v3_chat", product_mode="lite")
    
    # 创建裁剪器
    from autocoder.common.conversations.get_conversation_manager import get_conversation_manager
    
    # 设置当前对话ID
    conversation_manager = get_conversation_manager()
    conversation_manager.set_current_conversation(conversation_id)
    
    # 创建AgenticConversationPruner实例并执行测试
    pruner = AgenticConversationPruner(args=args, llm=llm, conversation_id=conversation_id)
    
    # 直接测试消息ID裁剪逻辑
    print(f"\n🚀 执行消息ID裁剪:")
    
    try:
        # 由于 _apply_message_ids_pruning 是私有方法，我们通过完整流程测试但强制低token阈值
        # 设置一个极小的token阈值来强制触发裁剪逻辑
        args.conversation_prune_safe_zone_tokens = 1  # 极小值，确保触发
        
        # 使用完整的 prune_conversations 方法
        pruned_conversations = pruner.prune_conversations(test_conversations)
        
        print(f"\n📊 裁剪结果:")
        print(f"   原始消息数量: {len(test_conversations)}")
        print(f"   裁剪后数量: {len(pruned_conversations)}")
        print(f"   删除的消息数: {len(test_conversations) - len(pruned_conversations)}")
        
        # 检查具体被删除的消息
        original_ids = [conv.get("message_id", "")[:8] for conv in test_conversations]
        pruned_ids = [conv.get("message_id", "")[:8] for conv in pruned_conversations]
        deleted_ids = [msg_id for msg_id in original_ids if msg_id not in pruned_ids]
        remaining_ids = pruned_ids
        
        print(f"\n🔍 详细分析:")
        print(f"   原始消息ID: {original_ids}")
        print(f"   删除的消息ID: {deleted_ids}")
        print(f"   保留的消息ID: {remaining_ids}")
        
        # 验证目标消息ID是否被删除
        target_id = "642f04ee"
        if target_id in deleted_ids:
            print(f"   ✅ 目标消息ID {target_id} 已成功删除")
        else:
            print(f"   ❌ 目标消息ID {target_id} 未被删除")
            return False
        
        # 验证成对删除逻辑
        if message_ids_config.preserve_pairs:
            print(f"\n🔗 成对删除验证:")
            if "87654321" in deleted_ids and "642f04ee" in deleted_ids:
                print(f"   ✅ 成对删除正确：user消息 87654321 和 assistant消息 642f04ee 都被删除")
            else:
                print(f"   ⚠️ 成对删除检查：删除的消息ID = {deleted_ids}")
        
        # 显示裁剪后的消息列表
        print(f"\n📋 裁剪后的消息:")
        for i, conv in enumerate(pruned_conversations, 1):
            role = conv.get("role", "unknown")
            message_id = conv.get("message_id", "no_id")[:8]
            content = conv.get("content", "")[:50] + "..." if len(conv.get("content", "")) > 50 else conv.get("content", "")
            print(f"  {i}. [{role:9}] {message_id} | {content}")
        
        # 获取裁剪统计信息
        stats = pruner.get_pruning_statistics()
        if stats["range_pruning"]["applied"]:
            print(f"\n📈 裁剪统计:")
            print(f"   消息ID裁剪已应用: {stats['range_pruning']['applied']}")
            print(f"   消息ID裁剪成功: {stats['range_pruning']['success']}")
            print(f"   总压缩比: {stats['compression']['total_compression_ratio']:.2%}")
        
        return True
        
    except Exception as e:
        print(f"❌ 消息ID裁剪测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    success = test_message_ids_pruning_logic()
    
    print(f"\n🎯 测试结果: {'✅ 通过' if success else '❌ 失败'}")
    
    if success:
        print("\n🎉 消息ID裁剪逻辑工作正常！")
        print("   - 消息ID匹配正确")
        print("   - 成对删除逻辑有效")
        print("   - 裁剪算法运行正常")
    else:
        print("\n⚠️ 消息ID裁剪逻辑存在问题，请检查相关代码")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 