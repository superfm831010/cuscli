"""
代码检查报告生成器

支持生成 JSON 和 Markdown 格式的检查报告。
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from loguru import logger

from autocoder.checker.types import (
    FileCheckResult,
    BatchCheckResult,
    Issue,
    Severity
)


class ReportGenerator:
    """
    报告生成器

    支持生成单文件报告和批量检查汇总报告，支持 JSON 和 Markdown 两种格式。

    报告目录结构:
        codecheck/
        └── {check_id}_YYYYMMDD_HHMMSS/
            ├── check.log             # 检查任务日志（详细执行过程）
            ├── summary.json          # 批量检查汇总（JSON）
            ├── summary.md            # 批量检查汇总（Markdown）
            └── files/
                ├── with_issues/      # 有问题的文件报告
                │   ├── file1_py.json
                │   ├── file1_py.md
                │   └── ...
                └── no_issues/        # 无问题的文件报告
                    ├── file2_py.json
                    ├── file2_py.md
                    └── ...

    Attributes:
        output_dir: 报告输出根目录
    """

    def __init__(self, output_dir: str = "codecheck"):
        """
        初始化报告生成器

        Args:
            output_dir: 报告输出根目录，默认为 "codecheck"
        """
        self.output_dir = output_dir
        logger.info(f"报告生成器已初始化，输出目录: {output_dir}")

    def generate_file_report(
        self, result: FileCheckResult, report_dir: str
    ) -> None:
        """
        生成单个文件的检查报告（JSON + Markdown）

        Args:
            result: 文件检查结果
            report_dir: 报告输出目录

        Raises:
            RuntimeError: 如果报告生成失败
        """
        try:
            # 根据是否有问题决定保存到哪个子目录
            has_issues = result.get_total_issues() > 0
            subdir = "with_issues" if has_issues else "no_issues"

            # 创建对应的子目录
            files_dir = os.path.join(report_dir, "files", subdir)
            os.makedirs(files_dir, exist_ok=True)

            # 生成安全的文件名
            safe_filename = self._safe_path(result.file_path)

            # 生成 JSON 报告
            json_path = os.path.join(files_dir, f"{safe_filename}.json")
            self._generate_json_report(result, json_path)

            # 验证 JSON 文件是否真的创建成功
            if not os.path.exists(json_path):
                raise RuntimeError(
                    f"JSON 报告文件未创建成功: {json_path}\n"
                    f"可能原因：权限不足、磁盘空间不足或路径包含特殊字符"
                )

            # 生成 Markdown 报告
            md_path = os.path.join(files_dir, f"{safe_filename}.md")
            md_content = self._format_file_markdown(result)
            self._generate_markdown_report(md_content, md_path)

            # 验证 Markdown 文件是否真的创建成功
            if not os.path.exists(md_path):
                raise RuntimeError(
                    f"Markdown 报告文件未创建成功: {md_path}\n"
                    f"可能原因：权限不足、磁盘空间不足或路径包含特殊字符"
                )

            logger.info(f"已生成文件报告: {result.file_path} -> {subdir}")

        except Exception as e:
            error_msg = f"生成文件报告失败 {result.file_path}: {e}"
            logger.error(error_msg, exc_info=True)
            # 重新抛出异常，让调用者知道报告生成失败
            raise RuntimeError(error_msg) from e

    def generate_summary_report(
        self, results: List[FileCheckResult], report_dir: str
    ) -> None:
        """
        生成批量检查的汇总报告（JSON + Markdown）

        Args:
            results: 所有文件的检查结果列表
            report_dir: 报告输出目录
        """
        try:
            # 确保报告目录存在
            os.makedirs(report_dir, exist_ok=True)

            # 构建批量检查结果
            start_time = datetime.now().isoformat()
            end_time = datetime.now().isoformat()

            total_issues = sum(len(r.issues) for r in results)
            total_errors = sum(r.error_count for r in results)
            total_warnings = sum(r.warning_count for r in results)
            total_infos = sum(r.info_count for r in results)

            batch_result = BatchCheckResult(
                check_id=os.path.basename(report_dir),
                start_time=start_time,
                end_time=end_time,
                total_files=len(results),
                checked_files=len([r for r in results if r.status == "success"]),
                total_issues=total_issues,
                total_errors=total_errors,
                total_warnings=total_warnings,
                total_infos=total_infos,
                file_results=results
            )

            # 生成 JSON 汇总报告
            json_path = os.path.join(report_dir, "summary.json")
            self._generate_json_report(batch_result, json_path)

            # 生成 Markdown 汇总报告
            md_path = os.path.join(report_dir, "summary.md")
            md_content = self._format_summary_markdown(batch_result)
            self._generate_markdown_report(md_content, md_path)

            logger.info(f"已生成汇总报告: {report_dir}")

        except Exception as e:
            logger.error(f"生成汇总报告失败: {e}", exc_info=True)

    def _generate_json_report(self, data: Any, output_path: str) -> None:
        """
        生成 JSON 格式报告

        Args:
            data: 要保存的数据（支持 pydantic 模型）
            output_path: 输出文件路径

        Raises:
            OSError: 如果文件写入失败
            RuntimeError: 如果文件创建后验证失败
        """
        try:
            # 确保目录存在
            parent_dir = os.path.dirname(output_path)
            if parent_dir:  # 避免空字符串导致的问题
                os.makedirs(parent_dir, exist_ok=True)

            # 如果是 pydantic 模型，使用 model_dump
            if hasattr(data, 'model_dump'):
                json_data = data.model_dump()
            else:
                json_data = data

            # 写入 JSON 文件
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)

            # 验证文件是否真的创建成功
            if not os.path.exists(output_path):
                raise RuntimeError(
                    f"JSON 文件写入后验证失败，文件不存在: {output_path}\n"
                    f"可能原因：写入时发生错误但未抛出异常"
                )

            # 验证文件大小
            file_size = os.path.getsize(output_path)
            if file_size == 0:
                raise RuntimeError(
                    f"JSON 文件写入后验证失败，文件大小为 0: {output_path}"
                )

            logger.debug(f"JSON 报告已保存: {output_path} (大小: {file_size} 字节)")

        except (OSError, IOError) as e:
            error_msg = f"生成 JSON 报告失败 {output_path}: {e}"
            logger.error(error_msg, exc_info=True)
            raise OSError(error_msg) from e
        except Exception as e:
            error_msg = f"生成 JSON 报告时发生未预期的错误 {output_path}: {e}"
            logger.error(error_msg, exc_info=True)
            raise

    def _generate_markdown_report(self, content: str, output_path: str) -> None:
        """
        生成 Markdown 格式报告

        Args:
            content: Markdown 内容
            output_path: 输出文件路径

        Raises:
            OSError: 如果文件写入失败
            RuntimeError: 如果文件创建后验证失败
        """
        try:
            # 确保目录存在
            parent_dir = os.path.dirname(output_path)
            if parent_dir:  # 避免空字符串导致的问题
                os.makedirs(parent_dir, exist_ok=True)

            # 写入 Markdown 文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # 验证文件是否真的创建成功
            if not os.path.exists(output_path):
                raise RuntimeError(
                    f"Markdown 文件写入后验证失败，文件不存在: {output_path}\n"
                    f"可能原因：写入时发生错误但未抛出异常"
                )

            # 验证文件大小
            file_size = os.path.getsize(output_path)
            if file_size == 0:
                raise RuntimeError(
                    f"Markdown 文件写入后验证失败，文件大小为 0: {output_path}"
                )

            logger.debug(f"Markdown 报告已保存: {output_path} (大小: {file_size} 字节)")

        except (OSError, IOError) as e:
            error_msg = f"生成 Markdown 报告失败 {output_path}: {e}"
            logger.error(error_msg, exc_info=True)
            raise OSError(error_msg) from e
        except Exception as e:
            error_msg = f"生成 Markdown 报告时发生未预期的错误 {output_path}: {e}"
            logger.error(error_msg, exc_info=True)
            raise

    def _format_file_markdown(self, result: FileCheckResult) -> str:
        """
        格式化单文件检查结果为 Markdown

        Args:
            result: 文件检查结果

        Returns:
            Markdown 格式的报告内容
        """
        # 确定状态图标
        status_icon = {
            "success": "✅",
            "failed": "❌",
            "skipped": "⏭️"
        }.get(result.status, "❓")

        # 构建 Markdown 内容
        md = f"""# 📄 文件检查报告

