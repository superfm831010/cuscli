"""
Git 检查功能集成测试

测试 Git 检查功能的端到端流程，包括：
- 从 Git 仓库获取文件
- 检查 Git 相关的文件（staged/unstaged/commit/diff）
- 生成包含 Git 信息的报告
"""

import pytest
import os
import tempfile
from pathlib import Path
from git import Repo
from unittest.mock import Mock, patch

from autocoder.checker.git_helper import GitFileHelper, TempFileManager
from autocoder.checker.core import CodeChecker
from autocoder.checker.types import Rule, Severity, GitInfo


@pytest.mark.integration
class TestGitStagedIntegration:
    """测试暂存区检查的端到端功能"""

    @pytest.fixture
    def git_repo(self, tmp_path):
        """创建测试用 Git 仓库"""
        repo_dir = tmp_path / "test_repo"
        repo_dir.mkdir()

        # 初始化 Git 仓库
        repo = Repo.init(str(repo_dir))
        repo.config_writer().set_value("user", "name", "Test User").release()
        repo.config_writer().set_value("user", "email", "test@example.com").release()

        # 创建初始文件并提交
        initial_file = repo_dir / "initial.py"
        initial_file.write_text("def initial(): pass\n")
        repo.index.add(["initial.py"])
        repo.index.commit("Initial commit")

        return str(repo_dir)

    def test_staged_file_detection(self, git_repo):
        """测试检测暂存区文件"""
        # 创建新文件并暂存
        repo = Repo(git_repo)
        new_file = Path(git_repo) / "new.py"
        new_file.write_text("def new_function(): pass\n")
        repo.index.add(["new.py"])

        # 获取暂存区文件
        helper = GitFileHelper(git_repo)
        staged_files = helper.get_staged_files()

        # 验证
        assert len(staged_files) == 1
        assert any("new.py" in f for f in staged_files)

    def test_staged_file_check_workflow(self, git_repo, mock_llm, mock_args):
        """测试暂存区文件检查的完整流程"""
        # 1. 创建并暂存文件
        repo = Repo(git_repo)
        test_file = Path(git_repo) / "test.py"
        test_file.write_text("""
def test_function():
    if True:
        if True:
            pass
""")
        repo.index.add(["test.py"])

        # 2. 获取暂存区文件
        helper = GitFileHelper(git_repo)
        staged_files = helper.get_staged_files()
        assert len(staged_files) > 0

        # 3. 检查文件
        checker = CodeChecker(mock_llm, mock_args)
        mock_rules = [
            Rule(
                id="test_001",
                category="测试",
                title="测试规则",
                description="测试",
                severity=Severity.INFO
            )
        ]

        with patch.object(checker.rules_loader, 'get_applicable_rules', return_value=mock_rules):
            result = checker.check_file(staged_files[0])

            # 验证检查完成
            assert result.status == "success"
            assert result.file_path == staged_files[0]

    @pytest.fixture
    def mock_llm(self):
        """创建 Mock LLM"""
        llm = Mock()
        mock_response = Mock()
        mock_response.output = "```json\n[]\n```"
        llm.chat_oai.return_value = [mock_response]
        return llm

    @pytest.fixture
    def mock_args(self):
        """创建 Mock Args"""
        args = Mock()
        args.source_dir = "/test"
        args.checker_llm_config = None
        args.checker_llm_temperature = None
        args.checker_llm_top_p = None
        args.checker_llm_seed = None
        args.checker_chunk_overlap_multiplier = None
        args.checker_chunk_token_limit = None
        return args


