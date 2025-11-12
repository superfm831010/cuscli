"""命令处理器 - 处理各种用户命令"""

from pathlib import Path
import asyncio

from autocoder.common.terminal_paste import resolve_paste_placeholders
from autocoder.common.core_config import get_memory_manager
from autocoder.common.global_cancel import CancelRequestedException
from autocoder.events.event_manager_singleton import gengerate_event_file_path
from autocoder.terminal.utils.shell import get_shell, run_shell_command_async
from autocoder.chat_auto_coder_lang import get_message as get_message_lang
from autocoder.common.ac_style_command_parser import parse_query
from autocoder.common.international import get_message, get_message_with_format
from autocoder.workflow_agents import (
    run_workflow_from_yaml,
    print_workflow_result,
    list_available_workflows,
)


class CommandProcessor:
    """命令处理器类，封装所有命令处理逻辑"""

    def __init__(
        self,
        plugin_manager,
        wrapped_functions,
        configure_func,
        global_cancel,
        show_help_func,
        debug=False,
    ):
        self.plugin_manager = plugin_manager
        self.wrapped_functions = wrapped_functions
        self.configure = configure_func
        self.global_cancel = global_cancel
        self.show_help = show_help_func
        self.debug = debug

        # 从 wrapped_functions 中提取常用函数
        self.run_agentic = wrapped_functions.get("run_agentic")
        self.coding = wrapped_functions.get("coding")
        self.chat = wrapped_functions.get("chat")
        self.execute_shell_command = wrapped_functions.get("execute_shell_command")
        self.voice_input = wrapped_functions.get("voice_input")
        self.design = wrapped_functions.get("design")
        self.active_context = wrapped_functions.get("active_context")

    def preprocess_input(self, user_input: str) -> str:
        """预处理用户输入"""
        # 首先解析粘贴占位符
        user_input = resolve_paste_placeholders(user_input)

        # 处理 user_input 的空格
        if user_input:
            temp_user_input = user_input.lstrip()  # 去掉左侧空格
            if temp_user_input.startswith("/"):
                user_input = temp_user_input

        return user_input

    async def handle_shell_enter(self, user_input: str, context: dict) -> bool:
        """处理 /shell 命令（进入 shell）"""
        session = context.get("session")
        shell = get_shell()
        await run_shell_command_async(shell, session)
        return True

    async def handle_shell_single(self, user_input: str, context: dict) -> bool:
        """处理 ! 开头的单行 shell 命令"""
        session = context.get("session")
        command = user_input[1:]  # 去掉 ! 前缀
        await run_shell_command_async(command, session)
        return True

    def handle_plugin_command(self, user_input: str, context: dict) -> bool:
        """尝试让插件处理命令"""
        if user_input.startswith("/"):
            plugin_result = self.plugin_manager.process_command(user_input)
            if plugin_result:
                plugin_name, handler, args = plugin_result
                if handler:
                    handler(*args)
                    return True
        return False

    async def handle_shell_mode(self, user_input: str, context: dict) -> bool:
        """处理 shell 模式下的输入"""
        memory_manager = get_memory_manager()
        if (
            memory_manager.is_shell_mode()
            and user_input
            and not user_input.startswith("/")
        ):
            session = context.get("session")
            shell = get_shell()
            if session and hasattr(session, "app"):
                try:
                    await session.app.run_system_command(
                        user_input, wait_for_enter=False
                    )
                except Exception:
                    import subprocess

                    subprocess.call([shell, "-c", user_input])
            else:
                output = self.execute_shell_command(user_input)
                if output:
                    print(output)
            return True
        return False

    def handle_auto_detect_mode(self, user_input: str, context: dict) -> bool:
        """处理自动检测模式"""
        memory_manager = get_memory_manager()
        if (
            memory_manager.is_auto_detect_mode()
            and user_input
            and not user_input.startswith("/")
        ):
            event_file, file_id = gengerate_event_file_path()
            self.configure(f"event_file:{event_file}")
            self.global_cancel.register_token(event_file)
            self.run_agentic(user_input, cancel_token=event_file)
            return True
        return False

    def handle_voice_input_mode(self, user_input: str, context: dict) -> bool:
        """处理语音输入模式"""
        memory_manager = get_memory_manager()
        new_prompt_callback = context.get("new_prompt_callback")

        if memory_manager.is_voice_input_mode() and not user_input.startswith("/"):
            text = self.voice_input()
            if text:
                new_prompt_callback("/coding " + text)
            return True
        return False

    def handle_voice_input_command(self, user_input: str, context: dict) -> bool:
        """/voice_input 命令"""
        new_prompt_callback = context.get("new_prompt_callback")
        text = self.voice_input()
        if text:
            new_prompt_callback("/coding " + text)
        return True

    def handle_clear(self, user_input: str, context: dict) -> bool:
        """/clear 或 /cls 命令"""
        print("\033c")
        return True

    def handle_add_files(self, user_input: str, context: dict) -> bool:
        """/add_files 命令"""
        from autocoder.auto_coder_runner import add_files

        args = user_input[len("/add_files") :].strip().split()
        add_files(args)
        return True

    def handle_remove_files(self, user_input: str, context: dict) -> bool:
        """/remove_files 命令"""
        from autocoder.auto_coder_runner import remove_files

        file_names = user_input[len("/remove_files") :].strip().split(",")
        remove_files(file_names)
        return True

    def handle_index_query(self, user_input: str, context: dict) -> bool:
        """/index/query 命令"""
        from autocoder.auto_coder_runner import index_query

        query = user_input[len("/index/query") :].strip()
        index_query(query)
        return True

    def handle_index_build(self, user_input: str, context: dict) -> bool:
        """/index/build 命令"""
        from autocoder.auto_coder_runner import index_build

        event_file, file_id = gengerate_event_file_path()
        self.configure(f"event_file:{event_file}")
        self.global_cancel.register_token(event_file)
        index_build()
        return True

    def handle_index_export(self, user_input: str, context: dict) -> bool:
        """/index/export 命令"""
        from autocoder.auto_coder_runner import index_export

        export_path = user_input[len("/index/export") :].strip()
        index_export(export_path)
        return True

    def handle_index_import(self, user_input: str, context: dict) -> bool:
        """/index/import 命令"""
        from autocoder.auto_coder_runner import index_import

        import_path = user_input[len("/index/import") :].strip()
        index_import(import_path)
        return True

    def handle_list_files(self, user_input: str, context: dict) -> bool:
        """/list_files 命令"""
        from autocoder.auto_coder_runner import list_files

        list_files()
        return True

    def handle_models(self, user_input: str, context: dict) -> bool:
        """/models 命令"""
        from autocoder.chat.models_command import handle_models_command

        query = user_input[len("/models") :].strip()
        handle_models_command(query)
        return True

    def handle_mode(self, user_input: str, context: dict) -> bool:
        """/mode 命令"""
        from autocoder.common.core_config import get_mode, set_mode

        conf = user_input[len("/mode") :].strip()
        if not conf:
            print(get_mode())
        else:
            set_mode(conf)
        return True

    def handle_conf_export(self, user_input: str, context: dict) -> bool:
        """/conf/export 命令"""
        from autocoder.common.conf_import_export import export_conf
        import os

        export_conf(os.getcwd(), user_input[len("/conf/export") :].strip() or ".")
        return True

    def handle_plugins(self, user_input: str, context: dict) -> bool:
        """/plugins 命令"""
        args = user_input[len("/plugins") :].strip().split()
        result = self.plugin_manager.handle_plugins_command(args)
        print(result, end="")
        return True

    def handle_conf(self, user_input: str, context: dict) -> bool:
        """/conf 命令"""
        from autocoder.chat.conf_command import handle_conf_command

        command_args = user_input[len("/conf") :].strip()
        result_message = handle_conf_command(command_args)
        print(result_message)
        return True

    def handle_revert(self, user_input: str, context: dict) -> bool:
        """/revert 命令"""
        from autocoder.auto_coder_runner import revert

        revert()
        return True

    def handle_commit(self, user_input: str, context: dict) -> bool:
        """/commit 命令"""
        from autocoder.auto_coder_runner import commit

        query = user_input[len("/commit") :].strip()
        commit(query)
        return True

    def handle_help(self, user_input: str, context: dict) -> bool:
        """/help 命令"""
        query = user_input[len("/help") :].strip()
        if not query:
            self.show_help()
        else:
            from autocoder.auto_coder_runner import help

            help(query)
        return True

    def handle_exclude_dirs(self, user_input: str, context: dict) -> bool:
        """/exclude_dirs 命令"""
        from autocoder.auto_coder_runner import exclude_dirs

        dir_names = user_input[len("/exclude_dirs") :].strip().split(",")
        exclude_dirs(dir_names)
        return True

    def handle_exclude_files(self, user_input: str, context: dict) -> bool:
        """/exclude_files 命令"""
        from autocoder.auto_coder_runner import exclude_files

        query = user_input[len("/exclude_files") :].strip()
        exclude_files(query)
        return True

    def handle_exit(self, user_input: str, context: dict) -> None:
        """/exit 命令"""
        raise EOFError()

    def handle_coding(self, user_input: str, context: dict) -> bool:
        """/coding 命令"""
        event_file, file_id = gengerate_event_file_path()
        self.configure(f"event_file:{event_file}")
        self.global_cancel.register_token(event_file)
        query = user_input[len("/coding") :].strip()
        if not query:
            print(f"\033[91m{get_message_lang('please_enter_request')}\033[0m")
            return True
        self.coding(query, cancel_token=event_file)
        return True

    def handle_chat(self, user_input: str, context: dict) -> bool:
        """/chat 命令"""
        event_file, file_id = gengerate_event_file_path()
        self.configure(f"event_file:{event_file}")
        self.global_cancel.register_token(event_file)
        query = user_input[len("/chat") :].strip()
        if not query:
            print(f"\033[91m{get_message_lang('please_enter_request')}\033[0m")
        else:
            self.chat(query)
        return True

    def handle_design(self, user_input: str, context: dict) -> bool:
        """/design 命令"""
        query = user_input[len("/design") :].strip()
        if not query:
            print(f"\033[91m{get_message_lang('please_enter_design_request')}\033[0m")
        else:
            self.design(query)
        return True

    def handle_summon(self, user_input: str, context: dict) -> bool:
        """/summon 命令"""
        from autocoder.auto_coder_runner import summon

        query = user_input[len("/summon") :].strip()
        if not query:
            print(f"\033[91m{get_message_lang('please_enter_request')}\033[0m")
        else:
            summon(query)
        return True

    def handle_lib(self, user_input: str, context: dict) -> bool:
        """/lib 命令"""
        from autocoder.auto_coder_runner import lib_command

        args = user_input[len("/lib") :].strip().split()
        lib_command(args)
        return True

    def handle_rules(self, user_input: str, context: dict) -> bool:
        """/rules 命令"""
        from autocoder.auto_coder_runner import rules

        query = user_input[len("/rules") :].strip()
        rules(query)
        return True

    def handle_mcp(self, user_input: str, context: dict) -> bool:
        """/mcp 命令"""
        from autocoder.auto_coder_runner import mcp

        query = user_input[len("/mcp") :].strip()
        if not query:
            print(get_message_lang("please_enter_query"))
        else:
            mcp(query)
        return True

    def handle_active_context(self, user_input: str, context: dict) -> bool:
        """/active_context 命令"""
        query = user_input[len("/active_context") :].strip()
        self.active_context(query)
        return True

    def handle_auto(self, user_input: str, context: dict) -> bool:
        """/auto 命令"""
        query = user_input[len("/auto") :].strip()
        event_file, _ = gengerate_event_file_path()
        self.global_cancel.register_token(event_file)
        self.configure(f"event_file:{event_file}")
        self.run_agentic(query, cancel_token=event_file)
        return True

    def handle_debug(self, user_input: str, context: dict) -> bool:
        """/debug 命令"""
        code = user_input[len("/debug") :].strip()
        try:
            result = eval(code)
            print(f"Debug result: {result}")
        except Exception as e:
            print(f"Debug error: {str(e)}")
        return True

    def handle_shell_command(self, user_input: str, context: dict) -> bool:
        """/shell <command> 命令"""
        from autocoder.auto_coder_runner import gen_and_exec_shell_command

        memory_manager = get_memory_manager()

        command = user_input[len("/shell") :].strip()
        if not command:
            # 如果没有命令参数，切换到 shell 模式
            memory_manager.set_mode("shell")
            print(get_message_lang("switched_to_shell_mode"))
        else:
            if command.startswith("/chat"):
                event_file, file_id = gengerate_event_file_path()
                self.global_cancel.register_token(event_file)
                self.configure(f"event_file:{event_file}")
                command = command[len("/chat") :].strip()
                gen_and_exec_shell_command(command)
            else:
                self.execute_shell_command(command)
        return True

    def handle_workflow(self, user_input: str, context: dict) -> bool:
        """/workflow 命令"""
        # 解析命令参数
        query = user_input[len("/workflow") :].strip()

        # 如果是 /workflow /help，打印帮助信息
        if query == "/help" or query == "help" or not query:
            self._print_workflow_help()
            return True

        event_file, _ = gengerate_event_file_path()
        self.global_cancel.register_token(event_file)
        self.configure(f"event_file:{event_file}")

        # 使用 ac_style_command_parser 解析参数
        parsed = parse_query(f"/workflow {query}")
        workflow_info = parsed.get("workflow", {})
        args = workflow_info.get("args", [])
        kwargs = workflow_info.get("kwargs", {})

        if not args:
            print(f"\033[91m{get_message('workflow_error_no_name')}\033[0m")
            print(get_message("workflow_help_hint"))
            return True

        workflow_name = args[0]

        # 获取当前目录
        source_dir = str(Path.cwd())

        # 运行 workflow
        try:
            print(
                f"\n🚀 {get_message_with_format('workflow_running', workflow_name=workflow_name)}"
            )
            if kwargs:
                print(
                    f"📋 {get_message_with_format('workflow_parameters', kwargs=kwargs)}"
                )
            print()

            result = run_workflow_from_yaml(
                yaml_path=workflow_name,
                source_dir=source_dir,
                vars_override=kwargs,
                cancel_token=event_file,
            )

            # 打印结果
            print_workflow_result(result)

        except FileNotFoundError as e:
            print(
                f"\033[91m❌ {get_message_with_format('workflow_not_found', workflow_name=workflow_name)}\033[0m"
            )
            print(f"\n{get_message('workflow_available_list')}")
            workflows = list_available_workflows(source_dir)
            if workflows:
                for name, path in workflows.items():
                    print(f"  - {name}: {path}")
            else:
                print(f"  {get_message('workflow_none_found')}")
        except Exception as e:
            print(
                f"\033[91m❌ {get_message_with_format('workflow_run_failed', error=str(e))}\033[0m"
            )
            if self.debug:
                import traceback

                traceback.print_exc()

        return True

    def _print_workflow_help(self):
        """打印 workflow 命令帮助信息"""
        # 使用国际化的帮助文本
        print(get_message("workflow_help_text"))

        # 列出可用的 workflows
        source_dir = str(Path.cwd())
        workflows = list_available_workflows(source_dir)

        if workflows:
            print(f"\n✨ {get_message('workflow_available_title')}")
            for name, path in workflows.items():
                print(f"  - {name}")
                print(f"    {path}")
        else:
            print(f"\n⚠️  {get_message('workflow_no_workflows_found')}")

        print()

    def handle_unknown_or_fallback(self, user_input: str, context: dict) -> bool:
        """处理未知命令或非命令输入"""
        if user_input and user_input.strip():
            if user_input.startswith("/"):
                command = user_input.split(" ")[0][1:]
                query = user_input[len(command) + 1 :].strip()
                user_input = f"/auto /command {command}.md {query}"
            else:
                user_input = f"/auto {user_input}"

            # 只有非命令输入才执行auto_command
            self.handle_auto(user_input, context)
        return True
