"""
集成测试 - 测试完整的代码检查流程

测试从文件扫描、规则加载、代码检查到报告生成的完整流程
"""

import pytest
import os
import tempfile
import shutil
from datetime import datetime
from unittest.mock import Mock, patch

from autocoder.checker.core import CodeChecker
from autocoder.checker.rules_loader import RulesLoader
from autocoder.checker.file_processor import FileProcessor
from autocoder.checker.progress_tracker import ProgressTracker
from autocoder.checker.report_generator import ReportGenerator
from autocoder.checker.types import (
    Rule, Severity, FileFilters, Issue
)


@pytest.mark.integration
class TestFullCheckWorkflow:
    """测试完整的检查工作流"""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """创建临时项目"""
        # 创建项目结构
        src_dir = tmp_path / "src"
        src_dir.mkdir()

        # 创建测试文件
        (src_dir / "main.py").write_text("""
def nested_function():
    if True:
        if True:
            if True:
                if True:
                    pass  # 嵌套过深
""")

        (src_dir / "utils.py").write_text("""
def helper():
    x = None
    return x.value  # 潜在空指针
""")

        return tmp_path

    @pytest.fixture
    def mock_llm(self):
        """创建 Mock LLM"""
        llm = Mock()
        mock_response = Mock()
        mock_response.output = """```json
[
    {
        "rule_id": "test_001",
        "severity": "warning",
        "line_start": 3,
        "line_end": 7,
        "description": "发现深层嵌套",
        "suggestion": "建议重构代码"
    }
]
```"""
        llm.chat_oai.return_value = [mock_response]
        return llm

    @pytest.fixture
    def mock_rules(self):
        """创建测试规则"""
        return [
            Rule(
                id="test_001",
                category="代码结构",
                title="避免深层嵌套",
                description="if 嵌套不应超过 3 层",
                severity=Severity.WARNING
            ),
            Rule(
                id="test_002",
                category="安全性",
                title="防止空指针",
                description="检查 null 引用",
                severity=Severity.ERROR
            )
        ]

    def test_single_file_check_workflow(self, temp_project, mock_llm, mock_args, mock_rules):
        """测试单文件检查完整流程"""
        # 1. 初始化检查器
        checker = CodeChecker(mock_llm, mock_args)

        # Mock 规则加载器
        with patch.object(checker.rules_loader, 'get_applicable_rules', return_value=mock_rules):
            # 2. 检查文件
            test_file = temp_project / "src" / "main.py"
            result = checker.check_file(str(test_file))

            # 3. 验证结果
            assert result.status == "success"
            assert result.file_path == str(test_file)
            assert len(result.issues) >= 0

            # 4. 验证 LLM 被调用
            assert mock_llm.chat_oai.called

    def test_batch_check_workflow(self, temp_project, mock_llm, mock_args, mock_rules):
        """测试批量检查完整流程"""
        # 1. 扫描文件
        file_processor = FileProcessor()
        filters = FileFilters(extensions=[".py"])
        files = file_processor.scan_files(str(temp_project / "src"), filters)

        assert len(files) >= 2  # main.py 和 utils.py

        # 2. 初始化检查器
        checker = CodeChecker(mock_llm, mock_args)

        # Mock 规则加载器
        with patch.object(checker.rules_loader, 'get_applicable_rules', return_value=mock_rules):
            # 3. 批量检查
            results = checker.check_files(files)

            # 4. 验证结果
            assert results.total_files == len(files)
            assert results.checked_files == len(files)
            assert len(results.file_results) == len(files)

            # 验证每个文件都有结果
            for file_path in files:
                file_results = [r for r in results.file_results if r.file_path == file_path]
                assert len(file_results) == 1

    def test_workflow_with_report_generation(self, temp_project, mock_llm, mock_args, mock_rules):
        """测试检查流程 + 报告生成"""
        # 1. 检查文件
        checker = CodeChecker(mock_llm, mock_args)

        with patch.object(checker.rules_loader, 'get_applicable_rules', return_value=mock_rules):
            test_file = temp_project / "src" / "main.py"
            result = checker.check_file(str(test_file))

        # 2. 生成报告
        report_dir = temp_project / "reports"
        report_dir.mkdir()

        generator = ReportGenerator()
        generator.generate_file_report(result, str(report_dir))

        # 3. 验证报告文件
        files_dir = report_dir / "files"
        assert files_dir.exists()

        # 应该生成 JSON 和 Markdown 报告
        report_files = list(files_dir.glob("*"))
        assert len(report_files) >= 1  # 至少有一个报告文件

    def test_workflow_with_progress_tracking(self, temp_project, mock_llm, mock_args, mock_rules):
        """测试检查流程 + 进度跟踪"""
        # 1. 扫描文件
        file_processor = FileProcessor()
        filters = FileFilters(extensions=[".py"])
        files = file_processor.scan_files(str(temp_project / "src"), filters)

        # 2. 创建进度跟踪器
        progress_dir = temp_project / ".progress"
        progress_dir.mkdir()

        tracker = ProgressTracker(state_dir=str(progress_dir))

        # 3. 开始检查并跟踪进度
        check_id = tracker.start_check(
            files=files,
            config={"path": str(temp_project / "src")},
            project_name="test_project"
        )

        # 4. 模拟检查过程
        checker = CodeChecker(mock_llm, mock_args)

        with patch.object(checker.rules_loader, 'get_applicable_rules', return_value=mock_rules):
            for file_path in files:
                # 检查文件
                result = checker.check_file(file_path)

                # 标记完成
                tracker.mark_completed(check_id, file_path)

        # 5. 验证进度
        state = tracker.load_state(check_id)
        assert state is not None
        assert len(state.completed_files) == len(files)
        assert len(state.remaining_files) == 0