@pytest.mark.integration
class TestGitUnstagedIntegration:
    """测试工作区检查的端到端功能"""

    @pytest.fixture
    def git_repo(self, tmp_path):
        """创建测试用 Git 仓库"""
        repo_dir = tmp_path / "test_repo"
        repo_dir.mkdir()

        repo = Repo.init(str(repo_dir))
        repo.config_writer().set_value("user", "name", "Test User").release()
        repo.config_writer().set_value("user", "email", "test@example.com").release()

        # 创建初始文件并提交
        initial_file = repo_dir / "main.py"
        initial_file.write_text("def main(): pass\n")
        repo.index.add(["main.py"])
        repo.index.commit("Initial commit")

        return str(repo_dir)

    def test_unstaged_file_detection(self, git_repo):
        """测试检测工作区修改文件"""
        # 修改已存在的文件（不暂存）
        main_file = Path(git_repo) / "main.py"
        main_file.write_text("def main(): return 42\n")

        # 获取工作区修改文件
        helper = GitFileHelper(git_repo)
        unstaged_files = helper.get_unstaged_files()

        # 验证
        assert len(unstaged_files) == 1
        assert any("main.py" in f for f in unstaged_files)

    def test_unstaged_file_check_workflow(self, git_repo, mock_llm, mock_args):
        """测试工作区文件检查的完整流程"""
        # 1. 修改文件（不暂存）
        main_file = Path(git_repo) / "main.py"
        main_file.write_text("""
def modified_function():
    # Modified content
    pass
""")

        # 2. 获取工作区文件
        helper = GitFileHelper(git_repo)
        unstaged_files = helper.get_unstaged_files()
        assert len(unstaged_files) > 0

        # 3. 检查文件
        checker = CodeChecker(mock_llm, mock_args)
        mock_rules = [
            Rule(
                id="test_001",
                category="测试",
                title="测试规则",
                description="测试",
                severity=Severity.INFO
            )
        ]

        with patch.object(checker.rules_loader, 'get_applicable_rules', return_value=mock_rules):
            result = checker.check_file(unstaged_files[0])

            # 验证检查完成
            assert result.status == "success"

    @pytest.fixture
    def mock_llm(self):
        """创建 Mock LLM"""
        llm = Mock()
        mock_response = Mock()
        mock_response.output = "```json\n[]\n```"
        llm.chat_oai.return_value = [mock_response]
        return llm

    @pytest.fixture
    def mock_args(self):
        """创建 Mock Args"""
        args = Mock()
        args.source_dir = "/test"
        args.checker_llm_config = None
        args.checker_llm_temperature = None
        args.checker_llm_top_p = None
        args.checker_llm_seed = None
        args.checker_chunk_overlap_multiplier = None
        args.checker_chunk_token_limit = None
        return args


@pytest.mark.integration
class TestGitCommitIntegration:
    """测试 Commit 检查的端到端功能"""

    @pytest.fixture
    def git_repo(self, tmp_path):
        """创建测试用 Git 仓库"""
        repo_dir = tmp_path / "test_repo"
        repo_dir.mkdir()

        repo = Repo.init(str(repo_dir))
        repo.config_writer().set_value("user", "name", "Test User").release()
        repo.config_writer().set_value("user", "email", "test@example.com").release()

        # 创建初始提交
        file1 = repo_dir / "file1.py"
        file1.write_text("def func1(): pass\n")
        repo.index.add(["file1.py"])
        repo.index.commit("Add file1")

        # 创建第二个提交
        file2 = repo_dir / "file2.py"
        file2.write_text("def func2(): pass\n")
        repo.index.add(["file2.py"])
        repo.index.commit("Add file2")

        return str(repo_dir)

    def test_commit_file_detection(self, git_repo):
        """测试检测 commit 变更文件"""
        repo = Repo(git_repo)
        commit_hash = repo.head.commit.hexsha

        # 获取 commit 文件
        helper = GitFileHelper(git_repo)
        commit_files = helper.get_commit_files(commit_hash)

        # 验证
        assert len(commit_files) == 1
        assert "file2.py" in commit_files[0]

    def test_commit_file_with_temp_manager(self, git_repo):
        """测试 commit 文件使用临时文件管理器"""
        # 获取 commit 信息
        repo = Repo(git_repo)
        commit_hash = repo.head.commit.hexsha

        helper = GitFileHelper(git_repo)
        commit_files = helper.get_commit_files(commit_hash)

        # 创建临时文件
        with TempFileManager() as manager:
            for file_path in commit_files:
                # 获取文件内容
                content = helper.get_file_content_at_commit(file_path, commit_hash)
                assert content is not None

                # 创建临时文件
                temp_path = manager.create_temp_file(file_path, content)
                assert os.path.exists(temp_path)

                # 验证内容
                with open(temp_path, 'r') as f:
                    assert f.read() == content

        # 退出 context 后临时文件应该被清理
        # (由 TempFileManager 测试覆盖)

    def test_commit_check_workflow(self, git_repo, mock_llm, mock_args):
        """测试 commit 检查的完整流程"""
        # 1. 获取 commit 信息
        repo = Repo(git_repo)
        commit_hash = repo.head.commit.hexsha

        helper = GitFileHelper(git_repo)
        commit_files = helper.get_commit_files(commit_hash)
        assert len(commit_files) > 0

        # 2. 准备临时文件
        with TempFileManager() as manager:
            temp_files = []
            for file_path in commit_files:
                content = helper.get_file_content_at_commit(file_path, commit_hash)
                if content:
                    temp_path = manager.create_temp_file(file_path, content)
                    temp_files.append(temp_path)

            # 3. 检查临时文件
            checker = CodeChecker(mock_llm, mock_args)
            mock_rules = [
                Rule(
                    id="test_001",
                    category="测试",
                    title="测试规则",
                    description="测试",
                    severity=Severity.INFO
                )
            ]

            with patch.object(checker.rules_loader, 'get_applicable_rules', return_value=mock_rules):
                for temp_file in temp_files:
                    result = checker.check_file(temp_file)
                    assert result.status == "success"

    @pytest.fixture
    def mock_llm(self):
        """创建 Mock LLM"""
        llm = Mock()
        mock_response = Mock()
        mock_response.output = "```json\n[]\n```"
        llm.chat_oai.return_value = [mock_response]
        return llm

    @pytest.fixture
    def mock_args(self):
        """创建 Mock Args"""
        args = Mock()
        args.source_dir = "/test"
        args.checker_llm_config = None
        args.checker_llm_temperature = None
        args.checker_llm_top_p = None
        args.checker_llm_seed = None
        args.checker_chunk_overlap_multiplier = None
        args.checker_chunk_token_limit = None
        return args


