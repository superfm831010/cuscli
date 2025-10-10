"""
代码检查报告生成器

支持生成 JSON 和 Markdown 格式的检查报告。
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from autocoder.checker.types import (
    FileCheckResult,
    BatchCheckResult,
    Issue,
    Severity
)
from autocoder.utils.log import log

logger = log.get_logger(__name__)


class ReportGenerator:
    """
    报告生成器

    支持生成单文件报告和批量检查汇总报告，支持 JSON 和 Markdown 两种格式。

    报告目录结构:
        codecheck/
        └── {check_id}_YYYYMMDD_HHMMSS/
            ├── summary.json          # 批量检查汇总（JSON）
            ├── summary.md            # 批量检查汇总（Markdown）
            └── files/
                ├── file1_py.json     # 单文件报告（JSON）
                ├── file1_py.md       # 单文件报告（Markdown）
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
        """
        try:
            # 创建 files 子目录
            files_dir = os.path.join(report_dir, "files")
            os.makedirs(files_dir, exist_ok=True)

            # 生成安全的文件名
            safe_filename = self._safe_path(result.file_path)

            # 生成 JSON 报告
            json_path = os.path.join(files_dir, f"{safe_filename}.json")
            self._generate_json_report(result, json_path)

            # 生成 Markdown 报告
            md_path = os.path.join(files_dir, f"{safe_filename}.md")
            md_content = self._format_file_markdown(result)
            self._generate_markdown_report(md_content, md_path)

            logger.info(f"已生成文件报告: {result.file_path}")

        except Exception as e:
            logger.error(f"生成文件报告失败 {result.file_path}: {e}", exc_info=True)

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
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # 如果是 pydantic 模型，使用 model_dump
            if hasattr(data, 'model_dump'):
                json_data = data.model_dump()
            else:
                json_data = data

            # 写入 JSON 文件
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)

            logger.debug(f"JSON 报告已保存: {output_path}")

        except Exception as e:
            logger.error(f"生成 JSON 报告失败 {output_path}: {e}", exc_info=True)
            raise

    def _generate_markdown_report(self, content: str, output_path: str) -> None:
        """
        生成 Markdown 格式报告

        Args:
            content: Markdown 内容
            output_path: 输出文件路径
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # 写入 Markdown 文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.debug(f"Markdown 报告已保存: {output_path}")

        except Exception as e:
            logger.error(f"生成 Markdown 报告失败 {output_path}: {e}", exc_info=True)
            raise

    def _format_file_markdown(self, result: FileCheckResult) -> str:
        """
        格式化单文件检查结果为 Markdown

        Args:
            result: 文件检查结果

        Returns:
            Markdown 格式的报告内容
        """
        # 此方法将在 Task 6.3 中实现
        return f"# 文件检查报告: {result.file_path}\n\n（待实现）"

    def _format_summary_markdown(self, batch_result: BatchCheckResult) -> str:
        """
        格式化批量检查结果为 Markdown

        Args:
            batch_result: 批量检查结果

        Returns:
            Markdown 格式的汇总报告内容
        """
        # 此方法将在 Task 6.3 中实现
        return f"# 批量检查汇总报告\n\n（待实现）"

    def _safe_path(self, file_path: str) -> str:
        """
        将文件路径转换为安全的文件名

        将路径中的斜杠、反斜杠、点等特殊字符替换为下划线

        Args:
            file_path: 原始文件路径

        Returns:
            安全的文件名

        Examples:
            >>> gen = ReportGenerator()
            >>> gen._safe_path("autocoder/checker/core.py")
            'autocoder_checker_core_py'
            >>> gen._safe_path("path\\to\\file.js")
            'path_to_file_js'
        """
        # 替换路径分隔符和点
        safe = file_path.replace('/', '_').replace('\\', '_').replace('.', '_')
        # 去除开头的下划线
        safe = safe.lstrip('_')
        return safe
