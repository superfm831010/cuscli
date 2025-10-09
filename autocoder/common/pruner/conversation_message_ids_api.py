"""
会话消息ID管理API
提供高级的会话消息ID管理接口，包括验证、错误处理和便捷方法
"""

import re
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass
from loguru import logger

from .conversation_message_ids_manager import (
    ConversationMessageIdsManager, 
    ConversationMessageIds, 
    get_conversation_message_ids_manager
)


@dataclass
class MessageIdsValidationResult:
    """消息ID验证结果"""
    is_valid: bool
    error_message: str = ""
    warnings: Optional[List[str]] = None
    normalized_message_ids: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.normalized_message_ids is None:
            self.normalized_message_ids = []


@dataclass
class MessageIdsParseResult:
    """消息ID解析结果"""
    success: bool
    message_ids: Optional[List[str]] = None
    error_message: str = ""
    
    def __post_init__(self):
        if self.message_ids is None:
            self.message_ids = []


class ConversationMessageIdsAPI:
    """会话消息ID管理API - 高级接口"""
    
    def __init__(self, storage_dir: Optional[str] = None):
        """初始化API
        
        Args:
            storage_dir: 存储目录，如果为None则使用默认目录
        """
        self.manager = get_conversation_message_ids_manager(storage_dir)
    
    def save_conversation_message_ids(
        self, 
        conversation_id: str, 
        message_ids: Union[List[str], str], 
        description: str = "",
        preserve_pairs: bool = True,
        conversation_message_ids: Optional[List[str]] = None
    ) -> tuple[bool, str, Optional[ConversationMessageIds]]:
        """保存或更新会话消息ID
        
        Args:
            conversation_id: 会话ID
            message_ids: 消息ID列表或消息ID字符串 (如 "9226b3a4,204e1cd8")
            description: 描述信息
            preserve_pairs: 是否保证user/assistant成对裁剪
            conversation_message_ids: 对话中所有消息的ID列表（用于验证）
            
        Returns:
            (是否成功, 错误信息, ConversationMessageIds对象)
        """
        try:
            # 解析消息ID
            if isinstance(message_ids, str):
                parse_result = self.parse_message_ids_string(message_ids)
                if not parse_result.success:
                    return False, parse_result.error_message, None
                message_ids_list = parse_result.message_ids or []
            else:
                message_ids_list = message_ids
            
            # 验证消息ID
            if conversation_message_ids is not None:
                validation_result = self.validate_message_ids(message_ids_list, conversation_message_ids)
                if not validation_result.is_valid:
                    return False, validation_result.error_message, None
                if validation_result.normalized_message_ids:
                    message_ids_list = validation_result.normalized_message_ids
            
            # 保存消息ID
            message_ids_obj = self.manager.save_message_ids(
                conversation_id=conversation_id,
                message_ids=message_ids_list,
                description=description,
                preserve_pairs=preserve_pairs
            )
            
            logger.info(f"Successfully saved message IDs for conversation {conversation_id}: {message_ids_list}")
            return True, "", message_ids_obj
            
        except Exception as e:
            error_msg = f"Failed to save conversation message IDs: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None
    
    def get_conversation_message_ids(self, conversation_id: str) -> Optional[ConversationMessageIds]:
        """获取会话消息ID
        
        Args:
            conversation_id: 会话ID
            
        Returns:
            ConversationMessageIds对象或None
        """
        return self.manager.get_message_ids(conversation_id)
    
    def delete_conversation_message_ids(self, conversation_id: str) -> tuple[bool, str]:
        """删除会话消息ID
        
        Args:
            conversation_id: 会话ID
            
        Returns:
            (是否成功, 错误信息)
        """
        try:
            success = self.manager.delete_message_ids(conversation_id)
            if success:
                logger.info(f"Successfully deleted message IDs for conversation {conversation_id}")
                return True, ""
            else:
                return False, f"No message IDs found for conversation {conversation_id}"
        except Exception as e:
            error_msg = f"Failed to delete conversation message IDs: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def list_all_message_ids(self) -> List[ConversationMessageIds]:
        """列出所有会话消息ID
        
        Returns:
            会话消息ID列表
        """
        return self.manager.get_all_message_ids()
    
    def list_conversation_ids(self) -> List[str]:
        """列出所有已配置消息ID的会话ID
        
        Returns:
            会话ID列表
        """
        return self.manager.list_conversation_ids()
    
    def validate_message_ids(
        self, 
        message_ids: List[str], 
        conversation_message_ids: List[str],
        auto_fix: bool = True,
        allow_missing: bool = True
    ) -> MessageIdsValidationResult:
        """验证消息ID有效性
        
        Args:
            message_ids: 要删除的消息ID列表
            conversation_message_ids: 对话中所有消息的ID列表
            auto_fix: 是否自动修复一些问题
            allow_missing: 是否允许某些消息ID不存在（用于部分对话场景）
            
        Returns:
            验证结果
        """
        result = MessageIdsValidationResult(is_valid=True)
        
        if not message_ids:
            result.is_valid = False
            result.error_message = "消息ID列表不能为空"
            return result
        
        normalized_ids = []
        warnings = []
        
        # 创建有效ID集合 (取前8个字符)
        valid_ids = {msg_id[:8] for msg_id in conversation_message_ids}
        
        for i, msg_id in enumerate(message_ids):
            # 类型检查
            if not isinstance(msg_id, str):
                result.is_valid = False
                result.error_message = f"消息ID {i+1}: ID必须是字符串"
                return result
            
            # 长度检查和自动修复
            if len(msg_id) < 8:
                result.is_valid = False
                result.error_message = f"消息ID {i+1}: ID长度必须至少8个字符"
                return result
            elif len(msg_id) > 8:
                if auto_fix:
                    msg_id = msg_id[:8]
                    warnings.append(f"消息ID {i+1}: 自动截取前8个字符")
                else:
                    result.is_valid = False
                    result.error_message = f"消息ID {i+1}: ID长度超过8个字符"
                    return result
            
            # 有效性检查
            if msg_id not in valid_ids:
                if allow_missing:
                    # 允许缺失模式：跳过不存在的消息ID，给出警告
                    warnings.append(f"消息ID {i+1}: '{msg_id}' 在对话中不存在，已跳过")
                    continue
                else:
                    # 严格模式：任何不存在的消息ID都导致验证失败
                    result.is_valid = False
                    result.error_message = f"消息ID {i+1}: '{msg_id}' 在对话中不存在"
                    return result
            
            normalized_ids.append(msg_id)
        
        # 移除重复ID
        if auto_fix:
            seen = set()
            unique_ids = []
            for msg_id in normalized_ids:
                if msg_id not in seen:
                    seen.add(msg_id)
                    unique_ids.append(msg_id)
            
            if len(unique_ids) < len(normalized_ids):
                warnings.append(f"自动移除重复的消息ID: {len(normalized_ids)} -> {len(unique_ids)}")
                normalized_ids = unique_ids
        
        result.warnings = warnings
        result.normalized_message_ids = normalized_ids
        return result
    
    def parse_message_ids_string(self, message_ids_string: str) -> MessageIdsParseResult:
        """解析消息ID字符串
        
        Args:
            message_ids_string: 消息ID字符串，如 "9226b3a4,204e1cd8,1f3a5b7c"
            
        Returns:
            解析结果
        """
        try:
            message_ids = []
            
            # 去除空白字符
            message_ids_string = message_ids_string.strip()
            
            if not message_ids_string:
                return MessageIdsParseResult(
                    success=False,
                    error_message="消息ID字符串不能为空"
                )
            
            # 分割多个消息ID (支持逗号和分号分隔)
            id_parts = re.split(r'[,;]', message_ids_string)
            
            for i, part in enumerate(id_parts):
                part = part.strip()
                if not part:
                    continue                                                
                message_ids.append(part.lower())  # 统一转为小写
            
            return MessageIdsParseResult(
                success=True,
                message_ids=message_ids
            )
            
        except Exception as e:
            return MessageIdsParseResult(
                success=False,
                error_message=f"解析消息ID字符串失败: {str(e)}"
            )
    
    def format_message_ids_to_string(self, message_ids: List[str]) -> str:
        """将消息ID列表格式化为字符串
        
        Args:
            message_ids: 消息ID列表
            
        Returns:
            格式化后的字符串
        """
        return ",".join(message_ids)
    
    def get_message_ids_statistics(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """获取消息ID统计信息
        
        Args:
            conversation_id: 会话ID
            
        Returns:
            统计信息字典或None
        """
        message_ids_obj = self.get_conversation_message_ids(conversation_id)
        if not message_ids_obj:
            return None
        
        total_count = message_ids_obj.get_total_message_count()
        
        return {
            "conversation_id": conversation_id,
            "total_message_ids": len(message_ids_obj.message_ids),
            "unique_message_ids": total_count,
            "message_ids": message_ids_obj.message_ids,
            "preserve_pairs": message_ids_obj.preserve_pairs,
            "description": message_ids_obj.description,
            "created_at": message_ids_obj.created_at,
            "updated_at": message_ids_obj.updated_at
        }
    
    def export_message_ids_to_dict(self) -> Dict[str, Any]:
        """导出所有消息ID为字典格式
        
        Returns:
            包含所有消息ID的字典
        """
        all_message_ids = self.list_all_message_ids()
        return {
            "version": "1.0",
            "total_configs": len(all_message_ids),
            "message_configs": [config.to_dict() for config in all_message_ids]
        }
    
    def import_message_ids_from_dict(self, data: Dict[str, Any]) -> tuple[bool, str, int]:
        """从字典导入消息ID配置
        
        Args:
            data: 包含消息ID数据的字典
            
        Returns:
            (是否成功, 错误信息, 成功导入的数量)
        """
        try:
            if "message_configs" not in data:
                return False, "数据格式错误: 缺少 'message_configs' 字段", 0
            
            success_count = 0
            
            for config_data in data["message_configs"]:
                try:
                    message_ids_obj = ConversationMessageIds.from_dict(config_data)
                    self.manager.save_message_ids(
                        conversation_id=message_ids_obj.conversation_id,
                        message_ids=message_ids_obj.message_ids,
                        description=message_ids_obj.description,
                        preserve_pairs=message_ids_obj.preserve_pairs
                    )
                    success_count += 1
                except Exception as e:
                    logger.warning(f"Failed to import message IDs for conversation {config_data.get('conversation_id', 'unknown')}: {e}")
            
            return True, f"成功导入 {success_count} 个消息ID配置", success_count
            
        except Exception as e:
            error_msg = f"导入消息ID配置失败: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, 0


# 全局API实例
_conversation_message_ids_api = None


def get_conversation_message_ids_api(storage_dir: Optional[str] = None) -> ConversationMessageIdsAPI:
    """获取全局会话消息ID API实例
    
    Args:
        storage_dir: 存储目录
        
    Returns:
        ConversationMessageIdsAPI实例
    """
    global _conversation_message_ids_api
    
    if _conversation_message_ids_api is None:
        _conversation_message_ids_api = ConversationMessageIdsAPI(storage_dir)
        
    return _conversation_message_ids_api 