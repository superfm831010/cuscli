"""
CLI 主入口点模块

提供命令行接口的主要实现，处理参数解析和命令执行。
"""

import sys
import os
import argparse
from typing import Optional, List
from .options import CLIOptions, get_default_async_workdir
from ..models.responses import CLIResult
from .handlers import PrintModeHandler
from autocoder.run_context import get_run_context, RunMode
from autocoder.common.international import get_message, get_message_with_format
from autocoder.common.file_monitor import FileMonitor
import os

# 设置运行模式为终端模式
get_run_context().set_mode(RunMode.CLI)


class AutoCoderCLI:
    """命令行接口主类，处理命令行参数和执行相应的操作。"""

    def __init__(self):
        """初始化CLI实例。"""
        pass

    def run(self, options: CLIOptions, cwd: Optional[str] = None) -> CLIResult:
        """
        运行CLI命令。

        Args:
            options: CLI选项
            cwd: 当前工作目录，如果为None则使用系统当前目录

        Returns:
            命令执行结果
        """
        try:
            # 验证选项
            options.validate()

            # 根据命令类型分发处理
            if options.command == "config":
                return self.handle_config_command(options, cwd)
            else:
                # 默认处理代码生成命令
                return self.handle_print_mode(options, cwd)

        except Exception as e:
            return CLIResult(success=False, output="", error=str(e))

    def handle_config_command(
        self, options: CLIOptions, cwd: Optional[str] = None
    ) -> CLIResult:
        """
        处理 config 命令。

        Args:
            options: CLI选项
            cwd: 当前工作目录

        Returns:
            命令执行结果
        """
        try:
            from autocoder.auto_coder_runner import configure

            if not options.config_args:
                return CLIResult(
                    success=False,
                    output="",
                    error="配置参数不能为空。用法: auto-coder.run config model=v3_chat",
                )

            # 处理每个配置参数
            results = []
            for config_arg in options.config_args:
                if "=" not in config_arg:
                    return CLIResult(
                        success=False,
                        output="",
                        error=f"配置参数格式错误: {config_arg}。应使用 key=value 格式",
                    )

                # 将 key=value 转换为 key:value 格式（configure 函数需要的格式）
                key, value = config_arg.split("=", 1)
                config_str = f"{key.strip()}:{value.strip()}"

                try:
                    configure(config_str, skip_print=True)
                    results.append(f"✓ 配置成功: {key.strip()} = {value.strip()}")
                except Exception as e:
                    return CLIResult(
                        success=False,
                        output="",
                        error=f"配置失败 {config_str}: {str(e)}",
                    )

            output = "\n".join(results)
            return CLIResult(success=True, output=output)

        except Exception as e:
            return CLIResult(
                success=False,
                output="",
                error=get_message_with_format("config_command_failed", error=str(e)),
            )

    def handle_print_mode(
        self, options: CLIOptions, cwd: Optional[str] = None
    ) -> CLIResult:
        """
        处理打印模式。

        Args:
            options: CLI选项
            cwd: 当前工作目录

        Returns:
            命令执行结果
        """
        # 检查是否启用异步模式
        if options.async_mode:
            from ..async_runner.async_handler import AsyncAgentHandler

            handler = AsyncAgentHandler(options, cwd)
            return handler.handle()
        else:
            handler = PrintModeHandler(options, cwd)
            return handler.handle()

    @classmethod
    def parse_args(cls, args: Optional[List[str]] = None) -> CLIOptions:
        """
        解析命令行参数。

        Args:
            args: 命令行参数列表，如果为None则使用sys.argv

        Returns:
            解析后的CLI选项
        """
        parser = argparse.ArgumentParser(
            description=get_message("cli_description"),
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=get_message("cli_examples"),
        )

        # 创建子命令解析器
        subparsers = parser.add_subparsers(
            dest="command", help=get_message("help_available_commands")
        )

        # config 子命令
        config_parser = subparsers.add_parser(
            "config", help=get_message("help_config_command")
        )
        config_parser.add_argument(
            "config_args", nargs="*", help=get_message("help_config_args")
        )

        # 默认命令（代码生成）- 当没有子命令时使用
        # 会话选项（移除模式选择，--continue 和 --resume 作为独立参数）
        parser.add_argument(
            "-c",
            "--continue",
            dest="continue_session",
            action="store_true",
            help=get_message("help_continue_session"),
        )
        parser.add_argument(
            "-r",
            "--resume",
            dest="resume_session",
            metavar="SESSION_ID",
            help=get_message("help_resume_session"),
        )

        # 输入输出选项
        parser.add_argument("prompt", nargs="?", help=get_message("help_prompt"))
        parser.add_argument(
            "--output-format",
            choices=["text", "json", "stream-json"],
            default="text",
            help=get_message("help_output_format"),
        )
        parser.add_argument(
            "--input-format",
            choices=["text", "json", "stream-json"],
            default="text",
            help=get_message("help_input_format"),
        )
        parser.add_argument(
            "-v", "--verbose", action="store_true", help=get_message("help_verbose")
        )

        # 高级选项
        advanced = parser.add_argument_group(get_message("help_advanced_options"))
        advanced.add_argument(
            "--max-turns", type=int, default=10000, help=get_message("help_max_turns")
        )
        advanced.add_argument("--system-prompt", help=get_message("help_system_prompt"))
        advanced.add_argument(
            "--system-prompt-path", help=get_message("help_system_prompt_path")
        )
        advanced.add_argument(
            "--allowed-tools", nargs="+", help=get_message("help_allowed_tools")
        )
        advanced.add_argument(
            "--permission-mode",
            choices=["manual", "acceptEdits"],
            default="manual",
            help=get_message("help_permission_mode"),
        )
        advanced.add_argument("--model", required=False, help=get_message("help_model"))
        advanced.add_argument(
            "--include-rules",
            action="store_true",
            help=get_message("help_include_rules"),
        )
        advanced.add_argument("--pr", action="store_true", help=get_message("help_pr"))
        advanced.add_argument(
            "--is-sub-agent", action="store_true", help=get_message("help_is_sub_agent")
        )
        advanced.add_argument(
            "--loop", type=int, default=1, help=get_message("help_loop")
        )
        advanced.add_argument(
            "--loop-keep-conversation",
            dest="loop_keep_conversation",
            action="store_true",
            help=get_message("help_loop_keep_conversation"),
        )
        advanced.add_argument(
            "--loop-additional-prompt",
            dest="loop_additional_prompt",
            help=get_message("help_loop_additional_prompt"),
        )
        advanced.add_argument(
            "--include-libs", dest="include_libs", help=get_message("help_include_libs")
        )
        advanced.add_argument(
            "--workflow", help="执行指定的 workflow（名称或文件路径）"
        )

        # 异步代理运行器选项
        async_group = parser.add_argument_group(get_message("help_async_group_title"))
        async_group.add_argument(
            "--async",
            dest="async_mode",
            action="store_true",
            help=get_message("help_async_mode"),
        )
        async_group.add_argument(
            "--split",
            dest="split_mode",
            choices=["h1", "h2", "h3", "any", "delimiter"],
            default="h1",
            help=get_message("help_split_mode"),
        )
        async_group.add_argument(
            "--delimiter", default="===", help=get_message("help_delimiter")
        )
        async_group.add_argument(
            "--min-level", type=int, default=1, help=get_message("help_min_level")
        )
        async_group.add_argument(
            "--max-level", type=int, default=3, help=get_message("help_max_level")
        )
        async_group.add_argument(
            "--workdir",
            default=get_default_async_workdir(),
            help=get_message("help_workdir"),
        )
        async_group.add_argument(
            "--from",
            dest="from_branch",
            default="",
            help=get_message("help_from_branch"),
        )
        async_group.add_argument(
            "--bg",
            dest="bg_mode",
            action="store_true",
            help=get_message("help_bg_mode"),
        )
        async_group.add_argument(
            "--task-prefix",
            dest="task_prefix",
            default="",
            help=get_message("help_task_prefix"),
        )
        async_group.add_argument(
            "--worktree-name",
            dest="worktree_name",
            help=get_message("help_worktree_name"),
        )

        # 解析参数
        parsed_args = parser.parse_args(args)

        # 转换为CLIOptions
        options = CLIOptions(
            command=getattr(parsed_args, "command", None),
            config_args=getattr(parsed_args, "config_args", []),
            continue_session=parsed_args.continue_session,
            resume_session=parsed_args.resume_session,
            prompt=parsed_args.prompt,
            output_format=parsed_args.output_format,
            input_format=parsed_args.input_format,
            verbose=parsed_args.verbose,
            max_turns=parsed_args.max_turns,
            system_prompt=parsed_args.system_prompt,
            system_prompt_path=getattr(parsed_args, "system_prompt_path", None),
            allowed_tools=parsed_args.allowed_tools or [],
            permission_mode=parsed_args.permission_mode,
            model=parsed_args.model,
            include_rules=parsed_args.include_rules,
            pr=parsed_args.pr,
            is_sub_agent=parsed_args.is_sub_agent,
            loop=parsed_args.loop,
            loop_keep_conversation=parsed_args.loop_keep_conversation,
            loop_additional_prompt=parsed_args.loop_additional_prompt,
            include_libs=(
                [lib.strip() for lib in parsed_args.include_libs.split(",")]
                if parsed_args.include_libs
                else []
            ),
            workflow=getattr(parsed_args, "workflow", None),
            # 异步代理运行器相关参数
            async_mode=parsed_args.async_mode,
            split_mode=parsed_args.split_mode,
            delimiter=parsed_args.delimiter,
            min_level=parsed_args.min_level,
            max_level=parsed_args.max_level,
            workdir=parsed_args.workdir,
            from_branch=parsed_args.from_branch,
            bg_mode=parsed_args.bg_mode,
            task_prefix=parsed_args.task_prefix,
            worktree_name=parsed_args.worktree_name,
        )

        return options

    @classmethod
    def main(cls) -> int:
        """
        CLI主入口点。

        Returns:
            退出码，0表示成功，非0表示失败
        """
        try:
            options = cls.parse_args()
            cli = cls()
            result = cli.run(options)

            if result.success:
                if result.output:
                    print(result.output)
                return 0
            else:
                print(
                    get_message_with_format("error_prefix", error=result.error),
                    file=sys.stderr,
                )
                return 1

        except Exception as e:
            # 如果是 verbose 模式，打印完整的异常堆栈
            if hasattr(options, "verbose") and options.verbose:
                import traceback

                print(f"[DEBUG] Unhandled exception:", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
            print(
                get_message_with_format("unhandled_error", error=str(e)),
                file=sys.stderr,
            )
            return 1

        finally:
            try:
                FileMonitor(os.getcwd()).stop()
            except Exception as e:
                pass


if __name__ == "__main__":
    sys.exit(AutoCoderCLI.main())
