"""
Conversation Message IDs Read Tool Resolver

This resolver handles reading existing conversation message IDs configurations.
It retrieves the current message IDs settings for the active conversation.
"""

import os
from typing import Optional
from autocoder.common.v2.agent.agentic_edit_tools.base_tool_resolver import BaseToolResolver
from autocoder.common.v2.agent.agentic_edit_types import ConversationMessageIdsReadTool, ToolResult
from autocoder.common import AutoCoderArgs
from autocoder.common.pruner import get_conversation_message_ids_api
from loguru import logger
import typing

if typing.TYPE_CHECKING:
    from autocoder.common.v2.agent.agentic_edit import AgenticEdit


class ConversationMessageIdsReadToolResolver(BaseToolResolver):
    """
    Resolver for the ConversationMessageIdsReadTool.
    
    This resolver handles reading existing conversation message IDs configurations
    to show which messages are currently configured for deletion.
    """
    
    def __init__(self, agent: 'AgenticEdit', tool: ConversationMessageIdsReadTool, args: AutoCoderArgs):
        super().__init__(agent, tool, args)
        self.tool = tool

    def resolve(self) -> ToolResult:
        """
        Read conversation message IDs configuration.
        
        Returns:
            ToolResult with configuration details or information about no configuration
        """
        try:
            # Get current conversation ID            
            conversation_id = self.agent.conversation_config.conversation_id
            
            if not conversation_id:
                return ToolResult(
                    success=False,
                    message="无法获取当前会话ID",
                    content={
                        "error_type": "no_conversation_id",
                        "has_message_ids_config": False,
                        "message": "当前没有活跃的会话，无法读取消息ID配置"
                    }
                )
            
            # Get message IDs API
            message_ids_api = get_conversation_message_ids_api(
                storage_dir=self.args.range_storage_dir if hasattr(self.args, 'range_storage_dir') else None
            )
            
            # Get message IDs configuration for current conversation
            message_ids_obj = message_ids_api.get_conversation_message_ids(conversation_id)
            
            if message_ids_obj:
                # Get detailed statistics
                stats = message_ids_api.get_message_ids_statistics(conversation_id)
                
                # Get message details with content preview
                message_details = self._get_message_details_with_content(conversation_id, message_ids_obj.message_ids)
                
                return ToolResult(
                    success=True,
                    message=f"找到会话 {conversation_id} 的消息ID配置",
                    content={
                        "conversation_id": conversation_id,
                        "has_message_ids_config": True,
                        "message_ids": message_details,
                        "description": message_ids_obj.description,
                        "preserve_pairs": message_ids_obj.preserve_pairs,
                        "created_at": message_ids_obj.created_at,
                        "updated_at": message_ids_obj.updated_at,
                        "statistics": stats,
                        "summary": f"当前配置了 {len(message_ids_obj.message_ids)} 个消息ID用于删除。配对保护: {'启用' if message_ids_obj.preserve_pairs else '禁用'}。"
                    }
                )
            else:
                # No configuration found
                # List all available configurations for reference
                all_configs = message_ids_api.list_all_message_ids()
                available_conversation_ids = [config.conversation_id for config in all_configs]
                
                return ToolResult(
                    success=True,
                    message=f"会话 {conversation_id} 没有消息ID配置",
                    content={
                        "conversation_id": conversation_id,
                        "has_message_ids_config": False,
                        "message_ids": [],
                        "description": "",
                        "preserve_pairs": True,
                        "available_configurations": len(all_configs),
                        "available_conversation_ids": available_conversation_ids[:10],  # 限制显示前10个
                        "summary": "当前会话没有配置删除消息ID。如需配置，请使用 conversation_message_ids_write 工具。"
                    }
                )
                
        except Exception as e:
            error_msg = f"读取会话消息ID配置时发生异常: {str(e)}"
            logger.error(error_msg)
            return ToolResult(
                success=False,
                message=error_msg,
                content={
                    "error_type": "exception",
                    "has_message_ids_config": False,
                    "error_message": str(e),
                    "conversation_id": getattr(self, '_conversation_id', 'unknown')
                }
            )
    
    def _get_message_details_with_content(self, conversation_id: str, message_ids: list) -> list:
        """
        获取消息ID对应的详细信息，包含消息内容前100个字符，按原始顺序排列
        
        Args:
            conversation_id: 会话ID
            message_ids: 消息ID列表
            
        Returns:
            包含消息详情的列表，每个元素包含id和content_preview字段
        """
        try:
            # 获取会话管理器
            from autocoder.common.conversations.get_conversation_manager import get_conversation_manager
            conversation_manager = get_conversation_manager()
            
            # 获取会话中的所有消息
            all_messages = conversation_manager.get_messages(conversation_id)
            
            # 创建消息ID到消息的映射，保持原始顺序
            message_map = {}
            for msg in all_messages:
                msg_id = msg.get('message_id', '')
                if msg_id:
                    # 截取前8个字符用于匹配
                    short_id = msg_id[:8]
                    message_map[short_id] = {
                        'full_id': msg_id,
                        'content': msg.get('content', ''),
                        'role': msg.get('role', ''),
                        'timestamp': msg.get('timestamp', 0),
                        'index': len(message_map)  # 保存原始顺序索引
                    }
            
            # 构建结果列表，保持配置中的顺序，但按conversation中的原始顺序排序
            message_details = []
            matched_messages = []
            
            for config_id in message_ids:
                if config_id in message_map:
                    msg_info = message_map[config_id]
                    matched_messages.append({
                        'config_id': config_id,
                        'msg_info': msg_info,
                        'original_index': msg_info['index']
                    })
                else:
                    # 如果消息ID不存在，仍然显示但标记为未找到
                    message_details.append({
                        'id': config_id,
                        'content_preview': '[消息未找到]',
                        'role': 'unknown',
                        'status': 'not_found'
                    })
            
            # 按原始顺序排序匹配到的消息
            matched_messages.sort(key=lambda x: x['original_index'])
            
            # 构建最终结果
            for match in matched_messages:
                config_id = match['config_id']
                msg_info = match['msg_info']
                content = msg_info['content']
                
                # 处理不同类型的content
                if isinstance(content, str):
                    content_preview = content[:100]
                elif isinstance(content, (dict, list)):
                    # 将复杂对象转换为字符串再截取
                    import json
                    try:
                        content_str = json.dumps(content, ensure_ascii=False)
                        content_preview = content_str[:100]
                    except:
                        content_preview = str(content)[:100]
                else:
                    content_preview = str(content)[:100]
                
                # 如果内容被截断，添加省略号
                if len(str(content)) > 100:
                    content_preview += "..."
                
                message_details.append({
                    'id': config_id,
                    'content_preview': content_preview,
                    'role': msg_info['role'],
                    'status': 'found'
                })
            
            return message_details
            
        except Exception as e:
            logger.error(f"获取消息详情时发生错误: {str(e)}")
            # 如果出错，返回基本的ID列表
            return [{'id': msg_id, 'content_preview': '[获取内容失败]', 'role': 'unknown', 'status': 'error'} for msg_id in message_ids]
