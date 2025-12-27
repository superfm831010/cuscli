import os
from typing import Optional, List, Tuple, Union
from autocoder.common import AutoCoderArgs, SourceCode
from autocoder.common.autocoderargs_parser import AutoCoderArgsParser
from autocoder.common.v2.agent.agentic_edit_tools.base_tool_resolver import (
    BaseToolResolver,
)
from autocoder.common.v2.agent.agentic_edit_types import ReadFileTool, ToolResult
from autocoder.common.pruner.context_pruner import PruneContext
from autocoder.common.tokens import count_string_tokens as count_tokens
from autocoder.common.wrap_llm_hint.utils import add_hint_to_text
from loguru import logger
import typing
from autocoder.rag.loaders import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_ppt,
    extract_text_from_excel,
)

if typing.TYPE_CHECKING:
    from autocoder.common.v2.agent.agentic_edit import AgenticEdit


class ReadFileToolResolver(BaseToolResolver):
    """简化的文件读取工具解析器"""

    def __init__(
        self, agent: Optional["AgenticEdit"], tool: ReadFileTool, args: AutoCoderArgs
    ):
        super().__init__(agent, tool, args)
        self.tool: ReadFileTool = tool

        self.args_parser = AutoCoderArgsParser()
        self.safe_zone_tokens = self._get_parsed_safe_zone_tokens()

        # 初始化 context_pruner 用于 query 抽取
        self.context_pruner = (
            PruneContext(
                max_tokens=self.safe_zone_tokens,
                args=self.args,
                llm=self.agent.context_prune_llm,
            )
            if self.agent and self.agent.context_prune_llm
            else None
        )

    def _get_parsed_safe_zone_tokens(self) -> int:
        """解析 safe_zone_tokens 参数"""
        return self.args_parser.parse_context_prune_safe_zone_tokens(
            self.args.context_prune_safe_zone_tokens, self.args.code_model
        )

    def _extract_lines_by_range(
        self, content: str, start_line: Optional[int], end_line: Optional[int]
    ) -> str:
        """根据行号范围提取内容（1-based，支持负数索引）"""
        if start_line is None and end_line is None:
            return content

        lines = content.split("\n")
        total_lines = len(lines)

        # 处理起始行
        if start_line is None:
            start_idx = 0
        elif start_line < 0:
            start_idx = max(0, total_lines + start_line)
        else:
            start_idx = max(0, start_line - 1)

        # 处理结束行
        if end_line is None or end_line == -1:
            end_idx = total_lines
        elif end_line < -1:
            end_idx = max(0, total_lines + end_line + 1)
        else:
            end_idx = min(total_lines, end_line)

        # 验证范围
        if start_idx >= total_lines:
            return f"Error: start_line {start_line} exceeds total lines {total_lines}"
        if start_idx >= end_idx:
            return f"Error: invalid line range (start={start_line}, end={end_line})"

        return "\n".join(lines[start_idx:end_idx])

    def _extract_content_by_query(
        self, content: str, query: str, file_path: str
    ) -> str:
        """根据 query 从内容中抽取相关部分"""
        if not query or not self.context_pruner:
            return content

        try:
            source_code = SourceCode(
                module_name=file_path, source_code=content, tokens=count_tokens(content)
            )
            pruned_sources = self.context_pruner.handle_overflow(
                file_sources=[source_code],
                conversations=[{"role": "user", "content": query}],
                strategy=self.args.context_prune_strategy,
            )
            return pruned_sources[0].source_code if pruned_sources else content
        except Exception as e:
            logger.warning(f"Query extraction failed for '{query}': {e}")
            return content

    def _read_raw_content(self, file_path: str) -> str:
        """读取原始文件内容"""
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".pdf":
            return extract_text_from_pdf(file_path)
        elif ext == ".docx":
            return extract_text_from_docx(file_path)
        elif ext in (".pptx", ".ppt"):
            slides = extract_text_from_ppt(file_path)
            return "\n\n".join(f"--- Slide {idx} ---\n{text}" for idx, text in slides)
        elif ext in (".xlsx", ".xls"):
            sheets = extract_text_from_excel(file_path)
            return "\n\n".join(
                f"--- Sheet: {sheet_name.split('#')[-1]} ---\n{content}"
                for sheet_name, content in sheets
            )
        else:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()

    def _read_file_content(
        self,
        file_path: str,
        start_line: Optional[int],
        end_line: Optional[int],
        query: Optional[str],
    ) -> Tuple[str, bool]:
        """
        读取文件内容

        Returns:
            Tuple[content, is_truncated]: 内容和是否被截断的标记
        """
        content = self._read_raw_content(file_path)

        # 1. 如果指定了行号范围，按范围提取
        if start_line is not None or end_line is not None:
            return self._extract_lines_by_range(content, start_line, end_line), False

        # 2. 如果有 query，根据 query 抽取
        if query:
            return self._extract_content_by_query(content, query, file_path), False

        # 3. 检查是否超过 safe_zone_tokens
        file_tokens = count_tokens(content)
        if file_tokens > self.safe_zone_tokens:
            total_lines = len(content.split("\n"))
            preview = content[: self.safe_zone_tokens]
            hint = (
                f"Cannot read entire file ({file_tokens} tokens, {total_lines} lines). "
                f"Only first {self.safe_zone_tokens} characters shown. "
                f"Use start_line/end_line for specific range, "
                f"or query to extract relevant content."
            )
            return add_hint_to_text(preview, hint), True

        return content, False

    def _parse_single_int(
        self, value: Optional[Union[str, int]], field_name: str
    ) -> Optional[int]:
        """解析单个整数参数"""
        if value is None:
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            v = value.strip()
            if not v:
                return None
            if "," in v:
                raise ValueError(
                    f"Parameter format error: '{field_name}' contains comma but only one file path is specified. "
                    f"For single file: use a single value like {field_name}='10'. "
                    f"For multiple files: specify multiple paths like path='a.py, b.py' with {field_name}='10, 20'."
                )
            return int(v)
        raise ValueError(f"Invalid type for '{field_name}': {type(value)}")

    def _split_values(self, raw: Optional[Union[str, int]]) -> List[Optional[str]]:
        """将参数拆分为列表"""
        if raw is None:
            return []
        if isinstance(raw, int):
            return [str(raw)]
        if isinstance(raw, str):
            parts = [p.strip() for p in raw.split(",")]
            return [p if p else None for p in parts]
        return []

    def _parse_int_list(
        self, items: List[Optional[str]], field_name: str
    ) -> Tuple[bool, Optional[List[Optional[int]]], Optional[str]]:
        """解析整数列表"""
        if not items:
            return True, None, None
        parsed = []
        for raw in items:
            if raw is None or raw == "":
                parsed.append(None)
            else:
                try:
                    parsed.append(int(raw))
                except ValueError:
                    return False, None, f"'{field_name}' must be integers. Got: {raw}"
        return True, parsed, None

    def read_single_file(self, file_path: str) -> ToolResult:
        """读取单个文件"""
        if not os.path.exists(file_path):
            return ToolResult(success=False, message=f"File not found: {file_path}")
        if not os.path.isfile(file_path):
            return ToolResult(success=False, message=f"Not a file: {file_path}")

        try:
            start_line = self._parse_single_int(self.tool.start_line, "start_line")
            end_line = self._parse_single_int(self.tool.end_line, "end_line")
        except ValueError as e:
            return ToolResult(success=False, message=str(e))

        try:
            content, is_truncated = self._read_file_content(
                file_path, start_line, end_line, self.tool.query
            )

            # 构建消息
            msg_parts = [file_path]
            if start_line or end_line:
                msg_parts.append(f"lines {start_line or 1}-{end_line or 'end'}")
            if self.tool.query:
                msg_parts.append(f"query: '{self.tool.query}'")
            if is_truncated:
                msg_parts.append("(truncated)")

            return ToolResult(
                success=True, message=" ".join(msg_parts), content=content
            )
        except Exception as e:
            logger.exception(f"Error reading file '{file_path}'")
            return ToolResult(
                success=False, message=f"Error reading '{file_path}': {e}"
            )

    def resolve(self) -> ToolResult:
        """解析读取文件请求，支持多文件"""
        raw_path = self.tool.path or ""
        paths = [p.strip() for p in raw_path.split(",") if p.strip()]

        if not paths:
            return ToolResult(success=False, message="'path' is required")

        # 单文件模式
        if len(paths) == 1:
            # 检查单文件模式下是否误用了逗号分隔的参数
            for field, value in [
                ("start_line", self.tool.start_line),
                ("end_line", self.tool.end_line),
            ]:
                if isinstance(value, str) and value and "," in value:
                    return ToolResult(
                        success=False,
                        message=(
                            f"Parameter format error: '{field}' has comma-separated values but only one file path is specified. "
                            f"For single file: use a single value like {field}='10'. "
                            f"For multiple files: specify multiple paths like path='a.py, b.py' with {field}='10, 20'."
                        ),
                    )
            return self.read_single_file(paths[0])

        # 多文件模式
        start_items = self._split_values(self.tool.start_line)
        end_items = self._split_values(self.tool.end_line)
        query_items = self._split_values(self.tool.query)

        # 验证参数数量
        for name, items in [
            ("start_line", start_items),
            ("end_line", end_items),
            ("query", query_items),
        ]:
            if items and len(items) != len(paths):
                return ToolResult(
                    success=False,
                    message=(
                        f"Parameter mismatch: '{name}' has {len(items)} value(s) but you specified {len(paths)} file path(s). "
                        f"When reading multiple files with '{name}', you must provide comma-separated values matching the number of paths. "
                        f"Example: path='a.py, b.py' with {name}='value1, value2'. "
                        f"Alternatively, omit '{name}' to read all files without this filter."
                    ),
                )

        # 解析整数列表
        ok, start_lines, err = self._parse_int_list(start_items, "start_line")
        if not ok:
            return ToolResult(success=False, message=err or "Invalid start_line")
        ok, end_lines, err = self._parse_int_list(end_items, "end_line")
        if not ok:
            return ToolResult(success=False, message=err or "Invalid end_line")

        # 读取每个文件
        results = []
        failures = []
        for i, path in enumerate(paths):
            if not os.path.exists(path):
                failures.append(f"[{i+1}] not found: {path}")
                continue
            if not os.path.isfile(path):
                failures.append(f"[{i+1}] not a file: {path}")
                continue

            try:
                s = start_lines[i] if start_lines else None
                e = end_lines[i] if end_lines else None
                q = query_items[i] if query_items else None
                content, _ = self._read_file_content(path, s, e, q)
                results.append(f"---- File: {path} ----\n{content}")
            except Exception as ex:
                logger.exception(ex)
                failures.append(f"[{i+1}] error: {path}: {ex}")

        if not results:
            return ToolResult(
                success=False,
                message="Failed to read all files. " + "; ".join(failures),
            )

        summary = f"{len(results)}/{len(paths)} files read"
        if failures:
            summary += f" | failures: {'; '.join(failures)}"

        return ToolResult(success=True, message=summary, content="\n\n".join(results))
