"""
测试 CodeCheckerPlugin 插件

测试插件的命令注册、参数解析和命令执行
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime

from autocoder.plugins.code_checker_plugin import CodeCheckerPlugin
from autocoder.checker.types import (
    FileCheckResult, Severity, Issue, CheckState
)


class TestPluginInitialization:
    """测试插件初始化"""

    @pytest.fixture
    def mock_manager(self):
        """创建 Mock PluginManager"""
        manager = Mock()
        return manager

    @pytest.fixture
    def plugin(self, mock_manager):
        """创建插件实例"""
        plugin = CodeCheckerPlugin(mock_manager, config={})
        return plugin

    def test_plugin_attributes(self, plugin):
        """测试插件属性"""
        assert plugin.name == "code_checker"
        assert plugin.version == "1.0.0"
        assert "代码规范检查" in plugin.description

    def test_plugin_initialization(self, plugin):
        """测试插件初始化"""
        # 初始状态，checker 应为 None
        assert plugin.checker is None

        # 调用 initialize
        result = plugin.initialize()

        # 应该成功初始化基础组件
        assert result is True
        assert plugin.rules_loader is not None
        assert plugin.file_processor is not None
        assert plugin.report_generator is not None
        assert plugin.progress_tracker is not None

    def test_get_commands(self, plugin):
        """测试命令注册"""
        commands = plugin.get_commands()

        assert "check" in commands
        handler, description = commands["check"]
        assert callable(handler)
        assert "代码" in description

    def test_get_completions(self, plugin):
        """测试静态补全"""
        completions = plugin.get_completions()

        assert "/check" in completions
        assert "/file" in completions["/check"]
        assert "/folder" in completions["/check"]
        assert "/resume" in completions["/check"]

        assert "/check /folder" in completions
        assert "/path" in completions["/check /folder"]
        assert "/ext" in completions["/check /folder"]


class TestCommandParsing:
    """测试命令解析"""

    @pytest.fixture
    def plugin(self):
        """创建已初始化的插件"""
        manager = Mock()
        plugin = CodeCheckerPlugin(manager, config={})
        plugin.initialize()
        return plugin

    def test_parse_folder_options_defaults(self, plugin):
        """测试解析默认选项"""
        options = plugin._parse_folder_options("")

        assert options["path"] == "."
        assert options["extensions"] is None
        assert options["ignored"] is None
        assert options["workers"] == 5

    def test_parse_folder_options_with_path(self, plugin):
        """测试解析路径选项"""
        options = plugin._parse_folder_options("/path src")

        assert options["path"] == "src"

    def test_parse_folder_options_with_ext(self, plugin):
        """测试解析扩展名选项"""
        options = plugin._parse_folder_options("/ext .py,.js")

        assert options["extensions"] == [".py", ".js"]

    def test_parse_folder_options_with_ignore(self, plugin):
        """测试解析忽略选项"""
        options = plugin._parse_folder_options("/ignore tests,__pycache__")

        assert options["ignored"] == ["tests", "__pycache__"]

    def test_parse_folder_options_with_workers(self, plugin):
        """测试解析并发数选项"""
        options = plugin._parse_folder_options("/workers 10")

        assert options["workers"] == 10

    def test_parse_folder_options_combined(self, plugin):
        """测试解析组合选项"""
        options = plugin._parse_folder_options(
            "/path src /ext .py /ignore tests /workers 3"
        )

        assert options["path"] == "src"
        assert options["extensions"] == [".py"]
        assert options["ignored"] == ["tests"]
        assert options["workers"] == 3

    def test_parse_folder_options_invalid_workers(self, plugin, capsys):
        """测试无效的并发数"""
        options = plugin._parse_folder_options("/workers abc")

        # 应使用默认值
        assert options["workers"] == 5

        # 应有警告输出
        captured = capsys.readouterr()
        assert "无效的并发数" in captured.out


class TestCheckFileCommand:
    """测试 /check /file 命令"""

    @pytest.fixture
    def plugin(self):
        """创建已初始化的插件"""
        manager = Mock()
        plugin = CodeCheckerPlugin(manager, config={})
        plugin.initialize()
        return plugin

    def test_check_file_no_path(self, plugin, capsys):
        """测试没有提供文件路径"""
        plugin._check_file("")

        captured = capsys.readouterr()
        assert "请指定文件路径" in captured.out

    def test_check_file_not_exists(self, plugin, capsys):
        """测试文件不存在"""
        plugin._check_file("/nonexistent/file.py")

        captured = capsys.readouterr()
        assert "文件不存在" in captured.out

    def test_check_file_success(self, plugin, capsys, tmp_path):
        """测试成功检查文件"""
        # 创建测试文件
        test_file = tmp_path / "test.py"
        test_file.write_text("def test(): pass")

        # Mock checker
        with patch.object(plugin, '_ensure_checker'):
            mock_checker = Mock()
            plugin.checker = mock_checker

            # Mock 检查结果
            mock_result = FileCheckResult(
                file_path=str(test_file),
                check_time=datetime.now().isoformat(),
                issues=[
                    Issue(
                        rule_id="test_001",
                        severity=Severity.WARNING,
                        line_start=1,
                        line_end=1,
                        description="测试问题",
                        suggestion="测试建议"
                    )
                ],
                error_count=0,
                warning_count=1,
                info_count=0,
                status="success"
            )
            mock_checker.check_file.return_value = mock_result

            # 执行检查
            plugin._check_file(str(test_file))

            # 验证
            mock_checker.check_file.assert_called_once_with(str(test_file))

            captured = capsys.readouterr()
            assert "检查完成" in captured.out
            assert "发现问题: 1" in captured.out

    def test_check_file_skipped(self, plugin, capsys, tmp_path):
        """测试文件被跳过"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("text content")

        with patch.object(plugin, '_ensure_checker'):
            mock_checker = Mock()
            plugin.checker = mock_checker

            mock_result = FileCheckResult(
                file_path=str(test_file),
                check_time=datetime.now().isoformat(),
                issues=[],
                error_count=0,
                warning_count=0,
                info_count=0,
                status="skipped"
            )
            mock_checker.check_file.return_value = mock_result

            plugin._check_file(str(test_file))

            captured = capsys.readouterr()
            assert "已跳过" in captured.out


