"""
测试类型定义模块
"""

import pytest
from datetime import datetime

from autocoder.checker.types import (
    Severity,
    Rule,
    Issue,
    FileCheckResult,
    BatchCheckResult,
    CheckState,
    CodeChunk,
    FileFilters,
)


class TestSeverity:
    """测试 Severity 枚举"""

    def test_severity_values(self):
        """测试严重程度的值"""
        assert Severity.ERROR.value == "error"
        assert Severity.WARNING.value == "warning"
        assert Severity.INFO.value == "info"

    def test_severity_enum(self):
        """测试枚举类型"""
        assert isinstance(Severity.ERROR, Severity)
        assert len(list(Severity)) == 3


class TestRule:
    """测试 Rule 类"""

    def test_rule_creation(self):
        """测试规则创建"""
        rule = Rule(
            id="backend_001",
            category="代码结构",
            title="测试规则",
            description="这是一个测试规则",
            severity=Severity.WARNING
        )
        assert rule.id == "backend_001"
        assert rule.category == "代码结构"
        assert rule.enabled is True
        assert rule.severity == Severity.WARNING

    def test_rule_with_examples(self):
        """测试带示例的规则"""
        rule = Rule(
            id="backend_002",
            category="安全性",
            title="安全规则",
            description="安全检查",
            severity=Severity.ERROR,
            examples="示例代码"
        )
        assert rule.examples == "示例代码"

    def test_rule_disabled(self):
        """测试禁用规则"""
        rule = Rule(
            id="backend_003",
            category="其他",
            title="禁用规则",
            description="这个规则被禁用",
            severity=Severity.INFO,
            enabled=False
        )
        assert rule.enabled is False


class TestIssue:
    """测试 Issue 类"""

    def test_issue_creation(self):
        """测试问题创建"""
        issue = Issue(
            rule_id="backend_001",
            severity=Severity.ERROR,
            line_start=10,
            line_end=15,
            description="发现错误",
            suggestion="修复建议"
        )
        assert issue.rule_id == "backend_001"
        assert issue.line_start == 10
        assert issue.line_end == 15
        assert issue.description == "发现错误"

    def test_issue_with_code_snippet(self):
        """测试带代码片段的问题"""
        issue = Issue(
            rule_id="backend_002",
            severity=Severity.WARNING,
            line_start=20,
            line_end=25,
            description="发现警告",
            suggestion="修复建议",
            code_snippet="def foo():\n    pass"
        )
        assert issue.code_snippet is not None


class TestFileCheckResult:
    """测试 FileCheckResult 类"""

    def test_file_check_result_creation(self):
        """测试文件检查结果创建"""
        result = FileCheckResult(
            file_path="test.py",
            check_time=datetime.now().isoformat(),
            status="success"
        )
        assert result.file_path == "test.py"
        assert result.status == "success"
        assert result.error_count == 0
        assert result.get_total_issues() == 0

    def test_file_check_result_with_issues(self):
        """测试带问题的文件检查结果"""
        issues = [
            Issue(
                rule_id="backend_001",
                severity=Severity.ERROR,
                line_start=10,
                line_end=15,
                description="错误1",
                suggestion="建议1"
            ),
            Issue(
                rule_id="backend_002",
                severity=Severity.WARNING,
                line_start=20,
                line_end=25,
                description="警告1",
                suggestion="建议2"
            )
        ]

        result = FileCheckResult(
            file_path="test.py",
            check_time=datetime.now().isoformat(),
            issues=issues,
            error_count=1,
            warning_count=1,
            status="success"
        )

        assert result.get_total_issues() == 2
        assert result.has_errors() is True


class TestBatchCheckResult:
    """测试 BatchCheckResult 类"""

    def test_batch_check_result_creation(self):
        """测试批量检查结果创建"""
        result = BatchCheckResult(
            check_id="test_20251010_120000",
            start_time=datetime.now().isoformat(),
            end_time=datetime.now().isoformat(),
            total_files=10,
            checked_files=10
        )
        assert result.check_id == "test_20251010_120000"
        assert result.total_files == 10
        assert result.get_completion_rate() == 100.0

    def test_batch_check_result_partial(self):
        """测试部分完成的批量检查结果"""
        result = BatchCheckResult(
            check_id="test_20251010_120000",
            start_time=datetime.now().isoformat(),
            end_time=datetime.now().isoformat(),
            total_files=10,
            checked_files=5
        )
        assert result.get_completion_rate() == 50.0


class TestCheckState:
    """测试 CheckState 类"""

    def test_check_state_creation(self):
        """测试检查状态创建"""
        state = CheckState(
            check_id="test_20251010_120000",
            start_time=datetime.now().isoformat(),
            total_files=["file1.py", "file2.py", "file3.py"],
            completed_files=["file1.py"],
            remaining_files=["file2.py", "file3.py"]
        )
        assert state.check_id == "test_20251010_120000"
        assert len(state.total_files) == 3
        assert len(state.completed_files) == 1
        assert state.get_progress_percentage() == pytest.approx(33.33, rel=0.01)


class TestCodeChunk:
    """测试 CodeChunk 类"""

    def test_code_chunk_creation(self):
        """测试代码分块创建"""
        chunk = CodeChunk(
            content="def foo():\n    pass",
            start_line=1,
            end_line=2,
            chunk_index=0
        )
        assert chunk.start_line == 1
        assert chunk.end_line == 2
        assert chunk.get_line_count() == 2


class TestFileFilters:
    """测试 FileFilters 类"""

    def test_file_filters_creation(self):
        """测试文件过滤器创建"""
        filters = FileFilters(
            extensions=[".py", ".js"],
            ignored=["__pycache__", "*.pyc"]
        )
        assert ".py" in filters.extensions
        assert "__pycache__" in filters.ignored

    def test_should_ignore(self):
        """测试忽略判断"""
        filters = FileFilters(
            ignored=["__pycache__", "node_modules", "*.pyc"]
        )
        assert filters.should_ignore("__pycache__/test.py") is True
        assert filters.should_ignore("src/main.py") is False
        assert filters.should_ignore("test.pyc") is True

    def test_matches_extension(self):
        """测试扩展名匹配"""
        filters = FileFilters(extensions=[".py", ".js"])
        assert filters.matches_extension("test.py") is True
        assert filters.matches_extension("test.js") is True
        assert filters.matches_extension("test.txt") is False

    def test_no_filters(self):
        """测试无过滤条件"""
        filters = FileFilters()
        assert filters.should_ignore("any_file.py") is False
        assert filters.matches_extension("any_file.txt") is True