@pytest.mark.integration
class TestConcurrentCheck:
    """测试并发检查功能"""

    @pytest.fixture
    def temp_files(self, tmp_path):
        """创建多个测试文件"""
        files = []
        for i in range(10):
            file_path = tmp_path / f"file_{i}.py"
            file_path.write_text(f"""
def function_{i}():
    # Test function {i}
    if True:
        pass
""")
            files.append(str(file_path))
        return files

    @pytest.fixture
    def mock_llm(self):
        """创建 Mock LLM"""
        llm = Mock()
        mock_response = Mock()
        mock_response.output = "```json\n[]\n```"  # 无问题
        llm.chat_oai.return_value = [mock_response]
        return llm

    def test_concurrent_check_results(self, temp_files, mock_llm, mock_args):
        """测试并发检查结果一致性"""
        checker = CodeChecker(mock_llm, mock_args)

        # Mock 规则
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
            # 使用生成器收集结果
            results = list(checker.check_files_concurrent(temp_files, max_workers=3))

            # 验证所有文件都被检查
            assert len(results) == len(temp_files)

            # 验证每个结果
            for result in results:
                assert result.status in ["success", "skipped", "failed"]
                assert result.file_path in temp_files

    def test_concurrent_check_thread_safety(self, temp_files, mock_llm, mock_args):
        """测试并发检查的线程安全性"""
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
            # 多次并发检查
            for _ in range(3):
                results = list(checker.check_files_concurrent(temp_files, max_workers=5))
                assert len(results) == len(temp_files)


@pytest.mark.integration
class TestErrorHandling:
    """测试错误处理的集成场景"""

    @pytest.fixture
    def mock_llm_error(self):
        """创建会失败的 Mock LLM"""
        llm = Mock()
        llm.chat_oai.side_effect = Exception("LLM API error")
        return llm

    def test_llm_error_handling(self, tmp_path, mock_llm_error, mock_args):
        """测试 LLM 错误处理"""
        # 创建测试文件
        test_file = tmp_path / "test.py"
        test_file.write_text("def test(): pass")

        checker = CodeChecker(mock_llm_error, mock_args)

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
            # 检查应该失败但不抛出异常
            result = checker.check_file(str(test_file))

            # 应该返回空结果（因为 LLM 调用失败）
            assert result.status == "success"  # 不应该失败整个检查
            assert len(result.issues) == 0  # 但没有发现问题

    def test_file_not_found_handling(self, mock_llm, mock_args):
        """测试文件不存在的处理"""
        checker = CodeChecker(mock_llm, mock_args)

        # 检查不存在的文件
        result = checker.check_file("/nonexistent/file.py")

        # 应该返回失败状态
        assert result.status == "failed"
        assert result.error_message is not None


@pytest.mark.integration
class TestLargeFileHandling:
    """测试大文件处理"""

    @pytest.fixture
    def large_file(self, tmp_path):
        """创建大文件"""
        file_path = tmp_path / "large.py"

        # 生成大量代码（超过 chunk_size）
        lines = []
        for i in range(1000):
            lines.append(f"def function_{i}():\n")
            lines.append(f"    # Function {i}\n")
            lines.append(f"    pass\n")
            lines.append(f"\n")

        file_path.write_text("".join(lines))
        return str(file_path)

    @pytest.fixture
    def mock_llm(self):
        """创建 Mock LLM"""
        llm = Mock()
        mock_response = Mock()
        mock_response.output = "```json\n[]\n```"
        llm.chat_oai.return_value = [mock_response]
        return llm

    def test_large_file_chunking(self, large_file, mock_llm, mock_args):
        """测试大文件分块处理"""
        checker = CodeChecker(mock_llm, mock_args)

        # 分块文件
        chunks = checker.file_processor.chunk_file(large_file)

        # 应该被分成多个块
        assert len(chunks) > 1

        # 验证块的连续性
        for i in range(len(chunks) - 1):
            current_chunk = chunks[i]
            next_chunk = chunks[i + 1]

            # 检查行号连续（考虑 overlap）
            assert next_chunk.start_line <= current_chunk.end_line + 1

    def test_large_file_check_workflow(self, large_file, mock_llm, mock_args):
        """测试大文件检查完整流程"""
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
            result = checker.check_file(large_file)

            # 检查应该成功
            assert result.status == "success"

            # LLM 应该被调用多次（每个 chunk 一次）
            chunks = checker.file_processor.chunk_file(large_file)
            assert mock_llm.chat_oai.call_count >= len(chunks)