class TestCheckFolderCommand:
    """测试 /check /folder 命令"""

    @pytest.fixture
    def plugin(self):
        """创建已初始化的插件"""
        manager = Mock()
        plugin = CodeCheckerPlugin(manager, config={})
        plugin.initialize()
        return plugin

    def test_check_folder_not_exists(self, plugin, capsys):
        """测试目录不存在"""
        plugin._check_folder("/path /nonexistent")

        captured = capsys.readouterr()
        assert "目录不存在" in captured.out

    def test_check_folder_no_files(self, plugin, capsys, tmp_path):
        """测试没有找到文件"""
        # Mock file_processor 返回空列表
        plugin.file_processor.scan_files.return_value = []

        plugin._check_folder(f"/path {tmp_path}")

        captured = capsys.readouterr()
        assert "未找到符合条件的文件" in captured.out


class TestResumeCommand:
    """测试 /check /resume 命令"""

    @pytest.fixture
    def plugin(self):
        """创建已初始化的插件"""
        manager = Mock()
        plugin = CodeCheckerPlugin(manager, config={})
        plugin.initialize()
        return plugin

    def test_resume_no_check_id(self, plugin, capsys):
        """测试没有提供 check_id"""
        # Mock list_checks 返回空列表
        plugin.progress_tracker.list_checks.return_value = []

        plugin._resume_check("")

        captured = capsys.readouterr()
        assert "没有可恢复的检查任务" in captured.out

    def test_resume_check_not_found(self, plugin, capsys):
        """测试检查记录不存在"""
        plugin.progress_tracker.load_state.return_value = None

        plugin._resume_check("invalid_check_id")

        captured = capsys.readouterr()
        assert "检查记录不存在" in captured.out

    def test_resume_already_completed(self, plugin, capsys):
        """测试检查已完成"""
        state = CheckState(
            check_id="test_check",
            start_time=datetime.now().isoformat(),
            config={},
            total_files=["file1.py"],
            completed_files=["file1.py"],
            remaining_files=[],
            status="completed"
        )
        plugin.progress_tracker.load_state.return_value = state

        plugin._resume_check("test_check")

        captured = capsys.readouterr()
        assert "已完成" in captured.out


