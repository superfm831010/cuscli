"""
报告生成器单元测试
"""

import unittest
import os
import json
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

from autocoder.checker.report_generator import ReportGenerator
from autocoder.checker.types import (
    FileCheckResult,
    BatchCheckResult,
    Issue,
    Severity
)


class TestReportGenerator(unittest.TestCase):
    """报告生成器测试"""

    def setUp(self):
        """测试前准备"""
        # 创建临时目录
        self.test_dir = tempfile.mkdtemp()
        self.generator = ReportGenerator(output_dir=self.test_dir)

    def tearDown(self):
        """测试后清理"""
        # 删除临时目录
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_init(self):
        """测试初始化"""
        gen = ReportGenerator(output_dir="test_output")
        self.assertEqual(gen.output_dir, "test_output")

    def test_safe_path(self):
        """测试路径转换"""
        gen = ReportGenerator()

        # 测试斜杠替换
        self.assertEqual(
            gen._safe_path("autocoder/checker/core.py"),
            "autocoder_checker_core_py"
        )

        # 测试反斜杠替换
        self.assertEqual(
            gen._safe_path("path\\to\\file.js"),
            "path_to_file_js"
        )

        # 测试混合路径
        self.assertEqual(
            gen._safe_path("src/app\\main.ts"),
            "src_app_main_ts"
        )

        # 测试前导斜杠
        self.assertEqual(
            gen._safe_path("/root/file.py"),
            "root_file_py"
        )

    def test_generate_json_report_with_pydantic_model(self):
        """测试使用 pydantic 模型生成 JSON 报告"""
        # 创建测试数据
        issue = Issue(
            rule_id="test_001",
            severity=Severity.ERROR,
            line_start=10,
            line_end=15,
            description="测试问题",
            suggestion="测试建议"
        )

        result = FileCheckResult(
            file_path="test.py",
            check_time=datetime.now().isoformat(),
            issues=[issue],
            error_count=1,
            warning_count=0,
            info_count=0,
            status="success"
        )

        # 生成 JSON 报告
        output_path = os.path.join(self.test_dir, "test.json")
        self.generator._generate_json_report(result, output_path)

        # 验证文件存在
        self.assertTrue(os.path.exists(output_path))

        # 验证 JSON 格式
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertEqual(data['file_path'], "test.py")
        self.assertEqual(data['error_count'], 1)
        self.assertEqual(len(data['issues']), 1)
        self.assertEqual(data['issues'][0]['rule_id'], "test_001")

    def test_generate_json_report_with_dict(self):
        """测试使用字典生成 JSON 报告"""
        data = {
            "test": "value",
            "number": 123,
            "nested": {"key": "value"}
        }

        output_path = os.path.join(self.test_dir, "dict_test.json")
        self.generator._generate_json_report(data, output_path)

        # 验证
        with open(output_path, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)

        self.assertEqual(loaded_data, data)

    def test_generate_markdown_report(self):
        """测试生成 Markdown 报告"""
        content = "# Test Report\n\nThis is a test."
        output_path = os.path.join(self.test_dir, "test.md")

        self.generator._generate_markdown_report(content, output_path)

        # 验证文件存在
        self.assertTrue(os.path.exists(output_path))

        # 验证内容
        with open(output_path, 'r', encoding='utf-8') as f:
            saved_content = f.read()

        self.assertEqual(saved_content, content)

    def test_format_file_markdown_with_issues(self):
        """测试格式化单文件 Markdown（有问题）"""
        issues = [
            Issue(
                rule_id="backend_001",
                severity=Severity.ERROR,
                line_start=10,
                line_end=10,
                description="测试错误",
                suggestion="修复建议1"
            ),
            Issue(
                rule_id="backend_002",
                severity=Severity.WARNING,
                line_start=20,
                line_end=25,
                description="测试警告",
                suggestion="修复建议2",
                code_snippet="def test():\n    pass"
            ),
            Issue(
                rule_id="backend_003",
                severity=Severity.INFO,
                line_start=30,
                line_end=30,
                description="测试提示",
                suggestion="修复建议3"
            )
        ]

        result = FileCheckResult(
            file_path="test.py",
            check_time="2025-10-10T10:00:00",
            issues=issues,
            error_count=1,
            warning_count=1,
            info_count=1,
            status="success"
        )

        md = self.generator._format_file_markdown(result)

        # 验证内容
        self.assertIn("# 📄 文件检查报告", md)
        self.assertIn("test.py", md)
        self.assertIn("✅", md)  # success 状态
        self.assertIn("❌ 错误 (1)", md)
        self.assertIn("⚠️ 警告 (1)", md)
        self.assertIn("ℹ️ 提示 (1)", md)
        self.assertIn("测试错误", md)
        self.assertIn("测试警告", md)
        self.assertIn("测试提示", md)
        self.assertIn("backend_001", md)
        self.assertIn("backend_002", md)
        self.assertIn("backend_003", md)
        self.assertIn("def test():", md)  # 代码片段

    def test_format_file_markdown_without_issues(self):
        """测试格式化单文件 Markdown（无问题）"""
        result = FileCheckResult(
            file_path="clean_file.py",
            check_time="2025-10-10T10:00:00",
            issues=[],
            error_count=0,
            warning_count=0,
            info_count=0,
            status="success"
        )

        md = self.generator._format_file_markdown(result)

        # 验证内容
        self.assertIn("✅ 未发现问题", md)
        self.assertIn("恭喜", md)

    def test_format_file_markdown_failed_status(self):
        """测试格式化失败状态的文件 Markdown"""
        result = FileCheckResult(
            file_path="error_file.py",
            check_time="2025-10-10T10:00:00",
            issues=[],
            error_count=0,
            warning_count=0,
            info_count=0,
            status="failed",
            error_message="FileNotFoundError: 文件不存在"
        )

        md = self.generator._format_file_markdown(result)

        # 验证内容
        self.assertIn("❌", md)  # failed 状态
        self.assertIn("检查错误", md)
        self.assertIn("FileNotFoundError", md)

    def test_format_summary_markdown_with_issues(self):
        """测试格式化汇总 Markdown（有问题）"""
        # 创建多个文件结果
        results = [
            FileCheckResult(
                file_path="file1.py",
                check_time="2025-10-10T10:00:00",
                issues=[
                    Issue(
                        rule_id="test_001",
                        severity=Severity.ERROR,
                        line_start=10,
                        line_end=10,
                        description="错误1",
                        suggestion="建议1"
                    ),
                    Issue(
                        rule_id="test_002",
                        severity=Severity.WARNING,
                        line_start=20,
                        line_end=20,
                        description="警告1",
                        suggestion="建议2"
                    )
                ],
                error_count=1,
                warning_count=1,
                info_count=0,
                status="success"
            ),
            FileCheckResult(
                file_path="file2.py",
                check_time="2025-10-10T10:01:00",
                issues=[
                    Issue(
                        rule_id="test_003",
                        severity=Severity.INFO,
                        line_start=5,
                        line_end=5,
                        description="提示1",
                        suggestion="建议3"
                    )
                ],
                error_count=0,
                warning_count=0,
                info_count=1,
                status="success"
            )
        ]

        batch_result = BatchCheckResult(
            check_id="test_check_001",
            start_time="2025-10-10T10:00:00",
            end_time="2025-10-10T10:05:00",
            total_files=2,
            checked_files=2,
            total_issues=3,
            total_errors=1,
            total_warnings=1,
            total_infos=1,
            file_results=results
        )

        md = self.generator._format_summary_markdown(batch_result)

        # 验证内容
        self.assertIn("# 📊 代码检查汇总报告", md)
        self.assertIn("test_check_001", md)
        self.assertIn("总文件数", md)
        self.assertIn("| 2 |", md)  # 总文件数
        self.assertIn("问题详情", md)
        self.assertIn("file1.py", md)
        self.assertIn("file2.py", md)
        self.assertIn("错误1", md)
        self.assertIn("警告1", md)
        self.assertIn("提示1", md)

    def test_format_summary_markdown_no_issues(self):
        """测试格式化汇总 Markdown（无问题）"""
        results = [
            FileCheckResult(
                file_path="clean1.py",
                check_time="2025-10-10T10:00:00",
                issues=[],
                error_count=0,
                warning_count=0,
                info_count=0,
                status="success"
            )
        ]

        batch_result = BatchCheckResult(
            check_id="test_check_002",
            start_time="2025-10-10T10:00:00",
            end_time="2025-10-10T10:00:01",
            total_files=1,
            checked_files=1,
            total_issues=0,
            total_errors=0,
            total_warnings=0,
            total_infos=0,
            file_results=results
        )

        md = self.generator._format_summary_markdown(batch_result)

        # 验证内容
        self.assertIn("✅ 检查完成", md)
        self.assertIn("所有文件均未发现问题", md)

    def test_generate_file_report(self):
        """测试生成完整的文件报告"""
        issue = Issue(
            rule_id="test_001",
            severity=Severity.WARNING,
            line_start=15,
            line_end=20,
            description="测试问题",
            suggestion="测试建议"
        )

        result = FileCheckResult(
            file_path="autocoder/test.py",
            check_time=datetime.now().isoformat(),
            issues=[issue],
            error_count=0,
            warning_count=1,
            info_count=0,
            status="success"
        )

        report_dir = os.path.join(self.test_dir, "test_report")
        self.generator.generate_file_report(result, report_dir)

        # 验证文件存在
        files_dir = os.path.join(report_dir, "files")
        self.assertTrue(os.path.exists(files_dir))

        # 验证 JSON 文件
        json_file = os.path.join(files_dir, "autocoder_test_py.json")
        self.assertTrue(os.path.exists(json_file))

        # 验证 Markdown 文件
        md_file = os.path.join(files_dir, "autocoder_test_py.md")
        self.assertTrue(os.path.exists(md_file))

        # 验证 JSON 内容
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.assertEqual(data['warning_count'], 1)

        # 验证 Markdown 内容
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
        self.assertIn("测试问题", md_content)

    def test_generate_summary_report(self):
        """测试生成汇总报告"""
        results = [
            FileCheckResult(
                file_path="file1.py",
                check_time=datetime.now().isoformat(),
                issues=[],
                error_count=0,
                warning_count=0,
                info_count=0,
                status="success"
            ),
            FileCheckResult(
                file_path="file2.py",
                check_time=datetime.now().isoformat(),
                issues=[
                    Issue(
                        rule_id="test_001",
                        severity=Severity.ERROR,
                        line_start=10,
                        line_end=10,
                        description="错误",
                        suggestion="建议"
                    )
                ],
                error_count=1,
                warning_count=0,
                info_count=0,
                status="success"
            )
        ]

        report_dir = os.path.join(self.test_dir, "summary_report")
        self.generator.generate_summary_report(results, report_dir)

        # 验证目录存在
        self.assertTrue(os.path.exists(report_dir))

        # 验证 JSON 文件
        json_file = os.path.join(report_dir, "summary.json")
        self.assertTrue(os.path.exists(json_file))

        # 验证 Markdown 文件
        md_file = os.path.join(report_dir, "summary.md")
        self.assertTrue(os.path.exists(md_file))

        # 验证 JSON 内容
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.assertEqual(data['total_files'], 2)
        self.assertEqual(data['total_errors'], 1)

        # 验证 Markdown 内容
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
        self.assertIn("file1.py", md_content)
        self.assertIn("file2.py", md_content)

    def test_directory_auto_creation(self):
        """测试目录自动创建"""
        # 使用不存在的深层目录
        deep_path = os.path.join(self.test_dir, "a", "b", "c", "test.json")

        data = {"test": "value"}
        self.generator._generate_json_report(data, deep_path)

        # 验证目录和文件都被创建
        self.assertTrue(os.path.exists(deep_path))

    def test_format_issue_markdown(self):
        """测试格式化单个问题"""
        issue = Issue(
            rule_id="test_001",
            severity=Severity.ERROR,
            line_start=10,
            line_end=15,
            description="这是一个测试问题",
            suggestion="这是修复建议",
            code_snippet="def test():\n    return None"
        )

        md = self.generator._format_issue_markdown(1, issue)

        # 验证内容
        self.assertIn("### 问题 1", md)
        self.assertIn("第 10-15 行", md)
        self.assertIn("test_001", md)
        self.assertIn("这是一个测试问题", md)
        self.assertIn("这是修复建议", md)
        self.assertIn("def test():", md)

    def test_format_issue_markdown_single_line(self):
        """测试格式化单行问题"""
        issue = Issue(
            rule_id="test_002",
            severity=Severity.WARNING,
            line_start=20,
            line_end=20,  # 单行
            description="单行问题",
            suggestion="建议"
        )

        md = self.generator._format_issue_markdown(1, issue)

        # 验证显示为单行而不是范围
        self.assertIn("第 20 行", md)
        self.assertNotIn("20-20", md)

    def test_empty_issues_list(self):
        """测试空问题列表"""
        result = FileCheckResult(
            file_path="empty.py",
            check_time=datetime.now().isoformat(),
            issues=[],
            error_count=0,
            warning_count=0,
            info_count=0,
            status="success"
        )

        md = self.generator._format_file_markdown(result)
        self.assertIn("未发现问题", md)


