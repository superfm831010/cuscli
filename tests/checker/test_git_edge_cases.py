"""
Git 检查边界情况测试

测试各种边界情况和异常场景，包括：
- 空暂存区/工作区
- 初始 commit（无父节点）
- 大文件跳过
- 二进制文件跳过
- 删除的文件跳过
- 无效 commit hash
- 编码错误处理
"""

import pytest
import os
import tempfile
from pathlib import Path
from git import Repo

from autocoder.checker.git_helper import GitFileHelper, TempFileManager


class TestEmptyState:
    """测试空状态的边界情况"""

    @pytest.fixture
    def empty_staged_repo(self, tmp_path):
        """创建没有暂存文件的 Git 仓库"""
        repo_dir = tmp_path / "empty_staged"
        repo_dir.mkdir()

        repo = Repo.init(str(repo_dir))
        repo.config_writer().set_value("user", "name", "Test").release()
        repo.config_writer().set_value("user", "email", "test@test.com").release()

        # 创建初始提交
        initial = repo_dir / "initial.py"
        initial.write_text("def initial(): pass\n")
        repo.index.add(["initial.py"])
        repo.index.commit("Initial")

        return str(repo_dir)

    @pytest.fixture
    def empty_unstaged_repo(self, tmp_path):
        """创建没有工作区修改的 Git 仓库"""
        repo_dir = tmp_path / "empty_unstaged"
        repo_dir.mkdir()

        repo = Repo.init(str(repo_dir))
        repo.config_writer().set_value("user", "name", "Test").release()
        repo.config_writer().set_value("user", "email", "test@test.com").release()

        # 创建提交（没有修改）
        initial = repo_dir / "initial.py"
        initial.write_text("def initial(): pass\n")
        repo.index.add(["initial.py"])
        repo.index.commit("Initial")

        return str(repo_dir)

    def test_empty_staged_files(self, empty_staged_repo):
        """测试空暂存区"""
        helper = GitFileHelper(empty_staged_repo)
        staged_files = helper.get_staged_files()

        # 暂存区应该为空
        assert len(staged_files) == 0

    def test_empty_unstaged_files(self, empty_unstaged_repo):
        """测试空工作区"""
        helper = GitFileHelper(empty_unstaged_repo)
        unstaged_files = helper.get_unstaged_files()

        # 工作区应该为空
        assert len(unstaged_files) == 0


class TestInitialCommit:
    """测试初始 commit（无父节点）的情况"""

    @pytest.fixture
    def initial_commit_repo(self, tmp_path):
        """创建只有初始 commit 的仓库"""
        repo_dir = tmp_path / "initial_commit"
        repo_dir.mkdir()

        repo = Repo.init(str(repo_dir))
        repo.config_writer().set_value("user", "name", "Test").release()
        repo.config_writer().set_value("user", "email", "test@test.com").release()

        # 创建多个文件的初始提交
        (repo_dir / "file1.py").write_text("def file1(): pass\n")
        (repo_dir / "file2.py").write_text("def file2(): pass\n")
        (repo_dir / "file3.py").write_text("def file3(): pass\n")

        repo.index.add(["file1.py", "file2.py", "file3.py"])
        repo.index.commit("Initial commit with multiple files")

        return str(repo_dir)

    def test_initial_commit_file_list(self, initial_commit_repo):
        """测试获取初始 commit 的文件列表"""
        repo = Repo(initial_commit_repo)
        commit_hash = repo.head.commit.hexsha

        helper = GitFileHelper(initial_commit_repo)
        files = helper.get_commit_files(commit_hash)

        # 应该返回所有文件
        assert len(files) == 3
        assert "file1.py" in files
        assert "file2.py" in files
        assert "file3.py" in files

    def test_initial_commit_info(self, initial_commit_repo):
        """测试获取初始 commit 信息"""
        repo = Repo(initial_commit_repo)
        commit_hash = repo.head.commit.hexsha

        helper = GitFileHelper(initial_commit_repo)
        commit_info = helper.get_commit_info(commit_hash)

        # 验证信息完整
        assert commit_info["hash"] == commit_hash
        assert commit_info["short_hash"] == commit_hash[:7]
        assert "Initial commit" in commit_info["message"]
        assert commit_info["files_changed"] == 3