@pytest.mark.integration
class TestGitDiffIntegration:
    """测试 Diff 检查的端到端功能"""

    @pytest.fixture
    def git_repo(self, tmp_path):
        """创建测试用 Git 仓库，包含多个提交"""
        repo_dir = tmp_path / "test_repo"
        repo_dir.mkdir()

        repo = Repo.init(str(repo_dir))
        repo.config_writer().set_value("user", "name", "Test User").release()
        repo.config_writer().set_value("user", "email", "test@example.com").release()

        # 第一次提交
        file1 = repo_dir / "file1.py"
        file1.write_text("def version1(): pass\n")
        repo.index.add(["file1.py"])
        commit1 = repo.index.commit("Version 1")

        # 第二次提交
        file2 = repo_dir / "file2.py"
        file2.write_text("def version2(): pass\n")
        repo.index.add(["file2.py"])
        commit2 = repo.index.commit("Version 2")

        # 第三次提交
        file3 = repo_dir / "file3.py"
        file3.write_text("def version3(): pass\n")
        repo.index.add(["file3.py"])
        commit3 = repo.index.commit("Version 3")

        return str(repo_dir)

    def test_diff_file_detection(self, git_repo):
        """测试检测 diff 变更文件"""
        repo = Repo(git_repo)

        # 获取两个 commit 间的 diff
        helper = GitFileHelper(git_repo)
        diff_files = helper.get_diff_files("HEAD~2", "HEAD")

        # 应该包含 file2.py 和 file3.py
        assert len(diff_files) >= 2
        assert any("file2.py" in f for f in diff_files)
        assert any("file3.py" in f for f in diff_files)

    def test_diff_check_workflow(self, git_repo, mock_llm, mock_args):
        """测试 diff 检查的完整流程"""
        # 1. 获取 diff 文件
        helper = GitFileHelper(git_repo)
        diff_files = helper.get_diff_files("HEAD~1", "HEAD")
        assert len(diff_files) > 0

        # 2. 准备临时文件
        with TempFileManager() as manager:
            temp_files = []
            for file_path in diff_files:
                content = helper.get_file_content_at_commit(file_path, "HEAD")
                if content:
                    temp_path = manager.create_temp_file(file_path, content)
                    temp_files.append(temp_path)

            # 3. 检查临时文件
            checker = CodeChecker(mock_llm, mock_args)
            mock_rules = [
                Rule(
                    id="test_001",
                    category="测试",
                    title="测试规则",
                    description="测试",
                    severity=Severity.INFO
                )
            ]

            with patch.object(checker.rules_loader, 'get_applicable_rules', return_value=mock_rules):
                results = []
                for temp_file in temp_files:
                    result = checker.check_file(temp_file)
                    results.append(result)
                    assert result.status == "success"

                # 验证所有文件都被检查
                assert len(results) == len(temp_files)

    @pytest.fixture
    def mock_llm(self):
        """创建 Mock LLM"""
        llm = Mock()
        mock_response = Mock()
        mock_response.output = "```json\n[]\n```"
        llm.chat_oai.return_value = [mock_response]
        return llm

    @pytest.fixture
    def mock_args(self):
        """创建 Mock Args"""
        args = Mock()
        args.source_dir = "/test"
        args.checker_llm_config = None
        args.checker_llm_temperature = None
        args.checker_llm_top_p = None
        args.checker_llm_seed = None
        args.checker_chunk_overlap_multiplier = None
        args.checker_chunk_token_limit = None
        return args


