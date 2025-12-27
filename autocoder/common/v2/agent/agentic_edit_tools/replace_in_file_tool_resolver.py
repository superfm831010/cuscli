import os
from typing import Dict, Any, Optional, List, Tuple
import typing
from autocoder.common import AutoCoderArgs
from autocoder.common.v2.agent.agentic_edit_tools.linter_enabled_tool_resolver import (
    LinterEnabledToolResolver,
)
from autocoder.common.v2.agent.agentic_edit_types import ReplaceInFileTool, ToolResult
from autocoder.common.file_checkpoint.models import FileChange as CheckpointFileChange
from loguru import logger
from autocoder.common.auto_coder_lang import get_message_with_format
from autocoder.common.text_similarity import TextSimilarity
from autocoder.common.search_replace_patch import SearchReplaceManager
from autocoder.common.wrap_llm_hint.utils import add_hint_to_text
import pydantic
from autocoder.common import files as FileUtils

if typing.TYPE_CHECKING:
    from autocoder.common.v2.agent.agentic_edit import AgenticEdit


class PathAndCode(pydantic.BaseModel):
    path: str
    content: str


class ReplacementFailureBlockAnalysis(pydantic.BaseModel):
    """Structured analysis for a single SEARCH block when replacement fails."""

    search_preview: str
    similarity: float
    start_line: int
    end_line: int
    best_window_preview: str
    hints: List[str] = []


class ReplacementFailureReport(pydantic.BaseModel):
    """Structured, extensible failure feedback for replacement operations."""

    reason: str = "replacement_failed"
    file_path: Optional[str] = None
    used_strategy: Optional[str] = None
    tried_strategies: List[str] = []
    suggestions: List[str] = []
    blocks: List[ReplacementFailureBlockAnalysis] = []