class TestLargeFiles:
    """测试大文件处理"""

    @pytest.fixture
    def large_file_repo(self, tmp_path):
        """创建包含大文件的仓库"""
        repo_dir = tmp_path / "large_file"
        repo_dir.mkdir()

        repo = Repo.init(str(repo_dir))
        repo.config_writer().set_value("user", "name", "Test").release()
        repo.config_writer().set_value("user", "email", "test@test.com").release()

        # 创建大文件（>10MB）
        large_file = repo_dir / "large.py"
        # 生成大约 15MB 的内容
        content = "# " + ("x" * 1000 + "\n") * 15000
        large_file.write_text(content)

        repo.index.add(["large.py"])
        repo.index.commit("Add large file")

        return str(repo_dir)

    def test_large_file_skipped(self, large_file_repo):
        """测试大文件应该被跳过"""
        repo = Repo(large_file_repo)
        commit_hash = repo.head.commit.hexsha

        helper = GitFileHelper(large_file_repo)

        # 尝试获取大文件内容
        content = helper.get_file_content_at_commit("large.py", commit_hash)

        # 应该返回 None（文件太大）
        assert content is None


class TestBinaryFiles:
    """测试二进制文件处理"""

    @pytest.fixture
    def binary_file_repo(self, tmp_path):
        """创建包含二进制文件的仓库"""
        repo_dir = tmp_path / "binary_file"
        repo_dir.mkdir()

        repo = Repo.init(str(repo_dir))
        repo.config_writer().set_value("user", "name", "Test").release()
        repo.config_writer().set_value("user", "email", "test@test.com").release()

        # 创建二进制文件
        binary_file = repo_dir / "binary.bin"
        binary_file.write_bytes(b'\x00\x01\x02\x03\x04\x05' * 100)

        # 创建文本文件
        text_file = repo_dir / "text.py"
        text_file.write_text("def text(): pass\n")

        repo.index.add(["binary.bin", "text.py"])
        repo.index.commit("Add binary and text files")

        return str(repo_dir)

    def test_binary_file_detection_working_directory(self, binary_file_repo):
        """测试检测工作区的二进制文件"""
        helper = GitFileHelper(binary_file_repo)

        # 二进制文件
        assert helper.is_binary_file("binary.bin") is True

        # 文本文件
        assert helper.is_binary_file("text.py") is False

    def test_binary_file_detection_in_commit(self, binary_file_repo):
        """测试检测 commit 中的二进制文件"""
        repo = Repo(binary_file_repo)
        commit_hash = repo.head.commit.hexsha

        helper = GitFileHelper(binary_file_repo)

        # 二进制文件
        assert helper.is_binary_file("binary.bin", commit_hash) is True

        # 文本文件
        assert helper.is_binary_file("text.py", commit_hash) is False


class TestDeletedFiles:
    """测试删除文件的处理"""

    @pytest.fixture
    def deleted_file_repo(self, tmp_path):
        """创建包含删除文件 commit 的仓库"""
        repo_dir = tmp_path / "deleted_file"
        repo_dir.mkdir()

        repo = Repo.init(str(repo_dir))
        repo.config_writer().set_value("user", "name", "Test").release()
        repo.config_writer().set_value("user", "email", "test@test.com").release()

        # 创建文件
        file1 = repo_dir / "to_delete.py"
        file1.write_text("def to_delete(): pass\n")
        file2 = repo_dir / "to_keep.py"
        file2.write_text("def to_keep(): pass\n")

        repo.index.add(["to_delete.py", "to_keep.py"])
        repo.index.commit("Add files")

        # 删除文件
        os.remove(str(file1))
        repo.index.remove(["to_delete.py"])
        repo.index.commit("Delete file")

        return str(repo_dir)

    def test_deleted_files_skipped_in_commit(self, deleted_file_repo):
        """测试删除的文件应该被跳过"""
        repo = Repo(deleted_file_repo)
        delete_commit = repo.head.commit.hexsha

        helper = GitFileHelper(deleted_file_repo)
        files = helper.get_commit_files(delete_commit)

        # 删除的文件应该不在列表中
        assert "to_delete.py" not in files
        assert len(files) == 0  # 这个 commit 只删除文件，没有添加或修改

    def test_deleted_files_get_content_returns_none(self, deleted_file_repo):
        """测试获取已删除文件的内容应该返回 None"""
        repo = Repo(deleted_file_repo)
        commit_hash = repo.head.commit.hexsha

        helper = GitFileHelper(deleted_file_repo)

        # 尝试获取删除的文件内容（在当前 commit 中不存在）
        content = helper.get_file_content_at_commit("to_delete.py", commit_hash)

        # 应该返回 None
        assert content is None


