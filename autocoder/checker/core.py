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
        try:
            logger.debug(f"开始检查代码块，规则数量: {len(rules)}")

            # 1. 格式化规则
            rules_text = self._format_rules_for_prompt(rules)

            # 2. 构造 prompt
            prompt = self.check_code_prompt.prompt(code, rules_text)

            # 3. 调用 LLM
            conversations = [{"role": "user", "content": prompt}]
            logger.debug("调用 LLM 进行代码检查")

            response = self.llm.chat_oai(conversations=conversations)

            # 4. 解析响应
            if response and len(response) > 0:
                response_text = response[0].output
                logger.debug(f"LLM 响应: {response_text[:200]}...")
                issues = self._parse_llm_response(response_text)
                logger.debug(f"解析出 {len(issues)} 个问题")
                return issues
            else:
                logger.warning("LLM 返回空响应")
                return []

        except Exception as e:
            logger.error(f"检查代码块失败: {e}", exc_info=True)
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

    @byzerllm.prompt()
    def check_code_prompt(self, code_with_lines: str, rules: str) -> str:
        """
        代码检查 Prompt

        你是一个代码审查专家。请根据提供的规则检查代码，找出不符合规范的地方。

        ## 检查规则

        {{ rules }}

        ## 待检查代码（带行号）

        ```
        {{ code_with_lines }}
        ```

        ## 输出要求

        请仔细检查代码，对于每个发现的问题：
        1. 准确定位问题的起始和结束行号（注意：代码中的行号格式为 "行号 代码内容"，请提取正确的行号）
        2. 引用违反的规则ID
        3. 描述问题
        4. 提供修复建议

        以 JSON 数组格式输出，每个问题包含：
        - rule_id: 违反的规则ID（字符串）
        - severity: 严重程度（字符串，只能是 "error"、"warning" 或 "info"）
        - line_start: 问题起始行号（整数，从代码行号中提取）
        - line_end: 问题结束行号（整数，从代码行号中提取）
        - description: 问题描述（字符串）
        - suggestion: 修复建议（字符串）
        - code_snippet: 问题代码片段（字符串，可选）

        **重要提示**：
        1. 行号必须从代码的行号列中提取，例如 "15 def foo():" 中的行号是 15
        2. 只返回确实违反规则的问题，不要臆测
        3. 每个问题都必须有明确的规则依据

        如果没有发现问题，返回空数组 []

        ## 输出示例

        ```json
        [
            {
                "rule_id": "backend_006",
                "severity": "warning",
                "line_start": 15,
                "line_end": 32,
                "description": "发现复杂的 if-else 嵌套，嵌套层数为 4，超过规定的 3 层",
                "suggestion": "建议将内层逻辑抽取为独立方法，或使用策略模式简化",
                "code_snippet": "if condition1:\\n    if condition2:\\n        ..."
            }
        ]
        ```

        请严格按照上述格式输出 JSON 数组。
        """
        return {
            "rules": rules,
            "code_with_lines": code_with_lines
        }

    def _format_rules_for_prompt(self, rules: List[Rule]) -> str:
        """
        将规则列表格式化为适合 LLM 的文本

        Args:
            rules: 规则列表

        Returns:
            str: 格式化后的规则文本
        """
        lines = []
        for rule in rules:
            lines.append(f"### {rule.id}: {rule.title}")
            lines.append(f"**严重程度**: {rule.severity}")
            lines.append(f"**描述**: {rule.description}")
            if rule.examples:
                lines.append(f"**示例**:")
                lines.append(rule.examples)
            lines.append("")  # 空行分隔

        return "\n".join(lines)

    def _parse_llm_response(self, response_text: str) -> List[Issue]:
        """
        解析 LLM 响应为 Issue 列表

        Args:
            response_text: LLM 的响应文本

        Returns:
            List[Issue]: 解析出的问题列表
        """
        try:
            # 尝试提取 JSON 内容（可能包含在 ```json...``` 中）
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                logger.debug("从 JSON 代码块中提取内容")
            else:
                # 尝试直接解析整个响应
                json_str = response_text
                logger.debug("直接解析响应内容")

            # 去除可能的前后空白
            json_str = json_str.strip()

            # 解析 JSON
            issues_data = json.loads(json_str)

            # 验证是否为列表
            if not isinstance(issues_data, list):
                logger.warning(f"LLM 响应不是数组格式: {type(issues_data)}")
                return []

            # 转换为 Issue 对象
            issues = []
            for i, issue_dict in enumerate(issues_data):
                try:
                    # 确保所有必需字段存在
                    if not all(key in issue_dict for key in ['rule_id', 'severity', 'line_start', 'line_end', 'description', 'suggestion']):
                        logger.warning(f"问题 {i} 缺少必需字段: {issue_dict}")
                        continue

                    # 转换 severity 为 Severity 枚举
                    severity_str = issue_dict['severity'].lower()
                    if severity_str not in ['error', 'warning', 'info']:
                        logger.warning(f"无效的 severity 值: {severity_str}，默认为 info")
                        severity_str = 'info'

                    # 创建 Issue 对象
                    issue = Issue(
                        rule_id=issue_dict['rule_id'],
                        severity=Severity(severity_str),
                        line_start=int(issue_dict['line_start']),
                        line_end=int(issue_dict['line_end']),
                        description=issue_dict['description'],
                        suggestion=issue_dict['suggestion'],
                        code_snippet=issue_dict.get('code_snippet')
                    )
                    issues.append(issue)

                except Exception as e:
                    logger.warning(f"解析问题 {i} 失败: {e}, 数据: {issue_dict}")
                    continue

            logger.info(f"成功解析 {len(issues)} 个问题")
            return issues

        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}\n响应内容: {response_text[:500]}...")
            return []
        except Exception as e:
            logger.error(f"解析 LLM 响应失败: {e}\n响应内容: {response_text[:500]}...", exc_info=True)
            return []
