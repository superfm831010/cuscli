"""
会话消息ID管理器
用于管理会话中的消息ID删除功能
"""

import os
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from loguru import logger


@dataclass
class ConversationMessageIds:
    """会话消息ID数据模型"""
    conversation_id: str                    # 会话ID (来自conversations模块)
    message_ids: List[str]                 # 要删除的消息ID列表 (使用前8个字符)
    created_at: str                        # 创建时间
    updated_at: str                        # 更新时间
    description: str = ""                  # 描述信息
    preserve_pairs: bool = True            # 是否保证user/assistant成对裁剪
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ConversationMessageIds':
        """从字典创建实例"""
        return cls(
            conversation_id=data['conversation_id'],
            message_ids=data['message_ids'],
            created_at=data['created_at'],
            updated_at=data['updated_at'],
            description=data.get('description', ''),
            preserve_pairs=data.get('preserve_pairs', True)
        )
    
    def remove_duplicate_ids(self) -> None:
        """移除重复的消息ID，保持顺序"""
        seen = set()
        unique_ids = []
        for msg_id in self.message_ids:
            if msg_id not in seen:
                seen.add(msg_id)
                unique_ids.append(msg_id)
        self.message_ids = unique_ids
        
    def validate_message_ids(self, conversation_message_ids: List[str]) -> tuple[bool, str]:
        """验证消息ID有效性
        
        Args:
            conversation_message_ids: 对话中所有消息的ID列表
            
        Returns:
            (是否有效, 错误信息)
        """
        if not self.message_ids:
            return False, "消息ID列表不能为空"
        
        # 创建有效ID集合 (取前8个字符)
        valid_ids = {msg_id[:8] for msg_id in conversation_message_ids}
        
        # 检查每个要删除的ID是否存在
        for i, msg_id in enumerate(self.message_ids):
            if not isinstance(msg_id, str):
                return False, f"消息ID {i+1}: ID必须是字符串"
                
            if len(msg_id) != 8:
                return False, f"消息ID {i+1}: ID长度必须是8个字符"
                
            if msg_id not in valid_ids:
                return False, f"消息ID {i+1}: '{msg_id}' 在对话中不存在"
        
        return True, ""
    
    def get_total_message_count(self) -> int:
        """计算要删除的消息总数"""
        self.remove_duplicate_ids()
        return len(self.message_ids)