**文件路径**: `{result.file_path}`
**检查时间**: {result.check_time}
**检查状态**: {status_icon} {result.status}
**问题总数**: {result.get_total_issues()} 个

## 📊 问题统计

| 严重程度 | 数量 |
|---------|------|
| ❌ 错误 (ERROR) | {result.error_count} |
| ⚠️ 警告 (WARNING) | {result.warning_count} |
| ℹ️ 提示 (INFO) | {result.info_count} |
| **总计** | **{result.get_total_issues()}** |

---

"""

        # 如果检查失败，显示错误信息
        if result.status == "failed" and result.error_message:
            md += f"""## ❌ 检查错误

```
{result.error_message}
```

---

"""

        # 如果没有问题
        if not result.issues:
            md += """## ✅ 未发现问题

恭喜！此文件未发现任何代码规范问题。

"""
            return md

        # 按严重程度分组
        errors = [i for i in result.issues if i.severity == Severity.ERROR]
        warnings = [i for i in result.issues if i.severity == Severity.WARNING]
        infos = [i for i in result.issues if i.severity == Severity.INFO]

        # 显示错误
        if errors:
            md += f"## ❌ 错误 ({len(errors)})\n\n"
            md += "以下问题必须修复，可能导致系统崩溃、安全漏洞或数据丢失：\n\n"
            for idx, issue in enumerate(errors, 1):
                md += self._format_issue_markdown(idx, issue)

        # 显示警告
        if warnings:
            md += f"## ⚠️ 警告 ({len(warnings)})\n\n"
            md += "以下问题强烈建议修复，影响代码质量、性能或可维护性：\n\n"
            for idx, issue in enumerate(warnings, 1):
                md += self._format_issue_markdown(idx, issue)

        # 显示提示
        if infos:
            md += f"## ℹ️ 提示 ({len(infos)})\n\n"
            md += "以下是代码改进建议：\n\n"
            for idx, issue in enumerate(infos, 1):
                md += self._format_issue_markdown(idx, issue)

        return md

    def _format_issue_markdown(self, index: int, issue: Issue) -> str:
        """
        格式化单个问题为 Markdown

        Args:
            index: 问题序号
            issue: 问题对象

        Returns:
            Markdown 格式的问题描述
        """
        md = f"### 问题 {index}\n\n"
        md += f"- **位置**: 第 {issue.line_start}"
        if issue.line_end != issue.line_start:
            # 计算实际行数（包含性：line_end - line_start + 1）
            line_count = issue.line_end - issue.line_start + 1
            md += f"-{issue.line_end} 行（共 {line_count} 行）\n"
        else:
            md += " 行\n"
        md += f"- **规则**: `{issue.rule_id}`\n"
        md += f"- **描述**: {issue.description}\n"
        md += f"- **建议**: {issue.suggestion}\n"

        # 如果有代码片段
        if issue.code_snippet:
            md += f"\n**问题代码**:\n```\n{issue.code_snippet}\n```\n"

        md += "\n---\n\n"
        return md

    def _format_summary_markdown(self, batch_result: BatchCheckResult) -> str:
        """
        格式化批量检查结果为 Markdown

        Args:
            batch_result: 批量检查结果

        Returns:
            Markdown 格式的汇总报告内容
        """
        # 计算耗时
        duration = batch_result.get_duration_seconds()
        duration_str = f"{duration:.2f} 秒"
        if duration >= 60:
            duration_str = f"{duration / 60:.2f} 分钟"

        # 构建 Markdown 内容
        md = f"""# 📊 代码检查汇总报告

