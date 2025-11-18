"""
代码检查报告生成器

支持生成 JSON 和 Markdown 格式的检查报告。
"""

import json
import os
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

from autocoder.checker.types import (
    FileCheckResult,
    BatchCheckResult,
    GitInfo,
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
        self, results: List[FileCheckResult], report_dir: str, git_info: Optional[GitInfo] = None
    ) -> None:
        """
        生成批量检查的汇总报告（JSON + Markdown）

        Args:
            results: 所有文件的检查结果列表
            report_dir: 报告输出目录
            git_info: Git 检查信息（可选，Phase 4 新增）
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
                file_results=results,
                git_info=git_info  # Phase 4: 传递 Git 信息
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
"""

        # Phase 5: 显示审核模式和统计信息
        if result.audit_mode:
            audit_mode_icon = "🎯" if result.audit_mode == "diff-only" else "📄"
            audit_mode_text = "Diff-Only（差异审核）" if result.audit_mode == "diff-only" else "全文件审核"
            md += f"**审核模式**: {audit_mode_icon} {audit_mode_text}\n"

            if result.audit_stats and result.audit_mode == "diff-only":
                audit_summary = result.get_audit_summary()
                if audit_summary:
                    md += f"**审核范围**: {audit_summary}\n"

        md += f"**问题总数**: {result.get_total_issues()} 个\n\n"
        md += f"""## 📊 问题统计

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

    def _get_git_report_title(self, git_info: GitInfo) -> str:
        """
        根据 Git 类型生成报告标题（Phase 4）

        Args:
            git_info: Git 检查信息

        Returns:
            报告标题字符串
        """
        if git_info.type == "staged":
            return "代码检查报告 - Git 暂存区"
        elif git_info.type == "unstaged":
            return "代码检查报告 - Git 工作区"
        elif git_info.type == "commit":
            return "代码检查报告 - Git Commit"
        elif git_info.type == "diff":
            return "代码检查报告 - Git Diff"
        else:
            return "代码检查报告"

    def _format_git_info_markdown(self, git_info: GitInfo) -> List[str]:
        """
        格式化 Git 信息为 Markdown（Phase 4）

        Args:
            git_info: Git 检查信息

        Returns:
            Markdown 格式的 Git 信息行列表
        """
        lines = []

        if git_info.type == "staged":
            lines.append("**检查类型**: Git 暂存区文件")
            if git_info.branch:
                lines.append(f"**当前分支**: {git_info.branch}")
            lines.append(f"**文件数量**: {git_info.files_changed} 个")

        elif git_info.type == "unstaged":
            lines.append("**检查类型**: Git 工作区修改文件")
            if git_info.branch:
                lines.append(f"**当前分支**: {git_info.branch}")
            lines.append(f"**文件数量**: {git_info.files_changed} 个")

        elif git_info.type == "commit":
            lines.append("**检查类型**: Git Commit 检查")
            if git_info.short_hash and git_info.message:
                # 截断过长的 commit message（只显示第一行）
                message_first_line = git_info.message.splitlines()[0] if git_info.message else ""
                if len(message_first_line) > 80:
                    message_first_line = message_first_line[:77] + "..."
                lines.append(f"**Commit**: `{git_info.short_hash}` - {message_first_line}")
            if git_info.author:
                lines.append(f"**作者**: {git_info.author}")
            if git_info.date:
                lines.append(f"**日期**: {git_info.date}")
            lines.append(f"**变更文件**: {git_info.files_changed} 个")

        elif git_info.type == "diff":
            lines.append("**检查类型**: Git Diff 检查")
            if git_info.commit1 and git_info.commit2:
                lines.append(f"**对比范围**: `{git_info.commit1}`...`{git_info.commit2}`")
            lines.append(f"**差异文件**: {git_info.files_changed} 个")

        return lines

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

        # Phase 4: 根据是否有 Git 信息决定标题
        if batch_result.git_info:
            title = self._get_git_report_title(batch_result.git_info)
        else:
            title = "代码检查汇总报告"

        # 构建 Markdown 内容
        md = f"# 📊 {title}\n\n"

        # Phase 4: 如果有 Git 信息，先显示 Git 信息
        if batch_result.git_info:
            git_lines = self._format_git_info_markdown(batch_result.git_info)
            for line in git_lines:
                md += f"{line}\n"
            md += f"**检查时间**: {batch_result.end_time}\n"
            md += "\n---\n\n"
        else:
            # 非 Git 检查，显示原有的检查 ID 和时间信息
            md += f"**检查 ID**: `{batch_result.check_id}`\n"
            md += f"**开始时间**: {batch_result.start_time}\n"
            md += f"**结束时间**: {batch_result.end_time}\n"
            md += f"**总耗时**: {duration_str}\n\n"

        md += "## 📈 检查概览\n\n"
        md += "| 统计项 | 数量 |\n"
        md += "|--------|------|\n"
        md += f"| 总文件数 | {batch_result.total_files} |\n"
        md += f"| 已检查文件 | {batch_result.checked_files} |\n"
        md += f"| 完成率 | {batch_result.get_completion_rate():.1f}% |\n"
        md += f"| **总问题数** | **{batch_result.total_issues}** |\n\n"

        # Phase 5: 显示审核模式统计
        diff_only_files = [r for r in batch_result.file_results if r.audit_mode == "diff-only"]
        full_files = [r for r in batch_result.file_results if r.audit_mode == "full"]

        if diff_only_files:
            md += "## 🎯 审核模式统计\n\n"
            md += "| 审核模式 | 文件数 | 占比 |\n"
            md += "|---------|-------|------|\n"
            md += f"| 🎯 Diff-Only（差异审核） | {len(diff_only_files)} | {len(diff_only_files) / batch_result.total_files * 100:.1f}% |\n"
            md += f"| 📄 全文件审核 | {len(full_files)} | {len(full_files) / batch_result.total_files * 100:.1f}% |\n\n"

            # 计算 diff-only 模式的整体效率提升
            total_audited = sum(r.audit_stats.get("audited_lines", 0) for r in diff_only_files if r.audit_stats)
            total_lines = sum(r.audit_stats.get("total_lines", 0) for r in diff_only_files if r.audit_stats)

            if total_lines > 0:
                overall_coverage = int(total_audited / total_lines * 100)
                efficiency_gain = 100 - overall_coverage

                md += f"**Diff-Only 模式效率**:\n"
                md += f"- 审核了 {total_audited:,}/{total_lines:,} 行代码\n"
                md += f"- 覆盖率: {overall_coverage}%\n"
                md += f"- 效率提升: 约 {efficiency_gain}% Token 节省\n\n"
                md += "---\n\n"


        md += "## 🔍 问题分布\n\n"
        md += "| 严重程度 | 数量 | 占比 |\n"
        md += "|---------|------|------|\n"
        md += f"| ❌ 错误 (ERROR) | {batch_result.total_errors} | {batch_result.total_errors / max(batch_result.total_issues, 1) * 100:.1f}% |\n"
        md += f"| ⚠️ 警告 (WARNING) | {batch_result.total_warnings} | {batch_result.total_warnings / max(batch_result.total_issues, 1) * 100:.1f}% |\n"
        md += f"| ℹ️ 提示 (INFO) | {batch_result.total_infos} | {batch_result.total_infos / max(batch_result.total_issues, 1) * 100:.1f}% |\n\n"
        md += "---\n\n"
        md += "## 📋 文件检查详情\n\n"

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
        将文件路径转换为安全的短文件名

        使用"文件名_扩展名_哈希"格式，避免路径过长。
        哈希值基于完整路径计算，确保不同路径的同名文件不会冲突。

        Args:
            file_path: 原始文件路径

        Returns:
            安全的短文件名（格式：filename_ext_hash6）

        Examples:
            >>> gen = ReportGenerator()
            >>> gen._safe_path("autocoder/checker/core.py")
            'core_py_a1b2c3'
            >>> gen._safe_path("autocoder/plugins/core.py")
            'core_py_d4e5f6'  # 不同路径的同名文件，哈希不同
            >>> gen._safe_path("docs/二次开发记录.md")
            '二次开发记录_md_f7g8h9'
        """
        # 规范化路径分隔符（统一使用正斜杠），确保跨平台哈希一致性
        normalized_path = file_path.replace('\\', '/')

        # 提取文件名（不含路径）
        filename = os.path.basename(normalized_path)

        # 分离文件名和扩展名
        name_parts = filename.rsplit('.', 1)
        if len(name_parts) == 2:
            base_name, extension = name_parts
        else:
            base_name = name_parts[0]
            extension = ''

        # 清理文件名中的特殊字符（保留中文、字母、数字、下划线、短横线）
        def clean_name(s):
            # Windows 非法字符: < > : " / \ | ? *
            illegal_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
            result = s
            for char in illegal_chars:
                result = result.replace(char, '_')
            # 去除前后空格
            result = result.strip()
            # 如果为空，使用默认名称
            if not result:
                result = 'unnamed'
            return result

        clean_base_name = clean_name(base_name)
        clean_extension = clean_name(extension) if extension else ''

        # 计算完整路径的哈希值（6位十六进制）
        # 使用 MD5 算法，确保跨平台一致性
        path_hash = hashlib.md5(normalized_path.encode('utf-8')).hexdigest()[:6]

        # 组合文件名：文件名_扩展名_哈希
        if clean_extension:
            safe_filename = f"{clean_base_name}_{clean_extension}_{path_hash}"
        else:
            safe_filename = f"{clean_base_name}_{path_hash}"

        # 限制总长度（避免超长文件名）
        # Windows 文件名限制 255 字符，留余量给报告扩展名 (.json/.md)
        if len(safe_filename) > 100:
            # 如果太长，截断文件名部分（保留扩展名和哈希）
            max_base_len = 100 - len(clean_extension) - len(path_hash) - 2  # 2个下划线
            if clean_extension:
                safe_filename = f"{clean_base_name[:max_base_len]}_{clean_extension}_{path_hash}"
            else:
                safe_filename = f"{clean_base_name[:max_base_len]}_{path_hash}"

        return safe_filename