class ConversationMessageIdsManager:
    """会话消息ID管理器"""
    
    def __init__(self, storage_dir: Optional[str] = None):
        """初始化管理器
        
        Args:
            storage_dir: 存储目录，默认为.auto-coder/pruner/conversations
        """
        if storage_dir is None:
            self.storage_dir = os.path.join(
                os.getcwd(), 
                '.auto-coder', 
                'pruner', 
                'conversations'
            )
        else:
            self.storage_dir = storage_dir
            
        # 确保存储目录存在
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # 消息ID信息存储文件
        self.message_ids_file = os.path.join(self.storage_dir, 'conversation_message_ids.json')
        self.backup_dir = os.path.join(self.storage_dir, 'backup')
        os.makedirs(self.backup_dir, exist_ok=True)
        
    def save_message_ids(self, conversation_id: str, message_ids: List[str], 
                        description: str = "", preserve_pairs: bool = True) -> ConversationMessageIds:
        """保存会话消息ID
        
        Args:
            conversation_id: 会话ID
            message_ids: 要删除的消息ID列表
            description: 描述信息
            preserve_pairs: 是否保证user/assistant成对裁剪
            
        Returns:
            ConversationMessageIds实例
        """
        now = datetime.now().isoformat()
        
        # 创建新的消息ID对象
        message_ids_data = ConversationMessageIds(
            conversation_id=conversation_id,
            message_ids=message_ids,
            created_at=now,
            updated_at=now,
            description=description,
            preserve_pairs=preserve_pairs
        )
        
        # 移除重复ID
        message_ids_data.remove_duplicate_ids()
        
        # 读取现有数据
        storage_data = self._load_storage_data()
        
        # 查找是否已存在该会话的消息ID配置
        existing_index = -1
        for i, existing_config in enumerate(storage_data['message_configs']):
            if existing_config['conversation_id'] == conversation_id:
                existing_index = i
                break
        
        # 更新或添加配置
        if existing_index >= 0:
            # 更新现有配置，保留原创建时间
            original_created_at = storage_data['message_configs'][existing_index].get('created_at', now)
            message_ids_data.created_at = original_created_at
            storage_data['message_configs'][existing_index] = message_ids_data.to_dict()
            logger.info(f"Updated message IDs for conversation {conversation_id}")
        else:
            # 添加新配置
            storage_data['message_configs'].append(message_ids_data.to_dict())
            logger.info(f"Added new message IDs for conversation {conversation_id}")
        
        # 更新最后修改时间
        storage_data['last_updated'] = now
        
        # 创建备份
        self._create_backup()
        
        # 保存到文件
        with open(self.message_ids_file, 'w', encoding='utf-8') as f:
            json.dump(storage_data, f, ensure_ascii=False, indent=2)
            
        return message_ids_data
    
    def get_message_ids(self, conversation_id: str) -> Optional[ConversationMessageIds]:
        """获取会话的消息ID配置
        
        Args:
            conversation_id: 会话ID
            
        Returns:
            ConversationMessageIds实例或None
        """
        storage_data = self._load_storage_data()
        
        # 查找指定会话的消息ID配置
        for config_dict in storage_data['message_configs']:
            if config_dict['conversation_id'] == conversation_id:
                return ConversationMessageIds.from_dict(config_dict)
                
        return None
    
    def get_all_message_ids(self) -> List[ConversationMessageIds]:
        """获取所有会话消息ID配置
        
        Returns:
            会话消息ID配置列表
        """
        storage_data = self._load_storage_data()
        return [ConversationMessageIds.from_dict(data) for data in storage_data['message_configs']]
    
    def delete_message_ids(self, conversation_id: str) -> bool:
        """删除会话的消息ID配置
        
        Args:
            conversation_id: 会话ID
            
        Returns:
            是否删除成功
        """
        storage_data = self._load_storage_data()
        
        # 过滤掉指定会话的配置
        original_count = len(storage_data['message_configs'])
        storage_data['message_configs'] = [config for config in storage_data['message_configs'] 
                                         if config['conversation_id'] != conversation_id]
        
        if len(storage_data['message_configs']) < original_count:
            # 创建备份
            self._create_backup()
            
            # 更新最后修改时间
            storage_data['last_updated'] = datetime.now().isoformat()
            
            # 保存更新后的数据
            with open(self.message_ids_file, 'w', encoding='utf-8') as f:
                json.dump(storage_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Deleted message IDs for conversation {conversation_id}")
            return True
            
        return False
    
    def list_conversation_ids(self) -> List[str]:
        """列出所有已配置消息ID的会话ID
        
        Returns:
            会话ID列表
        """
        storage_data = self._load_storage_data()
        return [config['conversation_id'] for config in storage_data['message_configs']]
    
    def validate_conversation_message_ids(self, conversation_id: str, 
                                        conversation_message_ids: List[str]) -> tuple[bool, str]:
        """验证指定会话的消息ID配置
        
        Args:
            conversation_id: 会话ID
            conversation_message_ids: 对话中所有消息的ID列表
            
        Returns:
            (是否有效, 错误信息)
        """
        message_ids_data = self.get_message_ids(conversation_id)
        if not message_ids_data:
            return False, f"未找到会话 {conversation_id} 的消息ID配置"
            
        return message_ids_data.validate_message_ids(conversation_message_ids)
    
    def _load_storage_data(self) -> Dict:
        """加载存储数据"""
        if not os.path.exists(self.message_ids_file):
            return {
                "version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "message_configs": []
            }
            
        try:
            with open(self.message_ids_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 确保数据格式正确
            if 'message_configs' not in data:
                data['message_configs'] = []
            if 'version' not in data:
                data['version'] = "1.0"
            if 'last_updated' not in data:
                data['last_updated'] = datetime.now().isoformat()
                
            return data
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Failed to load message IDs data: {e}")
            return {
                "version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "message_configs": []
            }
    
    def _create_backup(self) -> None:
        """创建备份文件"""
        if not os.path.exists(self.message_ids_file):
            return
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(self.backup_dir, f"message_ids_backup_{timestamp}.json")
            
            # 复制当前文件作为备份
            import shutil
            shutil.copy2(self.message_ids_file, backup_file)
            
            # 只保留最近10个备份文件
            self._cleanup_old_backups()
            
            logger.debug(f"Created backup: {backup_file}")
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
    
    def _cleanup_old_backups(self, max_backups: int = 10) -> None:
        """清理旧的备份文件"""
        try:
            backup_files = []
            for file in os.listdir(self.backup_dir):
                if file.startswith('message_ids_backup_') and file.endswith('.json'):
                    file_path = os.path.join(self.backup_dir, file)
                    backup_files.append((file_path, os.path.getmtime(file_path)))
            
            # 按修改时间排序，保留最新的
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # 删除多余的备份文件
            for file_path, _ in backup_files[max_backups:]:
                os.remove(file_path)
                logger.debug(f"Removed old backup: {file_path}")
                
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")


# 全局单例管理器
_conversation_message_ids_manager = None


def get_conversation_message_ids_manager(storage_dir: Optional[str] = None) -> ConversationMessageIdsManager:
    """获取全局单例会话消息ID管理器
    
    Args:
        storage_dir: 存储目录
        
    Returns:
        ConversationMessageIdsManager实例
    """
    global _conversation_message_ids_manager
    
    if _conversation_message_ids_manager is None:
        _conversation_message_ids_manager = ConversationMessageIdsManager(storage_dir)
        
    return _conversation_message_ids_manager 