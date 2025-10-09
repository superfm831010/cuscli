"""
文件变更管理器

整个模块的主入口，提供高层次的API接口，用于应用、记录和撤销文件变更。
"""

import os
import uuid
import logging
import difflib
import time
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from autocoder.common.file_checkpoint.models import (
    FileChange, ChangeRecord, ApplyResult, UndoResult, DiffResult
)
from autocoder.common.file_checkpoint.backup import FileBackupManager
from autocoder.common.file_checkpoint.store import FileChangeStore
from autocoder.common.file_checkpoint.conversation_checkpoint import ConversationCheckpointStore,ConversationCheckpoint

logger = logging.getLogger(__name__)


def _generate_checkpoint_id(input_string: str) -> str:
    """
    根据输入字符串生成安全的checkpoint_id
    
    Args:
        input_string: 输入字符串（通常是change_group_id或文件路径）
        
    Returns:
        str: MD5哈希生成的checkpoint_id
    """
    if not input_string:
        return str(uuid.uuid4())
    
    # 使用MD5生成固定长度的哈希值
    return hashlib.md5(input_string.encode('utf-8')).hexdigest()


class FileChangeManager:
    """文件变更管理器，提供高层次的API接口"""
    
    def __init__(self, project_dir: str, backup_dir: Optional[str] = None, 
                 store_dir: Optional[str] = None, max_history: int = 50,
                 conversation_store_dir: Optional[str] = None):
        """
        初始化文件变更管理器
        
        Args:
            project_dir: 用户项目的根目录
            backup_dir: 备份文件存储目录，默认为用户主目录下的.autocoder/backups
            store_dir: 变更记录存储目录，默认为用户主目录下的.autocoder/changes
            max_history: 最大保存的历史版本数量
            conversation_store_dir: 对话检查点存储目录
        """
        self.project_dir = os.path.abspath(project_dir)
        self.backup_manager = FileBackupManager(backup_dir)
        self.change_store = FileChangeStore(store_dir, max_history)
        
        # 初始化对话检查点存储
        if conversation_store_dir is None and store_dir is not None:
            # 默认在变更记录存储目录的同级目录创建 conversation_checkpoints 目录
            parent_dir = os.path.dirname(store_dir)
            conversation_store_dir = os.path.join(parent_dir, "conversation_checkpoints")
        
        # 让异常直接抛出，确保 conversation_store 始终可用
        self.conversation_store = ConversationCheckpointStore(conversation_store_dir, max_history)
        logger.info(f"对话检查点存储初始化成功: {conversation_store_dir}")
    
    def apply_changes_with_conversation(self, changes: Dict[str, FileChange], 
                                   conversation_id: str,
                                   first_message_id: Optional[str] = None,
                                   last_message_id: Optional[str] = None,
                                   change_group_id: Optional[str] = None,
                                   metadata: Optional[Dict[str, Any]] = None) -> ApplyResult:
        """
        应用文件变更并保存对话状态
        
        Args:
            changes: 文件变更字典，格式为 {file_path: FileChange}
            conversation_id: 对话会话ID
            first_message_id: 对话消息区间起始ID
            last_message_id: 对话消息区间结束ID
            change_group_id: 变更组ID，用于将相关变更归为一组
            metadata: 元数据，可包含额外信息
            
        Returns:
            ApplyResult: 应用结果对象
        """
        # 记录原始的change_group_id是否为None
        original_group_id_is_none = change_group_id is None
        
        # 应用文件变更
        result = self.apply_changes(changes, change_group_id)
        
        if result.success:
            try:                
                # 创建并保存对话检查点 
                # 生成安全的checkpoint_id（使用MD5哈希）
                if not original_group_id_is_none:
                    # 用户提供了group_id，使用MD5哈希
                    checkpoint_id = _generate_checkpoint_id(change_group_id)
                else:
                    # 用户没有提供group_id，我们需要获取实际使用的group_id
                    if result.change_ids:
                        # 获取第一个变更的记录来找到实际的group_id
                        first_change = self.change_store.get_change(result.change_ids[0])
                        if first_change and first_change.group_id:
                            checkpoint_id = _generate_checkpoint_id(first_change.group_id)
                        else:
                            checkpoint_id = result.change_ids[0]
                    else:
                        checkpoint_id = str(uuid.uuid4())
                
                checkpoint = ConversationCheckpoint(
                    checkpoint_id=checkpoint_id,
                    timestamp=time.time(),
                    conversation_id=conversation_id,
                    first_message_id=first_message_id,
                    last_message_id=last_message_id,
                    metadata=metadata
                )
                
                saved_id = self.conversation_store.save_checkpoint(checkpoint)
                logger.info(f"已保存对话检查点: {checkpoint_id}")
            except Exception as e:
                logger.error(f"保存对话检查点失败: {str(e)}")
        else:
            logger.warning(f"文件变更应用失败，跳过对话检查点保存")
        
        return result
    
    def apply_changes(self, changes: Dict[str, FileChange], change_group_id: Optional[str] = None) -> ApplyResult:
        """
        应用一组文件变更
        
        Args:
            changes: 文件变更字典，格式为 {file_path: FileChange}
            change_group_id: 变更组ID，用于将相关变更归为一组
            
        Returns:
            ApplyResult: 应用结果对象
        """
        # 如果没有提供变更组ID，生成一个新的
        if change_group_id is None:
            change_group_id = str(uuid.uuid4())
        
        result = ApplyResult(success=True)
        
        # 处理每个文件的变更
        for file_path, change in changes.items():
            try:
                # 获取文件的绝对路径
                abs_file_path = self._get_absolute_path(file_path)
                
                # 确定文件是否是新文件
                is_new = not os.path.exists(abs_file_path)
                
                # 备份原文件（如果存在）
                backup_id = None
                if not is_new and not change.is_deletion:
                    backup_id = self.backup_manager.backup_file(abs_file_path)
                
                # 处理文件变更
                if change.is_deletion:
                    # 如果是删除操作，先备份再删除
                    backup_id = self.backup_manager.backup_file(abs_file_path)
                    if os.path.exists(abs_file_path):
                        os.remove(abs_file_path)
                else:
                    # 确保目录存在
                    dir_path = os.path.dirname(abs_file_path)
                    if dir_path:
                        os.makedirs(dir_path, exist_ok=True)
                    
                    # 写入文件内容
                    with open(abs_file_path, 'w', encoding='utf-8') as f:
                        f.write(change.content)
                
                # 创建变更记录
                change_record = ChangeRecord.create(
                    file_path=file_path,
                    backup_id=backup_id,
                    is_new=is_new,
                    is_deletion=change.is_deletion,
                    group_id=change_group_id
                )
                
                # 保存变更记录
                change_id = self.change_store.save_change(change_record)
                result.add_change_id(change_id)
                
                logger.info(f"已应用变更到文件 {file_path}")
            
            except Exception as e:
                error_message = f"应用变更到文件 {file_path} 失败: {str(e)}"
                logger.error(error_message)
                result.add_error(file_path, error_message)
        
        return result
    
    def preview_changes(self, changes: Dict[str, FileChange]) -> Dict[str, DiffResult]:
        """
        预览变更的差异
        
        Args:
            changes: 文件变更字典
            
        Returns:
            Dict[str, DiffResult]: 每个文件的差异结果
        """
        diff_results = {}
        
        for file_path, change in changes.items():
            try:
                # 获取文件的绝对路径
                abs_file_path = self._get_absolute_path(file_path)
                
                # 确定文件是否是新文件
                is_new = not os.path.exists(abs_file_path)
                
                # 获取原文件内容
                old_content = None
                if not is_new and not change.is_deletion:
                    try:
                        with open(abs_file_path, 'r', encoding='utf-8') as f:
                            old_content = f.read()
                    except Exception as e:
                        logger.error(f"读取文件 {abs_file_path} 失败: {str(e)}")
                
                # 创建差异结果
                diff_result = DiffResult(
                    file_path=file_path,
                    old_content=old_content,
                    new_content=change.content,
                    is_new=is_new,
                    is_deletion=change.is_deletion
                )
                
                diff_results[file_path] = diff_result
            
            except Exception as e:
                logger.error(f"预览文件 {file_path} 的变更差异失败: {str(e)}")
        
        return diff_results
    
    def undo_last_change_with_conversation(self) -> Tuple[UndoResult, Optional[ConversationCheckpoint]]:
        """
        撤销最近的一次变更并恢复对话状态
        
        Returns:
            Tuple[UndoResult, Optional[ConversationCheckpoint]]: 撤销结果和恢复的对话检查点
        """
        # 获取最近的变更记录
        latest_changes = self.change_store.get_latest_changes(limit=1)
        if not latest_changes:
            return UndoResult(success=False, errors={"general": "没有找到最近的变更记录"}), None
        
        latest_change = latest_changes[0]
        
        # 如果最近的变更属于一个组，撤销整个组
        if latest_change.group_id:
            return self.undo_change_group_with_conversation(latest_change.group_id)
        else:
            # 否则只撤销这一个变更
            return self.undo_change_with_conversation(latest_change.change_id)
    
    def undo_last_change(self) -> UndoResult:
        """
        撤销最近的一次变更
        
        Returns:
            UndoResult: 撤销结果对象
        """
        # 获取最近的变更记录
        latest_changes = self.change_store.get_latest_changes(limit=1)
        if not latest_changes:
            return UndoResult(success=False, errors={"general": "没有找到最近的变更记录"})
        
        latest_change = latest_changes[0]
        
        # 如果最近的变更属于一个组，撤销整个组
        if latest_change.group_id:
            return self.undo_change_group(latest_change.group_id)
        else:
            # 否则只撤销这一个变更
            return self.undo_change(latest_change.change_id)
    
    def undo_change_with_conversation(self, change_id: str) -> Tuple[UndoResult, Optional[ConversationCheckpoint]]:
        """
        撤销指定的变更并恢复对话状态
        
        Args:
            change_id: 变更记录ID
            
        Returns:
            Tuple[UndoResult, Optional[ConversationCheckpoint]]: 撤销结果和恢复的对话检查点
        """
        # 获取变更记录
        change_record = self.change_store.get_change(change_id)
        if change_record is None:
            return UndoResult(success=False, errors={"general": f"变更记录 {change_id} 不存在"}), None
        
        # 获取关联的对话检查点
        checkpoint = None
        # 生成安全的checkpoint_id
        checkpoint_id = _generate_checkpoint_id(change_record.group_id) if change_record.group_id else change_id
        
        try:
            checkpoint = self.conversation_store.get_checkpoint(checkpoint_id)
            if checkpoint:
                logger.info(f"找到关联的对话检查点: {checkpoint_id}")
            else:
                logger.debug(f"未找到关联的对话检查点: {checkpoint_id}")
        except Exception as e:
            logger.error(f"获取对话检查点失败: {str(e)}")
        
        # 撤销文件变更
        undo_result = self.undo_change(change_id)
        
        return undo_result, checkpoint
    
    def undo_change(self, change_id: str) -> UndoResult:
        """
        撤销指定的变更
        
        Args:
            change_id: 变更记录ID
            
        Returns:
            UndoResult: 撤销结果对象
        """
        # 获取变更记录
        change_record = self.change_store.get_change(change_id)
        if change_record is None:
            return UndoResult(success=False, errors={"general": f"变更记录 {change_id} 不存在"})
        
        result = UndoResult(success=True)
        
        try:
            # 获取文件的绝对路径
            abs_file_path = self._get_absolute_path(change_record.file_path)
            
            # 根据变更类型执行撤销操作
            if change_record.is_new:
                # 如果是新建文件的变更，删除该文件
                if os.path.exists(abs_file_path):
                    os.remove(abs_file_path)
                    result.add_restored_file(change_record.file_path)
            elif change_record.is_deletion:
                # 如果是删除文件的变更，从备份恢复
                if change_record.backup_id:
                    success = self.backup_manager.restore_file(abs_file_path, change_record.backup_id)
                    if success:
                        result.add_restored_file(change_record.file_path)
                    else:
                        result.add_error(change_record.file_path, "从备份恢复文件失败")
                else:
                    result.add_error(change_record.file_path, "没有找到文件备份")
            else:
                # 如果是修改文件的变更，从备份恢复
                if change_record.backup_id:
                    success = self.backup_manager.restore_file(abs_file_path, change_record.backup_id)
                    if success:
                        result.add_restored_file(change_record.file_path)
                    else:
                        result.add_error(change_record.file_path, "从备份恢复文件失败")
                else:
                    result.add_error(change_record.file_path, "没有找到文件备份")
            
            # 删除变更记录
            self.change_store.delete_change(change_id)
            
            logger.info(f"已撤销变更 {change_id}")
        
        except Exception as e:
            error_message = f"撤销变更 {change_id} 失败: {str(e)}"
            logger.error(error_message)
            result.add_error(change_record.file_path, error_message)
            result.success = False
        
        return result
            
    def undo_change_group_with_conversation(self, group_id: str) -> Tuple[UndoResult, Optional[ConversationCheckpoint]]:
        """
        撤销指定组的所有变更并恢复对话状态
        
        Args:
            group_id: 变更组ID
            
        Returns:
            Tuple[UndoResult, Optional[ConversationCheckpoint]]: 撤销结果和恢复的对话检查点
        """
        # 获取组内的所有变更记录
        changes = self.change_store.get_changes_by_group(group_id)
        if not changes:
            return UndoResult(success=False, errors={"general": f"变更组 {group_id} 不存在或为空"}), None
        
        # 获取关联的对话检查点
        checkpoint = None
        checkpoint_id = _generate_checkpoint_id(group_id) if group_id else group_id
        
        try:
            checkpoint = self.conversation_store.get_checkpoint(checkpoint_id)
            if checkpoint:
                logger.info(f"找到关联的对话检查点: {checkpoint_id}")
            else:
                logger.debug(f"未找到关联的对话检查点: {checkpoint_id}")
        except Exception as e:
            logger.error(f"获取对话检查点失败: {str(e)}")
        
        # 撤销文件变更
        undo_result = self.undo_change_group(group_id)
        
        return undo_result, checkpoint
    
    def undo_change_group(self, group_id: str) -> UndoResult:
        """
        撤销指定组的所有变更
        
        Args:
            group_id: 变更组ID
            
        Returns:
            UndoResult: 撤销结果对象
        """
        # 获取组内的所有变更记录
        changes = self.change_store.get_changes_by_group(group_id)
        if not changes:
            return UndoResult(success=False, errors={"general": f"变更组 {group_id} 不存在或为空"})
        
        result = UndoResult(success=True)
        
        # 按时间戳降序排序，确保按照相反的顺序撤销
        changes.sort(key=lambda x: x.timestamp, reverse=True)
        
        # 逐个撤销变更
        for change in changes:
            change_result = self.undo_change(change.change_id)
            
            # 合并结果
            result.success = result.success and change_result.success
            result.restored_files.extend(change_result.restored_files)
            result.errors.update(change_result.errors)
        
        return result
    
    def undo_to_version_with_conversation(self, version_id: str) -> Tuple[UndoResult, Optional[ConversationCheckpoint]]:
        """
        撤销到指定的历史版本并恢复对话状态
        
        Args:
            version_id: 目标版本ID（变更记录ID）
            
        Returns:
            Tuple[UndoResult, Optional[ConversationCheckpoint]]: 撤销结果和恢复的对话检查点
        """
        # 获取目标版本的变更记录
        target_change = self.change_store.get_change(version_id)
        if target_change is None:
            return UndoResult(success=False, errors={"general": f"变更记录 {version_id} 不存在"}), None
        
        # 获取关联的对话检查点
        checkpoint = None
        checkpoint_id = _generate_checkpoint_id(target_change.group_id) if target_change.group_id else version_id
        
        try:
            checkpoint = self.conversation_store.get_checkpoint(checkpoint_id)
            if checkpoint:
                logger.info(f"找到关联的对话检查点: {checkpoint_id}")
            else:
                logger.debug(f"未找到关联的对话检查点: {checkpoint_id}")
        except Exception as e:
            logger.error(f"获取对话检查点失败: {str(e)}")
        
        # 撤销文件变更
        undo_result = self.undo_to_version(version_id)
        
        return undo_result, checkpoint
    
    def undo_to_version(self, version_id: str) -> UndoResult:
        """
        撤销到指定的历史版本
        
        Args:
            version_id: 目标版本ID（变更记录ID）
            
        Returns:
            UndoResult: 撤销结果对象
        """
        # 获取目标版本的变更记录
        target_change = self.change_store.get_change(version_id)
        if target_change is None:
            return UndoResult(success=False, errors={"general": f"变更记录 {version_id} 不存在"})
        
        # 获取最近的变更记录
        latest_changes = self.change_store.get_latest_changes()
        if not latest_changes:
            return UndoResult(success=False, errors={"general": "没有找到最近的变更记录"})
        
        # 找出需要撤销的变更记录
        changes_to_undo = []
        for change in latest_changes:
            if change.timestamp > target_change.timestamp:
                changes_to_undo.append(change)
        
        if not changes_to_undo:
            return UndoResult(success=True, restored_files=[])
        
        result = UndoResult(success=True)
        
        # 按时间戳降序排序，确保按照相反的顺序撤销
        changes_to_undo.sort(key=lambda x: x.timestamp, reverse=True)
        
        # 逐个撤销变更
        for change in changes_to_undo:
            change_result = self.undo_change(change.change_id)
            
            # 合并结果
            result.success = result.success and change_result.success
            result.restored_files.extend(change_result.restored_files)
            result.errors.update(change_result.errors)
        
        return result
    
    def get_change_history(self, limit: int = 10) -> List[ChangeRecord]:
        """
        获取变更历史记录
        
        Args:
            limit: 返回的历史记录数量限制
            
        Returns:
            List[ChangeRecord]: 变更记录列表
        """
        return self.change_store.get_latest_changes(limit)
    
    def get_file_history(self, file_path: str, limit: int = 10) -> List[ChangeRecord]:
        """
        获取指定文件的变更历史
        
        Args:
            file_path: 文件路径
            limit: 返回的历史记录数量限制
            
        Returns:
            List[ChangeRecord]: 变更记录列表
        """
        return self.change_store.get_changes_by_file(file_path, limit)
    
    def get_changes_by_group(self, group_id: str) -> List[ChangeRecord]:
        """
        获取指定变更组的所有变更记录
        
        Args:
            group_id: 变更组ID
            
        Returns:
            List[ChangeRecord]: 变更记录列表
        """
        return self.change_store.get_changes_by_group(group_id)
    
    def get_change_groups(self, limit: int = 10) -> List[Tuple[str, float, int]]:
        """
        获取变更组列表
        
        Args:
            limit: 返回的组数量限制
            
        Returns:
            List[Tuple[str, float, int]]: 变更组ID、最新时间戳和变更数量的列表
        """
        return self.change_store.get_change_groups(limit)
    
    def get_available_checkpoints(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取可用的检查点列表，包含对话状态信息
        
        Args:
            limit: 返回的检查点数量限制
            
        Returns:
            List[Dict[str, Any]]: 检查点信息列表
        """
        # 获取变更组列表
        change_groups = self.get_change_groups(limit)
        
        # 构建检查点信息
        checkpoints = []
        for group_id, timestamp, count in change_groups:
            has_conversation = False
            
            # 检查是否有对话检查点
            try:
                checkpoint = self.conversation_store.get_checkpoint(group_id)
                has_conversation = checkpoint is not None
            except Exception as e:
                logger.error(f"获取对话检查点失败: {str(e)}")
            
            checkpoints.append({
                "id": group_id,
                "timestamp": timestamp,
                "changes_count": count,
                "has_conversation": has_conversation
            })
        
        return checkpoints
    
    def get_checkpointed_message_ids(self, conversation_id: str) -> List[str]:
        """
        获取所有有checkpoint的message_id（只返回last_message_id）
        
        Args:
            conversation_id: 对话ID
            
        Returns:
            List[str]: 有checkpoint关联的last_message_id列表
        """
        checkpointed_message_ids = []
        
        try:
            # 获取所有变更组
            change_groups = self.get_change_groups(limit=1000)  # 获取更多的记录
            
            # 遍历每个变更组，查找对应的checkpoint
            for group_id, _, _ in change_groups:
                # 生成安全的checkpoint_id
                checkpoint_id = _generate_checkpoint_id(group_id) if group_id else group_id
                
                try:
                    checkpoint = self.conversation_store.get_checkpoint(checkpoint_id)
                    if checkpoint and checkpoint.conversation_id == conversation_id:
                        # 只收集last_message_id
                        if checkpoint.last_message_id and checkpoint.last_message_id not in checkpointed_message_ids:
                            checkpointed_message_ids.append(checkpoint.last_message_id)
                except Exception as e:
                    logger.debug(f"获取checkpoint {checkpoint_id} 失败: {str(e)}")
                    continue
            
            # 也检查没有group_id的单独变更
            latest_changes = self.change_store.get_latest_changes(limit=100)
            for change in latest_changes:
                if not change.group_id:  # 单独的变更
                    checkpoint_id = change.change_id
                    try:
                        checkpoint = self.conversation_store.get_checkpoint(checkpoint_id)
                        if checkpoint and checkpoint.conversation_id == conversation_id:
                            if checkpoint.last_message_id and checkpoint.last_message_id not in checkpointed_message_ids:
                                checkpointed_message_ids.append(checkpoint.last_message_id)
                    except Exception:
                        continue
            
            logger.info(f"找到 {len(checkpointed_message_ids)} 个有checkpoint的last_message_id")
            return checkpointed_message_ids
            
        except Exception as e:
            logger.error(f"获取checkpointed message_ids失败: {str(e)}")
            return checkpointed_message_ids
    
    def rollback_to_message(self, message_id: str, conversation_id: Optional[str] = None) -> Tuple[UndoResult, Optional[ConversationCheckpoint]]:
        """
        回滚到指定message_id所在的checkpoint
        
        Args:
            message_id: 目标消息ID
            conversation_id: 可选的对话ID，用于过滤checkpoint
            
        Returns:
            Tuple[UndoResult, Optional[ConversationCheckpoint]]: 回滚结果和找到的对话检查点
        """
        try:
            # 查找包含该message_id的checkpoint
            found_checkpoint = None
            found_group_id = None
            found_change_id = None
            
            # 先检查有group_id的变更
            change_groups = self.get_change_groups(limit=1000)
            for group_id, _, _ in change_groups:
                checkpoint_id = _generate_checkpoint_id(group_id) if group_id else group_id
                
                try:
                    checkpoint = self.conversation_store.get_checkpoint(checkpoint_id)
                    if checkpoint:
                        # 检查message_id是否在这个checkpoint的范围内
                        is_in_range = False
                        
                        # 检查是否匹配conversation_id（如果提供了）
                        if conversation_id and checkpoint.conversation_id != conversation_id:
                            continue
                            
                        if checkpoint.first_message_id == message_id or checkpoint.last_message_id == message_id:
                            is_in_range = True
                        elif checkpoint.first_message_id and checkpoint.last_message_id:
                            # 简化版本：如果message_id在checkpoint的范围内，我们假设它匹配
                            # 注意：这里无法准确判断message_id是否在范围内，除非有完整的消息列表
                            # 但如果first或last匹配，我们已经在上面处理了
                            pass
                        
                        if is_in_range:
                            found_checkpoint = checkpoint
                            found_group_id = group_id
                            logger.info(f"找到包含message_id {message_id} 的checkpoint (group: {group_id})")
                            break
                            
                except Exception as e:
                    logger.debug(f"检查checkpoint {checkpoint_id} 时出错: {str(e)}")
                    continue
            
            # 如果没找到，检查单独的变更
            if not found_checkpoint:
                latest_changes = self.change_store.get_latest_changes(limit=100)
                for change in latest_changes:
                    if not change.group_id:
                        checkpoint_id = change.change_id
                        try:
                            checkpoint = self.conversation_store.get_checkpoint(checkpoint_id)
                            if checkpoint:
                                if (checkpoint.first_message_id == message_id or 
                                    checkpoint.last_message_id == message_id):
                                    found_checkpoint = checkpoint
                                    found_change_id = change.change_id
                                    logger.info(f"找到包含message_id {message_id} 的checkpoint (change: {change.change_id})")
                                    break
                        except Exception:
                            continue
            
            if not found_checkpoint:
                logger.warning(f"未找到包含message_id {message_id} 的checkpoint")
                return UndoResult(success=False, errors={"general": f"未找到包含message_id {message_id} 的checkpoint"}), None
            
            # 执行回滚
            logger.info(f"开始回滚到message_id {message_id} 对应的checkpoint")
            
            # 获取当前所有的变更记录
            all_changes = self.change_store.get_latest_changes(limit=1000)
            
            # 找到目标checkpoint对应的变更记录
            target_timestamp = None
            if found_group_id:
                # 找到该组最后一个变更的时间戳
                group_changes = self.change_store.get_changes_by_group(found_group_id)
                if group_changes:
                    target_timestamp = max(change.timestamp for change in group_changes)
            elif found_change_id:
                # 找到该变更的时间戳
                for change in all_changes:
                    if change.change_id == found_change_id:
                        target_timestamp = change.timestamp
                        break
            
            if not target_timestamp:
                return UndoResult(success=False, errors={"general": "无法确定回滚目标时间点"}), found_checkpoint
            
            # 撤销所有在目标时间戳之后的变更
            result = UndoResult(success=True)
            changes_to_undo = []
            
            for change in all_changes:
                if change.timestamp > target_timestamp:
                    changes_to_undo.append(change)
            
            # 按时间戳降序排序，确保按照相反的顺序撤销
            changes_to_undo.sort(key=lambda x: x.timestamp, reverse=True)
            
            logger.info(f"需要撤销 {len(changes_to_undo)} 个变更")
            
            # 逐个撤销变更
            for change in changes_to_undo:
                change_result = self.undo_change(change.change_id)
                result.success = result.success and change_result.success
                result.restored_files.extend(change_result.restored_files)
                result.errors.update(change_result.errors)
            
            logger.info(f"回滚到message_id {message_id} 完成，恢复了 {len(result.restored_files)} 个文件")
            
            return result, found_checkpoint
            
        except Exception as e:
            logger.error(f"回滚到message_id {message_id} 失败: {str(e)}")
            return UndoResult(success=False, errors={"general": str(e)}), None
    
    def get_diff_text(self, old_content: str, new_content: str) -> str:
        """
        获取两个文本内容的差异文本
        
        Args:
            old_content: 原始内容
            new_content: 新内容
            
        Returns:
            str: 差异文本
        """
        if old_content is None:
            return "新文件"
        
        if new_content is None:
            return "文件已删除"
        
        old_lines = old_content.splitlines()
        new_lines = new_content.splitlines()
        
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            lineterm='',
            n=3  # 上下文行数
        )
        
        return '\n'.join(diff)
    
    def _get_absolute_path(self, file_path: str) -> str:
        """
        获取文件的绝对路径
        
        Args:
            file_path: 文件相对路径或绝对路径
            
        Returns:
            str: 文件的绝对路径
        """
        if os.path.isabs(file_path):
            return file_path
        else:
            return os.path.join(self.project_dir, file_path)
