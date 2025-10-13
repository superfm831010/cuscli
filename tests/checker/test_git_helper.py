"""
Git 文件获取辅助模块的单元测试

测试 GitFileHelper 类的各项功能，包括：
- 暂存区文件获取
- 工作区文件获取
- Commit 文件获取
- Diff 文件获取
- 边界情况处理
"""

import pytest
import os
import tempfile
from git import Repo
from autocoder.checker.git_helper import GitFileHelper


@pytest.fixture
def temp_git_repo():
    """
    创建临时 Git 仓库用于测试

    Yields:
        临时仓库的路径
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # 初始化仓库
        repo = Repo.init(tmpdir)

        # 配置用户信息
        repo.config_writer().set_value("user", "name", "Test User").release()
        repo.config_writer().set_value(
            "user", "email", "test@example.com"
        ).release()

        # 创建初始文件
        test_file = os.path.join(tmpdir, "test.py")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("print('hello')\n")

        repo.index.add(['test.py'])
        repo.index.commit("Initial commit")

        yield tmpdir


class TestGitFileHelper:
    """GitFileHelper 类的测试套件"""

    def test_init_valid_repo(self, temp_git_repo):
        """测试在有效 Git 仓库中初始化"""
        helper = GitFileHelper(temp_git_repo)
        assert helper.repo_path == temp_git_repo
        assert helper.repo is not None

    def test_init_invalid_repo(self):
        """测试在非 Git 仓库中初始化应该抛出异常"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(RuntimeError, match="不是有效的 Git 仓库"):
                GitFileHelper(tmpdir)

    def test_get_staged_files_empty(self, temp_git_repo):
        """测试获取空暂存区"""
        helper = GitFileHelper(temp_git_repo)
        files = helper.get_staged_files()
        assert len(files) == 0

    def test_get_staged_files_with_new_file(self, temp_git_repo):
        """测试获取暂存区文件（新增文件）"""
        # 创建新文件并 add
        new_file = os.path.join(temp_git_repo, "new.py")
        with open(new_file, 'w', encoding='utf-8') as f:
            f.write("print('new')\n")

        repo = Repo(temp_git_repo)
        repo.index.add(['new.py'])

        # 测试
        helper = GitFileHelper(temp_git_repo)
        files = helper.get_staged_files()

        assert len(files) == 1
        assert files[0].endswith('new.py')
        assert os.path.isabs(files[0])

    def test_get_staged_files_with_modified_file(self, temp_git_repo):
        """测试获取暂存区文件（修改现有文件）"""
        # 修改现有文件并 add
        test_file = os.path.join(temp_git_repo, "test.py")
        with open(test_file, 'a', encoding='utf-8') as f:
            f.write("print('modified')\n")

        repo = Repo(temp_git_repo)
        repo.index.add(['test.py'])

        # 测试
        helper = GitFileHelper(temp_git_repo)
        files = helper.get_staged_files()

        assert len(files) == 1
        assert files[0].endswith('test.py')

    def test_get_unstaged_files_empty(self, temp_git_repo):
        """测试获取空工作区"""
        helper = GitFileHelper(temp_git_repo)
        files = helper.get_unstaged_files()
        assert len(files) == 0

    def test_get_unstaged_files_with_modification(self, temp_git_repo):
        """测试获取工作区修改文件（未 add）"""
        # 修改现有文件但不 add
        test_file = os.path.join(temp_git_repo, "test.py")
        with open(test_file, 'a', encoding='utf-8') as f:
            f.write("print('modified')\n")

        helper = GitFileHelper(temp_git_repo)
        files = helper.get_unstaged_files()

        assert len(files) == 1
        assert files[0].endswith('test.py')
        assert os.path.isabs(files[0])

    def test_get_commit_files_initial_commit(self, temp_git_repo):
        """测试获取初始 commit 的文件"""
        helper = GitFileHelper(temp_git_repo)
        repo = Repo(temp_git_repo)

        # 获取初始 commit
        initial_commit = repo.head.commit.hexsha

        files = helper.get_commit_files(initial_commit)
        assert len(files) == 1
        assert 'test.py' in files[0]

    def test_get_commit_files_with_parent(self, temp_git_repo):
        """测试获取有父节点的 commit 文件"""
        repo = Repo(temp_git_repo)

        # 创建新的 commit
        new_file = os.path.join(temp_git_repo, "new.py")
        with open(new_file, 'w', encoding='utf-8') as f:
            f.write("print('new')\n")

        repo.index.add(['new.py'])
        new_commit = repo.index.commit("Add new file")

        # 测试
        helper = GitFileHelper(temp_git_repo)
        files = helper.get_commit_files(new_commit.hexsha)

        assert len(files) == 1
        assert 'new.py' in files[0]

    def test_get_commit_files_short_hash(self, temp_git_repo):
        """测试使用短哈希获取 commit 文件"""
        helper = GitFileHelper(temp_git_repo)
        repo = Repo(temp_git_repo)

        # 获取短哈希（7位）
        full_hash = repo.head.commit.hexsha
        short_hash = full_hash[:7]

        files = helper.get_commit_files(short_hash)
        assert len(files) == 1
        assert 'test.py' in files[0]

    def test_get_commit_files_invalid_hash(self, temp_git_repo):
        """测试使用无效哈希获取 commit 文件"""
        helper = GitFileHelper(temp_git_repo)

        with pytest.raises(ValueError, match="Commit 不存在"):
            helper.get_commit_files("invalid_hash_12345")

    def test_get_diff_files_between_commits(self, temp_git_repo):
        """测试获取两个 commit 之间的差异文件"""
        repo = Repo(temp_git_repo)
        first_commit = repo.head.commit.hexsha

        # 创建第二个 commit
        new_file = os.path.join(temp_git_repo, "new.py")
        with open(new_file, 'w', encoding='utf-8') as f:
            f.write("print('new')\n")

        repo.index.add(['new.py'])
        second_commit = repo.index.commit("Add new file")

        # 测试
        helper = GitFileHelper(temp_git_repo)
        files = helper.get_diff_files(first_commit, second_commit.hexsha)

        assert len(files) == 1
        assert 'new.py' in files[0]

    def test_get_diff_files_default_head(self, temp_git_repo):
        """测试获取 diff 文件（默认与 HEAD 对比）"""
        repo = Repo(temp_git_repo)
        first_commit = repo.head.commit.hexsha

        # 创建新 commit
        new_file = os.path.join(temp_git_repo, "new.py")
        with open(new_file, 'w', encoding='utf-8') as f:
            f.write("print('new')\n")

        repo.index.add(['new.py'])
        repo.index.commit("Add new file")

        # 测试（不指定第二个参数，默认 HEAD）
        helper = GitFileHelper(temp_git_repo)
        files = helper.get_diff_files(first_commit)

        assert len(files) == 1
        assert 'new.py' in files[0]

    def test_get_file_content_at_commit(self, temp_git_repo):
        """测试获取指定 commit 时的文件内容"""
        helper = GitFileHelper(temp_git_repo)
        repo = Repo(temp_git_repo)

        commit_hash = repo.head.commit.hexsha

        content = helper.get_file_content_at_commit("test.py", commit_hash)
        assert content is not None
        assert "print('hello')" in content

    def test_get_file_content_at_commit_nonexistent(self, temp_git_repo):
        """测试获取不存在的文件内容"""
        helper = GitFileHelper(temp_git_repo)
        repo = Repo(temp_git_repo)

        commit_hash = repo.head.commit.hexsha

        content = helper.get_file_content_at_commit(
            "nonexistent.py", commit_hash
        )
        assert content is None

    def test_is_binary_file_text(self, temp_git_repo):
        """测试判断文本文件"""
        helper = GitFileHelper(temp_git_repo)

        # 工作区文件
        is_binary = helper.is_binary_file("test.py")
        assert is_binary is False

    def test_is_binary_file_binary(self, temp_git_repo):
        """测试判断二进制文件"""
        # 创建二进制文件
        binary_file = os.path.join(temp_git_repo, "test.bin")
        with open(binary_file, 'wb') as f:
            f.write(b'\x00\x01\x02\x03\x04')

        repo = Repo(temp_git_repo)
        repo.index.add(['test.bin'])
        repo.index.commit("Add binary file")

        helper = GitFileHelper(temp_git_repo)

        # 工作区文件
        is_binary = helper.is_binary_file("test.bin")
        assert is_binary is True

    def test_is_binary_file_at_commit(self, temp_git_repo):
        """测试判断历史 commit 中的二进制文件"""
        # 创建二进制文件
        binary_file = os.path.join(temp_git_repo, "test.bin")
        with open(binary_file, 'wb') as f:
            f.write(b'\x00\x01\x02\x03\x04')

        repo = Repo(temp_git_repo)
        repo.index.add(['test.bin'])
        commit = repo.index.commit("Add binary file")

        helper = GitFileHelper(temp_git_repo)

        # 历史文件
        is_binary = helper.is_binary_file("test.bin", commit.hexsha)
        assert is_binary is True

    def test_get_commit_info(self, temp_git_repo):
        """测试获取 commit 详细信息"""
        helper = GitFileHelper(temp_git_repo)
        repo = Repo(temp_git_repo)

        commit_hash = repo.head.commit.hexsha

        info = helper.get_commit_info(commit_hash)

        assert info['hash'] == commit_hash
        assert info['short_hash'] == commit_hash[:7]
        assert info['message'] == 'Initial commit'
        assert 'Test User' in info['author']
        assert 'test@example.com' in info['author']
        assert info['files_changed'] == 1

    def test_get_commit_info_with_multiple_files(self, temp_git_repo):
        """测试获取包含多个文件的 commit 信息"""
        repo = Repo(temp_git_repo)

        # 创建多个文件
        for i in range(3):
            file_path = os.path.join(temp_git_repo, f"file{i}.py")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# File {i}\n")
            repo.index.add([f"file{i}.py"])

        commit = repo.index.commit("Add multiple files")

        helper = GitFileHelper(temp_git_repo)
        info = helper.get_commit_info(commit.hexsha)

        assert info['files_changed'] == 3
        assert 'Add multiple files' in info['message']

    def test_staged_files_skip_deleted(self, temp_git_repo):
        """测试暂存区跳过删除的文件"""
        repo = Repo(temp_git_repo)

        # 删除文件并 add
        test_file = os.path.join(temp_git_repo, "test.py")
        os.remove(test_file)
        repo.index.remove(['test.py'])

        helper = GitFileHelper(temp_git_repo)
        files = helper.get_staged_files()

        # 应该跳过删除的文件
        assert len(files) == 0

    def test_commit_files_skip_deleted(self, temp_git_repo):
        """测试 commit 文件跳过删除的文件"""
        repo = Repo(temp_git_repo)

        # 删除文件并提交
        test_file = os.path.join(temp_git_repo, "test.py")
        os.remove(test_file)
        repo.index.remove(['test.py'])
        commit = repo.index.commit("Delete test.py")

        helper = GitFileHelper(temp_git_repo)
        files = helper.get_commit_files(commit.hexsha)

        # 应该跳过删除的文件
        assert len(files) == 0

    def test_multiple_staged_files(self, temp_git_repo):
        """测试获取多个暂存区文件"""
        repo = Repo(temp_git_repo)

        # 创建多个新文件
        for i in range(3):
            file_path = os.path.join(temp_git_repo, f"file{i}.py")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# File {i}\n")
            repo.index.add([f"file{i}.py"])

        helper = GitFileHelper(temp_git_repo)
        files = helper.get_staged_files()

        assert len(files) == 3
        for i in range(3):
            assert any(f"file{i}.py" in f for f in files)
