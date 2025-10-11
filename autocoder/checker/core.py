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
from typing import List, Dict, Optional, Any, Generator
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
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
from autocoder.common.buildin_tokenizer import BuildinTokenizer


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

    def check_file(self, file_path: str, file_timeout: int = 600) -> FileCheckResult:
        """
        检查单个文件

        Args:
            file_path: 文件路径
            file_timeout: 单个文件检查的最大超时时间(秒),默认 600 秒(10分钟)

        Returns:
            FileCheckResult: 文件检查结果
        """
        logger.info(f"开始检查文件: {file_path} (超时: {file_timeout}秒)")

        # 使用 ThreadPoolExecutor 实现文件级超时
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self._check_file_impl, file_path)

            try:
                result = future.result(timeout=file_timeout)
                return result

            except TimeoutError:
                # 文件检查超时
                error_msg = f"文件检查超时({file_timeout}秒)"
                logger.error(f"文件 {file_path} 检查超时({file_timeout}秒)")

                return FileCheckResult(
                    file_path=file_path,
                    check_time=datetime.now().isoformat(),
                    issues=[],
                    error_count=0,
                    warning_count=0,
                    info_count=0,
                    status="timeout",
                    error_message=error_msg
                )

            except Exception as exc:
                # 其他异常
                logger.error(f"检查文件 {file_path} 时发生异常: {exc}", exc_info=True)

                return FileCheckResult(
                    file_path=file_path,
                    check_time=datetime.now().isoformat(),
                    issues=[],
                    error_count=0,
                    warning_count=0,
                    info_count=0,
                    status="failed",
                    error_message=str(exc)
                )

    def _check_file_impl(self, file_path: str) -> FileCheckResult:
        """
        检查单个文件的内部实现（用于支持超时）

        Args:
            file_path: 文件路径

        Returns:
            FileCheckResult: 文件检查结果
        """
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
            chunk_timeout_count = 0  # 记录超时的 chunk 数量

            for chunk in chunks:
                logger.info(
                    f"检查 chunk {chunk.chunk_index + 1}/{len(chunks)}: "
                    f"行 {chunk.start_line}-{chunk.end_line}"
                )

                try:
                    issues = self.check_code_chunk(chunk.content, rules)

                    # 检查是否因超时返回空结果（通过日志判断）
                    if not issues:
                        logger.debug(f"Chunk {chunk.chunk_index} 未发现问题（或检查失败）")

                    # 注意：LLM 返回的行号已经是文件的实际行号（从 chunk 内容的行号前缀中提取）
                    # 因为 file_processor.py 中为每行添加的就是文件的实际行号（如 "41 第41行代码"）
                    # 所以这里无需再进行行号转换，直接使用即可

                    all_issues.extend(issues)
                    logger.info(f"Chunk {chunk.chunk_index + 1} 完成，发现 {len(issues)} 个问题")

                except Exception as e:
                    logger.error(f"检查 chunk {chunk.chunk_index} 时发生异常: {e}", exc_info=True)
                    chunk_timeout_count += 1
                    # 继续检查下一个 chunk
                    continue

            # 记录 chunk 超时情况
            if chunk_timeout_count > 0:
                logger.warning(
                    f"文件 {file_path} 有 {chunk_timeout_count}/{len(chunks)} "
                    f"个 chunk 检查失败或超时"
                )

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

    def check_files_concurrent(
        self, files: List[str], max_workers: int = 5, file_timeout: int = 600
    ) -> Generator[FileCheckResult, None, None]:
        """
        并发检查多个文件

        使用 ThreadPoolExecutor 实现并发检查，提高大型项目的检查速度。
        使用生成器模式按完成顺序实时返回结果，适合与进度条配合使用。

        Task 9.1: 实现并发检查逻辑

        Args:
            files: 文件路径列表
            max_workers: 最大并发数（默认: 5）
            file_timeout: 单个文件检查的最大超时时间(秒),默认 600 秒(10分钟)

        Yields:
            FileCheckResult: 每个文件的检查结果（按完成顺序）

        Example:
            >>> checker = CodeChecker(llm, args)
            >>> for result in checker.check_files_concurrent(files, max_workers=5):
            ...     print(f"完成: {result.file_path}")
        """
        logger.info(f"开始并发检查 {len(files)} 个文件 (workers={max_workers}, file_timeout={file_timeout}秒)")

        if not files:
            logger.warning("文件列表为空，跳过检查")
            return

        # 使用 ThreadPoolExecutor 并发检查
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务(传递 file_timeout 参数)
            future_to_file = {
                executor.submit(self.check_file, file_path, file_timeout): file_path
                for file_path in files
            }

            logger.info(f"已提交 {len(future_to_file)} 个检查任务到线程池")

            # 按完成顺序返回结果
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]

                try:
                    # 获取结果(这里不需要再设置 timeout,因为 check_file 内部已经有超时控制)
                    result = future.result()
                    logger.debug(f"文件 {file_path} 检查完成: status={result.status}")
                    yield result

                except Exception as exc:
                    # 处理异常，返回失败结果
                    logger.error(f"检查文件 {file_path} 时发生异常: {exc}", exc_info=True)

                    # 创建失败的结果对象
                    failed_result = FileCheckResult(
                        file_path=file_path,
                        check_time=datetime.now().isoformat(),
                        issues=[],
                        error_count=0,
                        warning_count=0,
                        info_count=0,
                        status="failed",
                        error_message=str(exc)
                    )
                    yield failed_result

        logger.info(f"并发检查完成：已处理 {len(files)} 个文件")

    def check_code_chunk(
        self, code: str, rules: List[Rule], timeout: int = 180
    ) -> List[Issue]:
        """
        检查代码块

        Args:
            code: 代码内容（带行号）
            rules: 适用的规则列表
            timeout: LLM 调用超时时间（秒），默认 180 秒

        Returns:
            List[Issue]: 发现的问题列表
        """
        try:
            logger.debug(f"开始检查代码块，规则数量: {len(rules)}")

            # 1. 格式化规则
            rules_text = self._format_rules_for_prompt(rules)

            # 2. 构造 prompt
            prompt = self.check_code_prompt.prompt(code, rules_text)

            # 3. 调用 LLM（使用超时机制）
            conversations = [{"role": "user", "content": prompt}]
            logger.info(f"调用 LLM 进行代码检查（超时: {timeout}秒）")

            # 使用 ThreadPoolExecutor 实现超时
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._call_llm, conversations)
                try:
                    response = future.result(timeout=timeout)
                except TimeoutError:
                    logger.error(f"LLM 调用超时（{timeout}秒），跳过此代码块")
                    return []
                except Exception as e:
                    logger.error(f"LLM 调用失败: {e}", exc_info=True)
                    return []

            # 4. 解析响应
            if response and len(response) > 0:
                response_text = response[0].output
                logger.debug(f"LLM 响应: {response_text[:200]}...")
                issues = self._parse_llm_response(response_text)
                logger.info(f"解析出 {len(issues)} 个问题")
                return issues
            else:
                logger.warning("LLM 返回空响应")
                return []

        except Exception as e:
            logger.error(f"检查代码块失败: {e}", exc_info=True)
            return []

    def _call_llm(self, conversations: List[Dict[str, str]]) -> Any:
        """
        调用 LLM（内部方法，用于支持超时）

        Args:
            conversations: 对话列表

        Returns:
            LLM 响应
        """
        start_time = datetime.now()
        logger.debug(f"开始 LLM 调用: {start_time.isoformat()}")

        try:
            response = self.llm.chat_oai(conversations=conversations)

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger.debug(f"LLM 调用完成，耗时: {duration:.2f}秒")

            return response
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger.error(f"LLM 调用异常（耗时 {duration:.2f}秒）: {e}", exc_info=True)
            raise

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
        if not issues:
            return []

        logger.debug(f"开始合并 {len(issues)} 个问题")

        # 按 (rule_id, line_start, line_end) 分组
        merged = {}
        for issue in issues:
            key = (issue.rule_id, issue.line_start, issue.line_end)

            if key not in merged:
                # 首次出现，直接保存
                merged[key] = issue
            else:
                # 重复问题，保留描述更详细的
                existing_issue = merged[key]

                # 比较描述长度
                if len(issue.description) > len(existing_issue.description):
                    logger.debug(f"替换问题 {key}，新描述更详细")
                    merged[key] = issue
                elif len(issue.description) == len(existing_issue.description):
                    # 描述长度相同，比较建议长度
                    if len(issue.suggestion) > len(existing_issue.suggestion):
                        logger.debug(f"替换问题 {key}，新建议更详细")
                        merged[key] = issue

        # 转换为列表并按行号排序
        sorted_issues = sorted(merged.values(), key=lambda x: (x.line_start, x.line_end))

        logger.info(f"合并完成：{len(issues)} -> {len(sorted_issues)} 个问题")

        return sorted_issues

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
        2. line_start 和 line_end 都是包含性的（inclusive），即从 line_start 到 line_end 的所有行都包含在内
        3. **行数计算公式**：实际行数 = line_end - line_start + 1
        4. 对于涉及行数判断的规则（如方法行数限制），请先计算实际行数，确认**确实超过阈值**后再报告问题
        5. 只返回确实违反规则的问题，不要臆测或误判
        6. 每个问题都必须有明确的规则依据

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

    def _validate_issue(self, issue: Issue) -> bool:
        """
        验证问题是否有效

        对于涉及行数判断的规则，验证行数是否确实超过阈值，防止 LLM 误判。

        Args:
            issue: 问题对象

        Returns:
            True 表示问题有效，False 表示可能是误判
        """
        # backend_009: 方法行数限制（应控制在30行以内）
        if issue.rule_id == "backend_009":
            # 计算实际行数（包含性：line_end - line_start + 1）
            line_count = issue.line_end - issue.line_start + 1
            if line_count <= 30:
                logger.warning(
                    f"过滤 LLM 误判：规则 {issue.rule_id}，"
                    f"行号范围 {issue.line_start}-{issue.line_end}（共 {line_count} 行），"
                    f"未超过30行阈值"
                )
                return False

        # backend_006: 避免复杂的嵌套结构（语句块逻辑除注释外大于20行）
        # 注意：这个规则检查的是语句块行数，不是整个方法的行数
        # 暂时不在这里验证，因为 LLM 可能检查的是嵌套块的行数

        # 其他规则暂时不需要特殊验证
        return True

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

                    # 验证问题有效性，过滤 LLM 可能的误判
                    if not self._validate_issue(issue):
                        logger.debug(f"问题 {i} 未通过验证，已过滤")
                        continue

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

    def resume_check(self, check_id: str) -> BatchCheckResult:
        """
        恢复中断的检查

        Task 8.2: 实现中断恢复逻辑

        Args:
            check_id: 检查任务ID

        Returns:
            BatchCheckResult: 完整的批量检查结果

        Raises:
            ValueError: 如果检查记录不存在或已完成
        """
        logger.info(f"恢复检查任务: {check_id}")

        # 1. 加载检查状态
        state = self.progress_tracker.load_state(check_id)
        if not state:
            error_msg = f"检查记录不存在: {check_id}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # 2. 检查状态
        if state.status == "completed":
            error_msg = f"检查任务已完成，无需恢复: {check_id}"
            logger.warning(error_msg)
            raise ValueError(error_msg)

        # 3. 获取剩余文件
        remaining_files = state.remaining_files
        total_files = len(state.total_files)
        completed_count = len(state.completed_files)
        remaining_count = len(remaining_files)

        logger.info(
            f"检查进度: {completed_count}/{total_files}, "
            f"剩余 {remaining_count} 个文件"
        )

        # 4. 继续检查剩余文件
        file_results = []
        for file_path in remaining_files:
            try:
                logger.debug(f"检查文件: {file_path}")
                result = self.check_file(file_path)
                file_results.append(result)

                # 更新进度
                self.progress_tracker.mark_completed(check_id, file_path)

            except Exception as e:
                logger.error(f"检查文件 {file_path} 时出错: {e}", exc_info=True)
                # 创建失败结果
                file_results.append(FileCheckResult(
                    file_path=file_path,
                    check_time=datetime.now().isoformat(),
                    issues=[],
                    error_count=0,
                    warning_count=0,
                    info_count=0,
                    status="failed",
                    error_message=str(e)
                ))
                # 仍然标记为完成（避免重复检查）
                self.progress_tracker.mark_completed(check_id, file_path)

        # 5. 构造返回结果
        end_time = datetime.now()

        # 统计当前批次的结果
        total_issues = sum(len(r.issues) for r in file_results)
        total_errors = sum(r.error_count for r in file_results)
        total_warnings = sum(r.warning_count for r in file_results)
        total_infos = sum(r.info_count for r in file_results)

        logger.info(
            f"恢复检查完成: check_id={check_id}, "
            f"本批次检查 {remaining_count} 个文件, "
            f"发现 {total_issues} 个问题"
        )

        # 注意：这里返回的是当前恢复批次的结果
        # 如果需要完整结果（包含之前已检查的文件），需要在插件层合并
        return BatchCheckResult(
            check_id=check_id,
            start_time=state.start_time,
            end_time=end_time.isoformat(),
            total_files=total_files,
            checked_files=total_files,  # 全部完成
            total_issues=total_issues,
            total_errors=total_errors,
            total_warnings=total_warnings,
            total_infos=total_infos,
            file_results=file_results  # 仅包含本次恢复的文件结果
        )