@pytest.mark.integration
class TestGitInfoIntegration:
    """测试 GitInfo 数据模型集成"""

    def test_gitinfo_creation(self):
        """测试 GitInfo 创建"""
        git_info = GitInfo(
            type="staged",
            branch="main",
            files_changed=5
        )

        assert git_info.type == "staged"
        assert git_info.branch == "main"
        assert git_info.files_changed == 5

    def test_gitinfo_with_commit_info(self):
        """测试带 commit 信息的 GitInfo"""
        git_info = GitInfo(
            type="commit",
            commit_hash="abc123def456",
            short_hash="abc123",
            message="feat: add new feature",
            author="Test User <test@example.com>",
            date="2025-01-10T10:30:00",
            files_changed=3
        )

        assert git_info.type == "commit"
        assert git_info.short_hash == "abc123"
        assert "new feature" in git_info.message

    def test_gitinfo_with_diff_info(self):
        """测试带 diff 信息的 GitInfo"""
        git_info = GitInfo(
            type="diff",
            commit1="abc123",
            commit2="def456",
            files_changed=10
        )

        assert git_info.type == "diff"
        assert git_info.commit1 == "abc123"
        assert git_info.commit2 == "def456"


@pytest.mark.integration
class TestGitWorkflowComplete:
    """测试完整的 Git 检查工作流"""

    @pytest.fixture
    def complex_git_repo(self, tmp_path):
        """创建复杂的 Git 仓库用于完整测试"""
        repo_dir = tmp_path / "complex_repo"
        repo_dir.mkdir()

        repo = Repo.init(str(repo_dir))
        repo.config_writer().set_value("user", "name", "Test User").release()
        repo.config_writer().set_value("user", "email", "test@example.com").release()

        # 创建多个文件和提交
        # Commit 1
        (repo_dir / "base.py").write_text("def base(): pass\n")
        repo.index.add(["base.py"])
        repo.index.commit("Initial commit")

        # Commit 2
        (repo_dir / "feature.py").write_text("def feature(): pass\n")
        repo.index.add(["feature.py"])
        repo.index.commit("Add feature")

        # 修改文件（工作区）
        (repo_dir / "feature.py").write_text("def feature():\n    return 42\n")

        # 添加新文件到暂存区
        (repo_dir / "new.py").write_text("def new(): pass\n")
        repo.index.add(["new.py"])

        return str(repo_dir)

    def test_complete_git_workflow(self, complex_git_repo):
        """测试完整的 Git 检查工作流"""
        helper = GitFileHelper(complex_git_repo)

        # 1. 测试暂存区
        staged_files = helper.get_staged_files()
        assert len(staged_files) > 0
        assert any("new.py" in f for f in staged_files)

        # 2. 测试工作区
        unstaged_files = helper.get_unstaged_files()
        assert len(unstaged_files) > 0
        assert any("feature.py" in f for f in unstaged_files)

        # 3. 测试 commit
        repo = Repo(complex_git_repo)
        commit_hash = repo.head.commit.hexsha
        commit_files = helper.get_commit_files(commit_hash)
        assert len(commit_files) > 0

        # 4. 测试 commit 信息
        commit_info = helper.get_commit_info(commit_hash)
        assert commit_info["short_hash"] == commit_hash[:7]
        assert "message" in commit_info
        assert "author" in commit_info