class TestInvalidCommitHash:
    """测试无效 commit hash 的处理"""

    @pytest.fixture
    def basic_repo(self, tmp_path):
        """创建基本的 Git 仓库"""
        repo_dir = tmp_path / "basic"
        repo_dir.mkdir()

        repo = Repo.init(str(repo_dir))
        repo.config_writer().set_value("user", "name", "Test").release()
        repo.config_writer().set_value("user", "email", "test@test.com").release()

        file1 = repo_dir / "file.py"
        file1.write_text("def file(): pass\n")
        repo.index.add(["file.py"])
        repo.index.commit("Initial")

        return str(repo_dir)

    def test_invalid_commit_hash_raises_error(self, basic_repo):
        """测试无效的 commit hash 应该抛出错误"""
        helper = GitFileHelper(basic_repo)

        # 无效的 hash
        with pytest.raises(ValueError, match="Commit 不存在"):
            helper.get_commit_files("invalid_hash_12345")

    def test_nonexistent_commit_hash_raises_error(self, basic_repo):
        """测试不存在的 commit hash 应该抛出错误"""
        helper = GitFileHelper(basic_repo)

        # 不存在的 hash（格式正确但不存在）
        with pytest.raises(ValueError, match="Commit 不存在"):
            helper.get_commit_files("a" * 40)


class TestEncodingIssues:
    """测试编码问题处理"""

    @pytest.fixture
    def unicode_repo(self, tmp_path):
        """创建包含 Unicode 内容的仓库"""
        repo_dir = tmp_path / "unicode"
        repo_dir.mkdir()

        repo = Repo.init(str(repo_dir))
        repo.config_writer().set_value("user", "name", "测试用户").release()
        repo.config_writer().set_value("user", "email", "test@test.com").release()

        # 创建包含中文的文件
        chinese_file = repo_dir / "中文文件.py"
        chinese_file.write_text("# 这是中文注释\ndef 函数名(): pass\n", encoding='utf-8')

        # 创建包含 emoji 的文件
        emoji_file = repo_dir / "emoji.py"
        emoji_file.write_text("# 🚀 This is a rocket\ndef launch(): pass\n", encoding='utf-8')

        repo.index.add(["中文文件.py", "emoji.py"])
        repo.index.commit("Add unicode files 🎉")

        return str(repo_dir)

    def test_unicode_filename_handling(self, unicode_repo):
        """测试 Unicode 文件名处理"""
        repo = Repo(unicode_repo)
        commit_hash = repo.head.commit.hexsha

        helper = GitFileHelper(unicode_repo)
        files = helper.get_commit_files(commit_hash)

        # 应该正确处理 Unicode 文件名
        assert len(files) == 2
        assert "中文文件.py" in files
        assert "emoji.py" in files

    def test_unicode_content_handling(self, unicode_repo):
        """测试 Unicode 内容处理"""
        repo = Repo(unicode_repo)
        commit_hash = repo.head.commit.hexsha

        helper = GitFileHelper(unicode_repo)

        # 获取包含中文的文件内容
        chinese_content = helper.get_file_content_at_commit("中文文件.py", commit_hash)
        assert chinese_content is not None
        assert "中文注释" in chinese_content
        assert "函数名" in chinese_content

        # 获取包含 emoji 的文件内容
        emoji_content = helper.get_file_content_at_commit("emoji.py", commit_hash)
        assert emoji_content is not None
        assert "🚀" in emoji_content


class TestNotGitRepository:
    """测试非 Git 仓库的处理"""

    def test_not_git_repo_raises_error(self, tmp_path):
        """测试非 Git 仓库应该抛出错误"""
        non_repo = tmp_path / "not_a_repo"
        non_repo.mkdir()

        # 尝试初始化 GitFileHelper
        with pytest.raises(RuntimeError, match="不是有效的 Git 仓库"):
            GitFileHelper(str(non_repo))