class TestReportGeneratorEdgeCases(unittest.TestCase):
    """报告生成器边界情况测试"""

    def test_long_file_path(self):
        """测试超长文件路径"""
        gen = ReportGenerator()
        long_path = "a" * 100 + "/b" * 100 + "/file.py"
        safe = gen._safe_path(long_path)

        # 验证所有斜杠都被替换
        self.assertNotIn("/", safe)
        self.assertNotIn("\\", safe)

    def test_special_characters_in_path(self):
        """测试路径中的特殊字符"""
        gen = ReportGenerator()
        special_path = "path/with spaces/and-dashes_and.dots.py"
        safe = gen._safe_path(special_path)

        # 验证斜杠和点被替换
        self.assertNotIn("/", safe)
        self.assertNotIn(".", safe)
        # 但空格、连字符、下划线被保留或替换
        self.assertIn("with", safe)

    def test_markdown_escaping(self):
        """测试 Markdown 中的特殊字符"""
        gen = ReportGenerator()
        issue = Issue(
            rule_id="test_001",
            severity=Severity.INFO,
            line_start=1,
            line_end=1,
            description="描述中包含 `代码` 和 **粗体**",
            suggestion="建议中包含 [链接](url)"
        )

        md = gen._format_issue_markdown(1, issue)

        # 验证特殊字符被包含（不需要转义，Markdown 会正确处理）
        self.assertIn("`代码`", md)
        self.assertIn("**粗体**", md)


if __name__ == '__main__':
    unittest.main()