class ReplaceInFileToolResolver(LinterEnabledToolResolver):
    def __init__(
        self,
        agent: Optional["AgenticEdit"],
        tool: ReplaceInFileTool,
        args: AutoCoderArgs,
    ):
        super().__init__(agent, tool, args)
        self.tool: ReplaceInFileTool = tool  # For type hinting
        self.args = args

        # 初始化智能替换管理器
        self.search_replace_manager = SearchReplaceManager()

        # Get fence parameters from tool
        self.fence_0 = getattr(tool, "fence_0", "```")
        self.fence_1 = getattr(tool, "fence_1", "```")

        # Markers used in SEARCH/REPLACE blocks
        self.SEARCH_MARKER: str = "<<<<<<< SEARCH"  # exact literal
        self.DIVIDER_MARKER: str = "======="
        self.REPLACE_MARKER: str = ">>>>>>> REPLACE"

    def parse_search_replace_blocks(self, diff_content: str) -> List[Tuple[str, str]]:
        """Parse diff content using configured markers into (search, replace) tuples.

        Preserves original newlines within each block.
        """
        blocks: List[Tuple[str, str]] = []
        lines = diff_content.splitlines(keepends=True)
        i = 0
        n = len(lines)

        while i < n:
            line = lines[i]
            if line.strip() == self.SEARCH_MARKER:
                i += 1
                search_lines: List[str] = []
                while i < n and lines[i].strip() != self.DIVIDER_MARKER:
                    search_lines.append(lines[i])
                    i += 1
                if i >= n:
                    logger.warning("Unterminated SEARCH block found in diff content.")
                    break
                i += 1  # skip divider

                replace_lines: List[str] = []
                while i < n and lines[i].strip() != self.REPLACE_MARKER:
                    replace_lines.append(lines[i])
                    i += 1
                if i >= n:
                    logger.warning("Unterminated REPLACE block found in diff content.")
                    break
                i += 1  # skip replace marker

                blocks.append(("".join(search_lines), "".join(replace_lines)))
            else:
                i += 1

        if not blocks and diff_content.strip():
            logger.warning(
                f"Could not parse any SEARCH/REPLACE blocks from diff (using markers): {diff_content}"
            )
        return blocks

    def _find_line_numbers(self, content: str, text_block: str) -> Tuple[int, int]:
        """
        Find the line numbers for a given text block in the content.

        Args:
            content: The full file content
            text_block: The text block to find

        Returns:
            Tuple of (start_line, end_line) numbers (1-indexed)
        """
        block_lines = text_block.splitlines()
        block_start_idx = content.find(text_block)
        if block_start_idx == -1:
            return (-1, -1)
        lines_before = content[:block_start_idx].count("\n")
        start_line = lines_before + 1
        lines_in_block = len(block_lines)
        end_line = start_line + lines_in_block - 1
        return (start_line, end_line)

    def _intelligent_replace(
        self, content: str, search_blocks: List[Tuple[str, str]]
    ) -> Tuple[bool, str, List[str]]:
        """
        使用智能替换策略进行文本替换（兼容旧签名）。

        新的结构化失败报告通过 _apply_replacements_with_fallback 提供；
        本方法保持返回 (success, new_content, errors) 以兼容旧调用点。
        """
        success, new_content, errors, _ = self._apply_replacements_with_fallback(
            content, search_blocks
        )
        return success, new_content, errors

    def _apply_replacements_with_fallback(
        self,
        content: str,
        search_blocks: List[Tuple[str, str]],
        file_path: Optional[str] = None,
    ) -> Tuple[bool, str, List[str], Optional[ReplacementFailureReport]]:
        """Apply replacements using the advanced fallback strategy.

        Returns (success, new_content, error_messages, failure_report).
        """
        if not self.search_replace_manager:
            return (
                False,
                content,
                ["Advanced text replacement system is not available"],
                None,
            )

        try:
            result = self.search_replace_manager.replace_with_fallback(
                content, search_blocks
            )

            if result.success:
                logger.info(
                    f"Intelligent replacement succeeded using {result.metadata.get('used_strategy', 'unknown')} strategy"
                )
                return True, (result.new_content or content), [], None

            # Build structured, extensible feedback
            failure_report = self._build_failure_report(
                content, search_blocks, result, file_path
            )
            error_message = self._format_failure_message(failure_report)
            logger.warning(f"Intelligent replacement failed: {error_message}")
            return False, content, [error_message], failure_report

        except Exception as e:
            logger.error(f"Error in intelligent replacement: {e}")
            return (
                False,
                content,
                [f"System error during text replacement: {str(e)}"],
                None,
            )

    def _build_failure_report(
        self,
        content: str,
        search_blocks: List[Tuple[str, str]],
        result: Any,
        file_path: Optional[str] = None,
    ) -> ReplacementFailureReport:
        blocks_analysis: List[ReplacementFailureBlockAnalysis] = []
        for search_text, _ in search_blocks:
            analysis = self._analyze_search_block_similarity(content, search_text)
            blocks_analysis.append(analysis)

        return ReplacementFailureReport(
            file_path=file_path,
            used_strategy=result.metadata.get("used_strategy"),
            tried_strategies=result.metadata.get("tried_strategies", []),
            suggestions=self._generate_common_suggestions(content),
            blocks=blocks_analysis,
        )

    def _format_failure_message(self, report: ReplacementFailureReport) -> str:
        """Format a human-friendly failure message optimized for LLM self-correction.

        Shows full content (no truncation) so LLM can directly copy the correct SEARCH block.
        """
        # Build header with summary
        total_blocks = len(report.blocks)
        if report.file_path:
            base_error = f"SEARCH block mismatch in '{report.file_path}' ({total_blocks} block(s) failed)."
        else:
            base_error = f"SEARCH block mismatch ({total_blocks} block(s) failed)."

        analysis_parts: List[str] = []
        for idx, blk in enumerate(report.blocks, 1):
            # Header with key metrics
            if blk.start_line != -1:
                header = f"❌ Block {idx} (similarity: {blk.similarity:.0%}, lines {blk.start_line}-{blk.end_line}):"
            else:
                header = f"❌ Block {idx} (similarity: {blk.similarity:.0%}):"

            parts = [header]

            # Show what user searched for
            parts.append("YOUR SEARCH:")
            parts.append(f"```\n{blk.search_preview}\n```")

            # Show actual content and actionable hint based on similarity
            if blk.similarity > 0.5 and blk.start_line != -1:
                parts.append("ACTUAL CONTENT (copy this as your SEARCH block):")
                parts.append(f"```\n{blk.best_window_preview}\n```")

                if blk.similarity > 0.8:
                    parts.append(
                        "✅ High similarity — use ACTUAL CONTENT above as your SEARCH block."
                    )
                else:
                    parts.append(
                        "⚠️ Moderate similarity — check whitespace/indentation, then use ACTUAL CONTENT."
                    )
            else:
                # Low similarity - need to re-read file
                if report.file_path:
                    parts.append(
                        f"⚠️ No match found. Re-read the file: read_file path='{report.file_path}'"
                    )
                else:
                    parts.append(
                        "⚠️ No match found. Use read_file to verify the target content."
                    )

            analysis_parts.append("\n".join(parts))

        detailed_analysis = "\n\n".join(analysis_parts)
        return add_hint_to_text(base_error, detailed_analysis)

    def _analyze_search_block_similarity(
        self, content: str, search_text: str
    ) -> ReplacementFailureBlockAnalysis:
        """Analyze how well a SEARCH block matches the file content.

        Returns full content without truncation so LLM can directly copy and use.
        """
        try:
            similarity_finder = TextSimilarity(search_text, content)
            similarity, best_window = similarity_finder.get_best_matching_window()
            start_line, end_line = self._find_line_numbers(content, best_window)

            return ReplacementFailureBlockAnalysis(
                search_preview=search_text,  # Full content for direct copy
                similarity=float(similarity),
                start_line=start_line,
                end_line=end_line,
                best_window_preview=best_window,  # Full content for direct copy
                hints=[],
            )
        except Exception as e:
            return ReplacementFailureBlockAnalysis(
                search_preview=search_text,
                similarity=0.0,
                start_line=-1,
                end_line=-1,
                best_window_preview=f"<analysis error: {str(e)}>",
                hints=[],
            )

    def _generate_common_suggestions(self, content: str) -> List[str]:
        """Generate general suggestions to help the LLM fix mismatches."""
        suggestions: List[str] = []

        has_crlf = "\r\n" in content
        has_lf = "\n" in content and "\r\n" not in content
        if has_crlf or has_lf:
            line_ending = "CRLF (\\r\\n)" if has_crlf else "LF (\\n)"
            suggestions.append(
                f"• File uses {line_ending} — ensure SEARCH blocks match exact line endings"
            )

        content_lines = content.splitlines()
        has_trailing_spaces = any(
            line.endswith(" ") or line.endswith("\t") for line in content_lines
        )
        if has_trailing_spaces:
            suggestions.append(
                "• File contains trailing whitespace — include exact spacing in SEARCH blocks"
            )

        suggestions.append(
            "• Use read_file tool to examine exact content around the target location"
        )
        suggestions.append(
            "• Consider searching for a smaller, more unique fragment first"
        )

        return suggestions

    def parse_whole_text(self, text: str) -> List[PathAndCode]:
        """
        从文本中抽取如下格式代码(two_line_mode)：

        ```python
        ##File: /project/path/src/autocoder/index/index.py
        <<<<<<< SEARCH
        =======
        >>>>>>> REPLACE
        ```

        或者 (one_line_mode)

        ```python:/project/path/src/autocoder/index/index.py
        <<<<<<< SEARCH
        =======
        >>>>>>> REPLACE
        ```

        """
        HEAD = self.SEARCH_MARKER
        DIVIDER = self.DIVIDER_MARKER
        UPDATED = self.REPLACE_MARKER
        lines = text.split("\n")
        lines_len = len(lines)
        start_marker_count = 0
        block = []
        path_and_code_list = []
        # two_line_mode or one_line_mode
        current_editblock_mode = "two_line_mode"
        current_editblock_path = None

        def guard(index):
            return index + 1 < lines_len

        def start_marker(line, index):
            nonlocal current_editblock_mode
            nonlocal current_editblock_path
            if (
                line.startswith(self.fence_0)
                and guard(index)
                and ":" in line
                and lines[index + 1].startswith(HEAD)
            ):

                current_editblock_mode = "one_line_mode"
                current_editblock_path = line.split(":", 1)[1].strip()
                return True

            if (
                line.startswith(self.fence_0)
                and guard(index)
                and lines[index + 1].startswith("##File:")
            ):
                current_editblock_mode = "two_line_mode"
                current_editblock_path = None
                return True

            return False

        def end_marker(line, index):
            return line.startswith(self.fence_1) and UPDATED in lines[index - 1]

        for index, line in enumerate(lines):
            if start_marker(line, index) and start_marker_count == 0:
                start_marker_count += 1
            elif end_marker(line, index) and start_marker_count == 1:
                start_marker_count -= 1
                if block:
                    if current_editblock_mode == "two_line_mode":
                        path = block[0].split(":", 1)[1].strip()
                        content = "\n".join(block[1:])
                    else:
                        path = current_editblock_path
                        content = "\n".join(block)
                    block = []
                    path_and_code_list.append(PathAndCode(path=path, content=content))
            elif start_marker_count > 0:
                block.append(line)

        return path_and_code_list

    def get_edits(self, content: str):
        edits = self.parse_whole_text(content)
        HEAD = self.SEARCH_MARKER
        DIVIDER = self.DIVIDER_MARKER
        UPDATED = self.REPLACE_MARKER
        result = []
        for edit in edits:
            heads = []
            updates = []
            c = edit.content
            in_head = False
            in_updated = False
            # 使用 splitlines(keepends=True) 来保留换行符信息
            lines = c.splitlines(keepends=True)
            for line in lines:
                if line.strip() == HEAD:
                    in_head = True
                    continue
                if line.strip() == DIVIDER:
                    in_head = False
                    in_updated = True
                    continue
                if line.strip() == UPDATED:
                    in_head = False
                    in_updated = False
                    continue
                if in_head:
                    heads.append(line)
                if in_updated:
                    updates.append(line)

            # 直接拼接，保留原始的换行符
            head_content = "".join(heads)
            update_content = "".join(updates)

            # 去掉可能的末尾换行符以避免重复
            if head_content.endswith("\n"):
                head_content = head_content[:-1]
            if update_content.endswith("\n"):
                update_content = update_content[:-1]

            result.append((edit.path, head_content, update_content))
        return result

    def replace_in_multiple_files(
        self, diff_content: str, source_dir: str, abs_project_dir: str
    ) -> ToolResult:
        """Replace content in multiple files when path is '*'.

        Enhanced with structured failure feedback in result.content when any block fails.
        """
        try:
            # 使用新的解析方法解析多文件格式
            codes = self.get_edits(diff_content)
            if not codes:
                return ToolResult(
                    success=False,
                    message=(
                        "No valid edit blocks found in diff content. "
                        "Each edit block must follow this format:\n"
                        "```\n##File: path/to/file.ext\n<<<<<<< SEARCH\n[exact content to find]\n=======\n[new content]\n>>>>>>> REPLACE\n```\n"
                        "Common issues: missing ##File header, incorrect fence markers, or malformed SEARCH/REPLACE delimiters."
                    ),
                )

            file_content_mapping: Dict[str, str] = {}
            failed_blocks: List[Tuple[str, str, str]] = []
            errors: List[str] = []
            failed_details_by_file: Dict[str, Any] = {}

            # 按文件分组处理块
            file_blocks_map: Dict[str, List[Tuple[str, str]]] = {}
            for block in codes:
                file_path, head, update = block
                abs_file_path = os.path.abspath(os.path.join(source_dir, file_path))

                # Security check
                if not abs_file_path.startswith(abs_project_dir):
                    errors.append(f"Access denied to file: {file_path}")
                    continue

                if file_path not in file_blocks_map:
                    file_blocks_map[file_path] = []
                file_blocks_map[file_path].append((head, update))

            # 对每个文件使用智能替换策略
            for file_path, blocks in file_blocks_map.items():
                abs_file_path = os.path.abspath(os.path.join(source_dir, file_path))

                if not os.path.exists(abs_file_path):
                    # New file - 对于新文件，直接使用所有更新块的内容
                    new_content = "\n".join(
                        [update for head, update in blocks if update]
                    )
                    file_content_mapping[file_path] = new_content
                else:
                    # 读取现有文件内容
                    existing_content = FileUtils.read_file(abs_file_path)

                    # 使用智能替换策略（与 normal 方法保持一致）
                    logger.info(f"Using intelligent replacement for file: {file_path}")
                    success, new_content, intelligent_errors = (
                        self._intelligent_replace(existing_content, blocks)
                    )

                    if success:
                        file_content_mapping[file_path] = new_content
                        logger.info(
                            f"Intelligent replacement succeeded for {len(blocks)} blocks in {file_path}"
                        )
                    else:
                        logger.warning(
                            f"Intelligent replacement failed for {file_path}: {intelligent_errors}"
                        )
                        # Build structured details for each failed file
                        try:
                            # reuse new failure report via internal method
                            _, _, _, failure_report = (
                                self._apply_replacements_with_fallback(
                                    existing_content, blocks, file_path
                                )
                            )
                            if failure_report is not None:
                                failed_details_by_file[file_path] = (
                                    failure_report.dict()
                                )
                        except Exception:
                            pass
                        errors.extend(
                            [f"{file_path}: {err}" for err in intelligent_errors]
                        )
                        failed_blocks.extend(
                            [(file_path, head, update) for head, update in blocks]
                        )

            if failed_blocks:
                total_blocks = sum(len(blocks) for blocks in file_blocks_map.values())
                failed_count = len(failed_blocks)
                message = (
                    f"Failed to apply {failed_count}/{total_blocks} blocks across multiple files. "
                    f"See content.failed_files for details."
                )
                content_details: Dict[str, Any] = {
                    "failed_files": failed_details_by_file,
                    "total_blocks": total_blocks,
                    "failed_blocks": failed_count,
                    "errors": errors,
                }
                return ToolResult(
                    success=False, message=message, content=content_details
                )

            # Apply changes to files
            changed_files = []
            for file_path, new_content in file_content_mapping.items():
                abs_file_path = os.path.abspath(os.path.join(source_dir, file_path))
                os.makedirs(os.path.dirname(abs_file_path), exist_ok=True)

                # Handle checkpoint manager if available
                if self.agent and self.agent.checkpoint_manager:
                    changes = {
                        file_path: CheckpointFileChange(
                            file_path=file_path,
                            content=new_content,
                            is_deletion=False,
                            is_new=not os.path.exists(abs_file_path),
                        )
                    }
                    change_group_id = self.args.event_file

                    conversation_id = (
                        self.agent.conversation_config.conversation_id
                        if self.agent
                        else None
                    )
                    logger.debug(
                        f"多文件对话检查点调试 - conversation_config存在: {self.agent.conversation_config is not None}, conversation_id: {conversation_id}"
                    )

                    if conversation_id:
                        first_message_id, last_message_id = (
                            self.agent.get_conversation_message_range()
                        )
                        logger.debug(
                            f"多文件获取消息范围 - first_message_id: {first_message_id}, last_message_id: {last_message_id}"
                        )

                        self.agent.checkpoint_manager.apply_changes_with_conversation(
                            changes=changes,
                            conversation_id=conversation_id,
                            first_message_id=first_message_id,
                            last_message_id=last_message_id,
                            change_group_id=change_group_id,
                            metadata={"event_file": self.args.event_file},
                        )
                        logger.debug(f"多文件已调用 apply_changes_with_conversation")
                    else:
                        logger.warning(
                            f"多文件conversation_id 为 None，跳过对话检查点保存"
                        )
                else:
                    with open(abs_file_path, "w", encoding="utf-8") as f:
                        f.write(new_content)

                changed_files.append(file_path)

                # Record file change for AgenticEdit
                if self.agent:
                    rel_path = os.path.relpath(abs_file_path, abs_project_dir)
                    self.agent.record_file_change(
                        rel_path, "modified", content=new_content
                    )

            # 计算统计信息（与 normal 方法保持一致）
            total_blocks = sum(len(blocks) for blocks in file_blocks_map.values())
            applied_blocks = total_blocks - len(failed_blocks)

            # 构建成功消息（与 normal 方法保持一致）
            if errors:
                success_message = f"Successfully applied {applied_blocks}/{total_blocks} blocks across {len(changed_files)} files: {', '.join(changed_files)}. Warnings: {'; '.join(errors)}"
            else:
                success_message = f"Successfully applied {applied_blocks}/{total_blocks} blocks across {len(changed_files)} files: {', '.join(changed_files)}"

            # Run linter check if enabled for multiple files
            result = ToolResult(success=True, message=success_message)
            if (
                self.linter_config
                and self.linter_config.enabled
                and self.linter_config.check_after_modification
            ):
                # Collect all modified files for linting
                files_to_lint = []
                for file_path in changed_files:
                    if self.should_lint(file_path):
                        abs_path = os.path.abspath(os.path.join(source_dir, file_path))
                        files_to_lint.append(abs_path)

                if files_to_lint:
                    logger.info(
                        f"Running linter check on {len(files_to_lint)} modified files"
                    )
                    lint_report = self.lint_files(files_to_lint)
                    if lint_report:
                        result = self.handle_lint_results(result, lint_report)

            return result

        except Exception as e:
            logger.error(f"Error in multiple file replacement: {str(e)}")
            return ToolResult(
                success=False,
                message=f"Error processing multiple file replacement: {str(e)}",
            )

    def replace_in_file_normal(
        self,
        file_path: str,
        diff_content: str,
        source_dir: str,
        abs_project_dir: str,
        abs_file_path: str,
    ) -> ToolResult:
        """Replace content in file directly without using shadow manager.

        Adds structured failure details to result.content when no blocks applied.
        """
        try:
            # Read original content
            if not os.path.exists(abs_file_path):
                return ToolResult(
                    success=False,
                    message=get_message_with_format(
                        "replace_in_file.file_not_found", file_path=file_path
                    ),
                )
            if not os.path.isfile(abs_file_path):
                return ToolResult(
                    success=False,
                    message=get_message_with_format(
                        "replace_in_file.not_a_file", file_path=file_path
                    ),
                )

            with open(abs_file_path, "r", encoding="utf-8", errors="replace") as f:
                original_content = f.read()

            parsed_blocks = self.parse_search_replace_blocks(diff_content)
            if not parsed_blocks:
                return ToolResult(
                    success=False,
                    message=get_message_with_format("replace_in_file.no_valid_blocks"),
                )

            current_content = original_content
            applied_count = 0
            errors = []

            # 使用智能替换
            logger.info("Using intelligent replacement with multiple strategies")
            success, new_content, intelligent_errors = self._intelligent_replace(
                current_content, parsed_blocks
            )

            if success:
                current_content = new_content
                applied_count = len(parsed_blocks)
                logger.info(
                    f"Intelligent replacement succeeded for all {applied_count} blocks"
                )
            else:
                logger.warning(f"Intelligent replacement failed: {intelligent_errors}")
                errors.extend(intelligent_errors)

            if applied_count == 0 and errors:
                # Provide structured report
                _, _, _, failure_report = self._apply_replacements_with_fallback(
                    original_content, parsed_blocks, file_path
                )
                content_details = failure_report.dict() if failure_report else None
                return ToolResult(
                    success=False,
                    message=get_message_with_format(
                        "replace_in_file.apply_failed", errors="\n\n".join(errors)
                    ),
                    content=content_details,
                )

            # Write the modified content back to file
            if self.agent and self.agent.checkpoint_manager:
                changes = {
                    file_path: CheckpointFileChange(
                        file_path=file_path,
                        content=current_content,
                        is_deletion=False,
                        is_new=False,
                    )
                }
                change_group_id = self.args.event_file

                conversation_id = (
                    self.agent.conversation_config.conversation_id
                    if self.agent
                    else None
                )
                logger.debug(
                    f"对话检查点调试 - conversation_config存在: {self.agent.conversation_config is not None}, conversation_id: {conversation_id}"
                )

                if conversation_id:
                    first_message_id, last_message_id = (
                        self.agent.get_conversation_message_range()
                    )
                    logger.debug(
                        f"获取消息范围 - first_message_id: {first_message_id}, last_message_id: {last_message_id}"
                    )

                    self.agent.checkpoint_manager.apply_changes_with_conversation(
                        changes=changes,
                        conversation_id=conversation_id,
                        first_message_id=first_message_id,
                        last_message_id=last_message_id,
                        change_group_id=change_group_id,
                        metadata={"event_file": self.args.event_file},
                    )
                    logger.debug(f"已调用 apply_changes_with_conversation")
                else:
                    logger.warning(f"conversation_id 为 None，跳过对话检查点保存")
            else:
                with open(abs_file_path, "w", encoding="utf-8") as f:
                    f.write(current_content)

            logger.info(
                f"Successfully applied {applied_count}/{len(parsed_blocks)} changes to file: {file_path}"
            )

            # 构建成功消息
            if errors:
                final_message = get_message_with_format(
                    "replace_in_file.apply_success_with_warnings",
                    applied=applied_count,
                    total=len(parsed_blocks),
                    file_path=file_path,
                    errors="\n".join(errors),
                )
            else:
                final_message = get_message_with_format(
                    "replace_in_file.apply_success",
                    applied=applied_count,
                    total=len(parsed_blocks),
                    file_path=file_path,
                )

            # 变更跟踪，回调AgenticEdit
            if self.agent:
                rel_path = os.path.relpath(abs_file_path, abs_project_dir)
                self.agent.record_file_change(
                    rel_path, "modified", diff=diff_content, content=current_content
                )

            # Run linter check if enabled
            result = ToolResult(success=True, message=final_message)
            if (
                self.should_lint(file_path)
                and self.linter_config
                and self.linter_config.check_after_modification
            ):
                logger.info(f"Running linter check on modified file: {file_path}")
                lint_report = self.lint_files([abs_file_path])
                if lint_report:
                    result = self.handle_lint_results(result, lint_report)

            return result
        except Exception as e:
            logger.error(
                f"Error writing replaced content to file '{file_path}': {str(e)}"
            )
            return ToolResult(
                success=False,
                message=get_message_with_format(
                    "replace_in_file.write_error", error=str(e)
                ),
            )

    def resolve(self) -> ToolResult:
        """Resolve the replace in file tool by calling the appropriate implementation"""
        # Check if we are in plan mode
        if self.args.agentic_mode == "plan":
            return ToolResult(
                success=False,
                message="Currently in plan mode, modification tools are disabled. ",
            )

        file_path = self.tool.path
        diff_content = self.tool.diff.strip()
        source_dir = self.args.source_dir or "."
        abs_project_dir = os.path.abspath(source_dir)

        # Check if this is multiple file mode (path="*")
        if file_path == "*":
            logger.info("Multiple file replacement mode detected")
            return self.replace_in_multiple_files(
                diff_content, source_dir, abs_project_dir
            )

        # Single file mode
        abs_file_path = os.path.abspath(os.path.join(source_dir, file_path))

        # Security check
        if not abs_file_path.startswith(abs_project_dir):
            return ToolResult(
                success=False,
                message=get_message_with_format(
                    "replace_in_file.access_denied", file_path=file_path
                ),
            )

        return self.replace_in_file_normal(
            file_path, diff_content, source_dir, abs_project_dir, abs_file_path
        )
