import sys
import re
from typing import List, Optional
from pathlib import Path

from .markdown_processor import MarkdownProcessor, SplitMode
from .worktree_manager import WorktreeManager
from .async_executor import AsyncExecutor, ExecutionResult
from ..cli.options import CLIOptions
from ..models.responses import CLIResult
from autocoder.common.international import get_message, get_message_with_format


class AsyncAgentHandler:
    """异步代理处理器，提供完整的异步代理运行器功能"""

    def __init__(self, options: CLIOptions, cwd: Optional[str] = None):
        """
        初始化异步代理处理器

        Args:
            options: CLI 选项
            cwd: 当前工作目录
        """
        self.options = options
        self.cwd = Path(cwd) if cwd else Path.cwd()

        # 初始化组件
        self.markdown_processor = MarkdownProcessor()
        self.worktree_manager = WorktreeManager(
            options.workdir, options.from_branch, original_project_path=str(self.cwd)
        )
        self.async_executor = AsyncExecutor(
            model=options.model,
            pull_request=options.pr,
            background_mode=options.bg_mode,
            max_workers=4,  # 可以考虑添加为配置选项
            verbose=options.verbose,
            task_prefix=options.task_prefix,
            worktree_name=options.worktree_name,
            include_libs=options.include_libs,
            workflow=options.workflow,
        )

        # 设置 worktree 管理器
        self.async_executor.set_worktree_manager(self.worktree_manager)

        # 配置 markdown 处理器
        self._configure_markdown_processor()

    def _configure_markdown_processor(self) -> None:
        """配置 Markdown 处理器"""
        # 设置分割模式
        if self.options.split_mode == "h1":
            self.markdown_processor.set_split_mode(SplitMode.HEADING1)
        elif self.options.split_mode == "h2":
            self.markdown_processor.set_split_mode(SplitMode.HEADING2)
        elif self.options.split_mode == "h3":
            self.markdown_processor.set_split_mode(SplitMode.HEADING3)
        elif self.options.split_mode == "any":
            self.markdown_processor.set_split_mode(SplitMode.ANY_HEADING)
            self.markdown_processor.set_heading_level_range(
                self.options.min_level, self.options.max_level
            )
        elif self.options.split_mode == "delimiter":
            self.markdown_processor.set_delimiter(self.options.delimiter)
        elif self.options.split_mode == "frontmatter":
            self.markdown_processor.set_split_mode(SplitMode.FRONT_MATTER)
        elif self.options.split_mode == "custom":
            # 这里可以扩展支持自定义模式
            print(f"警告: 自定义分割模式暂未完全支持，使用默认 H1 分割")
            self.markdown_processor.set_split_mode(SplitMode.HEADING1)
        else:
            print(f"警告: 未知的分割模式 '{self.options.split_mode}'，使用默认 H1 分割")
            self.markdown_processor.set_split_mode(SplitMode.HEADING1)

    def handle(self) -> CLIResult:
        """
        处理异步代理运行器请求

        Returns:
            CLI 结果
        """
        try:
            # 如果启用了 verbose，打印调试信息
            if self.options.verbose:
                print(f"[DEBUG] AsyncAgentHandler.handle() started")
                print(
                    f"[DEBUG] Options: async_mode={self.options.async_mode}, split_mode={self.options.split_mode}"
                )
                print(f"[DEBUG] Working directory: {self.cwd}")

            # 检查是否有标准输入
            if not self._has_stdin_input():
                error_msg = get_message("no_stdin_data")
                if self.options.verbose:
                    print(f"[DEBUG] No stdin input detected. Error: {error_msg}")
                return CLIResult(success=False, output="", error=error_msg)

            # 读取标准输入
            if self.options.verbose:
                print(f"[DEBUG] Reading stdin...")

            input_content = self._read_stdin()

            if self.options.verbose:
                print(f"[DEBUG] Read {len(input_content)} characters from stdin")
                if len(input_content) > 100:
                    print(f"[DEBUG] Content preview: {input_content[:100]}...")
                else:
                    print(f"[DEBUG] Content: {input_content}")

            if not input_content.strip():
                error_msg = get_message("input_content_empty")
                if self.options.verbose:
                    print(f"[DEBUG] Input content is empty. Error: {error_msg}")
                return CLIResult(success=False, output="", error=error_msg)

            # 验证内容
            try:
                self.markdown_processor.validate_content(input_content)
            except ValueError as e:
                return CLIResult(success=False, output="", error=str(e))

            # 处理 Markdown 内容
            documents = self.markdown_processor.process_content(input_content, "stdin")

            if not documents:
                return CLIResult(
                    success=False,
                    output="",
                    error=get_message("no_processable_document_content"),
                )

            print(
                get_message_with_format("parsed_document_parts", count=len(documents))
            )

            # 开始并行处理
            print(get_message("starting_async_document_processing"))
            try:
                results = self.async_executor.process_documents_sync(documents)
            except Exception as e:
                return CLIResult(
                    success=False,
                    output="",
                    error=get_message_with_format(
                        "async_execution_failed", error=str(e)
                    ),
                )

            # 汇总结果
            success_count = sum(1 for r in results if r.success)
            total_count = len(results)

            output_lines = []
            output_lines.append(get_message("async_agent_runner_completed"))
            output_lines.append(
                get_message_with_format("total_processed", total=total_count)
            )
            output_lines.append(
                get_message_with_format("success_count", count=success_count)
            )
            output_lines.append(
                get_message_with_format(
                    "failure_count", count=total_count - success_count
                )
            )

            if self.options.bg_mode:
                # 后台模式，显示日志文件信息
                log_files = [r.log_file for r in results if r.log_file]
                if log_files:
                    output_lines.append(f"\n{get_message('log_files')}")
                    for log_file in log_files:
                        output_lines.append(f"  - {log_file}")

            # 显示失败的任务
            failed_results = [r for r in results if not r.success]
            if failed_results:
                output_lines.append(f"\n{get_message('failed_tasks')}")
                for i, result in enumerate(failed_results):
                    output_lines.append(f"  {i+1}. {result.error}")

            return CLIResult(
                success=success_count > 0,  # 至少有一个成功就算成功
                output="\n".join(output_lines),
            )

        except Exception as e:
            error_msg = get_message_with_format(
                "async_agent_handler_execution_failed", error=str(e)
            )
            if self.options.verbose:
                print(f"[DEBUG] Exception in handle(): {e}")
                import traceback

                print(f"[DEBUG] Traceback:\n{traceback.format_exc()}")
            return CLIResult(success=False, output="", error=error_msg)

    def _has_stdin_input(self) -> bool:
        """检查是否有标准输入"""
        try:
            import os
            import stat

            # 如果启用了 verbose，打印调试信息
            if self.options.verbose:
                print(f"[DEBUG] Checking for stdin input...")

            # 检查 stdin 的状态
            try:
                stdin_stat = os.fstat(sys.stdin.fileno())

                # 如果是管道或重定向文件，则认为有输入
                if stat.S_ISFIFO(stdin_stat.st_mode):  # 管道
                    if self.options.verbose:
                        print(f"[DEBUG] Detected pipe input")
                    return True
                if stat.S_ISREG(stdin_stat.st_mode):  # 重定向文件
                    if self.options.verbose:
                        print(f"[DEBUG] Detected file input")
                    return True

                # 对于字符设备（终端），检查是否有数据可读
                if stat.S_ISCHR(stdin_stat.st_mode):
                    # 在 macOS 上，select 可能不能正确工作，尝试其他方法
                    try:
                        import select

                        # 使用 select 检查是否有数据可读（超时时间很短）
                        ready, _, _ = select.select([sys.stdin], [], [], 0.1)
                        has_input = bool(ready)
                        if self.options.verbose:
                            print(f"[DEBUG] Terminal input check (select): {has_input}")
                        return has_input
                    except Exception as e:
                        if self.options.verbose:
                            print(f"[DEBUG] select failed: {e}")
                        # select 失败时，尝试检查是否是 tty
                        if not sys.stdin.isatty():
                            if self.options.verbose:
                                print(
                                    f"[DEBUG] stdin is not a tty, assuming input exists"
                                )
                            return True
                        return False

                return False
            except Exception as e:
                if self.options.verbose:
                    print(f"[DEBUG] fstat failed: {e}")
                # 如果 fstat 失败，尝试其他方法
                if not sys.stdin.isatty():
                    if self.options.verbose:
                        print(f"[DEBUG] stdin is not a tty (fallback check)")
                    return True
                return False

        except Exception as e:
            if self.options.verbose:
                print(f"[DEBUG] Exception in _has_stdin_input: {e}")
            # 最后的备用方案：如果 stdin 不是 tty，假设有输入
            try:
                if not sys.stdin.isatty():
                    return True
            except:
                pass
            return False

    def _read_stdin(self) -> str:
        """读取标准输入内容"""
        try:
            # 如果 stdin 是二进制模式，需要解码
            if hasattr(sys.stdin, "buffer"):
                # 尝试从 buffer 读取（用于处理二进制输入）
                try:
                    content = sys.stdin.buffer.read().decode("utf-8")
                    if self.options.verbose:
                        print(f"[DEBUG] Read from stdin.buffer")
                    return content
                except:
                    # 如果失败，回退到文本模式
                    pass

            # 正常的文本模式读取
            content = sys.stdin.read()
            if self.options.verbose:
                print(f"[DEBUG] Read from stdin (text mode)")
            return content
        except Exception as e:
            if self.options.verbose:
                print(f"[DEBUG] Failed to read stdin: {e}")
            raise Exception(get_message_with_format("read_stdin_failed", error=str(e)))

    def cleanup_worktrees(self, pattern: str = "") -> CLIResult:
        """
        清理 worktree

        Args:
            pattern: 匹配模式

        Returns:
            CLI 结果
        """
        try:
            self.async_executor.cleanup_all_worktrees(pattern)
            return CLIResult(
                success=True, output=get_message("worktree_cleanup_completed")
            )
        except Exception as e:
            return CLIResult(
                success=False,
                output="",
                error=get_message_with_format("worktree_cleanup_failed", error=str(e)),
            )

    def split_by_pattern(self, content: str, pattern: str) -> List[str]:
        """
        按正则模式分割内容

        Args:
            content: 内容
            pattern: 正则模式

        Returns:
            分割后的内容列表
        """
        try:
            regex = re.compile(pattern)
        except re.error as e:
            print(f"正则模式编译失败: {e}，回退到换行符分割")
            return content.split("\n\n")

        # 找到所有匹配位置
        matches = list(regex.finditer(content))
        if not matches:
            return [content]

        parts = []
        start = 0

        for match in matches:
            if match.start() > start:
                # 添加当前部分
                part = content[start : match.start()].strip()
                if part:
                    parts.append(part)
            start = match.start()

        # 添加最后一部分
        if start < len(content):
            part = content[start:].strip()
            if part:
                parts.append(part)

        return parts