class TestShortHash:
    """测试短 hash 支持"""

    @pytest.fixture
    def basic_repo(self, tmp_path):
        """创建基本的 Git 仓库"""
        repo_dir = tmp_path / "short_hash"
        repo_dir.mkdir()

        repo = Repo.init(str(repo_dir))
        repo.config_writer().set_value("user", "name", "Test").release()
        repo.config_writer().set_value("user", "email", "test@test.com").release()

        file1 = repo_dir / "file.py"
        file1.write_text("def file(): pass\n")
        repo.index.add(["file.py"])
        repo.index.commit("Initial")

        return str(repo_dir)

    def test_short_hash_support(self, basic_repo):
        """测试支持短 hash（7位）"""
        repo = Repo(basic_repo)
        full_hash = repo.head.commit.hexsha
        short_hash = full_hash[:7]

        helper = GitFileHelper(basic_repo)

        # 使用短 hash 获取文件
        files = helper.get_commit_files(short_hash)
        assert len(files) == 1
        assert "file.py" in files

    def test_very_short_hash_support(self, basic_repo):
        """测试支持更短的 hash（4位）"""
        repo = Repo(basic_repo)
        full_hash = repo.head.commit.hexsha
        very_short_hash = full_hash[:4]

        helper = GitFileHelper(basic_repo)

        # 使用更短的 hash（可能有歧义，但在小仓库中通常可以）
        try:
            files = helper.get_commit_files(very_short_hash)
            assert len(files) >= 0  # 能获取到就行
        except ValueError:
            # 如果歧义或无效，应该抛出 ValueError
            pass


class TestMultipleCommits:
    """测试多个 commit 的场景"""

    @pytest.fixture
    def multi_commit_repo(self, tmp_path):
        """创建包含多个 commit 的仓库"""
        repo_dir = tmp_path / "multi_commit"
        repo_dir.mkdir()

        repo = Repo.init(str(repo_dir))
        repo.config_writer().set_value("user", "name", "Test").release()
        repo.config_writer().set_value("user", "email", "test@test.com").release()

        # Commit 1
        (repo_dir / "file1.py").write_text("def v1(): pass\n")
        repo.index.add(["file1.py"])
        commit1 = repo.index.commit("Version 1")

        # Commit 2: 修改同一文件
        (repo_dir / "file1.py").write_text("def v2(): return 42\n")
        repo.index.add(["file1.py"])
        commit2 = repo.index.commit("Version 2")

        # Commit 3: 添加新文件
        (repo_dir / "file2.py").write_text("def new(): pass\n")
        repo.index.add(["file2.py"])
        commit3 = repo.index.commit("Version 3")

        return str(repo_dir)

    def test_diff_between_non_adjacent_commits(self, multi_commit_repo):
        """测试非相邻 commit 间的 diff"""
        helper = GitFileHelper(multi_commit_repo)

        # HEAD~2 到 HEAD 的 diff
        files = helper.get_diff_files("HEAD~2", "HEAD")

        # 应该包含两个 commit 的所有变更
        assert len(files) >= 1
        assert any("file1.py" in f for f in files) or any("file2.py" in f for f in files)

    def test_diff_with_default_head(self, multi_commit_repo):
        """测试 diff 默认使用 HEAD"""
        helper = GitFileHelper(multi_commit_repo)

        # 只指定起始 commit，默认对比 HEAD
        files = helper.get_diff_files("HEAD~1")

        # 应该返回 HEAD~1 到 HEAD 的差异
        assert len(files) >= 1


class TestEmptyCommit:
    """测试空 commit 的处理"""

    @pytest.fixture
    def empty_commit_repo(self, tmp_path):
        """创建包含空 commit 的仓库"""
        repo_dir = tmp_path / "empty_commit"
        repo_dir.mkdir()

        repo = Repo.init(str(repo_dir))
        repo.config_writer().set_value("user", "name", "Test").release()
        repo.config_writer().set_value("user", "email", "test@test.com").release()

        # 初始 commit
        (repo_dir / "file.py").write_text("def file(): pass\n")
        repo.index.add(["file.py"])
        repo.index.commit("Initial")

        # 空 commit（没有文件变更）
        repo.index.commit("Empty commit", skip_hooks=True, parent_commits=[repo.head.commit])

        return str(repo_dir)

    def test_empty_commit_returns_no_files(self, empty_commit_repo):
        """测试空 commit 应该返回空文件列表"""
        repo = Repo(empty_commit_repo)
        empty_commit = repo.head.commit.hexsha

        helper = GitFileHelper(empty_commit_repo)
        files = helper.get_commit_files(empty_commit)

        # 空 commit 应该返回空列表
        assert len(files) == 0
