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
import math
import time
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
        self.progress_tracker = ProgressTracker()
        self.tokenizer = BuildinTokenizer()
        self.chunk_token_limit = self._resolve_chunk_token_limit()
        self.llm_repeat = self._resolve_llm_repeat()
        self.llm_consensus_ratio = self._resolve_llm_consensus_ratio()
        self.file_processor = FileProcessor(chunk_size=self.chunk_token_limit)
        self.llm_config = self._build_llm_config()
        self.chunk_overlap_multiplier = self._resolve_chunk_overlap_multiplier()

        if self.chunk_overlap_multiplier and self.chunk_overlap_multiplier > 1:
            base_overlap = self.file_processor.overlap
            new_overlap = max(int(base_overlap * self.chunk_overlap_multiplier), base_overlap)
            self.file_processor.overlap = new_overlap
            logger.info(
                "已根据配置调整 chunk overlap: "
                f"base={base_overlap} -> new={self.file_processor.overlap}"
            )

        logger.info("CodeChecker 初始化完成")
        logger.debug(f"CodeChecker 使用的 LLM 配置: {self.llm_config}")
        logger.debug(
            "CodeChecker 参数: chunk_token_limit=%s, llm_repeat=%s, consensus_ratio=%s",
            self.chunk_token_limit,
            self.llm_repeat,
            self.llm_consensus_ratio,
        )

    DEFAULT_LLM_CONFIG: Dict[str, Any] = {
        "temperature": 0.0,
        "top_p": 1.0,
    }

    DEFAULT_CHUNK_TOKEN_LIMIT = 20000

    DEFAULT_LLM_REPEAT = 1
    DEFAULT_LLM_CONSENSUS_RATIO = 1.0  # 单次调用时必须发现，多次调用时所有调用都要发现才保留（最少误报）

    def _resolve_chunk_token_limit(self) -> int:
        """
        解析 chunk token 限制，优先级：
        1. args.checker_chunk_token_limit
        2. 环境变量 CODECHECKER_CHUNK_TOKEN_LIMIT
        3. 默认 20000 tokens
        """
        limit = self.DEFAULT_CHUNK_TOKEN_LIMIT

        env_value = os.getenv("CODECHECKER_CHUNK_TOKEN_LIMIT")
        if env_value:
            try:
                limit = int(env_value)
            except ValueError:
                logger.warning(
                    f"无法解析 CODECHECKER_CHUNK_TOKEN_LIMIT={env_value}，使用默认值 {self.DEFAULT_CHUNK_TOKEN_LIMIT}"
                )

        arg_value = getattr(self.args, "checker_chunk_token_limit", None)
        if isinstance(arg_value, (int, float)):
            limit = int(arg_value)
        elif arg_value is not None:
            logger.warning(
                f"checker_chunk_token_limit 类型无效({type(arg_value)}), 使用默认值"
            )

        if limit is None or limit <= 0:
            logger.warning(
                f"chunk token limit 配置无效({limit})，回退到默认值 {self.DEFAULT_CHUNK_TOKEN_LIMIT}"
            )
            limit = self.DEFAULT_CHUNK_TOKEN_LIMIT

        return limit

    def _resolve_llm_repeat(self) -> int:
        """解析 LLM 重复校验次数"""
        repeat = self.DEFAULT_LLM_REPEAT

        env_value = os.getenv("CODECHECKER_LLM_REPEAT")
        if env_value:
            try:
                repeat = int(env_value)
            except ValueError:
                logger.warning(
                    f"无法解析 CODECHECKER_LLM_REPEAT={env_value}，使用默认值 {self.DEFAULT_LLM_REPEAT}"
                )

        arg_value = getattr(self.args, "checker_llm_repeat", None)
        if isinstance(arg_value, int):
            repeat = arg_value
        elif isinstance(arg_value, float):
            repeat = int(arg_value)
        elif arg_value is not None:
            logger.warning(
                f"checker_llm_repeat 类型无效({type(arg_value)}), 使用默认值"
            )

        if repeat is None or repeat < 1:
            logger.warning(
                f"llm_repeat 配置无效({repeat})，回退到默认值 {self.DEFAULT_LLM_REPEAT}"
            )
            repeat = self.DEFAULT_LLM_REPEAT

        return repeat

    def _resolve_llm_consensus_ratio(self) -> float:
        """解析 LLM 间的共识比例"""
        ratio = self.DEFAULT_LLM_CONSENSUS_RATIO

        env_value = os.getenv("CODECHECKER_LLM_CONSENSUS")
        if env_value:
            try:
                ratio = float(env_value)
            except ValueError:
                logger.warning(
                    f"无法解析 CODECHECKER_LLM_CONSENSUS={env_value}，使用默认值 {self.DEFAULT_LLM_CONSENSUS_RATIO}"
                )

        arg_value = getattr(self.args, "checker_llm_consensus_ratio", None)
        if isinstance(arg_value, (int, float)):
            ratio = float(arg_value)
        elif arg_value is not None:
            logger.warning(
                f"checker_llm_consensus_ratio 类型无效({type(arg_value)}), 使用默认值"
            )

        if ratio is None or ratio <= 0 or ratio > 1:
            logger.warning(
                f"llm_consensus_ratio 配置无效({ratio})，回退到默认值 {self.DEFAULT_LLM_CONSENSUS_RATIO}"
            )
            ratio = self.DEFAULT_LLM_CONSENSUS_RATIO

        return ratio

    def _aggregate_attempt_results(self, attempt_results: List[List[Issue]]) -> List[Issue]:
        """根据多次 LLM 调用结果取交集/多数票，并检测结果一致性"""
        if not attempt_results:
            return []

        attempts = len(attempt_results)
        threshold = max(1, math.ceil(self.llm_consensus_ratio * attempts))
        logger.debug(
            f"聚合 LLM 结果: attempts={attempts}, threshold={threshold}"
        )

        # 一致性检查：计算各次调用的问题数量
        issue_counts = [len(issues or []) for issues in attempt_results]
        avg_count = sum(issue_counts) / len(issue_counts) if issue_counts else 0
        max_count = max(issue_counts) if issue_counts else 0
        min_count = min(issue_counts) if issue_counts else 0

        # 检测异常情况：结果差异过大
        if attempts >= 2:
            # 计算变异系数 (CV = std / mean)，衡量相对波动
            if avg_count > 0:
                variance = sum((c - avg_count) ** 2 for c in issue_counts) / len(issue_counts)
                std_dev = math.sqrt(variance)
                cv = std_dev / avg_count

                # 如果变异系数 > 0.5（即标准差超过均值的50%），发出警告
                if cv > 0.5:
                    logger.warning(
                        f"⚠️  检测到 LLM 输出不一致：{attempts}次调用发现问题数分别为 {issue_counts}，"
                        f"平均={avg_count:.1f}，标准差={std_dev:.1f}，变异系数={cv:.2f}"
                    )

                # 特别警告："集体放水"现象（有些调用返回0，有些返回正常数量）
                if min_count == 0 and max_count > 3:
                    zero_count = sum(1 for c in issue_counts if c == 0)
                    logger.warning(
                        f"⚠️  检测到疑似'集体放水'：{attempts}次调用中有{zero_count}次返回0个问题，"
                        f"但其他调用发现了{max_count}个问题。建议检查 Prompt 是否足够严格。"
                    )

        aggregated: Dict[tuple, Dict[str, Any]] = {}

        for idx, issues in enumerate(attempt_results, start=1):
            seen_keys = set()
            for issue in issues or []:
                key = (issue.rule_id, issue.line_start, issue.line_end)
                entry = aggregated.setdefault(key, {"count": 0, "issue": issue})

                existing = entry["issue"]
                if len(issue.description) > len(existing.description) or (
                    len(issue.description) == len(existing.description)
                    and len(issue.suggestion) > len(existing.suggestion)
                ):
                    entry["issue"] = issue

                if key not in seen_keys:
                    entry["count"] += 1
                    seen_keys.add(key)

            logger.debug(
                f"Attempt {idx}/{attempts} 包含 {len(issues or [])} 个问题（去重后 {len(seen_keys)}）"
            )

        final_issues: List[Issue] = []
        for key, data in aggregated.items():
            if data["count"] >= threshold:
                final_issues.append(data["issue"])
            else:
                logger.debug(
                    f"丢弃问题 {key}：出现 {data['count']} 次 < 阈值 {threshold}"
                )

        return final_issues

    def _build_llm_config(self) -> Dict[str, Any]:
        """
        构建 LLM 调用配置，优先级：
        1. 传入的 args.checker_llm_config
        2. 单独的温度、top_p、seed 配置（args 或环境变量）
        3. 默认确定性配置（temperature=0, top_p=1, seed=42）
        """
        config: Dict[str, Any] = dict(self.DEFAULT_LLM_CONFIG)

        # 读取环境变量
        env_temperature = os.getenv("CODECHECKER_LLM_TEMPERATURE")
        env_top_p = os.getenv("CODECHECKER_LLM_TOP_P")
        env_seed = os.getenv("CODECHECKER_LLM_SEED")

        def _to_float(value: Optional[str]) -> Optional[float]:
            if value is None:
                return None
            try:
                return float(value)
            except ValueError:
                logger.warning(f"无法解析浮点值: {value}")
                return None

        def _to_int(value: Optional[str]) -> Optional[int]:
            if value is None:
                return None
            try:
                return int(value)
            except ValueError:
                logger.warning(f"无法解析整数值: {value}")
                return None

        # 环境变量优先覆盖默认值
        if env_temperature is not None:
            parsed = _to_float(env_temperature)
            if parsed is not None:
                config["temperature"] = parsed
        if env_top_p is not None:
            parsed = _to_float(env_top_p)
            if parsed is not None:
                config["top_p"] = parsed
        seed_value = _to_int(env_seed)

        # 处理 args 配置
        if getattr(self.args, "checker_llm_config", None):
            config.update(self.args.checker_llm_config)

        if getattr(self.args, "checker_llm_temperature", None) is not None:
            config["temperature"] = self.args.checker_llm_temperature

        if getattr(self.args, "checker_llm_top_p", None) is not None:
            config["top_p"] = self.args.checker_llm_top_p

        arg_seed = getattr(self.args, "checker_llm_seed", None)
        if arg_seed is not None:
            seed_value = arg_seed

        # 默认 seed，如果显式传入 -1 则视为关闭
        if seed_value is None:
            seed_value = 42
        if seed_value >= 0:
            config["seed"] = seed_value
        else:
            config.pop("seed", None)

        return config

    def _resolve_chunk_overlap_multiplier(self) -> Optional[float]:
        """解析 chunk overlap multiplier，用于增强上下文一致性"""
        env_value = os.getenv("CODECHECKER_CHUNK_OVERLAP_MULTIPLIER")
        result: Optional[float] = None

        if env_value:
            try:
                result = float(env_value)
            except ValueError:
                logger.warning(
                    f"无法解析 CODECHECKER_CHUNK_OVERLAP_MULTIPLIER={env_value}，将忽略该配置"
                )

        arg_value = getattr(self.args, "checker_chunk_overlap_multiplier", None)
        if arg_value is not None:
            result = arg_value

        if result is not None and result <= 0:
            logger.warning("chunk_overlap_multiplier <= 0，被忽略")
            return None

        return result

    def check_file(
        self,
        file_path: str,
        file_timeout: int = 600,
        progress_callback: Optional[callable] = None
    ) -> FileCheckResult:
        """
        检查单个文件

        Args:
            file_path: 文件路径
            file_timeout: 单个文件检查的最大超时时间(秒),默认 600 秒(10分钟)
            progress_callback: 可选的进度回调函数，用于报告检查进度
                回调参数: (step: str, **kwargs)
                step 可能的值:
                - "start": 开始检查
                - "rules_loaded": 规则加载完成 (total_rules: int)
                - "chunked": 文件分块完成 (total_chunks: int)
                - "chunk_start": 开始检查某个 chunk (chunk_index: int, total_chunks: int)
                - "chunk_done": 某个 chunk 检查完成 (chunk_index: int, total_chunks: int)
                - "merge_done": 结果合并完成

        Returns:
            FileCheckResult: 文件检查结果
        """
        logger.info(f"开始检查文件: {file_path} (超时: {file_timeout}秒)")

        # 使用 ThreadPoolExecutor 实现文件级超时
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self._check_file_impl, file_path, progress_callback)

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

    def _check_file_impl(
        self,
        file_path: str,
        progress_callback: Optional[callable] = None
    ) -> FileCheckResult:
        """
        检查单个文件的内部实现（用于支持超时）

        Args:
            file_path: 文件路径
            progress_callback: 可选的进度回调函数

        Returns:
            FileCheckResult: 文件检查结果
        """
        try:
            start_time = datetime.now()

            # 回调：开始检查
            if progress_callback:
                progress_callback(step="start")

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

            # 回调：规则加载完成
            if progress_callback:
                progress_callback(step="rules_loaded", total_rules=len(rules))

            # 2. 分块处理
            chunks = self.file_processor.chunk_file(file_path)
            logger.info(f"文件 {file_path} 被分为 {len(chunks)} 个 chunk")

            # 回调：文件分块完成
            if progress_callback:
                progress_callback(step="chunked", total_chunks=len(chunks))

            # 3. 检查每个 chunk
            all_issues = []
            chunk_timeout_count = 0  # 记录超时的 chunk 数量

            for chunk in chunks:
                logger.info(
                    f"检查 chunk {chunk.chunk_index + 1}/{len(chunks)}: "
                    f"行 {chunk.start_line}-{chunk.end_line}"
                )

                # 计算chunk的token数（用于进度显示）
                chunk_tokens = self.tokenizer.count_tokens(chunk.content)

                # 回调：开始检查某个 chunk
                if progress_callback:
                    progress_callback(
                        step="chunk_start",
                        chunk_index=chunk.chunk_index,
                        total_chunks=len(chunks),
                        start_line=chunk.start_line,
                        end_line=chunk.end_line,
                        tokens=chunk_tokens
                    )

                try:
                    issues = self.check_code_chunk(chunk.content, rules, progress_callback=progress_callback)

                    # 检查是否因超时返回空结果（通过日志判断）
                    if not issues:
                        logger.debug(f"Chunk {chunk.chunk_index} 未发现问题（或检查失败）")

                    # 注意：LLM 返回的行号已经是文件的实际行号（从 chunk 内容的行号前缀中提取）
                    # 因为 file_processor.py 中为每行添加的就是文件的实际行号（如 "41 第41行代码"）
                    # 所以这里无需再进行行号转换，直接使用即可

                    all_issues.extend(issues)
                    logger.info(f"Chunk {chunk.chunk_index + 1} 完成，发现 {len(issues)} 个问题")

                    # 回调：某个 chunk 检查完成
                    if progress_callback:
                        progress_callback(
                            step="chunk_done",
                            chunk_index=chunk.chunk_index,
                            total_chunks=len(chunks)
                        )

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
            filtered_issues = self._filter_backend009_boundary(merged_issues)
            logger.info(
                f"合并后共 {len(merged_issues)} 个问题，过滤 backend_009 边界后剩余 {len(filtered_issues)} 个问题"
            )

            # 回调：结果合并完成
            if progress_callback:
                progress_callback(step="merge_done")

            # 5. 统计
            error_count = sum(1 for i in filtered_issues if i.severity == Severity.ERROR)
            warning_count = sum(1 for i in filtered_issues if i.severity == Severity.WARNING)
            info_count = sum(1 for i in filtered_issues if i.severity == Severity.INFO)

            logger.info(f"文件 {file_path} 检查完成: 错误={error_count}, 警告={warning_count}, 提示={info_count}")

            return FileCheckResult(
                file_path=file_path,
                check_time=datetime.now().isoformat(),
                issues=filtered_issues,
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
        self, files: List[str], max_workers: int = 5, file_timeout: int = 600,
        progress_callback: Optional[callable] = None
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
            progress_callback: 可选的进度回调函数，用于报告检查进度（注意：并发场景下，
                回调会被多个线程同时调用，需要确保线程安全）

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
            # 提交所有任务(传递 file_timeout 和 progress_callback 参数)
            future_to_file = {
                executor.submit(self.check_file, file_path, file_timeout, progress_callback): file_path
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
        self,
        code: str,
        rules: List[Rule],
        timeout: int = 180,
        llm_overrides: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[callable] = None,
    ) -> List[Issue]:
        """
        检查代码块

        Args:
            code: 代码内容（带行号）
            rules: 适用的规则列表
            timeout: LLM 调用超时时间（秒），默认 180 秒
            llm_overrides: 临时覆盖的 LLM 配置
            progress_callback: 可选的进度回调函数

        Returns:
            List[Issue]: 发现的问题列表
        """
        try:
            logger.debug(f"开始检查代码块，规则数量: {len(rules)}")

            # 构建行号与代码的映射，便于结果校验
            line_map = self._build_line_map(code)

            # 1. 格式化规则
            rules_text = self._format_rules_for_prompt(rules)

            # 2. 构造 prompt
            prompt = self.check_code_prompt.prompt(code, rules_text)
            logger.debug(
                "LLM prompt 长度: chars=%s, preview=%s",
                len(prompt),
                prompt[:200].replace("\n", " ") + ("..." if len(prompt) > 200 else ""),
            )

            # 3. 调用 LLM（使用超时机制，设置确定性参数以保证结果稳定）
            conversations = [{"role": "user", "content": prompt}]
            attempts = max(1, self.llm_repeat)
            logger.info(
                f"调用 LLM 进行代码检查（超时: {timeout}秒，重复次数={attempts}，consensus={self.llm_consensus_ratio:.2f}）"
            )

            effective_llm_config = dict(self.llm_config)
            if llm_overrides:
                effective_llm_config.update(llm_overrides)
                logger.debug(f"使用覆盖后的 LLM 配置: {effective_llm_config}")
            else:
                logger.debug(f"使用默认 LLM 配置: {effective_llm_config}")

            attempt_results: List[List[Issue]] = []
            for attempt in range(attempts):
                logger.debug("LLM attempt %s/%s", attempt + 1, attempts)

                # 回调：LLM调用开始
                if progress_callback:
                    progress_callback(
                        step="llm_call_start",
                        attempt=attempt + 1,
                        total_attempts=attempts
                    )

                llm_start_time = time.time()

                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(self._call_llm, conversations, effective_llm_config)
                    try:
                        response = future.result(timeout=timeout)
                    except TimeoutError:
                        logger.error(
                            "LLM 调用超时（%s秒），attempt=%s/%s",
                            timeout,
                            attempt + 1,
                            attempts,
                        )
                        attempt_results.append([])

                        # 回调：LLM调用结束（超时）
                        if progress_callback:
                            progress_callback(
                                step="llm_call_end",
                                attempt=attempt + 1,
                                duration=time.time() - llm_start_time,
                                issues_found=0
                            )
                        continue
                    except Exception as e:
                        logger.error(
                            "LLM 调用失败: %s (attempt %s/%s)",
                            e,
                            attempt + 1,
                            attempts,
                            exc_info=True,
                        )
                        attempt_results.append([])

                        # 回调：LLM调用结束（失败）
                        if progress_callback:
                            progress_callback(
                                step="llm_call_end",
                                attempt=attempt + 1,
                                duration=time.time() - llm_start_time,
                                issues_found=0
                            )
                        continue

                llm_duration = time.time() - llm_start_time

                if response and len(response) > 0:
                    response_text = response[0].output
                    logger.debug(f"LLM 响应: {response_text[:200]}...")
                    issues = self._parse_llm_response(response_text, line_map=line_map)
                    logger.info(
                        f"Attempt {attempt + 1}/{attempts} 解析出 {len(issues)} 个问题"
                    )
                    attempt_results.append(issues)

                    # 回调：LLM调用结束（成功）
                    if progress_callback:
                        progress_callback(
                            step="llm_call_end",
                            attempt=attempt + 1,
                            duration=llm_duration,
                            issues_found=len(issues)
                        )
                else:
                    logger.warning("LLM 返回空响应 (attempt %s/%s)", attempt + 1, attempts)
                    attempt_results.append([])

                    # 回调：LLM调用结束（空响应）
                    if progress_callback:
                        progress_callback(
                            step="llm_call_end",
                            attempt=attempt + 1,
                            duration=llm_duration,
                            issues_found=0
                        )

            if not attempt_results:
                logger.warning("LLM 所有尝试均未返回结果")
                return []

            if attempts == 1:
                return attempt_results[0]

            # 回调：聚合多次调用结果
            if progress_callback:
                progress_callback(
                    step="llm_aggregate",
                    total_attempts=attempts
                )

            aggregated = self._aggregate_attempt_results(attempt_results)
            logger.info(
                f"多次尝试后保留 {len(aggregated)} 个问题 (consensus >= {self.llm_consensus_ratio:.2f})"
            )
            return aggregated

        except Exception as e:
            logger.error(f"检查代码块失败: {e}", exc_info=True)
            return []

    def _call_llm(self, conversations: List[Dict[str, str]], llm_config: Optional[Dict[str, Any]] = None) -> Any:
        """
        调用 LLM（内部方法，用于支持超时）

        Args:
            conversations: 对话列表
            llm_config: LLM 配置参数（temperature, top_p 等）

        Returns:
            LLM 响应
        """
        start_time = datetime.now()
        logger.debug(f"开始 LLM 调用: {start_time.isoformat()}")

        try:
            # 传递 llm_config 参数以控制输出的确定性
            logger.debug(f"LLM 最终配置: {llm_config}")
            response = self.llm.chat_oai(
                conversations=conversations,
                llm_config=llm_config if llm_config else {}
            )

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

        # 预过滤 backend_009 的边界情况，避免 30 行以内的提示残留
        filtered_issues: List[Issue] = []
        for issue in issues:
            if issue.rule_id == "backend_009":
                line_count = issue.line_end - issue.line_start + 1
                if line_count <= 30:
                    logger.debug(
                        f"合并前过滤 backend_009 边界问题，行号范围 "
                        f"{issue.line_start}-{issue.line_end} (共 {line_count} 行)"
                    )
                    continue
            filtered_issues.append(issue)

        if not filtered_issues:
            logger.debug("过滤后无剩余问题")
            return []

        merged: List[Issue] = []
        for issue in filtered_issues:
            norm_start = max(1, int(round(issue.line_start)))
            norm_end = max(norm_start, int(round(issue.line_end)))
            normalized_issue = issue.copy(
                update={
                    "line_start": norm_start,
                    "line_end": norm_end,
                }
            )

            match_index: Optional[int] = None
            for idx, existing_issue in enumerate(merged):
                if existing_issue.rule_id != normalized_issue.rule_id:
                    continue

                if (
                    abs(existing_issue.line_start - normalized_issue.line_start) <= 1
                    and abs(existing_issue.line_end - normalized_issue.line_end) <= 1
                ):
                    match_index = idx
                    break

            if match_index is None:
                merged.append(normalized_issue)
                continue

            existing_issue = merged[match_index]
            merged_start = min(existing_issue.line_start, normalized_issue.line_start)
            merged_end = max(existing_issue.line_end, normalized_issue.line_end)

            # 比较描述和建议长度，保留信息更丰富的版本
            should_replace = False
            if len(normalized_issue.description) > len(existing_issue.description):
                should_replace = True
            elif len(normalized_issue.description) == len(existing_issue.description):
                if len(normalized_issue.suggestion) > len(existing_issue.suggestion):
                    should_replace = True

            if should_replace:
                logger.debug(
                    "合并重复问题，选择描述更详细的版本: "
                    f"rule={normalized_issue.rule_id}, "
                    f"lines={normalized_issue.line_start}-{normalized_issue.line_end}"
                )
                merged[match_index] = normalized_issue.copy(update={"line_start": merged_start, "line_end": merged_end})
            else:
                merged[match_index] = existing_issue.copy(update={"line_start": merged_start, "line_end": merged_end})

        # 按行号排序
        sorted_issues = sorted(merged, key=lambda x: (x.line_start, x.line_end))

        logger.info(f"合并完成：{len(filtered_issues)} -> {len(sorted_issues)} 个问题")

        return sorted_issues

    def _filter_backend009_boundary(self, issues: List[Issue]) -> List[Issue]:
        """
        过滤 backend_009 的 30 行以内提示，确保最终结果不含误报

        Args:
            issues: 已合并的问题列表

        Returns:
            过滤后的问题列表
        """
        if not issues:
            return issues

        filtered: List[Issue] = []
        for issue in issues:
            if issue.rule_id == "backend_009":
                line_count = issue.line_end - issue.line_start + 1
                if line_count <= 30:
                    logger.debug(
                        f"最终结果过滤 backend_009 边界问题，行号范围 "
                        f"{issue.line_start}-{issue.line_end} (共 {line_count} 行)"
                    )
                    continue
            filtered.append(issue)
        return filtered

    @byzerllm.prompt()
    def check_code_prompt(self, code_with_lines: str, rules: str) -> str:
        """
        代码检查 Prompt

        你是一个严格的代码审查专家，你的职责是发现代码中的所有规范问题。

        **核心原则（最高优先级）**：
        1. **宁可误报，不可漏报** - 对于可疑的代码，应该报告问题而不是放过
        2. **严格执行规则** - 对照规则逐条检查，不要因为"看起来还行"就放宽标准
        3. **保持一致性** - 相同的代码问题每次检查都必须发现并报告
        4. **客观量化** - 对于涉及数值判断的规则（如行数、嵌套层数），严格按照阈值判断

        **常见错误（必须避免）**：
        ❌ 错误示例1：代码"看起来还可以"，就不报告问题 → 这是放水行为，严禁！
        ❌ 错误示例2：方法有35行，觉得"还不算太长"，就不报告 → 必须严格对照30行阈值
        ❌ 错误示例3：本次检查发现0个问题，但代码明显存在规范问题 → 这是严重失职

        ✅ 正确示例1：代码有魔数"0"用于判断，即使很常见也要报告
        ✅ 正确示例2：方法有31行，立即报告 backend_009 违规
        ✅ 正确示例3：发现未使用的import，无论多小都要报告

        ## 检查规则

        {{ rules }}

        ## 待检查代码（带行号）

        ```
        {{ code_with_lines }}
        ```

        ## 输出要求

        请逐条对照规则严格检查代码，对于每个发现的问题：
        1. 准确定位问题的起始和结束行号（注意：代码中的行号格式为 "行号 代码内容"，请提取正确的行号）
        2. 引用违反的规则ID
        3. 描述问题（要具体，说明违反了什么标准）
        4. 提供修复建议

        **检查策略**：
        - 对每条规则进行全文扫描，不要遗漏任何可疑点
        - 遇到边界情况（如正好30行）要严格按照规则判断
        - 即使是小问题（如单个魔数、一行注释代码）也要报告

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
        4. 对于涉及行数判断的规则（如 backend_009 方法行数限制），请务必准确计算：
           - **计算步骤**：先用公式计算实际行数，再与阈值比较
           - **backend_009 判断标准**：实际行数 ≤ 30 为合规，实际行数 > 30 才违规
           - **具体例子**：
             * 方法从第 10 行到第 38 行：实际行数 = 38 - 10 + 1 = 29 行，29 ≤ 30，**合规**，不应报告
             * 方法从第 10 行到第 39 行：实际行数 = 39 - 10 + 1 = 30 行，30 ≤ 30，**合规**，不应报告
             * 方法从第 10 行到第 40 行：实际行数 = 40 - 10 + 1 = 31 行，31 > 30，**违规**，应该报告
        5. **标准一致性要求**：
           - 使用一致的判断标准，确保同样的代码每次检查得到相同的结果
           - 对于明显违反规则的问题（如超过阈值、明确的规范冲突），应该准确报告
           - 使用客观、可计算的标准进行判断
           - 对于涉及数值判断的规则（如行数、嵌套层数），严格按照阈值判断
        6. 每个问题都必须有明确的规则依据

        **重要提醒**：
        - 只有在彻底检查所有规则后，确认代码完全符合所有规范，才返回空数组 []
        - 如果返回空数组，意味着你承诺代码完全合规，请三思而后行
        - 对于一个500+行的Java业务代码，通常会存在多个规范问题（如魔数、注释代码、过长方法等）

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

    def _validate_issue(
        self,
        issue: Issue,
        line_map: Optional[Dict[int, str]] = None
    ) -> bool:
        """
        验证问题是否有效

        对于涉及行数判断的规则，验证行数是否确实超过阈值，防止 LLM 误判。

        Args:
            issue: 问题对象

        Returns:
            True 表示问题有效，False 表示可能是误判
        """
        # backend_009: 方法行数限制（行数不应超过30行）
        if issue.rule_id == "backend_009":
            if issue.line_end < issue.line_start:
                logger.warning(
                    f"过滤 LLM 误判：规则 {issue.rule_id}，"
                    f"行号范围 {issue.line_start}-{issue.line_end} 非法（结束行小于起始行），"
                    "丢弃该问题"
                )
                return False

            # 默认按照行号差值计算
            computed_line_count = issue.line_end - issue.line_start + 1

            # 尝试根据行号映射获取真实存在的代码行数
            actual_line_count: Optional[int] = None
            if line_map:
                has_start = issue.line_start in line_map
                has_end = issue.line_end in line_map

                if has_start and has_end:
                    lines_in_range = [
                        line_no
                        for line_no in range(issue.line_start, issue.line_end + 1)
                        if line_no in line_map
                    ]
                    actual_line_count = len(lines_in_range)

                    missing_lines = computed_line_count - actual_line_count
                    if missing_lines > 0:
                        # 行号映射缺失部分行，无法准确计算，回退到默认值
                        logger.debug(
                            f"backend_009 校验时发现缺失 {missing_lines} 行，"
                            f"范围 {issue.line_start}-{issue.line_end}，回退使用计算值 {computed_line_count}"
                        )
                        actual_line_count = None

            line_count = actual_line_count if actual_line_count is not None else computed_line_count

            # 判断标准：≤ 30 行为合规，> 30 行才违规
            if line_count <= 30:
                logger.warning(
                    f"过滤 LLM 误判：规则 {issue.rule_id}，"
                    f"行号范围 {issue.line_start}-{issue.line_end}，"
                    f"实际行数 = {line_count} 行，"
                    f"{line_count} ≤ 30（合规），不应报告"
                )
                return False
            else:
                logger.debug(
                    f"验证通过：规则 {issue.rule_id}，"
                    f"行号范围 {issue.line_start}-{issue.line_end}，"
                    f"实际行数 = {line_count} 行，"
                    f"{line_count} > 30（违规），应报告"
                )

        # backend_006: 避免复杂的嵌套结构（语句块逻辑除注释外大于20行）
        # 注意：这个规则检查的是语句块行数，不是整个方法的行数
        # 暂时不在这里验证，因为 LLM 可能检查的是嵌套块的行数

        # 其他规则暂时不需要特殊验证
        return True

    def _build_line_map(self, code_with_lines: str) -> Dict[int, str]:
        """
        将带行号的代码转换为 {行号: 代码内容} 的映射

        Args:
            code_with_lines: 带行号的代码文本

        Returns:
            Dict[int, str]: 行号到代码内容的映射
        """
        line_map: Dict[int, str] = {}

        for raw_line in code_with_lines.splitlines():
            match = re.match(r'^\s*(\d+)\s(.*)$', raw_line)
            if not match:
                continue

            line_no = int(match.group(1))
            line_content = match.group(2)
            line_map[line_no] = line_content

        return line_map

    def _parse_llm_response(
        self,
        response_text: str,
        line_map: Optional[Dict[int, str]] = None
    ) -> List[Issue]:
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
                    if not self._validate_issue(issue, line_map=line_map):
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