class TestListResumableChecks:
    """测试可恢复检查列表"""

    @pytest.fixture
    def plugin(self):
        """创建已初始化的插件"""
        manager = Mock()
        plugin = CodeCheckerPlugin(manager, config={})
        plugin.initialize()
        return plugin

    def test_list_no_incomplete_checks(self, plugin, capsys):
        """测试没有未完成的检查"""
        plugin.progress_tracker.list_checks.return_value = [
            {"check_id": "check_1", "status": "completed"}
        ]

        plugin._list_resumable_checks()

        captured = capsys.readouterr()
        assert "没有可恢复的检查任务" in captured.out

    def test_list_incomplete_checks(self, plugin, capsys):
        """测试有未完成的检查"""
        plugin.progress_tracker.list_checks.return_value = [
            {
                "check_id": "check_1",
                "status": "interrupted",
                "start_time": "2025-10-10 12:00:00",
                "completed": 5,
                "total": 10,
                "remaining": 5,
                "progress": 50.0
            },
            {
                "check_id": "check_2",
                "status": "completed",
            }
        ]

        plugin._list_resumable_checks()

        captured = capsys.readouterr()
        assert "可恢复的检查任务" in captured.out
        assert "check_1" in captured.out
        assert "interrupted" in captured.out


class TestHelpers:
    """测试辅助函数"""

    @pytest.fixture
    def plugin(self):
        """创建已初始化的插件"""
        manager = Mock()
        plugin = CodeCheckerPlugin(manager, config={})
        plugin.initialize()
        return plugin

    def test_create_check_id(self, plugin):
        """测试生成 check_id"""
        check_id = plugin._create_check_id()

        # 应包含项目名和时间戳
        assert "_" in check_id
        parts = check_id.split("_")
        assert len(parts) >= 2

    def test_create_report_dir(self, plugin, tmp_path):
        """测试创建报告目录"""
        import os
        os.chdir(tmp_path)

        report_dir = plugin._create_report_dir("test_check_123")

        # 应创建目录
        assert os.path.exists(report_dir)
        assert os.path.isdir(report_dir)
        assert "test_check_123" in report_dir

        # 应包含 files 子目录
        files_dir = os.path.join(report_dir, "files")
        assert os.path.exists(files_dir)
        assert os.path.isdir(files_dir)

    def test_show_help(self, plugin, capsys):
        """测试显示帮助"""
        plugin._show_help()

        captured = capsys.readouterr()
        assert "代码检查命令帮助" in captured.out
        assert "/check /file" in captured.out
        assert "/check /folder" in captured.out
        assert "/check /resume" in captured.out


class TestHandleCheckCommand:
    """测试主命令处理"""

    @pytest.fixture
    def plugin(self):
        """创建已初始化的插件"""
        manager = Mock()
        plugin = CodeCheckerPlugin(manager, config={})
        plugin.initialize()
        return plugin

    def test_handle_check_no_args(self, plugin, capsys):
        """测试没有参数"""
        plugin.handle_check("")

        captured = capsys.readouterr()
        assert "代码检查命令帮助" in captured.out

    def test_handle_check_file(self, plugin):
        """测试 /file 子命令"""
        with patch.object(plugin, '_check_file') as mock_check_file:
            plugin.handle_check("/file test.py")
            mock_check_file.assert_called_once_with("test.py")

    def test_handle_check_folder(self, plugin):
        """测试 /folder 子命令"""
        with patch.object(plugin, '_check_folder') as mock_check_folder:
            plugin.handle_check("/folder /path src")
            mock_check_folder.assert_called_once_with("/path src")

    def test_handle_check_resume(self, plugin):
        """测试 /resume 子命令"""
        with patch.object(plugin, '_resume_check') as mock_resume:
            plugin.handle_check("/resume check_123")
            mock_resume.assert_called_once_with("check_123")

    def test_handle_check_unknown_subcommand(self, plugin, capsys):
        """测试未知子命令"""
        plugin.handle_check("/unknown arg")

        captured = capsys.readouterr()
        assert "未知的子命令" in captured.out