**检查 ID**: `{batch_result.check_id}`
**开始时间**: {batch_result.start_time}
**结束时间**: {batch_result.end_time}
**总耗时**: {duration_str}

## 📈 检查概览

| 统计项 | 数量 |
|--------|------|
| 总文件数 | {batch_result.total_files} |
| 已检查文件 | {batch_result.checked_files} |
| 完成率 | {batch_result.get_completion_rate():.1f}% |
| **总问题数** | **{batch_result.total_issues}** |

## 🔍 问题分布

| 严重程度 | 数量 | 占比 |
|---------|------|------|
| ❌ 错误 (ERROR) | {batch_result.total_errors} | {batch_result.total_errors / max(batch_result.total_issues, 1) * 100:.1f}% |
| ⚠️ 警告 (WARNING) | {batch_result.total_warnings} | {batch_result.total_warnings / max(batch_result.total_issues, 1) * 100:.1f}% |
| ℹ️ 提示 (INFO) | {batch_result.total_infos} | {batch_result.total_infos / max(batch_result.total_issues, 1) * 100:.1f}% |

---

## 📋 文件检查详情

"""

        # 按问题数量排序文件
        sorted_results = sorted(
            batch_result.file_results,
            key=lambda r: r.get_total_issues(),
            reverse=True
        )

        # 创建文件汇总表格
        md += "| 文件路径 | 状态 | 错误 | 警告 | 提示 | 总计 |\n"
        md += "|---------|------|------|------|------|------|\n"

        for result in sorted_results:
            status_icon = {
                "success": "✅",
                "failed": "❌",
                "skipped": "⏭️"
            }.get(result.status, "❓")

            # 截断过长的路径
            file_path = result.file_path
            if len(file_path) > 50:
                file_path = "..." + file_path[-47:]

            md += f"| `{file_path}` | {status_icon} | "
            md += f"{result.error_count} | {result.warning_count} | "
            md += f"{result.info_count} | **{result.get_total_issues()}** |\n"

        md += "\n---\n\n"

        # 显示有问题的文件详情
        files_with_issues = [r for r in sorted_results if r.get_total_issues() > 0]

        if not files_with_issues:
            md += """## ✅ 检查完成

