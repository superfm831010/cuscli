"""
索引管理器实现

提供对话索引管理功能，支持快速查询、搜索和过滤。
"""

import os
import json
import time
from typing import Optional, List, Dict, Any
from pathlib import Path

from typing import Optional, List, Dict, Any
from pathlib import Path


class IndexManager:
    """索引管理器，用于管理对话索引"""
    
    def __init__(self, index_path: str):
        """
        初始化索引管理器
        
        Args:
            index_path: 索引目录路径
        """
        self.index_path = Path(index_path)
        self.index_file = self.index_path / "conversations.idx"
        self.config_file = self.index_path / "config.json"
        self.lock_file = self.index_path / "index.lock"
        
        self._ensure_index_directory()
        self._load_index()
        self._load_config()
    
    def _ensure_index_directory(self):
        """确保索引目录存在"""
        self.index_path.mkdir(parents=True, exist_ok=True)
    
    def _load_index(self):
        """加载索引数据"""
        try:
            if self.index_file.exists():
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    self._index_data = json.load(f)
            else:
                self._index_data = {}
        except (json.JSONDecodeError, OSError, IOError):
            # 如果索引损坏，重建空索引
            self._index_data = {}
    
    def _load_config(self):
        """加载配置数据"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config_data = json.load(f)
            else:
                self._config_data = {}
        except (json.JSONDecodeError, OSError, IOError):
            # 如果配置损坏，重建空配置
            self._config_data = {}
        
        # 规范化配置：避免在 JSON 中使用 None 作为键（会被序列化为字符串 "null"）
        # 将默认命名空间的当前对话仅存储在 legacy 字段 current_conversation_id 中
        namespaced = self._config_data.get('namespaced_current_conversations')
        if isinstance(namespaced, dict):
            # 将可能存在的 "null" 或 None 键迁移到 current_conversation_id，并从映射中移除
            migrated_default = False
            default_keys = []
            for key in list(namespaced.keys()):
                if key is None or key == "null":
                    if not migrated_default and namespaced.get(key) is not None:
                        # 仅在未设置 legacy 字段时迁移
                        if self._config_data.get('current_conversation_id') is None:
                            self._config_data['current_conversation_id'] = namespaced.get(key)
                    default_keys.append(key)
            for k in default_keys:
                del namespaced[k]
            if default_keys:
                self._config_data['namespaced_current_conversations'] = namespaced
    
    def _save_index(self) -> bool:
        """
        保存索引数据
        
        Returns:
            bool: 保存成功返回True
        """
        try:
            # 使用临时文件进行原子写入
            temp_file = self.index_file.with_suffix('.tmp')
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self._index_data, f, ensure_ascii=False, indent=2)
            
            # 原子重命名
            temp_file.replace(self.index_file)
            return True
            
        except (OSError, IOError):
            return False
    
    def _save_config(self) -> bool:
        """
        保存配置数据
        
        Returns:
            bool: 保存成功返回True
        """
        try:
            # 使用临时文件进行原子写入
            temp_file = self.config_file.with_suffix('.tmp')
            
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self._config_data, f, ensure_ascii=False, indent=2)
            
            # 原子重命名
            temp_file.replace(self.config_file)
            return True
            
        except (OSError, IOError):
            return False
    
    def set_current_conversation(self, conversation_id: Optional[str], namespace: Optional[str] = None) -> bool:
        """
        设置当前对话ID
        
        Args:
            conversation_id: 对话ID，None表示清除当前对话
            namespace: 命名空间，None表示默认命名空间
            
        Returns:
            bool: 设置成功返回True
        """
        try:
            # 重新加载配置以获取最新数据
            self._load_config()
            
            # 确保 namespaced_current_conversations 字段存在
            if 'namespaced_current_conversations' not in self._config_data:
                self._config_data['namespaced_current_conversations'] = {}
            namespaced = self._config_data['namespaced_current_conversations']

            # 设置或清除当前对话ID
            if conversation_id is None:
                # 清除
                if namespace is None:
                    # 默认命名空间：仅使用向后兼容字段
                    self._config_data.pop('current_conversation_id', None)
                    # 兼容历史：移除可能存在的 None/"null" 键
                    if None in namespaced:
                        del namespaced[None]
                    if 'null' in namespaced:
                        del namespaced['null']
                else:
                    # 指定命名空间
                    if namespace in namespaced:
                        del namespaced[namespace]
            else:
                # 设置
                if namespace is None:
                    # 默认命名空间：仅设置 legacy 字段，避免在 JSON 中出现 "null" 键
                    self._config_data['current_conversation_id'] = conversation_id
                    # 兼容清理：移除可能存在的 None/"null" 键
                    if None in namespaced:
                        del namespaced[None]
                    if 'null' in namespaced:
                        del namespaced['null']
                else:
                    # 指定命名空间
                    namespaced[namespace] = conversation_id
            
            # 更新时间戳
            self._config_data['last_updated'] = time.time()
            
            # 保存配置
            return self._save_config()
            
        except Exception:
            return False
    
    def get_current_conversation_id(self, namespace: Optional[str] = None) -> Optional[str]:
        """
        获取当前对话ID
        
        Args:
            namespace: 命名空间，None表示默认命名空间
            
        Returns:
            Optional[str]: 当前对话ID，未设置返回None
        """
        try:
            # 重新加载配置以获取最新数据
            self._load_config()
            
            # 默认命名空间：使用向后兼容字段
            if namespace is None:
                return self._config_data.get('current_conversation_id')
            
            # 指定命名空间：从 namespaced_current_conversations 中获取
            namespaced_conversations = self._config_data.get('namespaced_current_conversations', {})
            return namespaced_conversations.get(namespace)
            
            return None
            
        except Exception:
            return None
    
    def clear_current_conversation(self, namespace: Optional[str] = None) -> bool:
        """
        清除当前对话设置
        
        Args:
            namespace: 命名空间，None表示默认命名空间
            
        Returns:
            bool: 清除成功返回True
        """
        return self.set_current_conversation(None, namespace)
    
    def add_conversation(self, conversation_metadata: Dict[str, Any]) -> bool:
        """
        添加对话到索引
        
        Args:
            conversation_metadata: 对话元数据
            
        Returns:
            bool: 添加成功返回True
        """
        if not conversation_metadata.get('conversation_id'):
            return False
        
        conversation_id = conversation_metadata['conversation_id']
        
        try:
            # 重新加载索引以获取最新数据
            self._load_index()
            
            # 添加或更新对话元数据
            self._index_data[conversation_id] = conversation_metadata.copy()
            
            # 保存索引
            return self._save_index()
            
        except Exception:
            return False
    
    def update_conversation(self, conversation_metadata: Dict[str, Any]) -> bool:
        """
        更新索引中的对话
        
        Args:
            conversation_metadata: 对话元数据
            
        Returns:
            bool: 更新成功返回True
        """
        if not conversation_metadata.get('conversation_id'):
            return False
        
        conversation_id = conversation_metadata['conversation_id']
        
        try:
            # 重新加载索引以获取最新数据
            self._load_index()
            
            # 检查对话是否存在
            if conversation_id not in self._index_data:
                return False
            
            # 更新对话元数据
            self._index_data[conversation_id] = conversation_metadata.copy()
            
            # 保存索引
            return self._save_index()
            
        except Exception:
            return False
    
    def remove_conversation(self, conversation_id: str) -> bool:
        """
        从索引中删除对话
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            bool: 删除成功返回True
        """
        try:
            # 重新加载索引以获取最新数据
            self._load_index()
            
            # 检查对话是否存在
            if conversation_id not in self._index_data:
                return False
            
            # 删除对话
            del self._index_data[conversation_id]
            
            # 保存索引
            return self._save_index()
            
        except Exception:
            return False
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        从索引获取对话信息
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            Optional[Dict[str, Any]]: 对话元数据，不存在返回None
        """
        try:
            # 重新加载索引以获取最新数据
            self._load_index()
            
            return self._index_data.get(conversation_id)
            
        except Exception:
            return None
    
    def conversation_exists(self, conversation_id: str) -> bool:
        """
        检查对话是否在索引中存在
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            bool: 存在返回True
        """
        return self.get_conversation(conversation_id) is not None
    
    def list_conversations(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        sort_by: str = 'updated_at',
        sort_order: str = 'desc'
    ) -> List[Dict[str, Any]]:
        """
        列出对话
        
        Args:
            limit: 限制返回数量
            offset: 偏移量
            sort_by: 排序字段
            sort_order: 排序顺序 ('asc' 或 'desc')
            
        Returns:
            List[Dict[str, Any]]: 对话元数据列表
        """
        try:
            # 重新加载索引以获取最新数据
            self._load_index()
            
            # 获取所有对话
            conversations = list(self._index_data.values())
            
            # 排序
            reverse = (sort_order.lower() == 'desc')
            
            if sort_by == 'name':
                conversations.sort(
                    key=lambda x: x.get('name', ''),
                    reverse=reverse
                )
            elif sort_by == 'created_at':
                conversations.sort(
                    key=lambda x: x.get('created_at', 0),
                    reverse=reverse
                )
            elif sort_by == 'updated_at':
                conversations.sort(
                    key=lambda x: x.get('updated_at', 0),
                    reverse=reverse
                )
            
            # 应用分页
            if limit is not None:
                return conversations[offset:offset + limit]
            else:
                return conversations[offset:]
                
        except Exception:
            return []
    
    def search_conversations(
        self,
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索对话
        
        Args:
            query: 搜索查询字符串
            filters: 过滤条件
            
        Returns:
            List[Dict[str, Any]]: 匹配的对话元数据列表
        """
        try:
            # 重新加载索引以获取最新数据
            self._load_index()
            
            conversations = list(self._index_data.values())
            results = []
            
            for conv in conversations:
                # 文本搜索
                if query:
                    query_lower = query.lower()
                    name_match = query_lower in conv.get('name', '').lower()
                    desc_match = query_lower in conv.get('description', '').lower()
                    
                    if not (name_match or desc_match):
                        continue
                
                # 应用过滤器
                if filters:
                    match = True
                    
                    # 时间范围过滤
                    # created_after: 大于等于这个时间的记录
                    if 'created_after' in filters:
                        created_at = conv.get('created_at', 0)
                        if created_at < filters['created_after']:
                            match = False
                    
                    # created_before: 小于这个时间的记录（不包含边界）
                    if 'created_before' in filters:
                        created_at = conv.get('created_at', float('inf'))
                        if created_at >= filters['created_before']:
                            match = False
                    
                    # 消息数量过滤
                    if 'min_message_count' in filters:
                        message_count = conv.get('message_count', 0)
                        if message_count < filters['min_message_count']:
                            match = False
                    
                    if 'max_message_count' in filters:
                        message_count = conv.get('message_count', float('inf'))
                        if message_count > filters['max_message_count']:
                            match = False
                    
                    if not match:
                        continue
                
                results.append(conv)
            
            # 按相关性或更新时间排序
            results.sort(
                key=lambda x: x.get('updated_at', 0),
                reverse=True
            )
            
            return results
            
        except Exception:
            return []
    
    def list_namespaces(self) -> List[Optional[str]]:
        """
        列出所有已使用的命名空间
        
        Returns:
            List[Optional[str]]: 命名空间列表，None 表示默认命名空间
        """
        try:
            # 重新加载配置以获取最新数据
            self._load_config()
            
            namespaces: List[Optional[str]] = []
            namespaced_conversations = self._config_data.get('namespaced_current_conversations', {})
            
            # 添加所有已配置的命名空间
            for namespace in namespaced_conversations.keys():
                # 忽略历史遗留的 None/"null" 键
                if namespace is None or namespace == 'null':
                    continue
                namespaces.append(namespace)
            
            # 如果存在旧的 current_conversation_id，添加默认命名空间
            if (self._config_data.get('current_conversation_id') is not None and
                None not in namespaces):
                namespaces.append(None)
            
            return namespaces
            
        except Exception:
            return []
    
    def get_all_current_conversations(self) -> Dict[Optional[str], str]:
        """
        获取所有命名空间的当前对话ID
        
        Returns:
            Dict[Optional[str], str]: 命名空间到对话ID的映射
        """
        try:
            # 重新加载配置以获取最新数据
            self._load_config()
            
            result: Dict[Optional[str], str] = {}
            namespaced_conversations = self._config_data.get('namespaced_current_conversations', {})
            
            # 添加所有已配置的命名空间对话
            for namespace, conversation_id in namespaced_conversations.items():
                # 忽略历史遗留的 None/"null" 键
                if namespace is None or namespace == 'null':
                    continue
                if conversation_id is not None:
                    result[namespace] = conversation_id
            
            # 默认命名空间（向后兼容字段）
            if self._config_data.get('current_conversation_id') is not None:
                result[None] = self._config_data['current_conversation_id']
            
            return result
            
        except Exception:
            return {}
