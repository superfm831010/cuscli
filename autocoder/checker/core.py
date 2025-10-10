"""
代码检查核心模块

功能：
1. 协调各模块完成检查任务
2. 调用 LLM 进行代码检查
3. 处理检查结果
4. 管理并发执行

作者: Claude AI
创建时间: 2025-10-10
"""

import os
import re
import json
from typing import List, Dict, Optional, Any
from datetime import datetime
from loguru import logger
import byzerllm

from autocoder.checker.types import (
    Rule, Issue, Severity, FileCheckResult,
    BatchCheckResult, CodeChunk
)
from autocoder.checker.rules_loader import RulesLoader
from autocoder.checker.file_processor import FileProcessor
from autocoder.checker.progress_tracker import ProgressTracker
from autocoder.auto_coder import AutoCoderArgs
from autocoder.common.tokenizer_env import BuildinTokenizer


class CodeChecker:
    """
    代码检查器核心类

    负责协调各模块完成代码规范检查任务。
    """

    def __init__(self, llm: byzerllm.ByzerLLM, args: AutoCoderArgs):
        """
        初始化代码检查器

        Args:
            llm: ByzerLLM 实例，用于调用大模型
            args: AutoCoderArgs 配置参数
        """
        self.llm = llm
        self.args = args
        self.rules_loader = RulesLoader()
        self.file_processor = FileProcessor()
        self.progress_tracker = ProgressTracker()
        self.tokenizer = BuildinTokenizer()

        logger.info("CodeChecker 初始化完成")

    def check_file(self, file_path: str) -> FileCheckResult:
        """
        检查单个文件

        Args:
            file_path: 文件路径

        Returns:
            FileCheckResult: 文件检查结果
        """
        logger.info(f"开始检查文件: {file_path}")

        try:
            start_time = datetime.now()

            # 1. 获取适用规则
            rules = self.rules_loader.get_applicable_rules(file_path)
            if not rules:
                logger.warning(f"文件 {file_path} 无适用规则，跳过检查")
                return FileCheckResult(
                    file_path=file_path,
                    check_time=start_time.isoformat(),
                    issues=[],
                    error_count=0,
                    warning_count=0,
                    info_count=0,
                    status="skipped"
                )

            logger.info(f"为文件 {file_path} 加载了 {len(rules)} 条规则")

            # 2. 分块处理
            chunks = self.file_processor.chunk_file(file_path)
            logger.info(f"文件 {file_path} 被分为 {len(chunks)} 个 chunk")

            # 3. 检查每个 chunk
            all_issues = []
            for chunk in chunks:
                logger.debug(f"检查 chunk {chunk.chunk_index}: 行 {chunk.start_line}-{chunk.end_line}")
                issues = self.check_code_chunk(chunk.content, rules)

                # 调整行号（chunk 的行号需要加上 chunk 的起始行偏移）
                # 注意：chunk.content 中的行号是从 1 开始的，需要映射到实际文件行号
                for issue in issues:
                    # issue.line_start 是相对于 chunk 的行号，需要转换为文件的实际行号
                    # chunk.start_line 是这个 chunk 在文件中的起始行号
                    actual_line_start = issue.line_start + chunk.start_line - 1
                    actual_line_end = issue.line_end + chunk.start_line - 1
                    issue.line_start = actual_line_start
                    issue.line_end = actual_line_end

                all_issues.extend(issues)
                logger.debug(f"Chunk {chunk.chunk_index} 发现 {len(issues)} 个问题")

            # 4. 合并重复问题
            merged_issues = self._merge_duplicate_issues(all_issues)
            logger.info(f"合并后共 {len(merged_issues)} 个问题")

            # 5. 统计
            error_count = sum(1 for i in merged_issues if i.severity == Severity.ERROR)
            warning_count = sum(1 for i in merged_issues if i.severity == Severity.WARNING)
            info_count = sum(1 for i in merged_issues if i.severity == Severity.INFO)

            logger.info(f"文件 {file_path} 检查完成: 错误={error_count}, 警告={warning_count}, 提示={info_count}")

            return FileCheckResult(
                file_path=file_path,
                check_time=datetime.now().isoformat(),
                issues=merged_issues,
                error_count=error_count,
                warning_count=warning_count,
                info_count=info_count,
                status="success"
            )

        except Exception as e:
            logger.error(f"检查文件 {file_path} 失败: {e}", exc_info=True)
            return FileCheckResult(
                file_path=file_path,
                check_time=datetime.now().isoformat(),
                issues=[],
                error_count=0,
                warning_count=0,
                info_count=0,
                status="failed",
                error_message=str(e)
            )

    def check_files(self, files: List[str]) -> BatchCheckResult:
        """
        批量检查文件

        Args:
            files: 文件路径列表

        Returns:
            BatchCheckResult: 批量检查结果
        """
        logger.info(f"开始批量检查 {len(files)} 个文件")

        start_time = datetime.now()
        check_id = f"check_{start_time.strftime('%Y%m%d_%H%M%S')}"

        file_results = []
        for file_path in files:
            result = self.check_file(file_path)
            file_results.append(result)

        end_time = datetime.now()

        # 统计
        total_issues = sum(len(r.issues) for r in file_results)
        total_errors = sum(r.error_count for r in file_results)
        total_warnings = sum(r.warning_count for r in file_results)
        total_infos = sum(r.info_count for r in file_results)

        logger.info(f"批量检查完成: 总问题={total_issues}, 错误={total_errors}, 警告={total_warnings}, 提示={total_infos}")

        return BatchCheckResult(
            check_id=check_id,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            total_files=len(files),
            checked_files=len([r for r in file_results if r.status == "success"]),
            total_issues=total_issues,
            total_errors=total_errors,
            total_warnings=total_warnings,
            total_infos=total_infos,
            file_results=file_results
        )

    def check_code_chunk(
        self, code: str, rules: List[Rule]
    ) -> List[Issue]:
        """
        检查代码块

        Args:
            code: 代码内容（带行号）
            rules: 适用的规则列表

        Returns:
            List[Issue]: 发现的问题列表
        """
        # 这个方法将在 Task 5.3 中实现
        return []

    def _merge_duplicate_issues(self, issues: List[Issue]) -> List[Issue]:
        """
        合并重复的问题

        合并策略：
        1. 按 (rule_id, line_start, line_end) 作为唯一键
        2. 如果有重复，保留描述更详细的

        Args:
            issues: 问题列表

        Returns:
            List[Issue]: 合并后的问题列表
        """
        # 这个方法将在 Task 5.4 中实现
        return issues

    def _format_rules_for_prompt(self, rules: List[Rule]) -> str:
        """
        将规则列表格式化为适合 LLM 的文本

        Args:
            rules: 规则列表

        Returns:
            str: 格式化后的规则文本
        """
        # 这个方法将在 Task 5.2 中实现
        return ""

    def _parse_llm_response(self, response_text: str) -> List[Issue]:
        """
        解析 LLM 响应为 Issue 列表

        Args:
            response_text: LLM 的响应文本

        Returns:
            List[Issue]: 解析出的问题列表
        """
        # 这个方法将在 Task 5.3 中实现
        return []
