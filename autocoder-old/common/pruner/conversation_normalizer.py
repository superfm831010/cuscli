
"""
Conversation Normalizer

This module provides tools to normalize conversation structures by ensuring
user/assistant role pairs are properly balanced. It offers two strategies:
merge and delete for handling unpaired messages.
"""

from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from pydantic import BaseModel
from loguru import logger
from autocoder.common.international.message_manager import get_message


class NormalizationStrategy(Enum):
    """规整化策略枚举"""
    MERGE = "merge"      # 合并连续的相同角色消息
    DELETE = "delete"    # 删除多余的消息，保留第一个


class NormalizationResult(BaseModel):
    """规整化结果"""
    normalized_conversations: List[Dict[str, Any]]
    original_count: int
    normalized_count: int
    changes_made: List[Dict[str, Any]]
    strategy_used: str
    
    
class ConversationNormalizer:
    """
    会话规整化工具类
    
    检查conversations内部user/assistant角色是否成对出现，
    如果不是成对出现，提供两种策略：
    1. merge: 合并连续的相同角色消息
    2. delete: 删除多余的消息，只保留第一个
    
    示例：
    输入: [user, user, assistant] 
    - merge策略: [merged_user, assistant]
    - delete策略: [first_user, assistant]
    """
    
    def __init__(self, default_strategy: NormalizationStrategy = NormalizationStrategy.MERGE):
        """
        初始化规整化器
        
        Args:
            default_strategy: 默认策略
        """
        self.default_strategy = default_strategy
        
    def normalize_conversations(
        self, 
        conversations: List[Dict[str, Any]], 
        strategy: Optional[NormalizationStrategy] = None
    ) -> NormalizationResult:
        """
        规整化会话列表
        
        Args:
            conversations: 原始会话列表
            strategy: 规整化策略，如果为None则使用默认策略
            
        Returns:
            NormalizationResult: 规整化结果
        """
        if strategy is None:
            strategy = self.default_strategy
            
        logger.info(f"开始规整化会话，策略: {strategy.value}, 原始消息数: {len(conversations)}")
        
        # 验证输入
        if not conversations:
            return NormalizationResult(
                normalized_conversations=[],
                original_count=0,
                normalized_count=0,
                changes_made=[],
                strategy_used=strategy.value
            )
        
        # 执行规整化
        if strategy == NormalizationStrategy.MERGE:
            result = self._merge_strategy(conversations)
        elif strategy == NormalizationStrategy.DELETE:
            result = self._delete_strategy(conversations)
        else:
            raise ValueError(f"不支持的策略: {strategy}")
            
        logger.info(f"规整化完成，原始: {result.original_count}, 规整化后: {result.normalized_count}, 变更: {len(result.changes_made)}")
        
        return result
    
    def _merge_strategy(self, conversations: List[Dict[str, Any]]) -> NormalizationResult:
        """
        合并策略实现
        
        连续的相同角色消息会被合并成一个消息
        """
        normalized = []
        changes_made = []
        
        i = 0
        while i < len(conversations):
            current_msg = conversations[i].copy()
            current_role = current_msg.get("role", "")
            
            # 查找连续的相同角色消息
            consecutive_messages = [current_msg]
            j = i + 1
            
            while j < len(conversations) and conversations[j].get("role", "") == current_role:
                consecutive_messages.append(conversations[j])
                j += 1
            
            # 如果有多个连续消息，进行合并
            if len(consecutive_messages) > 1:
                merged_content = self._merge_message_contents(consecutive_messages)
                merged_msg = {
                    "role": current_role,
                    "content": merged_content
                }
                
                # 保留其他字段（如果有的话）
                for key, value in current_msg.items():
                    if key not in ["role", "content"]:
                        merged_msg[key] = value
                
                normalized.append(merged_msg)
                
                # 记录变更
                changes_made.append({
                    "action": "merge",
                    "original_indices": list(range(i, j)),
                    "original_messages": consecutive_messages,
                    "merged_message": merged_msg,
                    "merged_count": len(consecutive_messages)
                })
            else:
                # 单个消息直接添加
                normalized.append(current_msg)
            
            i = j
        
        return NormalizationResult(
            normalized_conversations=normalized,
            original_count=len(conversations),
            normalized_count=len(normalized),
            changes_made=changes_made,
            strategy_used=NormalizationStrategy.MERGE.value
        )
    
    def _delete_strategy(self, conversations: List[Dict[str, Any]]) -> NormalizationResult:
        """
        删除策略实现
        
        连续的相同角色消息只保留第一个，删除其余的
        """
        normalized = []
        changes_made = []
        
        i = 0
        while i < len(conversations):
            current_msg = conversations[i].copy()
            current_role = current_msg.get("role", "")
            
            # 添加第一个消息
            normalized.append(current_msg)
            
            # 查找连续的相同角色消息
            consecutive_messages = [current_msg]
            j = i + 1
            
            while j < len(conversations) and conversations[j].get("role", "") == current_role:
                consecutive_messages.append(conversations[j])
                j += 1
            
            # 如果有多个连续消息，记录删除操作
            if len(consecutive_messages) > 1:
                deleted_messages = consecutive_messages[1:]  # 除了第一个之外的所有消息
                
                changes_made.append({
                    "action": "delete",
                    "kept_index": i,
                    "kept_message": current_msg,
                    "deleted_indices": list(range(i + 1, j)),
                    "deleted_messages": deleted_messages,
                    "deleted_count": len(deleted_messages)
                })
            
            i = j
        
        return NormalizationResult(
            normalized_conversations=normalized,
            original_count=len(conversations),
            normalized_count=len(normalized),
            changes_made=changes_made,
            strategy_used=NormalizationStrategy.DELETE.value
        )
    
    def _merge_message_contents(self, messages: List[Dict[str, Any]]) -> str:
        """
        合并多个消息的内容
        
        Args:
            messages: 要合并的消息列表
            
        Returns:
            合并后的内容字符串
        """
        contents = []
        
        for i, msg in enumerate(messages):
            content = msg.get("content", "")
            if content.strip():
                # 为每个消息添加序号标识
                if len(messages) > 1:
                    contents.append(f"[消息 {i+1}] {content}")
                else:
                    contents.append(content)
        
        return "\n\n".join(contents)
    
    def analyze_conversation_structure(self, conversations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析会话结构
        
        Args:
            conversations: 会话列表
            
        Returns:
            结构分析结果
        """
        if not conversations:
            return {
                "total_messages": 0,
                "role_distribution": {},
                "consecutive_groups": [],
                "needs_normalization": False,
                "issues": []
            }
        
        role_distribution = {}
        consecutive_groups = []
        issues = []
        
        # 统计角色分布
        for msg in conversations:
            role = msg.get("role", "unknown")
            role_distribution[role] = role_distribution.get(role, 0) + 1
        
        # 分析连续组
        current_group = {"role": conversations[0].get("role", ""), "count": 1, "start_index": 0}
        
        for i in range(1, len(conversations)):
            role = conversations[i].get("role", "")
            if role == current_group["role"]:
                current_group["count"] += 1
            else:
                if current_group["count"] > 1:
                    consecutive_groups.append(current_group.copy())
                current_group = {"role": role, "count": 1, "start_index": i}
        
        # 添加最后一组
        if current_group["count"] > 1:
            consecutive_groups.append(current_group)
        
        # 检查是否需要规整化
        needs_normalization = len(consecutive_groups) > 0
        
        # 收集问题
        if needs_normalization:
            for group in consecutive_groups:
                issues.append(f"连续的 {group['count']} 个 '{group['role']}' 消息从索引 {group['start_index']} 开始")
        
        # 检查是否以user开始
        if conversations and conversations[0].get("role") != "user":
            issues.append(f"会话不是以 'user' 角色开始，而是 '{conversations[0].get('role')}'")
        
        # 检查是否以assistant结束
        if conversations and conversations[-1].get("role") != "assistant":
            issues.append(f"会话不是以 'assistant' 角色结束，而是 '{conversations[-1].get('role')}'")
        
        return {
            "total_messages": len(conversations),
            "role_distribution": role_distribution,
            "consecutive_groups": consecutive_groups,
            "needs_normalization": needs_normalization,
            "issues": issues
        }
    
    def validate_normalized_conversation(self, conversations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        验证规整化后的会话是否符合预期
        
        Args:
            conversations: 规整化后的会话列表
            
        Returns:
            验证结果
        """
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "structure_info": {}
        }
        
        if not conversations:
            validation_result["warnings"].append("会话列表为空")
            return validation_result
        
        # 检查是否还有连续的相同角色
        for i in range(len(conversations) - 1):
            current_role = conversations[i].get("role", "")
            next_role = conversations[i + 1].get("role", "")
            
            if current_role == next_role:
                validation_result["is_valid"] = False
                validation_result["errors"].append(f"索引 {i} 和 {i+1} 处仍有连续的 '{current_role}' 角色")
        
        # 检查角色交替模式
        expected_pattern = True
        for i in range(len(conversations)):
            role = conversations[i].get("role", "")
            if i % 2 == 0:  # 偶数索引应该是user
                if role != "user":
                    expected_pattern = False
                    validation_result["warnings"].append(f"索引 {i} 期望 'user' 但得到 '{role}'")
            else:  # 奇数索引应该是assistant
                if role != "assistant":
                    expected_pattern = False
                    validation_result["warnings"].append(f"索引 {i} 期望 'assistant' 但得到 '{role}'")
        
        validation_result["structure_info"] = {
            "follows_user_assistant_pattern": expected_pattern,
            "total_messages": len(conversations),
            "starts_with_user": conversations[0].get("role") == "user" if conversations else False,
            "ends_with_assistant": conversations[-1].get("role") == "assistant" if conversations else False
        }
        
        return validation_result

