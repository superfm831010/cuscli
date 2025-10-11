"""
核心检查器单元测试

测试 CodeChecker 类的所有核心功能
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from autocoder.checker.core import CodeChecker
from autocoder.checker.types import (
    Rule, Issue, Severity, FileCheckResult, CodeChunk
)


class TestCodeChecker:
    """CodeChecker 核心功能测试"""

    @pytest.fixture
    def mock_llm(self):
        """Mock LLM"""
        llm = Mock()
        # Mock chat_oai 返回
        mock_response = Mock()
        mock_response.output = """```json
[
    {
        "rule_id": "backend_001",
        "severity": "error",
        "line_start": 10,
        "line_end": 15,
        "description": "测试问题描述",
        "suggestion": "测试修复建议",
        "code_snippet": "test code snippet"
    }
]
```"""
        llm.chat_oai.return_value = [mock_response]
        return llm

    @pytest.fixture
    def mock_args(self):
        """Mock AutoCoderArgs"""
        args = Mock()
        args.source_dir = "/test/project"
        return args

    @pytest.fixture
    def checker(self, mock_llm, mock_args):
        """创建 CodeChecker 实例"""
        return CodeChecker(mock_llm, mock_args)

    def test_init(self, checker):
        """测试初始化"""
        assert checker.llm is not None
        assert checker.args is not None
        assert checker.rules_loader is not None
        assert checker.file_processor is not None
        assert checker.progress_tracker is not None
        assert checker.tokenizer is not None

    def test_format_rules_for_prompt(self, checker):
        """测试规则格式化"""
        rules = [
            Rule(
                id="test_001",
                category="测试",
                title="测试规则1",
                description="这是测试规则1的描述",
                severity=Severity.WARNING,
                examples="示例代码1"
            ),
            Rule(
                id="test_002",
                category="测试",
                title="测试规则2",
                description="这是测试规则2的描述",
                severity=Severity.ERROR
            )
        ]

        formatted = checker._format_rules_for_prompt(rules)

        # 验证格式化内容
        assert "test_001" in formatted
        assert "测试规则1" in formatted
        assert "warning" in formatted
        assert "示例代码1" in formatted

        assert "test_002" in formatted
        assert "测试规则2" in formatted
        assert "error" in formatted

    def test_parse_llm_response_with_json_block(self, checker):
        """测试解析带 JSON 代码块的响应"""
        response = """```json
[
    {
        "rule_id": "backend_001",
        "severity": "error",
        "line_start": 10,
        "line_end": 15,
        "description": "测试问题",
        "suggestion": "测试建议",
        "code_snippet": "test code"
    },
    {
        "rule_id": "backend_002",
        "severity": "warning",
        "line_start": 20,
        "line_end": 25,
        "description": "另一个问题",
        "suggestion": "另一个建议"
    }
]
```"""
        issues = checker._parse_llm_response(response)

        assert len(issues) == 2
        assert issues[0].rule_id == "backend_001"
        assert issues[0].severity == Severity.ERROR
        assert issues[0].line_start == 10
        assert issues[0].line_end == 15
        assert issues[0].description == "测试问题"
        assert issues[0].suggestion == "测试建议"
        assert issues[0].code_snippet == "test code"

        assert issues[1].rule_id == "backend_002"
        assert issues[1].severity == Severity.WARNING

    def test_parse_llm_response_without_code_block(self, checker):
        """测试解析不带代码块的纯 JSON"""
        response = '''[
    {
        "rule_id": "test_001",
        "severity": "info",
        "line_start": 5,
        "line_end": 8,
        "description": "纯 JSON 测试",
        "suggestion": "测试建议"
    }
]'''
        issues = checker._parse_llm_response(response)

        assert len(issues) == 1
        assert issues[0].rule_id == "test_001"
        assert issues[0].severity == Severity.INFO

    def test_parse_llm_response_empty_array(self, checker):
        """测试解析空数组"""
        response = "```json\n[]\n```"
        issues = checker._parse_llm_response(response)

        assert len(issues) == 0

    def test_parse_llm_response_invalid_json(self, checker):
        """测试解析无效 JSON"""
        response = "这不是有效的 JSON"
        issues = checker._parse_llm_response(response)

        assert len(issues) == 0

    def test_parse_llm_response_missing_required_fields(self, checker):
        """测试缺少必需字段的响应"""
        response = """```json
[
    {
        "rule_id": "test_001",
        "severity": "error",
        "line_start": 10
    }
]
```"""
        issues = checker._parse_llm_response(response)

        # 缺少必需字段的问题应该被跳过
        assert len(issues) == 0

    def test_parse_llm_response_invalid_severity(self, checker):
        """测试无效的 severity 值"""
        response = """```json
[
    {
        "rule_id": "test_001",
        "severity": "critical",
        "line_start": 10,
        "line_end": 15,
        "description": "测试",
        "suggestion": "建议"
    }
]
```"""
        issues = checker._parse_llm_response(response)

        # 无效的 severity 应该默认为 info
        assert len(issues) == 1
        assert issues[0].severity == Severity.INFO

    def test_merge_duplicate_issues(self, checker):
        """测试合并重复问题"""
        issues = [
            Issue(
                rule_id="test_001",
                severity=Severity.ERROR,
                line_start=10,
                line_end=15,
                description="短描述",
                suggestion="建议1"
            ),
            Issue(
                rule_id="test_001",
                severity=Severity.ERROR,
                line_start=10,
                line_end=15,
                description="这是一个更详细、更长的描述",
                suggestion="建议2"
            ),
            Issue(
                rule_id="test_002",
                severity=Severity.WARNING,
                line_start=20,
                line_end=25,
                description="不同的问题",
                suggestion="建议3"
            )
        ]

        merged = checker._merge_duplicate_issues(issues)

        # 应该合并为 2 个问题
        assert len(merged) == 2

        # 第一个问题应该保留描述更详细的
        assert merged[0].rule_id == "test_001"
        assert merged[0].description == "这是一个更详细、更长的描述"

        # 第二个问题不变
        assert merged[1].rule_id == "test_002"

    def test_merge_duplicate_issues_empty(self, checker):
        """测试合并空列表"""
        merged = checker._merge_duplicate_issues([])
        assert len(merged) == 0

    def test_merge_duplicate_issues_sorting(self, checker):
        """测试合并后按行号排序"""
        issues = [
            Issue(
                rule_id="test_002",
                severity=Severity.ERROR,
                line_start=30,
                line_end=35,
                description="第三个",
                suggestion="建议"
            ),
            Issue(
                rule_id="test_001",
                severity=Severity.ERROR,
                line_start=10,
                line_end=15,
                description="第一个",
                suggestion="建议"
            ),
            Issue(
                rule_id="test_003",
                severity=Severity.ERROR,
                line_start=20,
                line_end=25,
                description="第二个",
                suggestion="建议"
            )
        ]

        merged = checker._merge_duplicate_issues(issues)

        # 应该按行号排序
        assert merged[0].line_start == 10
        assert merged[1].line_start == 20
        assert merged[2].line_start == 30

    def test_check_code_chunk_success(self, checker, mock_llm):
        """测试成功检查代码块"""
        code = "1 def test():\n2     pass"
        rules = [
            Rule(
                id="test_001",
                category="测试",
                title="测试规则",
                description="测试",
                severity=Severity.ERROR
            )
        ]

        issues = checker.check_code_chunk(code, rules)

        # 应该调用 LLM
        assert mock_llm.chat_oai.called

        # 应该返回解析后的问题
        assert len(issues) == 1
        assert issues[0].rule_id == "backend_001"

    def test_check_code_chunk_llm_error(self, checker, mock_llm):
        """测试 LLM 调用失败"""
        # Mock LLM 抛出异常
        mock_llm.chat_oai.side_effect = Exception("LLM error")

        code = "1 def test():\n2     pass"
        rules = [
            Rule(
                id="test_001",
                category="测试",
                title="测试规则",
                description="测试",
                severity=Severity.ERROR
            )
        ]

        issues = checker.check_code_chunk(code, rules)

        # 应该返回空列表
        assert len(issues) == 0

    @patch('autocoder.checker.core.CodeChecker.check_code_chunk')
    def test_check_file_success(self, mock_check_chunk, checker):
        """测试成功检查文件"""
        # Mock check_code_chunk 返回
        mock_check_chunk.return_value = [
            Issue(
                rule_id="backend_001",
                severity=Severity.ERROR,
                line_start=1,
                line_end=5,
                description="测试问题",
                suggestion="测试建议"
            )
        ]

        # Mock rules_loader
        with patch.object(checker.rules_loader, 'get_applicable_rules') as mock_get_rules:
            mock_get_rules.return_value = [
                Rule(
                    id="backend_001",
                    category="测试",
                    title="测试规则",
                    description="测试",
                    severity=Severity.ERROR
                )
            ]

            # Mock file_processor
            with patch.object(checker.file_processor, 'chunk_file') as mock_chunk_file:
                mock_chunk_file.return_value = [
                    CodeChunk(
                        content="1 test code",
                        start_line=1,
                        end_line=10,
                        chunk_index=0
                    )
                ]

                result = checker.check_file("test.py")

                assert result.status == "success"
                assert len(result.issues) == 1
                assert result.error_count == 1
                assert result.warning_count == 0
                assert result.info_count == 0

    def test_check_file_no_applicable_rules(self, checker):
        """测试文件无适用规则"""
        with patch.object(checker.rules_loader, 'get_applicable_rules') as mock_get_rules:
            mock_get_rules.return_value = []

            result = checker.check_file("unknown.txt")

            assert result.status == "skipped"
            assert len(result.issues) == 0

    def test_check_file_exception(self, checker):
        """测试检查文件时发生异常"""
        # Mock rules_loader 抛出异常
        with patch.object(checker.rules_loader, 'get_applicable_rules') as mock_get_rules:
            mock_get_rules.side_effect = Exception("Test error")

            result = checker.check_file("test.py")

            assert result.status == "failed"
            assert result.error_message == "Test error"

    def test_check_files_batch(self, checker):
        """测试批量检查文件"""
        with patch.object(checker, 'check_file') as mock_check_file:
            # Mock 两个文件的检查结果
            mock_check_file.side_effect = [
                FileCheckResult(
                    file_path="file1.py",
                    check_time=datetime.now().isoformat(),
                    issues=[
                        Issue(
                            rule_id="test_001",
                            severity=Severity.ERROR,
                            line_start=1,
                            line_end=5,
                            description="问题1",
                            suggestion="建议1"
                        )
                    ],
                    error_count=1,
                    warning_count=0,
                    info_count=0,
                    status="success"
                ),
                FileCheckResult(
                    file_path="file2.py",
                    check_time=datetime.now().isoformat(),
                    issues=[
                        Issue(
                            rule_id="test_002",
                            severity=Severity.WARNING,
                            line_start=10,
                            line_end=15,
                            description="问题2",
                            suggestion="建议2"
                        )
                    ],
                    error_count=0,
                    warning_count=1,
                    info_count=0,
                    status="success"
                )
            ]

            result = checker.check_files(["file1.py", "file2.py"])

            assert result.total_files == 2
            assert result.checked_files == 2
            assert result.total_issues == 2
            assert result.total_errors == 1
            assert result.total_warnings == 1
            assert result.total_infos == 0
            assert len(result.file_results) == 2


class TestCodeCheckerPrompt:
    """测试 Prompt 相关功能"""

    @pytest.fixture
    def checker(self):
        """创建 CodeChecker 实例（不需要真实 LLM）"""
        mock_llm = Mock()
        mock_args = Mock()
        mock_args.source_dir = "/test"
        return CodeChecker(mock_llm, mock_args)

    def test_check_code_prompt_structure(self, checker):
        """测试 Prompt 结构"""
        code = "1 def test():\n2     pass"
        rules = "### test_001: 测试规则"

        # 调用 prompt 方法获取渲染后的字符串
        prompt_text = checker.check_code_prompt.prompt(code, rules)

        # 验证 prompt 包含必要的元素
        assert isinstance(prompt_text, str)
        assert "代码审查专家" in prompt_text
        assert "test_001: 测试规则" in prompt_text
        assert "1 def test():" in prompt_text
        assert "2     pass" in prompt_text
        assert "JSON 数组格式" in prompt_text
        assert "rule_id" in prompt_text
        assert "severity" in prompt_text
        assert "line_start" in prompt_text


class TestValidateIssue:
    """测试 _validate_issue 方法（用于过滤 LLM 误判）"""

    @pytest.fixture
    def checker(self):
        """创建 CodeChecker 实例"""
        mock_llm = Mock()
        mock_args = Mock()
        mock_args.source_dir = "/test"
        return CodeChecker(mock_llm, mock_args)

    def test_backend_009_29_lines_should_pass(self, checker):
        """测试 backend_009：29 行方法应该合规（不报告）"""
        issue = Issue(
            rule_id="backend_009",
            severity=Severity.INFO,
            line_start=10,
            line_end=38,  # 38 - 10 + 1 = 29 行
            description="方法行数过多（29行），超过推荐的30行限制",
            suggestion="拆分方法"
        )

        # 29 行 <= 30，应该返回 False（不报告）
        assert checker._validate_issue(issue) is False

    def test_backend_009_30_lines_should_pass(self, checker):
        """测试 backend_009：30 行方法应该合规（不报告）"""
        issue = Issue(
            rule_id="backend_009",
            severity=Severity.INFO,
            line_start=10,
            line_end=39,  # 39 - 10 + 1 = 30 行
            description="方法行数过多（30行），超过推荐的30行限制",
            suggestion="拆分方法"
        )

        # 30 行 <= 30，应该返回 False（不报告）
        assert checker._validate_issue(issue) is False

    def test_backend_009_31_lines_should_fail(self, checker):
        """测试 backend_009：31 行方法应该违规（报告）"""
        issue = Issue(
            rule_id="backend_009",
            severity=Severity.INFO,
            line_start=10,
            line_end=40,  # 40 - 10 + 1 = 31 行
            description="方法行数过多（31行），超过推荐的30行限制",
            suggestion="拆分方法"
        )

        # 31 行 > 30，应该返回 True（报告）
        assert checker._validate_issue(issue) is True

    def test_backend_009_50_lines_should_fail(self, checker):
        """测试 backend_009：50 行方法应该违规（报告）"""
        issue = Issue(
            rule_id="backend_009",
            severity=Severity.INFO,
            line_start=100,
            line_end=149,  # 149 - 100 + 1 = 50 行
            description="方法行数过多（50行），超过推荐的30行限制",
            suggestion="拆分方法"
        )

        # 50 行 > 30，应该返回 True（报告）
        assert checker._validate_issue(issue) is True

    def test_other_rules_always_pass(self, checker):
        """测试其他规则不受 _validate_issue 影响（始终返回 True）"""
        # backend_006: 避免复杂嵌套
        issue1 = Issue(
            rule_id="backend_006",
            severity=Severity.WARNING,
            line_start=10,
            line_end=50,
            description="嵌套过深",
            suggestion="重构"
        )
        assert checker._validate_issue(issue1) is True

        # backend_001: 项目依赖规范
        issue2 = Issue(
            rule_id="backend_001",
            severity=Severity.ERROR,
            line_start=1,
            line_end=5,
            description="依赖不规范",
            suggestion="修改依赖"
        )
        assert checker._validate_issue(issue2) is True

    def test_backend_009_edge_case_1_line(self, checker):
        """测试 backend_009 边界情况：1 行方法（合规）"""
        issue = Issue(
            rule_id="backend_009",
            severity=Severity.INFO,
            line_start=10,
            line_end=10,  # 10 - 10 + 1 = 1 行
            description="方法行数过多",
            suggestion="拆分方法"
        )

        # 1 行 <= 30，应该返回 False（不报告）
        assert checker._validate_issue(issue) is False

    def test_parse_llm_response_with_backend_009_filter(self, checker):
        """测试解析 LLM 响应时自动过滤 backend_009 误判"""
        # 模拟 LLM 返回了一个 29 行的误报
        response = """```json
[
    {
        "rule_id": "backend_009",
        "severity": "info",
        "line_start": 10,
        "line_end": 38,
        "description": "方法行数过多（29行），超过推荐的30行限制",
        "suggestion": "拆分方法"
    },
    {
        "rule_id": "backend_009",
        "severity": "info",
        "line_start": 50,
        "line_end": 81,
        "description": "方法行数过多（32行），超过推荐的30行限制",
        "suggestion": "拆分方法"
    }
]
```"""
        issues = checker._parse_llm_response(response)

        # 29 行的应该被过滤，只保留 32 行的
        assert len(issues) == 1
        assert issues[0].line_start == 50
        assert issues[0].line_end == 81
        # 验证行数计算：81 - 50 + 1 = 32 行
