import pytest
import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, call

from autocoder.common.file_checkpoint.manager import FileChangeManager
from autocoder.common.file_checkpoint.models import (
    FileChange, ChangeRecord, ApplyResult, UndoResult, DiffResult
)
from autocoder.common.file_checkpoint.backup import FileBackupManager
from autocoder.common.file_checkpoint.store import FileChangeStore

@pytest.fixture
def temp_test_dir():
    """提供一个临时的测试目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def temp_backup_dir():
    """提供一个临时的备份目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def temp_store_dir():
    """提供一个临时的存储目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_file(temp_test_dir):
    """创建一个用于测试的样例文件"""
    file_path = os.path.join(temp_test_dir, "sample.txt")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("这是一个测试文件的内容")
    return file_path

@pytest.fixture
def nested_sample_file(temp_test_dir):
    """创建一个位于嵌套目录中的样例文件"""
    nested_dir = os.path.join(temp_test_dir, "nested", "dir")
    os.makedirs(nested_dir, exist_ok=True)
    
    file_path = os.path.join(nested_dir, "nested_sample.txt")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("这是一个嵌套目录中的测试文件")
    
    return file_path

@pytest.fixture
def sample_change():
    """创建一个用于测试的文件变更"""
    return FileChange(
        file_path="test.py",
        content="print('hello world')",
        is_new=True,
        is_deletion=False
    )

class TestFileChangeManager:
    """FileChangeManager类的单元测试"""
    
    def test_init(self, temp_test_dir, temp_backup_dir, temp_store_dir):
        """测试初始化"""
        manager = FileChangeManager(
            project_dir=temp_test_dir,
            backup_dir=temp_backup_dir,
            store_dir=temp_store_dir
        )
        
        assert manager.project_dir == os.path.abspath(temp_test_dir)
        assert isinstance(manager.backup_manager, FileBackupManager)
        assert isinstance(manager.change_store, FileChangeStore)
    
    def test_apply_changes_new_file(self, temp_test_dir, temp_backup_dir, temp_store_dir):
        """测试应用新文件变更"""
        manager = FileChangeManager(
            project_dir=temp_test_dir,
            backup_dir=temp_backup_dir,
            store_dir=temp_store_dir
        )
        
        # 准备变更
        test_file_path = "test_new.py"
        change = FileChange(
            file_path=test_file_path,
            content="print('hello world')",
            is_new=True
        )
        changes = {test_file_path: change}
        
        # 应用变更
        result = manager.apply_changes(changes)
        
        # 检查结果
        assert result.success is True
        assert len(result.change_ids) == 1
        assert not result.has_errors
        
        # 检查文件是否被创建
        expected_file_path = os.path.join(temp_test_dir, test_file_path)
        assert os.path.exists(expected_file_path)
        
        # 检查文件内容
        with open(expected_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert content == "print('hello world')"
    
    def test_apply_changes_modify_file(self, temp_test_dir, temp_backup_dir, temp_store_dir, sample_file):
        """测试应用修改文件变更"""
        manager = FileChangeManager(
            project_dir=temp_test_dir,
            backup_dir=temp_backup_dir,
            store_dir=temp_store_dir
        )
        
        # 准备变更
        rel_path = os.path.basename(sample_file)
        change = FileChange(
            file_path=rel_path,
            content="修改后的内容",
            is_new=False
        )
        changes = {rel_path: change}
        
        # 应用变更
        result = manager.apply_changes(changes)
        
        # 检查结果
        assert result.success is True
        assert len(result.change_ids) == 1
        assert not result.has_errors
        
        # 检查文件内容
        with open(sample_file, 'r', encoding='utf-8') as f:
            content = f.read()
        assert content == "修改后的内容"
    
    def test_apply_changes_delete_file(self, temp_test_dir, temp_backup_dir, temp_store_dir, sample_file):
        """测试应用删除文件变更"""
        manager = FileChangeManager(
            project_dir=temp_test_dir,
            backup_dir=temp_backup_dir,
            store_dir=temp_store_dir
        )
        
        # 准备变更
        rel_path = os.path.basename(sample_file)
        change = FileChange(
            file_path=rel_path,
            content="",
            is_deletion=True
        )
        changes = {rel_path: change}
        
        # 应用变更
        result = manager.apply_changes(changes)
        
        # 检查结果
        assert result.success is True
        assert len(result.change_ids) == 1
        assert not result.has_errors
        
        # 检查文件是否被删除
        assert not os.path.exists(sample_file)
    
    def test_apply_changes_create_nested_dirs(self, temp_test_dir, temp_backup_dir, temp_store_dir):
        """测试应用变更时创建嵌套目录"""
        manager = FileChangeManager(
            project_dir=temp_test_dir,
            backup_dir=temp_backup_dir,
            store_dir=temp_store_dir
        )
        
        # 准备变更
        nested_path = os.path.join("nested", "path", "to", "file.txt")
        change = FileChange(
            file_path=nested_path,
            content="嵌套目录中的文件内容",
            is_new=True
        )
        changes = {nested_path: change}
        
        # 应用变更
        result = manager.apply_changes(changes)
        
        # 检查结果
        assert result.success is True
        assert len(result.change_ids) == 1
        assert not result.has_errors
        
        # 检查文件是否被创建
        expected_file_path = os.path.join(temp_test_dir, nested_path)
        assert os.path.exists(expected_file_path)
        
        # 检查目录结构是否被创建
        nested_dir = os.path.dirname(expected_file_path)
        assert os.path.isdir(nested_dir)
    
    def test_apply_changes_with_error(self, temp_test_dir, temp_backup_dir, temp_store_dir):
        """测试应用变更出错的情况"""
        manager = FileChangeManager(
            project_dir=temp_test_dir,
            backup_dir=temp_backup_dir,
            store_dir=temp_store_dir
        )
        
        # 创建一个目标是目录的变更，这应该会导致错误
        os.makedirs(os.path.join(temp_test_dir, "existing_dir"))
        change = FileChange(
            file_path="existing_dir",
            content="这不会成功，因为目标已经是一个目录",
            is_new=False
        )
        changes = {"existing_dir": change}
        
        # 应用变更
        result = manager.apply_changes(changes)
        
        # 检查结果
        assert result.success is False
        assert result.has_errors
        assert "existing_dir" in result.errors
    
    def test_apply_changes_with_group_id(self, temp_test_dir, temp_backup_dir, temp_store_dir):
        """测试使用组ID应用变更"""
        manager = FileChangeManager(
            project_dir=temp_test_dir,
            backup_dir=temp_backup_dir,
            store_dir=temp_store_dir
        )
        
        # 准备变更
        change1 = FileChange(
            file_path="file1.txt",
            content="文件1内容"
        )
        change2 = FileChange(
            file_path="file2.txt",
            content="文件2内容"
        )
        changes = {
            "file1.txt": change1,
            "file2.txt": change2
        }
        
        # 应用变更，使用自定义组ID
        group_id = "test_group_123"
        result = manager.apply_changes(changes, change_group_id=group_id)
        
        # 检查结果
        assert result.success is True
        assert len(result.change_ids) == 2
        
        # 检查变更记录是否使用了指定的组ID
        for change_id in result.change_ids:
            record = manager.change_store.get_change(change_id)
            assert record.group_id == group_id
    
    def test_preview_changes(self, temp_test_dir, temp_backup_dir, temp_store_dir, sample_file):
        """测试预览变更"""
        manager = FileChangeManager(
            project_dir=temp_test_dir,
            backup_dir=temp_backup_dir,
            store_dir=temp_store_dir
        )
        
        # 准备变更
        rel_path = os.path.basename(sample_file)
        change1 = FileChange(
            file_path=rel_path,
            content="修改后的内容"
        )
        change2 = FileChange(
            file_path="new_file.txt",
            content="新文件内容",
            is_new=True
        )
        change3 = FileChange(
            file_path="to_be_deleted.txt",
            content="",
            is_deletion=True
        )
        
        # 创建to_be_deleted.txt文件
        delete_file_path = os.path.join(temp_test_dir, "to_be_deleted.txt")
        with open(delete_file_path, 'w', encoding='utf-8') as f:
            f.write("将被删除的文件")
        
        changes = {
            rel_path: change1,
            "new_file.txt": change2,
            "to_be_deleted.txt": change3
        }
        
        # 预览变更
        diff_results = manager.preview_changes(changes)
        
        # 检查结果
        assert len(diff_results) == 3
        
        # 检查修改文件的差异
        assert rel_path in diff_results
        modify_diff = diff_results[rel_path]
        assert modify_diff.file_path == rel_path
        assert modify_diff.old_content == "这是一个测试文件的内容"
        assert modify_diff.new_content == "修改后的内容"
        assert not modify_diff.is_new
        assert not modify_diff.is_deletion
        
        # 检查新文件的差异
        assert "new_file.txt" in diff_results
        new_diff = diff_results["new_file.txt"]
        assert new_diff.file_path == "new_file.txt"
        assert new_diff.old_content is None
        assert new_diff.new_content == "新文件内容"
        assert new_diff.is_new
        assert not new_diff.is_deletion
        
        # 检查删除文件的差异
        assert "to_be_deleted.txt" in diff_results
        delete_diff = diff_results["to_be_deleted.txt"]
        assert delete_diff.file_path == "to_be_deleted.txt"
        assert delete_diff.old_content in ["将被删除的文件", None]
        assert delete_diff.new_content == ""
        assert not delete_diff.is_new
        assert delete_diff.is_deletion
    
    def test_get_diff_text(self, temp_test_dir, temp_backup_dir, temp_store_dir):
        """测试获取差异文本"""
        manager = FileChangeManager(
            project_dir=temp_test_dir,
            backup_dir=temp_backup_dir,
            store_dir=temp_store_dir
        )
        
        old_content = "line1\nline2\nline3\n"
        new_content = "line1\nline2 modified\nline3\nline4\n"
        
        diff_text = manager.get_diff_text(old_content, new_content)
        
        # 检查差异文本
        assert "line2" in diff_text
        assert "line2 modified" in diff_text
        assert "line4" in diff_text
    
    def test_undo_last_change(self, temp_test_dir, temp_backup_dir, temp_store_dir, sample_file):
        """测试撤销最近的变更"""
        manager = FileChangeManager(
            project_dir=temp_test_dir,
            backup_dir=temp_backup_dir,
            store_dir=temp_store_dir
        )
        
        # 应用变更
        rel_path = os.path.basename(sample_file)
        change = FileChange(
            file_path=rel_path,
            content="修改后的内容"
        )
        changes = {rel_path: change}
        
        apply_result = manager.apply_changes(changes)
        assert apply_result.success is True
        
        # 检查文件已被修改
        with open(sample_file, 'r', encoding='utf-8') as f:
            content = f.read()
        assert content == "修改后的内容"
        
        # 撤销最近的变更
        undo_result = manager.undo_last_change()
        
        # 检查撤销结果
        assert undo_result.success is True
        assert len(undo_result.restored_files) == 1
        assert rel_path in undo_result.restored_files
        
        # 检查文件内容是否被恢复
        with open(sample_file, 'r', encoding='utf-8') as f:
            content = f.read()
        assert content == "这是一个测试文件的内容"
    
    def test_undo_change_group(self, temp_test_dir, temp_backup_dir, temp_store_dir):
        """测试撤销变更组"""
        manager = FileChangeManager(
            project_dir=temp_test_dir,
            backup_dir=temp_backup_dir,
            store_dir=temp_store_dir
        )
        
        # 准备变更
        change1 = FileChange(
            file_path="file1.txt",
            content="文件1内容"
        )
        change2 = FileChange(
            file_path="file2.txt",
            content="文件2内容"
        )
        changes = {
            "file1.txt": change1,
            "file2.txt": change2
        }
        
        # 应用变更，使用自定义组ID
        group_id = "test_group_456"
        apply_result = manager.apply_changes(changes, change_group_id=group_id)
        assert apply_result.success is True
        
        # 检查文件已被创建
        file1_path = os.path.join(temp_test_dir, "file1.txt")
        file2_path = os.path.join(temp_test_dir, "file2.txt")
        assert os.path.exists(file1_path)
        assert os.path.exists(file2_path)
        
        # 撤销变更组
        undo_result = manager.undo_change_group(group_id)
        
        # 检查撤销结果
        assert undo_result.success is True
        assert len(undo_result.restored_files) == 2
        assert "file1.txt" in undo_result.restored_files
        assert "file2.txt" in undo_result.restored_files
        
        # 检查文件是否被删除（因为是新文件）
        assert not os.path.exists(file1_path)
        assert not os.path.exists(file2_path)
    
    def test_undo_to_version(self, temp_test_dir, temp_backup_dir, temp_store_dir, sample_file):
        """测试撤销到指定版本"""
        manager = FileChangeManager(
            project_dir=temp_test_dir,
            backup_dir=temp_backup_dir,
            store_dir=temp_store_dir
        )
        
        # 应用多个变更
        rel_path = os.path.basename(sample_file)
        changes1 = {rel_path: FileChange(file_path=rel_path, content="第一次修改")}
        changes2 = {rel_path: FileChange(file_path=rel_path, content="第二次修改")}
        changes3 = {rel_path: FileChange(file_path=rel_path, content="第三次修改")}
        
        result1 = manager.apply_changes(changes1)
        result2 = manager.apply_changes(changes2)
        result3 = manager.apply_changes(changes3)
        
        assert result1.success and result2.success and result3.success
        
        # 获取变更历史
        history = manager.get_change_history()
        assert len(history) >= 3
        
        # 撤销到第一次变更后的版本
        version_id = result1.change_ids[0]
        undo_result = manager.undo_to_version(version_id)
        
        # 检查撤销结果
        assert undo_result.success is True
        assert len(undo_result.restored_files) >= 1
        assert rel_path in undo_result.restored_files
        
        # 检查文件内容是否被恢复到第一次修改后的状态
        with open(sample_file, 'r', encoding='utf-8') as f:
            content = f.read()
        assert content == "第一次修改"
    
    def test_get_change_history(self, temp_test_dir, temp_backup_dir, temp_store_dir):
        """测试获取变更历史"""
        manager = FileChangeManager(
            project_dir=temp_test_dir,
            backup_dir=temp_backup_dir,
            store_dir=temp_store_dir
        )
        
        # 模拟存储器的get_latest_changes方法
        mock_records = [
            ChangeRecord.create(file_path="file1.txt", backup_id="backup1"),
            ChangeRecord.create(file_path="file2.txt", backup_id="backup2")
        ]
        
        with patch.object(manager.change_store, 'get_latest_changes', return_value=mock_records) as mock_method:
            history = manager.get_change_history(limit=5)
            
            # 检查是否调用了正确的方法
            mock_method.assert_called_once_with(5)
            
            # 检查结果
            assert len(history) == 2
            assert history[0].file_path == "file1.txt"
            assert history[1].file_path == "file2.txt"
    
    def test_get_file_history(self, temp_test_dir, temp_backup_dir, temp_store_dir):
        """测试获取文件变更历史"""
        manager = FileChangeManager(
            project_dir=temp_test_dir,
            backup_dir=temp_backup_dir,
            store_dir=temp_store_dir
        )
        
        # 模拟存储器的get_changes_by_file方法
        mock_records = [
            ChangeRecord.create(file_path="test.py", backup_id="backup1"),
            ChangeRecord.create(file_path="test.py", backup_id="backup2")
        ]
        
        with patch.object(manager.change_store, 'get_changes_by_file', return_value=mock_records) as mock_method:
            history = manager.get_file_history("test.py", limit=5)
            
            # 检查是否调用了正确的方法
            mock_method.assert_called_once_with("test.py", 5)
            
            # 检查结果
            assert len(history) == 2
            assert history[0].file_path == "test.py"
            assert history[1].file_path == "test.py"
    
    def test_get_change_groups(self, temp_test_dir, temp_backup_dir, temp_store_dir):
        """测试获取变更组"""
        manager = FileChangeManager(
            project_dir=temp_test_dir,
            backup_dir=temp_backup_dir,
            store_dir=temp_store_dir
        )
        
        # 模拟存储器的get_change_groups方法
        mock_groups = [
            ("group1", 1000.0, 2),
            ("group2", 2000.0, 3)
        ]
        
        with patch.object(manager.change_store, 'get_change_groups', return_value=mock_groups) as mock_method:
            groups = manager.get_change_groups(limit=5)
            
            # 检查是否调用了正确的方法
            mock_method.assert_called_once_with(5)
            
            # 检查结果
            assert len(groups) == 2
            assert groups[0][0] == "group1"
            assert groups[1][0] == "group2"
    
    def test_get_absolute_path(self, temp_test_dir, temp_backup_dir, temp_store_dir):
        """测试获取绝对路径"""
        manager = FileChangeManager(
            project_dir=temp_test_dir,
            backup_dir=temp_backup_dir,
            store_dir=temp_store_dir
        )
        
        # 测试相对路径
        rel_path = "test/path.txt"
        abs_path = manager._get_absolute_path(rel_path)
        
        expected_path = os.path.join(temp_test_dir, rel_path)
        assert abs_path == expected_path
        
        # 测试绝对路径
        abs_path_input = os.path.abspath("/some/abs/path.txt")
        abs_path_output = manager._get_absolute_path(abs_path_input)
        
        # 应该保持原样
        assert abs_path_output == abs_path_input 
    
    def test_get_checkpointed_message_ids(self, temp_test_dir, temp_backup_dir, temp_store_dir):
        """测试获取有checkpoint的message_id列表"""
        manager = FileChangeManager(
            project_dir=temp_test_dir,
            backup_dir=temp_backup_dir,
            store_dir=temp_store_dir,
            conversation_store_dir=temp_store_dir  # 使用相同的目录
        )
        
        conversation_id = "test_conversation_123"
        
        # 场景1：创建带有对话checkpoint的变更组
        group_id_1 = "group_with_messages_1"
        changes_1 = {
            "file1.txt": FileChange(
                file_path="file1.txt",
                content="内容1",
                is_new=True
            )
        }
        
        result_1 = manager.apply_changes_with_conversation(
            changes=changes_1,
            conversation_id=conversation_id,
            first_message_id="msg_001",
            last_message_id="msg_002",
            change_group_id=group_id_1
        )
        assert result_1.success is True
        
        # 场景2：创建另一个带有对话checkpoint的变更组
        group_id_2 = "group_with_messages_2"
        changes_2 = {
            "file2.txt": FileChange(
                file_path="file2.txt",
                content="内容2",
                is_new=True
            )
        }
        
        result_2 = manager.apply_changes_with_conversation(
            changes=changes_2,
            conversation_id=conversation_id,
            first_message_id="msg_003",
            last_message_id="msg_004",
            change_group_id=group_id_2
        )
        assert result_2.success is True
        
        # 场景3：创建不同conversation_id的checkpoint（不应该被包含）
        group_id_3 = "group_other_conversation"
        changes_3 = {
            "file3.txt": FileChange(
                file_path="file3.txt",
                content="内容3",
                is_new=True
            )
        }
        
        result_3 = manager.apply_changes_with_conversation(
            changes=changes_3,
            conversation_id="other_conversation",
            first_message_id="msg_005",
            last_message_id="msg_006",
            change_group_id=group_id_3
        )
        assert result_3.success is True
        
        # 获取checkpointed message ids
        message_ids = manager.get_checkpointed_message_ids(conversation_id)
        
        # 验证结果
        assert len(message_ids) == 2
        assert "msg_002" in message_ids  # last_message_id from group_1
        assert "msg_004" in message_ids  # last_message_id from group_2
        assert "msg_006" not in message_ids  # 不同conversation的消息不应该包含
    
    def test_rollback_to_message(self, temp_test_dir, temp_backup_dir, temp_store_dir, sample_file):
        """测试回滚到指定message_id"""
        manager = FileChangeManager(
            project_dir=temp_test_dir,
            backup_dir=temp_backup_dir,
            store_dir=temp_store_dir,
            conversation_store_dir=temp_store_dir
        )
        
        conversation_id = "test_conversation_456"
        rel_path = os.path.basename(sample_file)
        
        # 步骤1：创建初始变更，关联message_id
        group_id_1 = "initial_change"
        changes_1 = {
            rel_path: FileChange(
                file_path=rel_path,
                content="第一次修改内容",
                is_new=False
            )
        }
        
        result_1 = manager.apply_changes_with_conversation(
            changes=changes_1,
            conversation_id=conversation_id,
            first_message_id="msg_100",
            last_message_id="msg_101",
            change_group_id=group_id_1
        )
        assert result_1.success is True
        
        # 验证文件内容
        with open(sample_file, 'r', encoding='utf-8') as f:
            content = f.read()
        assert content == "第一次修改内容"
        
        # 步骤2：创建第二个变更
        group_id_2 = "second_change"
        changes_2 = {
            rel_path: FileChange(
                file_path=rel_path,
                content="第二次修改内容",
                is_new=False
            )
        }
        
        result_2 = manager.apply_changes_with_conversation(
            changes=changes_2,
            conversation_id=conversation_id,
            first_message_id="msg_102",
            last_message_id="msg_103",
            change_group_id=group_id_2
        )
        assert result_2.success is True
        
        # 验证文件内容
        with open(sample_file, 'r', encoding='utf-8') as f:
            content = f.read()
        assert content == "第二次修改内容"
        
        # 步骤3：创建第三个变更
        group_id_3 = "third_change"
        changes_3 = {
            rel_path: FileChange(
                file_path=rel_path,
                content="第三次修改内容",
                is_new=False
            ),
            "new_file.txt": FileChange(
                file_path="new_file.txt",
                content="新文件内容",
                is_new=True
            )
        }
        
        result_3 = manager.apply_changes_with_conversation(
            changes=changes_3,
            conversation_id=conversation_id,
            first_message_id="msg_104",
            last_message_id="msg_105",
            change_group_id=group_id_3
        )
        assert result_3.success is True
        
        # 验证文件内容
        with open(sample_file, 'r', encoding='utf-8') as f:
            content = f.read()
        assert content == "第三次修改内容"
        
        new_file_path = os.path.join(temp_test_dir, "new_file.txt")
        assert os.path.exists(new_file_path)
        
        # 步骤4：回滚到msg_101（第一次修改后的状态）
        undo_result, checkpoint = manager.rollback_to_message("msg_101", conversation_id)
        
        # 验证回滚结果
        assert undo_result.success is True
        assert checkpoint is not None
        assert checkpoint.last_message_id == "msg_101"
        assert checkpoint.conversation_id == conversation_id
        
        # 验证文件状态：应该回到第一次修改后的状态
        with open(sample_file, 'r', encoding='utf-8') as f:
            content = f.read()
        assert content == "第一次修改内容"
        
        # 新文件应该被删除（因为它是在第三次修改时创建的）
        assert not os.path.exists(new_file_path)
    
    def test_rollback_to_message_not_found(self, temp_test_dir, temp_backup_dir, temp_store_dir):
        """测试回滚到不存在的message_id"""
        manager = FileChangeManager(
            project_dir=temp_test_dir,
            backup_dir=temp_backup_dir,
            store_dir=temp_store_dir,
            conversation_store_dir=temp_store_dir
        )
        
        # 尝试回滚到不存在的message_id
        undo_result, checkpoint = manager.rollback_to_message("non_existent_msg_id", "test_conversation")
        
        # 验证结果
        assert undo_result.success is False
        assert "未找到包含message_id non_existent_msg_id 的checkpoint" in undo_result.errors.get("general", "")
        assert checkpoint is None
    
    def test_rollback_to_message_with_single_change(self, temp_test_dir, temp_backup_dir, temp_store_dir):
        """测试回滚单个变更（非组变更）的message"""
        manager = FileChangeManager(
            project_dir=temp_test_dir,
            backup_dir=temp_backup_dir,
            store_dir=temp_store_dir,
            conversation_store_dir=temp_store_dir
        )
        
        conversation_id = "test_conversation_789"
        
        # 创建单个变更（不使用group_id）
        changes = {
            "single_file.txt": FileChange(
                file_path="single_file.txt",
                content="单个文件内容",
                is_new=True
            )
        }
        
        # 应用变更但不指定group_id
        result = manager.apply_changes_with_conversation(
            changes=changes,
            conversation_id=conversation_id,
            first_message_id="msg_200",
            last_message_id="msg_201",
            change_group_id=None  # 不使用group_id
        )
        assert result.success is True
        
        # 创建第二个变更
        changes_2 = {
            "another_file.txt": FileChange(
                file_path="another_file.txt",
                content="另一个文件",
                is_new=True
            )
        }
        
        result_2 = manager.apply_changes_with_conversation(
            changes=changes_2,
            conversation_id=conversation_id,
            first_message_id="msg_202",
            last_message_id="msg_203",
            change_group_id="group_after_single"
        )
        assert result_2.success is True
        
        # 验证文件存在
        single_file_path = os.path.join(temp_test_dir, "single_file.txt")
        another_file_path = os.path.join(temp_test_dir, "another_file.txt")
        assert os.path.exists(single_file_path)
        assert os.path.exists(another_file_path)
        
        # 回滚到msg_201（单个变更的消息）
        undo_result, checkpoint = manager.rollback_to_message("msg_201", conversation_id)
        
        # 验证回滚结果
        assert undo_result.success is True
        assert checkpoint is not None
        assert checkpoint.last_message_id == "msg_201"
        
        # 验证文件状态
        assert os.path.exists(single_file_path)  # 第一个文件应该还在
        assert not os.path.exists(another_file_path)  # 第二个文件应该被删除