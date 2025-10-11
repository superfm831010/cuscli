#!/usr/bin/env python3
"""
代码检测功能手动测试脚本

用于在没有交互式界面的情况下测试代码检测功能
"""

import os
import sys
from datetime import datetime
from unittest.mock import Mock, patch

# 添加项目路径
sys.path.insert(0, '/projects/cuscli')

from autocoder.checker.core import CodeChecker
from autocoder.checker.rules_loader import RulesLoader
from autocoder.checker.file_processor import FileProcessor
from autocoder.checker.report_generator import ReportGenerator
from autocoder.checker.types import FileFilters, Rule, Severity
from autocoder.auto_coder import AutoCoderArgs


def create_mock_llm():
    """创建模拟的 LLM 用于测试"""
    llm = Mock()

    # 模拟检查响应 - 返回一些示例问题
    mock_response = Mock()
    mock_response.output = """```json
[
    {
        "rule_id": "backend_006",
        "severity": "warning",
        "line_start": 95,
        "line_end": 840,
        "description": "main函数过长，包含大量嵌套逻辑和配置代码，超过30行标准",
        "suggestion": "建议将main函数拆分为多个小函数，如：setup_llm_config(), setup_models(), handle_commands()等",
        "code_snippet": "def main(input_args: Optional[List[str]] = None):\\n    args, raw_args = parse_args(input_args)\\n    ..."
    },
    {
        "rule_id": "backend_009",
        "severity": "info",
        "line_start": 50,
        "line_end": 56,
        "description": "resolve_include_path 函数功能单一，符合规范",
        "suggestion": "无需修改，代码质量良好"
    },
    {
        "rule_id": "backend_006",
        "severity": "error",
        "line_start": 216,
        "line_end": 475,
        "description": "存在深层嵌套的if-else判断逻辑，嵌套层数超过3层",
        "suggestion": "建议使用策略模式或字典映射来简化判断逻辑"
    }
]
```"""

    llm.chat_oai.return_value = [mock_response]
    return llm


def test_single_file_check():
    """测试单文件检查"""
    print("=" * 80)
    print("测试1: 单文件检查 - autocoder/auto_coder.py")
    print("=" * 80)
    print()

    # 创建测试环境
    llm = create_mock_llm()
    args = AutoCoderArgs()

    # 初始化检查器
    checker = CodeChecker(llm, args)

    # 目标文件
    test_file = "/projects/cuscli/autocoder/auto_coder.py"

    print(f"📁 目标文件: {test_file}")
    print(f"📊 文件大小: {os.path.getsize(test_file) / 1024:.2f} KB")

    with open(test_file) as f:
        line_count = len(f.readlines())
    print(f"📝 文件行数: {line_count}")
    print()

    # 加载规则
    print("📋 加载检查规则...")
    rules_loader = RulesLoader()
    rules = rules_loader.get_applicable_rules(test_file)
    print(f"✅ 已加载 {len(rules)} 条规则")
    print()

    # 检查文件
    print("🔍 开始检查文件...")
    start_time = datetime.now()

    # Mock 规则加载器
    with patch.object(checker.rules_loader, 'get_applicable_rules', return_value=rules):
        result = checker.check_file(test_file)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print(f"✅ 检查完成! 耗时: {duration:.2f}秒")
    print()

    # 显示结果
    print("=" * 80)
    print("检查结果汇总")
    print("=" * 80)
    print(f"状态: {result.status}")
    print(f"发现问题总数: {len(result.issues)}")
    print(f"  ❌ 错误 (ERROR):   {result.error_count}")
    print(f"  ⚠️  警告 (WARNING): {result.warning_count}")
    print(f"  ℹ️  提示 (INFO):    {result.info_count}")
    print()

    # 显示问题详情
    if result.issues:
        print("=" * 80)
        print("问题详情")
        print("=" * 80)
        for i, issue in enumerate(result.issues, 1):
            severity_icon = {
                Severity.ERROR: "❌",
                Severity.WARNING: "⚠️",
                Severity.INFO: "ℹ️"
            }.get(issue.severity, "?")

            severity_str = issue.severity if isinstance(issue.severity, str) else issue.severity.value
            print(f"\n{i}. {severity_icon} [{severity_str.upper()}] {issue.rule_id}")
            print(f"   位置: 第 {issue.line_start}-{issue.line_end} 行")
            print(f"   问题: {issue.description}")
            print(f"   建议: {issue.suggestion}")
            if issue.code_snippet:
                print(f"   代码: {issue.code_snippet[:100]}...")

    print()

    # 生成报告
    print("=" * 80)
    print("生成检查报告")
    print("=" * 80)
    report_dir = f"/projects/cuscli/codecheck/manual_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(report_dir, exist_ok=True)
    os.makedirs(os.path.join(report_dir, "files"), exist_ok=True)

    generator = ReportGenerator()
    generator.generate_file_report(result, report_dir)

    print(f"✅ 报告已生成: {report_dir}")
    print(f"   - Markdown: {report_dir}/files/autocoder_auto_coder_py.md")
    print(f"   - JSON: {report_dir}/files/autocoder_auto_coder_py.json")
    print()

    return result, report_dir