@pytest.mark.integration
class TestResumeWorkflow:
    """测试中断恢复工作流"""

    @pytest.fixture
    def temp_files(self, tmp_path):
        """创建多个测试文件"""
        files = []
        for i in range(5):
            file_path = tmp_path / f"file_{i}.py"
            file_path.write_text(f"def func_{i}(): pass")
            files.append(str(file_path))
        return files

    @pytest.fixture
    def mock_llm(self):
        """创建 Mock LLM"""
        llm = Mock()
        mock_response = Mock()
        mock_response.output = "```json\n[]\n```"
        llm.chat_oai.return_value = [mock_response]
        return llm

    def test_interrupt_and_resume(self, temp_files, mock_llm, mock_args, tmp_path):
        """测试中断和恢复流程"""
        # 1. 创建进度跟踪器
        progress_dir = tmp_path / ".progress"
        progress_dir.mkdir()
        tracker = ProgressTracker(state_dir=str(progress_dir))

        # 2. 开始检查
        check_id = tracker.start_check(
            files=temp_files,
            config={},
            project_name="test"
        )

        # 3. 模拟检查一部分文件（模拟中断）
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
            # 只检查前 3 个文件
            for file_path in temp_files[:3]:
                checker.check_file(file_path)
                tracker.mark_completed(check_id, file_path)

        # 4. 验证状态
        state = tracker.load_state(check_id)
        assert len(state.completed_files) == 3
        assert len(state.remaining_files) == 2

        # 5. 恢复检查剩余文件
        remaining = state.remaining_files
        for file_path in remaining:
            checker.check_file(file_path)
            tracker.mark_completed(check_id, file_path)

        # 6. 验证全部完成
        state = tracker.load_state(check_id)
        assert len(state.completed_files) == 5
        assert len(state.remaining_files) == 0


@pytest.mark.integration
class TestEndToEndScenarios:
    """端到端场景测试"""

    @pytest.fixture
    def real_project(self, tmp_path):
        """创建真实项目结构"""
        # 创建项目目录
        project = tmp_path / "myproject"
        project.mkdir()

        # 创建源码目录
        src = project / "src"
        src.mkdir()

        # 创建测试目录
        tests = project / "tests"
        tests.mkdir()

        # 创建配置文件
        (project / "config.py").write_text("DEBUG = True")

        # 创建源码文件
        (src / "main.py").write_text("""
def main():
    if True:
        if True:
            pass
""")

        (src / "utils.py").write_text("""
def helper(x):
    return x
""")

        # 创建测试文件
        (tests / "test_main.py").write_text("""
def test_main():
    assert True
""")

        return project

    @pytest.fixture
    def mock_llm(self):
        """创建 Mock LLM"""
        llm = Mock()
        mock_response = Mock()
        mock_response.output = "```json\n[]\n```"
        llm.chat_oai.return_value = [mock_response]
        return llm

    def test_full_project_check(self, real_project, mock_llm, mock_args):
        """测试完整项目检查"""
        # 1. 扫描项目
        file_processor = FileProcessor()
        filters = FileFilters(
            extensions=[".py"],
            ignored=["tests", "__pycache__"]
        )

        files = file_processor.scan_files(str(real_project), filters)

        # 应该找到 src 下的文件，忽略 tests
        assert len(files) >= 2  # main.py, utils.py, config.py
        assert all("tests" not in f for f in files)

        # 2. 检查所有文件
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
            results = checker.check_files(files)

            # 3. 生成报告
            report_dir = real_project / "reports"
            report_dir.mkdir()

            generator = ReportGenerator()

            # 生成每个文件的报告
            for file_result in results.file_results:
                generator.generate_file_report(file_result, str(report_dir))

            # 生成汇总报告
            generator.generate_summary_report(results.file_results, str(report_dir))

            # 4. 验证报告
            summary_file = report_dir / "summary.md"
            assert summary_file.exists()

            summary_json = report_dir / "summary.json"
            assert summary_json.exists()

            # 验证报告内容
            summary_content = summary_file.read_text()
            assert "检查完成时间" in summary_content
            assert "总文件数" in summary_content
