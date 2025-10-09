"""
会话消息ID裁剪器
实现基于消息ID的会话裁剪算法，支持成对裁剪和简单裁剪两种模式
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from loguru import logger
from .conversation_message_ids_api import get_conversation_message_ids_api
from .conversation_message_ids_manager import ConversationMessageIds


@dataclass
class MessageIdsPruningResult:
    """裁剪结果"""
    success: bool
    pruned_conversations: List[Dict[str, Any]]
    original_length: int
    pruned_length: int
    message_ids_applied: List[str]
    preserve_pairs: bool
    error_message: str = ""
    warnings: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
    
    @property
    def compression_ratio(self) -> float:
        """计算压缩比"""
        if self.original_length == 0:
            return 1.0
        return self.pruned_length / self.original_length
    
    @property
    def messages_removed(self) -> int:
        """计算移除的消息数量"""
        return self.original_length - self.pruned_length


@dataclass
class MessagePair:
    """消息配对信息"""
    user_index: int
    assistant_index: int
    user_message_id: str
    assistant_message_id: str
    pair_start: int
    pair_end: int
    
    def contains_message_id(self, message_id: str) -> bool:
        """检查消息ID是否在配对中"""
        return message_id in [self.user_message_id, self.assistant_message_id]
    
    def get_all_message_ids(self) -> List[str]:
        """获取配对中的所有消息ID"""
        return [self.user_message_id, self.assistant_message_id]


class ConversationMessageIdsPruner:
    """会话消息ID裁剪器"""
    
    def __init__(self):
        """初始化裁剪器"""
        pass
    
    def prune_conversations(
        self, 
        conversations: List[Dict[str, Any]], 
        conversation_message_ids: ConversationMessageIds
    ) -> MessageIdsPruningResult:
        """根据消息ID配置裁剪会话
        
        Args:
            conversations: 原始会话列表
            conversation_message_ids: 消息ID配置
            
        Returns:
            裁剪结果
        """
        try:
            original_length = len(conversations)
            
            if not conversations:
                return MessageIdsPruningResult(
                    success=True,
                    pruned_conversations=[],
                    original_length=0,
                    pruned_length=0,
                    message_ids_applied=[],
                    preserve_pairs=conversation_message_ids.preserve_pairs
                )
            
            # 验证消息ID - 使用API层的验证，允许部分消息ID缺失（适用于agentic_edit等部分对话场景）
            
            api = get_conversation_message_ids_api()
            
            # 正确提取消息ID：需要构造完整ID格式供验证使用
            conversation_msg_ids = []
            for conv in conversations:
                extracted_id = self._extract_message_id(conv)
                if extracted_id is not None:                    
                    conversation_msg_ids.append(extracted_id)                
            validation_result = api.validate_message_ids(
                conversation_message_ids.message_ids, 
                conversation_msg_ids,
                auto_fix=True,
                allow_missing=True  # 允许某些消息ID不存在，只删除存在的
            )
            
            if not validation_result.is_valid:
                return MessageIdsPruningResult(
                    success=False,
                    pruned_conversations=conversations,
                    original_length=original_length,
                    pruned_length=original_length,
                    message_ids_applied=[],
                    preserve_pairs=conversation_message_ids.preserve_pairs,
                    error_message=validation_result.error_message
                )
            
            # 使用验证后的消息ID列表（已过滤掉不存在的ID）
            effective_message_ids = validation_result.normalized_message_ids or []
            
            # 记录验证警告
            if validation_result.warnings:
                logger.info(f"Message IDs validation warnings: {validation_result.warnings}")
            
            # 如果所有消息ID都被过滤掉了，直接返回原对话
            if not effective_message_ids:
                logger.info("No valid message IDs found in conversation, skipping pruning")
                return MessageIdsPruningResult(
                    success=True,
                    pruned_conversations=conversations,
                    original_length=original_length,
                    pruned_length=original_length,
                    message_ids_applied=[],
                    preserve_pairs=conversation_message_ids.preserve_pairs,
                    warnings=validation_result.warnings
                )
            
            # 根据配置选择裁剪策略，使用有效的消息ID列表
            if conversation_message_ids.preserve_pairs:
                result = self._prune_with_pair_preservation(conversations, effective_message_ids)
            else:
                result = self._prune_simple(conversations, effective_message_ids)
            
            # 更新结果信息
            result.original_length = original_length
            result.preserve_pairs = conversation_message_ids.preserve_pairs
            result.message_ids_applied = effective_message_ids
            result.warnings = (result.warnings or []) + (validation_result.warnings or [])
            
            logger.info(f"Message IDs pruning completed: {original_length} -> {result.pruned_length} messages "
                       f"(compression: {result.compression_ratio:.2%})")
            
            return result
            
        except Exception as e:
            error_msg = f"Message IDs pruning failed: {str(e)}"
            logger.error(error_msg)
            return MessageIdsPruningResult(
                success=False,
                pruned_conversations=conversations,
                original_length=len(conversations),
                pruned_length=len(conversations),
                message_ids_applied=[],
                preserve_pairs=conversation_message_ids.preserve_pairs,
                error_message=error_msg
            )
    
    def _prune_with_pair_preservation(
        self, 
        conversations: List[Dict[str, Any]], 
        message_ids_to_delete: List[str]
    ) -> MessageIdsPruningResult:
        """成对裁剪算法 - 保证user/assistant成对"""
        
        try:
            # 1. 分析会话配对结构
            pairs = self._analyze_conversation_pairs(conversations)
            
            # 2. 调整删除列表以保证配对完整性
            adjusted_message_ids, warnings = self._adjust_message_ids_for_pairs(
                message_ids_to_delete, pairs, conversations
            )
            
            # 3. 删除调整后的消息
            pruned_conversations = self._remove_conversations_by_message_ids(
                conversations, adjusted_message_ids
            )
            
            return MessageIdsPruningResult(
                success=True,
                pruned_conversations=pruned_conversations,
                original_length=len(conversations),
                pruned_length=len(pruned_conversations),
                message_ids_applied=adjusted_message_ids,
                preserve_pairs=True,
                warnings=warnings
            )
            
        except Exception as e:
            return MessageIdsPruningResult(
                success=False,
                pruned_conversations=conversations,
                original_length=len(conversations),
                pruned_length=len(conversations),
                message_ids_applied=message_ids_to_delete,
                preserve_pairs=True,
                error_message=f"Pair preservation pruning failed: {str(e)}"
            )
    
    def _prune_simple(
        self, 
        conversations: List[Dict[str, Any]], 
        message_ids_to_delete: List[str]
    ) -> MessageIdsPruningResult:
        """简单裁剪算法 - 直接按消息ID删除"""
        
        try:
            pruned_conversations = self._remove_conversations_by_message_ids(
                conversations, message_ids_to_delete
            )
            
            return MessageIdsPruningResult(
                success=True,
                pruned_conversations=pruned_conversations,
                original_length=len(conversations),
                pruned_length=len(pruned_conversations),
                message_ids_applied=message_ids_to_delete,
                preserve_pairs=False
            )
            
        except Exception as e:
            return MessageIdsPruningResult(
                success=False,
                pruned_conversations=conversations,
                original_length=len(conversations),
                pruned_length=len(conversations),
                message_ids_applied=message_ids_to_delete,
                preserve_pairs=False,
                error_message=f"Simple pruning failed: {str(e)}"
            )
    
    def _analyze_conversation_pairs(self, conversations: List[Dict[str, Any]]) -> List[MessagePair]:
        """分析会话的配对结构
        
        Args:
            conversations: 会话列表
            
        Returns:
            配对信息列表
        """
        pairs = []
        
        i = 0
        while i < len(conversations):
            current_msg = conversations[i]
            current_role = current_msg.get("role", "")
            
            if current_role == "user":
                # 查找对应的assistant消息
                assistant_index = None
                for j in range(i + 1, len(conversations)):
                    if conversations[j].get("role") == "assistant":
                        assistant_index = j
                        break
                
                if assistant_index is not None:
                    # 提取消息ID，确保不为空
                    user_msg_id = self._extract_message_id(conversations[i])
                    assistant_msg_id = self._extract_message_id(conversations[assistant_index])
                    
                    # 只有在两个消息ID都存在时才创建配对
                    if user_msg_id is not None and assistant_msg_id is not None:
                        pair = MessagePair(
                            user_index=i,
                            assistant_index=assistant_index,
                            user_message_id=user_msg_id,
                            assistant_message_id=assistant_msg_id,
                            pair_start=i,
                            pair_end=assistant_index
                        )
                        pairs.append(pair)
                    i = assistant_index + 1  # 跳到下一个可能的user消息
                else:
                    # 没有找到配对的assistant，单独处理这个user消息
                    i += 1
            else:
                # 非user消息，单独处理
                i += 1
        
        logger.debug(f"Found {len(pairs)} conversation pairs in {len(conversations)} messages")
        return pairs
    
    def _adjust_message_ids_for_pairs(
        self, 
        message_ids_to_delete: List[str], 
        pairs: List[MessagePair],
        conversations: List[Dict[str, Any]]
    ) -> tuple[List[str], List[str]]:
        """调整消息ID列表以保证配对完整性
        
        Args:
            message_ids_to_delete: 原始要删除的消息ID列表
            pairs: 配对信息列表
            conversations: 会话列表
            
        Returns:
            (调整后的消息ID列表, 警告信息列表)
        """
        adjusted_message_ids = set(message_ids_to_delete)
        warnings = []
        
        # 检查每个配对
        for pair in pairs:
            user_id = pair.user_message_id
            assistant_id = pair.assistant_message_id
            
            user_to_delete = user_id in adjusted_message_ids
            assistant_to_delete = assistant_id in adjusted_message_ids
            
            # 如果只删除配对中的一个消息，需要调整
            if user_to_delete and not assistant_to_delete:
                # 用户消息要删除但助手消息不删除，添加助手消息到删除列表
                adjusted_message_ids.add(assistant_id)
                warnings.append(f"为保持配对完整性，同时删除助手消息 {assistant_id}")
            elif assistant_to_delete and not user_to_delete:
                # 助手消息要删除但用户消息不删除，添加用户消息到删除列表
                adjusted_message_ids.add(user_id)
                warnings.append(f"为保持配对完整性，同时删除用户消息 {user_id}")
        
        return list(adjusted_message_ids), warnings
    
    def _remove_conversations_by_message_ids(
        self, 
        conversations: List[Dict[str, Any]], 
        message_ids_to_delete: List[str]
    ) -> List[Dict[str, Any]]:
        """根据消息ID删除会话，返回剩余的会话
        
        Args:
            conversations: 原始会话列表
            message_ids_to_delete: 要删除的消息ID列表
            
        Returns:
            删除指定消息ID后剩余的会话列表
        """
        if not message_ids_to_delete:
            return conversations  # 没有要删除的消息ID，返回所有会话
        
        remaining = []
        
        # 创建要删除的消息ID集合（用于快速查找）
        delete_ids = set(message_ids_to_delete)
        
        # 按顺序提取未被删除的会话
        for conv in conversations:
            msg_id = self._extract_message_id(conv)
            if msg_id not in delete_ids:
                remaining.append(conv)
        
        return remaining
    
    def _extract_message_id(self, conversation: Dict[str, Any]) -> Optional[str]:
        """从会话中提取消息ID（前8个字符）
        
        Args:
            conversation: 会话字典
            
        Returns:
            消息ID（前8个字符）
        """
        # 方法1: 直接从message_id字段获取
        message_id = conversation.get("message_id", "")
        if isinstance(message_id, str) and len(message_id) >= 8:
            return message_id[:8]
        
        # 方法2: 从content中提取hint格式的message_id
        # 格式：[[message_id: 12345678]] 或 message_id: 12345678
        content = conversation.get("content", "")
        if isinstance(content, str):
            import re
            # 匹配 [[message_id: xxxxxxxx]] 格式
            pattern1 = r'\[\[message_id:\s*([a-fA-F0-9]{8})\]\]'
            match1 = re.search(pattern1, content)
            if match1:
                return match1.group(1).lower()
            
            # 匹配 message_id: xxxxxxxx 格式（用于兼容性）
            pattern2 = r'message_id:\s*([a-fA-F0-9]{8})'
            match2 = re.search(pattern2, content)
            if match2:
                return match2.group(1).lower()
                
        return None
    
    def preview_pruning(
        self, 
        conversations: List[Dict[str, Any]], 
        conversation_message_ids: ConversationMessageIds
    ) -> Dict[str, Any]:
        """预览裁剪结果（不实际执行裁剪）
        
        Args:
            conversations: 原始会话列表
            conversation_message_ids: 消息ID配置
            
        Returns:
            预览信息字典
        """
        original_length = len(conversations)
        
        if not conversations:
            return {
                "original_length": 0,
                "estimated_length": 0,
                "compression_ratio": 1.0,
                "message_ids_to_apply": [],
                "preserve_pairs": conversation_message_ids.preserve_pairs,
                "valid": True,
                "warnings": []
            }
        
        # 验证消息ID - 过滤掉None值
        conversation_msg_ids = []
        for conv in conversations:
            msg_id = self._extract_message_id(conv)
            if msg_id is not None:
                conversation_msg_ids.append(msg_id)
        is_valid, error_msg = conversation_message_ids.validate_message_ids(conversation_msg_ids)
        if not is_valid:
            return {
                "original_length": original_length,
                "estimated_length": original_length,
                "compression_ratio": 1.0,
                "message_ids_to_apply": conversation_message_ids.message_ids,
                "preserve_pairs": conversation_message_ids.preserve_pairs,
                "valid": False,
                "error_message": error_msg,
                "warnings": []
            }
        
        # 计算预估的裁剪结果
        message_ids_to_apply = conversation_message_ids.message_ids
        warnings = []
        
        if conversation_message_ids.preserve_pairs:
            pairs = self._analyze_conversation_pairs(conversations)
            message_ids_to_apply, warnings = self._adjust_message_ids_for_pairs(
                conversation_message_ids.message_ids, pairs, conversations
            )
        
        # 计算要删除的消息数量
        delete_ids = set(message_ids_to_apply)
        delete_count = sum(1 for conv in conversations 
                          if self._extract_message_id(conv) in delete_ids)
        
        estimated_length = original_length - delete_count
        compression_ratio = estimated_length / original_length if original_length > 0 else 1.0
        
        return {
            "original_length": original_length,
            "estimated_length": estimated_length,
            "compression_ratio": compression_ratio,
            "message_ids_to_apply": message_ids_to_apply,
            "preserve_pairs": conversation_message_ids.preserve_pairs,
            "valid": True,
            "warnings": warnings,
            "delete_message_ids": list(delete_ids)
        } 