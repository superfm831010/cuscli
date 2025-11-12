#!/usr/bin/env python3
"""
会话消息ID配置查询工具

命令行工具，用于查询和显示指定会话ID的消息删除配置信息。

消息ID格式支持：
    1. 直接字段格式: {"message_id": "9226b3a4-1234-5678-9abc-def012345678"}
    2. Hint嵌入格式: {"content": "消息内容 [[message_id: 9226b3a4]]"}
    3. 兼容格式: {"content": "消息内容 message_id: 9226b3a4"}

用法示例:
    python -m autocoder.common.pruner.tools.query_message_ids --conversation-id 796e1c2e-1ab8-46d1-9448-f9bd29d5c095
    python -m autocoder.common.pruner.tools.query_message_ids -c 796e1c2e-1ab8-46d1-9448-f9bd29d5c095 --verbose
    python -m autocoder.common.pruner.tools.query_message_ids --list-all
"""

import argparse
import sys
import json
from datetime import datetime
from typing import Optional

from ..conversation_message_ids_api import get_conversation_message_ids_api


def format_timestamp(timestamp: str) -> str:
    """格式化时间戳显示"""
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return timestamp


def print_separator(char: str = "=", length: int = 80):
    """打印分隔线"""
    print(char * length)


def print_section_header(title: str):
    """打印节标题"""
    print()
    print(f"📋 {title}:")


def query_conversation_message_ids(conversation_id: str, verbose: bool = False):
    """查询并打印指定会话ID的消息删除配置"""
    
    print(f"🔍 查询会话ID: {conversation_id}")
    print_separator()
    
    try:
        # 获取API实例
        api = get_conversation_message_ids_api()
        
        # 获取消息ID配置
        message_ids_config = api.get_conversation_message_ids(conversation_id)
        
        if not message_ids_config:
            print(f"❌ 未找到会话ID '{conversation_id}' 的消息删除配置")
            return False
        
        print(f"✅ 找到会话ID '{conversation_id}' 的消息删除配置")
        
        # 基本信息
        print_section_header("基本信息")
        print(f"  会话ID: {message_ids_config.conversation_id}")
        print(f"  描述: {message_ids_config.description or '无描述'}")
        print(f"  保持成对删除: {'是' if message_ids_config.preserve_pairs else '否'}")
        print(f"  创建时间: {format_timestamp(message_ids_config.created_at)}")
        print(f"  更新时间: {format_timestamp(message_ids_config.updated_at)}")
        
        # 消息ID列表
        print_section_header("要删除的消息ID列表")
        if message_ids_config.message_ids:
            for i, msg_id in enumerate(message_ids_config.message_ids, 1):
                print(f"  {i:2d}. {msg_id}")
            print(f"\n📊 总计: {len(message_ids_config.message_ids)} 个消息ID")
        else:
            print("  (无消息ID)")
        
        # 获取统计信息
        if verbose:
            stats = api.get_message_ids_statistics(conversation_id)
            if stats:
                print_section_header("详细统计信息")
                print(f"  配置的消息ID数量: {stats['total_message_ids']}")
                print(f"  唯一消息ID数量: {stats['unique_message_ids']}")
                print(f"  保持成对删除: {'是' if stats['preserve_pairs'] else '否'}")
                print(f"  创建时间: {format_timestamp(stats['created_at'])}")
                print(f"  更新时间: {format_timestamp(stats['updated_at'])}")
        
        # JSON格式输出
        if verbose:
            print_section_header("完整配置 (JSON格式)")
            config_dict = message_ids_config.to_dict()
            print(json.dumps(config_dict, ensure_ascii=False, indent=2))
        
        return True
        
    except Exception as e:
        print(f"❌ 查询过程中发生错误: {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()
        return False


def list_all_conversations(verbose: bool = False):
    """列出所有已配置的会话ID"""
    
    print("📋 所有已配置消息删除的会话列表")
    print_separator()
    
    try:
        api = get_conversation_message_ids_api()
        
        # 获取所有会话ID
        conversation_ids = api.list_conversation_ids()
        
        if not conversation_ids:
            print("❌ 未找到任何已配置消息删除的会话")
            return False
        
        print(f"✅ 找到 {len(conversation_ids)} 个已配置的会话:")
        print()
        
        # 列出每个会话的基本信息
        for i, conv_id in enumerate(conversation_ids, 1):
            config = api.get_conversation_message_ids(conv_id)
            if config:
                print(f"  {i:2d}. {conv_id}")
                if verbose:
                    print(f"      描述: {config.description or '无描述'}")
                    print(f"      消息ID数量: {len(config.message_ids)}")
                    print(f"      创建时间: {format_timestamp(config.created_at)}")
                    print(f"      保持成对删除: {'是' if config.preserve_pairs else '否'}")
                    print()
        
        if not verbose:
            print(f"\n💡 使用 --verbose 参数查看详细信息")
        
        return True
        
    except Exception as e:
        print(f"❌ 列表查询过程中发生错误: {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()
        return False


def export_all_configs(output_file: Optional[str] = None, verbose: bool = False):
    """导出所有消息ID配置"""
    
    print("📤 导出所有消息ID配置")
    print_separator()
    
    try:
        api = get_conversation_message_ids_api()
        
        # 导出数据
        export_data = api.export_message_ids_to_dict()
        
        if output_file:
            # 导出到文件
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            print(f"✅ 已导出 {export_data['total_configs']} 个配置到文件: {output_file}")
        else:
            # 打印到控制台
            print(f"✅ 共 {export_data['total_configs']} 个配置:")
            print(json.dumps(export_data, ensure_ascii=False, indent=2))
        
        return True
        
    except Exception as e:
        print(f"❌ 导出过程中发生错误: {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="会话消息ID配置查询工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 查询特定会话的消息删除配置
  %(prog)s --conversation-id 796e1c2e-1ab8-46d1-9448-f9bd29d5c095
  
  # 详细查询（包含JSON输出）
  %(prog)s -c 796e1c2e-1ab8-46d1-9448-f9bd29d5c095 --verbose
  
  # 列出所有已配置的会话
  %(prog)s --list-all
  
  # 详细列出所有会话
  %(prog)s --list-all --verbose
  
  # 导出所有配置到文件
  %(prog)s --export --output configs.json
        """
    )
    
    # 互斥的主要操作选项
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument(
        '-c', '--conversation-id',
        type=str,
        help='要查询的会话ID'
    )
    action_group.add_argument(
        '--list-all',
        action='store_true',
        help='列出所有已配置消息删除的会话'
    )
    action_group.add_argument(
        '--export',
        action='store_true',
        help='导出所有消息ID配置'
    )
    
    # 辅助选项
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='显示详细信息（包含JSON格式输出）'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='导出文件路径（仅在使用 --export 时有效）'
    )
    
    args = parser.parse_args()
    
    # 打印工具标题和时间戳
    print("🔍 会话消息ID配置查询工具")
    print(f"📅 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = False
    
    if args.conversation_id:
        # 查询特定会话
        success = query_conversation_message_ids(args.conversation_id, args.verbose)
    elif args.list_all:
        # 列出所有会话
        success = list_all_conversations(args.verbose)
    elif args.export:
        # 导出配置
        success = export_all_configs(args.output, args.verbose)
    
    # 根据结果设置退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 