def test_batch_check():
    """测试批量检查"""
    print("=" * 80)
    print("测试2: 批量检查 - autocoder/checker/ 目录")
    print("=" * 80)
    print()

    # 创建测试环境
    llm = create_mock_llm()
    args = AutoCoderArgs()
    checker = CodeChecker(llm, args)

    # 扫描文件
    file_processor = FileProcessor()
    filters = FileFilters(extensions=[".py"])
    test_dir = "/projects/cuscli/autocoder/checker"

    print(f"📁 目标目录: {test_dir}")
    files = file_processor.scan_files(test_dir, filters)
    print(f"✅ 找到 {len(files)} 个Python文件")
    for f in files:
        print(f"   - {os.path.basename(f)}")
    print()

    # 加载规则
    rules_loader = RulesLoader()
    sample_file = files[0] if files else ""
    rules = rules_loader.get_applicable_rules(sample_file)
    print(f"📋 已加载 {len(rules)} 条规则")
    print()

    # 批量检查
    print("🔍 开始批量检查...")
    start_time = datetime.now()

    with patch.object(checker.rules_loader, 'get_applicable_rules', return_value=rules):
        batch_result = checker.check_files(files)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print(f"✅ 批量检查完成! 耗时: {duration:.2f}秒")
    print()

    # 显示结果
    print("=" * 80)
    print("批量检查结果汇总")
    print("=" * 80)
    print(f"总文件数: {batch_result.total_files}")
    print(f"已检查: {batch_result.checked_files}")
    print(f"总问题数: {batch_result.total_issues}")
    print(f"  ❌ 错误:   {batch_result.total_errors}")
    print(f"  ⚠️  警告: {batch_result.total_warnings}")
    print(f"  ℹ️  提示:  {batch_result.total_infos}")
    print()

    # 显示各文件问题统计
    print("各文件问题统计:")
    for file_result in batch_result.file_results:
        if len(file_result.issues) > 0:
            print(f"  {os.path.basename(file_result.file_path)}: {len(file_result.issues)} 个问题")
    print()

    # 生成报告
    print("=" * 80)
    print("生成批量检查报告")
    print("=" * 80)
    report_dir = f"/projects/cuscli/codecheck/batch_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(report_dir, exist_ok=True)
    os.makedirs(os.path.join(report_dir, "files"), exist_ok=True)

    generator = ReportGenerator()

    # 生成单文件报告
    for file_result in batch_result.file_results:
        generator.generate_file_report(file_result, report_dir)

    # 生成汇总报告
    generator.generate_summary_report(batch_result.file_results, report_dir)

    print(f"✅ 报告已生成: {report_dir}")
    print(f"   - 汇总报告: {report_dir}/summary.md")
    print(f"   - 单文件报告: {report_dir}/files/ (共 {len(files)} 个)")
    print()

    return batch_result, report_dir


def main():
    """主函数"""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "代码检测功能手动测试" + " " * 20 + "           ║")
    print("╚" + "=" * 78 + "╝")
    print()

    try:
        # 测试1: 单文件检查
        single_result, single_report = test_single_file_check()

        print("\n" + "=" * 80 + "\n")

        # 测试2: 批量检查
        batch_result, batch_report = test_batch_check()

        # 总结
        print()
        print("╔" + "=" * 78 + "╗")
        print("║" + " " * 30 + "测试完成" + " " * 30 + "           ║")
        print("╚" + "=" * 78 + "╝")
        print()
        print("✅ 所有测试已完成!")
        print()
        print("📊 测试结果:")
        print(f"   - 单文件检查: {len(single_result.issues)} 个问题")
        print(f"   - 批量检查: {batch_result.total_issues} 个问题 ({batch_result.total_files} 个文件)")
        print()
        print("📄 报告位置:")
        print(f"   - 单文件: {single_report}")
        print(f"   - 批量:   {batch_report}")
        print()

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