所有文件均未发现问题，代码质量良好！

"""
            return md

        md += f"## 🔴 问题详情 (共 {len(files_with_issues)} 个文件有问题)\n\n"

        for file_result in files_with_issues:
            md += f"### 📄 {file_result.file_path}\n\n"
            md += f"**问题数**: {file_result.get_total_issues()} 个 "
            md += f"(❌ {file_result.error_count} ⚠️ {file_result.warning_count} "
            md += f"ℹ️ {file_result.info_count})\n\n"

            # 按严重程度分组问题
            errors = [i for i in file_result.issues if i.severity == Severity.ERROR]
            warnings = [i for i in file_result.issues if i.severity == Severity.WARNING]
            infos = [i for i in file_result.issues if i.severity == Severity.INFO]

            # 显示问题列表（简化版）
            for issue in errors[:3]:  # 最多显示 3 个错误
                md += f"- ❌ **第 {issue.line_start} 行**: {issue.description}\n"

            if len(errors) > 3:
                md += f"  _... 还有 {len(errors) - 3} 个错误_\n"

            for issue in warnings[:2]:  # 最多显示 2 个警告
                md += f"- ⚠️ **第 {issue.line_start} 行**: {issue.description}\n"

            if len(warnings) > 2:
                md += f"  _... 还有 {len(warnings) - 2} 个警告_\n"

            for issue in infos[:1]:  # 最多显示 1 个提示
                md += f"- ℹ️ **第 {issue.line_start} 行**: {issue.description}\n"

            if len(infos) > 1:
                md += f"  _... 还有 {len(infos) - 1} 个提示_\n"

            md += "\n"

        # 添加总结
        md += "---\n\n"
        md += "## 📝 建议\n\n"

        if batch_result.total_errors > 0:
            md += f"- ❌ 发现 **{batch_result.total_errors}** 个错误，请优先修复\n"

        if batch_result.total_warnings > 0:
            md += f"- ⚠️ 发现 **{batch_result.total_warnings}** 个警告，建议修复以提高代码质量\n"

        if batch_result.total_infos > 0:
            md += f"- ℹ️ 发现 **{batch_result.total_infos}** 个改进建议，可考虑优化\n"

        md += "\n## 📋 日志文件\n\n"
        md += "本次检查的详细执行日志已保存在：\n\n"
        md += f"- **日志文件**: `check.log`\n\n"
        md += "**日志文件用途**：\n"
        md += "- 记录完整的检查执行过程（文件扫描、规则加载、LLM 调用等）\n"
        md += "- 包含详细的 DEBUG 级别信息，便于问题排查\n"
        md += "- 记录所有警告和错误信息\n"
        md += "- 适用场景：\n"
        md += "  - 检查过程异常中断，需要了解中断原因\n"
        md += "  - LLM 调用失败或超时，需要查看详细错误信息\n"
        md += "  - 需要了解检查过程的性能数据（各文件耗时等）\n\n"

        md += "## 📁 报告文件组织\n\n"
        md += "为便于快速查看，报告文件已按问题分类存储：\n\n"

        # 统计有问题和无问题的文件数量
        files_with_issues = len([r for r in batch_result.file_results if r.get_total_issues() > 0])
        files_no_issues = len([r for r in batch_result.file_results if r.get_total_issues() == 0])

        md += f"- **有问题的文件** ({files_with_issues} 个): `files/with_issues/` 目录\n"
        md += f"- **无问题的文件** ({files_no_issues} 个): `files/no_issues/` 目录\n"
        md += f"- **日志文件**: `check.log`（详细执行过程）\n"
        md += "\n💡 **提示**: 优先查看 `files/with_issues/` 目录中的报告进行修复。如需排查问题，可查看 `check.log` 日志文件。\n"

        return md

    def _safe_path(self, file_path: str) -> str:
        """
        将文件路径转换为安全的文件名

        将路径中的斜杠、反斜杠、点等特殊字符替换为下划线。
        处理所有 Windows 非法字符，确保跨平台兼容性。

        Args:
            file_path: 原始文件路径

        Returns:
            安全的文件名（最长 200 字符）

        Examples:
            >>> gen = ReportGenerator()
            >>> gen._safe_path("autocoder/checker/core.py")
            'autocoder_checker_core_py'
            >>> gen._safe_path("path\\to\\file.js")
            'path_to_file_js'
            >>> gen._safe_path("file:with*invalid?chars.txt")
            'file_with_invalid_chars_txt'
        """
        # Windows 非法字符: < > : " / \ | ? *
        # 统一替换为下划线
        illegal_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        safe = file_path
        for char in illegal_chars:
            safe = safe.replace(char, '_')

        # 替换点号（扩展名分隔符）
        safe = safe.replace('.', '_')

        # 去除开头的下划线
        safe = safe.lstrip('_')

        # 限制文件名长度（Windows 限制 255，留一些余量给扩展名）
        if len(safe) > 200:
            safe = safe[:200]

        # 如果处理后为空，返回一个默认名称
        if not safe:
            safe = "unnamed_file"

        return safe
