from loguru import logger

logger.remove()  # 把默认 sink 去掉，彻底静音
from autocoder.run_context import get_run_context, RunMode

# 设置运行模式为终端模式
get_run_context().set_mode(RunMode.TERMINAL)

import sys
import asyncio
from autocoder.chat.conf_command import handle_conf_command
from autocoder.auto_coder_runner import (
    auto_command,
    run_agentic,
    # Keep configure if it's used elsewhere or by handle_conf_command internally (though we adapted handle_conf_command not to)
    configure,
    # manage_models, # Removed
    # print_conf, # Removed
    exclude_dirs,
    exclude_files,
    ask,
    coding,
    load_tokenizer,
    initialize_system,
    InitializeSystemRequest,
    add_files,
    remove_files,
    index_query,
    index_build,
    index_export,
    index_import,
    list_files,
    lib_command,
    mcp,
    revert,
    commit,
    design,
    voice_input,
    chat,
    gen_and_exec_shell_command,
    execute_shell_command,
    get_mcp_server,
    completer,
    summon,
    active_context,
    rules,
    start as start_engine,
    stop as stop_engine,
)

# Import memory and mode management from core_config module
from autocoder.common.core_config import (
    cycle_mode,
    get_mode,
    set_mode,
    toggle_human_as_model,
    get_human_as_model_string,
    get_memory_manager,
)
from autocoder.chat.models_command import handle_models_command
from autocoder.common.global_cancel import global_cancel, CancelRequestedException
from autocoder.events.event_manager_singleton import gengerate_event_file_path
from autocoder.plugins import PluginManager
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import FormattedText
from autocoder.chat_auto_coder_lang import (
    get_message,
    get_message_with_format as get_message_with_format_local,
)
from autocoder.common.international import (
    get_message as get_i18n_message,
    get_message_with_format,
)
from autocoder.version import __version__
from prompt_toolkit.styles import Style
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit import PromptSession
from autocoder.common.terminal_paste import (
    register_paste_handler,
    resolve_paste_placeholders,
)
import os
import argparse
import time


class TaskEvent:
    def __init__(self):
        self.state = "idle"  # idle, pending, started, running, completed
        self._event = asyncio.Event()
        self._event.set()  # 初始状态为可用

    def set_state(self, state):
        """设置任务状态"""
        self.state = state
        if state == "completed":
            self._event.set()
        else:
            self._event.clear()

    def get_state(self):
        """获取当前状态"""
        return self.state

    def is_completed(self):
        """检查是否完成"""
        return self.state == "completed"

    def is_running(self):
        """检查是否正在运行"""
        return self.state in ["started", "running"]

    async def wait(self):
        """等待任务完成"""
        await self._event.wait()

    def clear(self):
        """清除完成状态，重置为pending"""
        self.set_state("idle")


# Ensure the correct import is present

# Create a global plugin manager
plugin_manager = PluginManager()

# Create wrapped versions of intercepted functions
original_functions = {
    "ask": ask,
    "coding": coding,
    "chat": chat,
    "design": design,
    "voice_input": voice_input,
    "auto_command": auto_command,
    "run_agentic": run_agentic,
    "execute_shell_command": execute_shell_command,
    "active_context": active_context,
}


def parse_arguments():

    parser = argparse.ArgumentParser(description="Chat Auto Coder")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Enter the auto-coder.chat without initializing the system",
    )

    parser.add_argument(
        "--skip_provider_selection",
        action="store_true",
        help="Skip the provider selection",
    )

    parser.add_argument(
        "--product_mode",
        type=str,
        default="lite",
        help="The mode of the auto-coder.chat, lite/pro default is lite",
    )

    parser.add_argument("--lite", action="store_true", help="Lite mode")
    parser.add_argument("--pro", action="store_true", help="Pro mode")

    return parser.parse_args()


def show_help():
    print(f"\033[1m{get_message('supported_commands')}\033[0m")
    print()
    print(
        f"  \033[94m{get_message('commands')}\033[0m - \033[93m{get_message('description')}\033[0m"
    )
    print(
        f"  \033[94m/auto\033[0m \033[93m<query>\033[0m - \033[92m{get_message('auto_desc')}\033[0m"
    )
    print(
        f"    \033[94m/auto /new\033[0m \033[93m<query>\033[0m - \033[92m{get_message('auto_new_desc')}\033[0m"
    )
    print(
        f"    \033[94m/auto /resume\033[0m \033[93m<id> <query>\033[0m - \033[92m{get_message('auto_resume_desc')}\033[0m"
    )
    print(
        f"    \033[94m/auto /list\033[0m - \033[92m{get_message('auto_list_desc')}\033[0m"
    )
    print(
        f"    \033[94m/auto /command\033[0m \033[93m<file>\033[0m - \033[92m{get_message('auto_command_desc')}\033[0m"
    )

    print(f"  \033[94m/commit\033[0m - \033[92m{get_message('commit_desc')}\033[0m")

    print(
        f"  \033[94m/conf\033[0m \033[93m<key>:<value>\033[0m  - \033[92m{get_message('conf_desc')}\033[0m"
    )

    print(
        f"  \033[94m/shell\033[0m \033[93m<command>\033[0m - \033[92m{get_message('shell_desc')}\033[0m"
    )
    print(
        f"  \033[94m/shell\033[0m - \033[92m{get_message('shell_interactive_desc')}\033[0m"
    )
    print(
        f"  \033[94m!\033[0m\033[93m<command>\033[0m - \033[92m{get_message('shell_single_command_desc')}\033[0m"
    )

    print(
        f"  \033[94m/add_files\033[0m \033[93m<file1> <file2> ...\033[0m - \033[92m{get_message('add_files_desc')}\033[0m"
    )
    print(
        f"  \033[94m/remove_files\033[0m \033[93m<file1>,<file2> ...\033[0m - \033[92m{get_message('remove_files_desc')}\033[0m"
    )
    print(
        f"  \033[94m/chat\033[0m \033[93m<query>\033[0m - \033[92m{get_message('chat_desc')}\033[0m"
    )
    print(
        f"  \033[94m/coding\033[0m \033[93m<query>\033[0m - \033[92m{get_message('coding_desc')}\033[0m"
    )

    print(f"  \033[94m/revert\033[0m - \033[92m{get_message('revert_desc')}\033[0m")
    print(
        f"  \033[94m/index/query\033[0m \033[93m<args>\033[0m - \033[92m{get_message('index_query_desc')}\033[0m"
    )
    print(
        f"  \033[94m/index/build\033[0m - \033[92m{get_message('index_build_desc')}\033[0m"
    )
    print(
        f"  \033[94m/list_files\033[0m - \033[92m{get_message('list_files_desc')}\033[0m"
    )
    print(f"  \033[94m/help\033[0m - \033[92m{get_message('help_desc')}\033[0m")
    print(f"  \033[94m/mode\033[0m - \033[92m{get_message('mode_desc')}\033[0m")
    print(f"  \033[94m/lib\033[0m - \033[92m{get_message('lib_desc')}\033[0m")
    print(f"  \033[94m/models\033[0m - \033[92m{get_message('models_desc')}\033[0m")
    print(f"  \033[94m/plugins\033[0m - \033[92m{get_message('plugins_desc')}\033[0m")
    print(
        f"  \033[94m/active_context\033[0m - \033[92m{get_message('active_context_desc')}\033[0m"
    )
    print(f"  \033[94m/exit\033[0m - \033[92m{get_message('exit_desc')}\033[0m")
    print()

    # 显示插件命令
    if plugin_manager.command_handlers:
        print(f"\033[1m{get_message('plugin_commands_title')}\033[0m")
        print(
            f"  \033[94m{get_message('plugin_command_header')}\033[0m - \033[93m{get_message('plugin_description_header')}\033[0m"
        )

        # 收集已显示的插件，避免重复显示
        displayed_plugins = set()

        for cmd, (_, desc, plugin_id) in plugin_manager.command_handlers.items():
            plugin = plugin_manager.get_plugin(plugin_id)
            if plugin and plugin_id not in displayed_plugins:
                # 检查插件是否有自定义帮助文本
                custom_help = plugin.get_help_text()
                if custom_help:
                    # 使用插件自定义的折叠显示
                    print(custom_help)
                    displayed_plugins.add(plugin_id)
                else:
                    # 使用默认的单行显示
                    print(
                        f"  \033[94m{cmd}\033[0m - \033[92m{desc} ({get_message('plugin_from')} {plugin.plugin_name()})\033[0m"
                    )
            elif not plugin:
                print(
                    f"  \033[94m{cmd}\033[0m - \033[92m{desc} ({get_message('plugin_from_unknown')})\033[0m"
                )
        print()


class EnhancedCompleter(Completer):
    """结合内置补全器和插件补全功能的增强补全器"""

    def __init__(self, base_completer: Completer, plugin_manager: PluginManager):
        self.base_completer: Completer = base_completer
        self.plugin_manager: PluginManager = plugin_manager
        self._custom_commands_cache = set()
        self._cache_valid = False

    def _get_custom_commands(self):
        """获取自定义命令列表（从 .autocodercommands 目录）"""
        if self._cache_valid and self._custom_commands_cache:
            return sorted(list(self._custom_commands_cache))
        
        try:
            from autocoder.common.command_file_manager.manager import CommandManager
            
            # 创建命令管理器
            command_manager = CommandManager()
            
            # 列出所有命令文件
            result = command_manager.list_command_files(recursive=True)
            
            if result.success:
                commands = set()
                for file_name in result.command_files:
                    # 去掉 .md 后缀和路径前缀，只保留命令名
                    command_name = os.path.basename(file_name)
                    if command_name.endswith('.md'):
                        command_name = command_name[:-3]
                    # 添加 / 前缀形成完整命令
                    commands.add(f"/{command_name}")
                
                self._custom_commands_cache = commands
                self._cache_valid = True
                return sorted(list(commands))
        except Exception:
            # 静默处理异常，返回空列表
            pass
        
        return []

    def get_completions(self, document, complete_event):
        # 获取当前输入的文本
        text_before_cursor = document.text_before_cursor.lstrip()

        # 只有当我们需要处理命令补全时才进行处理
        if text_before_cursor.startswith("/"):

            # 获取当前输入的命令前缀
            current_input = text_before_cursor
            # 检查是否需要动态补全
            if " " in current_input:
                # 将连续的空格替换为单个空格
                _input_one_space = " ".join(current_input.split())
                # 先尝试动态补全特定命令
                dynamic_cmds = self.plugin_manager.get_dynamic_cmds()
                for dynamic_cmd in dynamic_cmds:
                    if _input_one_space.startswith(dynamic_cmd):
                        # 使用 PluginManager 处理动态补全，通常是用于命令或子命令动态的参数值列表的补全
                        completions = self.plugin_manager.process_dynamic_completions(
                            dynamic_cmd, current_input
                        )
                        for completion_text, display_text in completions:
                            yield Completion(
                                completion_text,
                                start_position=0,
                                display=display_text,
                            )
                        return

                # 如果不是特定命令，检查一般命令 + 空格的情况, 通常是用于固定的下级子命令列表的补全
                cmd_parts = current_input.split(maxsplit=1)
                base_cmd = cmd_parts[0]

                # 获取插件命令补全
                plugin_completions_dict = self.plugin_manager.get_plugin_completions()

                # 如果命令存在于补全字典中，进行处理
                if base_cmd in plugin_completions_dict:
                    yield from self._process_command_completions(
                        base_cmd, current_input, plugin_completions_dict[base_cmd]
                    )
                    return
            # 处理直接命令补全 - 如果输入不包含空格，匹配整个命令
            # 1. 插件和内置命令
            for command in self.plugin_manager.get_all_commands_with_prefix(
                current_input
            ):
                yield Completion(
                    command[len(current_input) :],
                    start_position=0,
                    display=command,
                )
            
            # 2. 自定义命令（从 .autocodercommands 目录）
            custom_commands = self._get_custom_commands()
            for command in custom_commands:
                if command.startswith(current_input):
                    yield Completion(
                        command[len(current_input) :],
                        start_position=0,
                        display=command,
                    )

        # 获取并返回基础补全器的补全
        if self.base_completer:
            for completion in self.base_completer.get_completions(
                document, complete_event
            ):
                yield completion

    def _process_command_completions(self, command, current_input, completions):
        """处理通用命令补全"""
        # 提取子命令前缀
        parts = current_input.split(maxsplit=1)
        cmd_prefix = ""
        if len(parts) > 1:
            cmd_prefix = parts[1].strip()

        # 对于任何命令，当子命令前缀为空或与补全选项匹配时，都显示补全
        for completion in completions:
            if cmd_prefix == "" or completion.startswith(cmd_prefix):
                # 只提供未输入部分作为补全
                remaining_text = completion[len(cmd_prefix) :]
                # 修复：设置 start_position 为 0，这样不会覆盖用户已输入的部分
                start_position = 0
                yield Completion(
                    remaining_text,
                    start_position=start_position,
                    display=completion,
                )

    async def get_completions_async(self, document, complete_event):
        """异步获取补全内容。

        使用 asyncio.run_in_executor 来异步执行耗时的补全操作，
        避免阻塞主线程导致输入卡顿。
        """
        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        # 获取当前输入的文本
        text_before_cursor = document.text_before_cursor.lstrip()

        # 只有当我们需要处理命令补全时才进行处理
        if text_before_cursor.startswith("/"):
            # 获取当前输入的命令前缀
            current_input = text_before_cursor

            # 使用线程池执行器来异步执行耗时操作
            loop = asyncio.get_event_loop()
            executor = ThreadPoolExecutor(max_workers=1)

            try:
                # 检查是否需要动态补全
                if " " in current_input:
                    # 将连续的空格替换为单个空格
                    _input_one_space = " ".join(current_input.split())

                    # 异步获取动态命令列表
                    dynamic_cmds = await loop.run_in_executor(
                        executor, self.plugin_manager.get_dynamic_cmds
                    )

                    for dynamic_cmd in dynamic_cmds:
                        if _input_one_space.startswith(dynamic_cmd):
                            # 异步处理动态补全
                            completions = await loop.run_in_executor(
                                executor,
                                self.plugin_manager.process_dynamic_completions,
                                dynamic_cmd,
                                current_input,
                            )
                            for completion_text, display_text in completions:
                                yield Completion(
                                    completion_text,
                                    start_position=0,
                                    display=display_text,
                                )
                            return

                    # 如果不是特定命令，检查一般命令 + 空格的情况
                    cmd_parts = current_input.split(maxsplit=1)
                    base_cmd = cmd_parts[0]

                    # 异步获取插件命令补全
                    plugin_completions_dict = await loop.run_in_executor(
                        executor, self.plugin_manager.get_plugin_completions
                    )

                    # 如果命令存在于补全字典中，进行处理
                    if base_cmd in plugin_completions_dict:
                        # 异步处理命令补全
                        completions_list = await loop.run_in_executor(
                            executor,
                            self._get_command_completions_list,
                            base_cmd,
                            current_input,
                            plugin_completions_dict[base_cmd],
                        )
                        for completion in completions_list:
                            yield completion
                        return
                else:
                    # 处理直接命令补全 - 异步获取所有匹配的命令
                    # 1. 插件和内置命令
                    commands = await loop.run_in_executor(
                        executor,
                        self.plugin_manager.get_all_commands_with_prefix,
                        current_input,
                    )
                    for command in commands:
                        yield Completion(
                            command[len(current_input) :],
                            start_position=0,
                            display=command,
                        )
                    
                    # 2. 自定义命令（从 .autocodercommands 目录）
                    custom_commands = await loop.run_in_executor(
                        executor,
                        self._get_custom_commands,
                    )
                    for command in custom_commands:
                        if command.startswith(current_input):
                            yield Completion(
                                command[len(current_input) :],
                                start_position=0,
                                display=command,
                            )
            finally:
                executor.shutdown(wait=False)

        # 异步获取基础补全器的补全
        if self.base_completer:
            # 如果基础补全器支持异步方法，优先使用
            if hasattr(self.base_completer, "get_completions_async"):
                async for completion in self.base_completer.get_completions_async(
                    document, complete_event
                ):
                    yield completion
            else:
                # 否则在线程池中运行同步方法
                loop = asyncio.get_event_loop()
                executor = ThreadPoolExecutor(max_workers=1)
                try:
                    completions = await loop.run_in_executor(
                        executor,
                        list,
                        self.base_completer.get_completions(document, complete_event),
                    )
                    for completion in completions:
                        yield completion
                finally:
                    executor.shutdown(wait=False)

    def _get_command_completions_list(self, command, current_input, completions):
        """获取命令补全列表（用于异步执行）"""
        return list(
            self._process_command_completions(command, current_input, completions)
        )


ARGS = None


def load_builtin_plugins():
    """加载内置插件"""
    try:
        # 发现所有可用的插件
        discovered_plugins = plugin_manager.discover_plugins()

        # 排除的示例插件列表
        excluded_plugins = {
            "autocoder.plugins.dynamic_completion_example",
            "autocoder.plugins.sample_plugin",
        }

        # 自动加载内置插件（在autocoder.plugins模块中的插件）
        builtin_loaded = 0
        for plugin_class in discovered_plugins:
            module_name = plugin_class.__module__
            if (
                module_name.startswith("autocoder.plugins.")
                and not module_name.endswith(".__init__")
                and module_name not in excluded_plugins
            ):
                try:
                    if plugin_manager.load_plugin(plugin_class):
                        builtin_loaded += 1
                        print(f"✓ Loaded builtin plugin: {plugin_class.plugin_name()}")
                except Exception as e:
                    print(
                        f"✗ Failed to load builtin plugin {plugin_class.plugin_name()}: {e}"
                    )

        if builtin_loaded > 0:
            print(
                get_message_with_format_local(
                    "loaded_plugins_builtin", count=builtin_loaded
                )
            )
        else:
            print(get_message("no_builtin_plugins_loaded"))

    except Exception as e:
        print(f"Error loading builtin plugins: {e}")


# 后台任务：监控全局状态或执行其他后台逻辑
async def background_task(stop_event: asyncio.Event, session=None):
    """后台任务：可以用于监控系统状态、清理任务等"""
    counter = 0
    toolbar_refresh_counter = 0
    last_async_task_count = 0

    # 配置刷新频率（秒）
    TOOLBAR_REFRESH_INTERVAL = 5  # 默认5秒刷新一次
    FAST_REFRESH_INTERVAL = 1  # 有异步任务时1秒刷新一次

    while not stop_event.is_set():
        try:
            # 检查是否有需要处理的后台任务
            # 这里可以添加系统监控逻辑
            counter += 1
            toolbar_refresh_counter += 1

            # 检查当前异步任务状态，决定刷新频率
            current_async_task_count = 0
            try:
                from pathlib import Path
                from autocoder.sdk.async_runner.task_metadata import TaskMetadataManager

                async_agent_dir = Path.home() / ".auto-coder" / "async_agent"
                meta_dir = async_agent_dir / "meta"

                if meta_dir.exists():
                    metadata_manager = TaskMetadataManager(str(meta_dir))
                    summary = metadata_manager.get_task_summary()
                    current_async_task_count = summary.get("running", 0)
            except Exception:
                # 静默处理异常
                pass

            # 智能刷新：有异步任务时更频繁刷新，无任务时降低刷新频率
            should_refresh = False
            if current_async_task_count > 0:
                # 有异步任务时，每秒刷新
                should_refresh = toolbar_refresh_counter >= FAST_REFRESH_INTERVAL
            else:
                # 无异步任务时，每5秒刷新
                should_refresh = toolbar_refresh_counter >= TOOLBAR_REFRESH_INTERVAL

            # 任务数量变化时立即刷新
            if current_async_task_count != last_async_task_count:
                should_refresh = True
                last_async_task_count = current_async_task_count

            # 执行工具栏刷新
            if should_refresh and session and hasattr(session, "app"):
                try:
                    session.app.invalidate()
                    toolbar_refresh_counter = 0
                except Exception:
                    # 静默处理刷新异常，不影响后台任务运行
                    pass

            # 每60秒执行一次清理
            if counter % 60 == 0:
                # 执行一些后台清理任务
                pass

            await asyncio.sleep(1)
        except asyncio.CancelledError:
            break
        except Exception as e:
            # 后台任务出错时，不要让整个应用崩溃
            if ARGS and ARGS.debug:
                print(f"Background task error: {e}")
            await asyncio.sleep(5)  # 出错后等待5秒再继续


async def process_user_input(user_input: str, new_prompt_callback, session=None):
    """处理用户输入的异步函数"""
    try:
        # 首先解析粘贴占位符
        user_input = resolve_paste_placeholders(user_input)

        # 处理 user_input 的空格
        if user_input:
            temp_user_input = user_input.lstrip()  # 去掉左侧空格
            if temp_user_input.startswith("/"):
                user_input = temp_user_input

        # 获取当前shell类型
        import platform

        shell = "/bin/bash" if platform.system() != "Windows" else "cmd.exe"

        # 1. 如果用户输入 /shell，启动一个子 shell
        if user_input == "/shell":
            if session and hasattr(session, "app"):
                try:
                    # 正确地等待异步方法
                    await session.app.run_system_command(shell, wait_for_enter=False)
                except Exception:
                    # 如果异步调用失败，回退到同步方式
                    import subprocess

                    subprocess.call([shell])
            else:
                import subprocess

                subprocess.call([shell])
            return

        # 2. 如果以 ! 开头，当作单行 shell 命令执行
        if user_input.startswith("!"):
            command = user_input[1:]  # 去掉 ! 前缀
            if session and hasattr(session, "app"):
                try:
                    # 正确地等待异步方法
                    await session.app.run_system_command(command, wait_for_enter=False)
                except Exception:
                    # 如果异步调用失败，回退到同步方式
                    import subprocess

                    subprocess.call([shell, "-c", command])
            else:
                import subprocess

                subprocess.call([shell, "-c", command])
            return

        # 修复插件命令处理逻辑
        plugin_handled = False
        if user_input.startswith("/"):
            plugin_result = plugin_manager.process_command(user_input)
            if plugin_result:
                plugin_name, handler, args = plugin_result
                if handler:
                    handler(*args)
                    plugin_handled = True

        # 如果插件已处理命令，直接返回
        if plugin_handled:
            return

        # 如果插件未处理，继续处理内置命令
        memory_manager = get_memory_manager()

        # Shell 模式处理 - 优先级最高
        if (
            memory_manager.is_shell_mode()
            and user_input
            and not user_input.startswith("/")
        ):
            if session and hasattr(session, "app"):
                try:
                    # 正确地等待异步方法
                    await session.app.run_system_command(
                        user_input, wait_for_enter=False
                    )
                except Exception:
                    # 如果异步调用失败，回退到同步方式
                    import subprocess

                    subprocess.call([shell, "-c", user_input])
            else:
                output = execute_shell_command(user_input)
                if output:
                    print(output)
            return

        if (
            memory_manager.is_auto_detect_mode()
            and user_input
            and not user_input.startswith("/")
        ):
            event_file, file_id = gengerate_event_file_path()
            configure(f"event_file:{event_file}")
            global_cancel.register_token(event_file)
            run_agentic(user_input, cancel_token=event_file)

        elif memory_manager.is_voice_input_mode() and not user_input.startswith("/"):
            text = voice_input()
            if text:  # Check if text is not None
                new_prompt_callback("/coding " + text)

        elif user_input.startswith("/voice_input"):
            text = voice_input()
            if text:  # Check if text is not None
                new_prompt_callback("/coding " + text)

        elif user_input.startswith("/clear") or user_input.startswith("/cls"):
            print("\033c")

        elif user_input.startswith("/add_files"):
            args = user_input[len("/add_files") :].strip().split()
            add_files(args)
        elif user_input.startswith("/remove_files"):
            file_names = user_input[len("/remove_files") :].strip().split(",")
            remove_files(file_names)
        elif user_input.startswith("/index/query"):
            query = user_input[len("/index/query") :].strip()
            index_query(query)

        elif user_input.startswith("/index/build"):
            event_file, file_id = gengerate_event_file_path()
            configure(f"event_file:{event_file}")
            global_cancel.register_token(event_file)
            index_build()

        elif user_input.startswith("/index/export"):
            export_path = user_input[len("/index/export") :].strip()
            index_export(export_path)

        elif user_input.startswith("/index/import"):
            import_path = user_input[len("/index/import") :].strip()
            index_import(import_path)

        elif user_input.startswith("/list_files"):
            list_files()

        elif user_input.startswith("/models"):
            query = user_input[len("/models") :].strip()
            handle_models_command(query)

        elif user_input.startswith("/mode"):
            conf = user_input[len("/mode") :].strip()
            if not conf:
                print(get_mode())
            else:
                set_mode(conf)

        elif user_input.startswith("/conf/export"):
            from autocoder.common.conf_import_export import export_conf

            export_conf(os.getcwd(), user_input[len("/conf/export") :].strip() or ".")

        elif user_input.startswith("/plugins"):
            # 提取命令参数并交由 plugin_manager 处理
            args = user_input[len("/plugins") :].strip().split()
            result = plugin_manager.handle_plugins_command(args)
            print(result, end="")

        # Handle /conf and its subcommands like /conf /export, /conf /import
        elif user_input.startswith("/conf"):
            # Extract everything after "/conf"
            command_args = user_input[len("/conf") :].strip()
            # Call the handler from conf_command.py and print its string result
            result_message = handle_conf_command(command_args)
            print(result_message)
        elif user_input.startswith("/revert"):
            revert()
        elif user_input.startswith("/commit"):
            query = user_input[len("/commit") :].strip()
            commit(query)
        elif user_input.startswith("/help"):
            query = user_input[len("/help") :].strip()
            if not query:
                show_help()
            else:
                from autocoder.auto_coder_runner import help

                help(query)

        elif user_input.startswith("/exclude_dirs"):
            dir_names = user_input[len("/exclude_dirs") :].strip().split(",")
            exclude_dirs(dir_names)

        elif user_input.startswith("/exclude_files"):
            query = user_input[len("/exclude_files") :].strip()
            exclude_files(query)

        elif user_input.startswith("/exit"):
            # 退出应用
            raise EOFError()

        elif user_input.startswith("/coding"):
            event_file, file_id = gengerate_event_file_path()
            configure(f"event_file:{event_file}")
            global_cancel.register_token(event_file)
            query = user_input[len("/coding") :].strip()
            if not query:
                print(f"\033[91m{get_message('please_enter_request')}\033[0m")
                return
            coding(query, cancel_token=event_file)
        elif user_input.startswith("/chat"):
            event_file, file_id = gengerate_event_file_path()
            configure(f"event_file:{event_file}")
            global_cancel.register_token(event_file)
            query = user_input[len("/chat") :].strip()
            if not query:
                print(f"\033[91m{get_message('please_enter_request')}\033[0m")
            else:
                chat(query)

        elif user_input.startswith("/design"):
            query = user_input[len("/design") :].strip()
            if not query:
                print(f"\033[91m{get_message('please_enter_design_request')}\033[0m")
            else:
                design(query)

        elif user_input.startswith("/summon"):
            query = user_input[len("/summon") :].strip()
            if not query:
                print(f"\033[91m{get_message('please_enter_request')}\033[0m")
            else:
                summon(query)

        elif user_input.startswith("/lib"):
            args = user_input[len("/lib") :].strip().split()
            lib_command(args)

        elif user_input.startswith("/rules"):
            query = user_input[len("/rules") :].strip()
            rules(query)

        elif user_input.startswith("/mcp"):
            query = user_input[len("/mcp") :].strip()
            if not query:
                print(get_message("please_enter_query"))
            else:
                mcp(query)

        elif user_input.startswith("/active_context"):
            query = user_input[len("/active_context") :].strip()
            active_context(query)

        elif user_input.startswith("/auto"):
            query = user_input[len("/auto") :].strip()
            event_file, _ = gengerate_event_file_path()
            global_cancel.register_token(event_file)
            configure(f"event_file:{event_file}")
            run_agentic(query, cancel_token=event_file)
        elif user_input.startswith("/debug"):
            code = user_input[len("/debug") :].strip()
            try:
                result = eval(code)
                print(f"Debug result: {result}")
            except Exception as e:
                print(f"Debug error: {str(e)}")

        elif user_input.startswith("/shell"):
            command = user_input[len("/shell") :].strip()
            if not command:
                # 如果没有命令参数，切换到 shell 模式
                memory_manager.set_mode("shell")
                print(get_message("switched_to_shell_mode"))
            else:
                if command.startswith("/chat"):
                    event_file, file_id = gengerate_event_file_path()
                    global_cancel.register_token(event_file)
                    configure(f"event_file:{event_file}")
                    command = command[len("/chat") :].strip()
                    gen_and_exec_shell_command(command)
                else:
                    execute_shell_command(command)
        else:
            # 对于未识别的命令，显示提示信息而不是执行auto_command
            if user_input and user_input.strip():
                if user_input.startswith("/"):                    
                    command = user_input.split(" ")[0][1:]
                    query = user_input[len(command) + 1:].strip()
                    user_input = f"/command {command}.md {query}"                    
                
                # 只有非命令输入才执行auto_command
                event_file, _ = gengerate_event_file_path()
                global_cancel.register_token(event_file)
                configure(f"event_file:{event_file}")
                run_agentic(user_input, cancel_token=event_file)

    except EOFError:
        # 重新抛出这些异常，让主循环处理
        raise
    except (CancelRequestedException, KeyboardInterrupt):
        pass
    except Exception as e:
        print(
            f"\033[91m 1. An error occurred:\033[0m \033[93m{type(e).__name__}\033[0m - {str(e)}"
        )
        if ARGS and ARGS.debug:
            import traceback

            traceback.print_exc()


async def run_app():
    """运行聊天应用"""
    global ask, coding, chat, design, voice_input, auto_command, run_agentic, active_context, execute_shell_command

    # 创建输入队列和忙碌状态
    input_queue = asyncio.Queue()
    busy_event = asyncio.Event()
    busy_event.set()  # 初始状态为空闲

    task_event = TaskEvent()
    task_completion_callbacks = []

    # 触发所有任务完成回调
    async def trigger_task_completion_callbacks():
        """触发所有注册的任务完成回调"""
        for callback in task_completion_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                print(
                    f"\033[91mError in task completion callback:\033[0m {type(e).__name__} - {str(e)}"
                )
                if ARGS and ARGS.debug:
                    import traceback

                    traceback.print_exc()
        task_completion_callbacks.clear()

    # 创建后台消费者协程
    async def consumer_loop():
        """后台处理用户输入的消费者协程"""
        nonlocal session
        while True:
            is_queue_geted = False
            try:
                # 给队列获取操作添加超时，让消费者有机会响应取消请求
                try:
                    user_input, new_prompt_callback, session = await asyncio.wait_for(
                        input_queue.get(), timeout=1.0
                    )
                    is_queue_geted = True
                except asyncio.TimeoutError:
                    # 超时后短暂休眠，然后继续循环等待
                    await asyncio.sleep(0.1)
                    continue

                # 设置任务状态为已开始
                task_event.set_state("started")
                busy_event.clear()  # 标记为忙碌

                # 设置任务状态为运行中
                task_event.set_state("running")

                # 直接调用异步的 process_user_input 函数
                await process_user_input(user_input, new_prompt_callback, session)

                await trigger_task_completion_callbacks()

                # 设置任务状态为已完成
                task_event.set_state("completed")

            except KeyboardInterrupt:
                global_cancel.set_active_tokens()
                task_event.set_state("completed")
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                if ARGS and ARGS.debug:
                    import traceback

                    traceback.print_exc()
                continue
            finally:
                busy_event.set()  # 标记为空闲
                if is_queue_geted:
                    input_queue.task_done()
                # 确保任务状态最终被重置
                if task_event.get_state() != "completed":
                    task_event.set_state("completed")

    # 启动消费者协程
    consumer_task = asyncio.create_task(consumer_loop())

    # 创建键盘绑定
    kb = KeyBindings()

    # 捕获 Ctrl+C 和 Ctrl+D
    @kb.add("c-c")
    def _(event):
        if event.app.layout.is_searching:
            event.app.current_buffer.history_search_text = None
            event.app.current_buffer.reset()
        # else:
        #     event.app.exit(exception=KeyboardInterrupt)

    @kb.add("c-d")
    def _(event):
        event.app.exit(exception=EOFError)

    @kb.add("tab")
    def _(event):
        b = event.current_buffer
        if b.complete_state:
            b.complete_next()
        else:
            b.start_completion(select_first=False)

    @kb.add("c-g")
    def _(event):
        transcription = voice_input()
        if transcription:
            event.app.current_buffer.insert_text(transcription)

    @kb.add("c-k")
    def _(event):
        cycle_mode()
        event.app.invalidate()

    @kb.add("c-n")
    def _(event):
        new_status_bool = toggle_human_as_model()
        new_status = "true" if new_status_bool else "false"
        configure(f"human_as_model:{new_status}", skip_print=True)
        event.app.invalidate()

    # 注册粘贴处理器
    register_paste_handler(kb)

    # 应用插件的键盘绑定
    plugin_manager.apply_keybindings(kb)

    def get_bottom_toolbar():
        mode = get_mode()
        human_as_model = get_human_as_model_string()
        MODES = {
            "normal": "normal",
            "auto_detect": "nature language auto detect",
            "voice_input": "voice input",
            "shell": "shell",
        }
        if mode not in MODES:
            mode = "auto_detect"
        pwd = os.getcwd()
        pwd_parts = pwd.split(os.sep)
        if len(pwd_parts) > 3:
            pwd = os.sep.join(pwd_parts[-3:])

        plugin_info = (
            f"Plugins: {len(plugin_manager.plugins)}" if plugin_manager.plugins else ""
        )

        # 获取正在运行的 async 任务数量
        async_tasks_info = ""
        try:
            from pathlib import Path
            from autocoder.sdk.async_runner.task_metadata import TaskMetadataManager

            async_agent_dir = Path.home() / ".auto-coder" / "async_agent"
            meta_dir = os.path.join(async_agent_dir, "meta")

            if os.path.exists(meta_dir):
                metadata_manager = TaskMetadataManager(meta_dir)
                summary = metadata_manager.get_task_summary()
                running_count = summary.get("running", 0)

                if running_count > 0:
                    async_tasks_info = f" | Async Tasks: 🔄 {running_count}"
        except Exception:
            # 静默处理异常，不影响底部工具栏的显示
            pass

        return f"Current Dir: {pwd} \nMode: {MODES[mode]}(ctrl+k) | Human as Model: {human_as_model}(ctrl+n) | {plugin_info}{async_tasks_info}"

    # 创建增强补全器
    enhanced_completer = EnhancedCompleter(completer, plugin_manager)

    # 定义历史文件路径
    history_file_path = os.path.join(
        os.getcwd(), ".auto-coder", "auto-coder.chat", "history", "command_history.txt"
    )
    os.makedirs(os.path.dirname(history_file_path), exist_ok=True)

    # 创建会话
    session = PromptSession(
        history=FileHistory(history_file_path),
        auto_suggest=AutoSuggestFromHistory(),
        enable_history_search=False,
        completer=enhanced_completer,
        complete_while_typing=False,
        key_bindings=kb,
        bottom_toolbar=get_bottom_toolbar,
        # 注意：bracketed paste 通过 Keys.BracketedPaste 键绑定处理
    )

    # 创建 wrapped functions
    wrapped_functions = {}
    for func_name, original_func in original_functions.items():
        wrapped_functions[func_name] = plugin_manager.wrap_function(
            original_func, func_name
        )

    # 替换原始函数
    ask = wrapped_functions.get("ask", ask)
    coding = wrapped_functions.get("coding", coding)
    chat = wrapped_functions.get("chat", chat)
    design = wrapped_functions.get("design", design)
    voice_input = wrapped_functions.get("voice_input", voice_input)
    auto_command = wrapped_functions.get("auto_command", auto_command)
    run_agentic = wrapped_functions.get("run_agentic", run_agentic)
    active_context = wrapped_functions.get("active_context", active_context)
    execute_shell_command = wrapped_functions.get(
        "execute_shell_command", execute_shell_command
    )

    stop_ev = asyncio.Event()
    new_prompt = ""

    # 用于设置新提示的回调函数
    def set_new_prompt(prompt):
        nonlocal new_prompt
        new_prompt = prompt

    # 样式定义
    style = Style.from_dict(
        {
            "username": "#884444",
            "at": "#00aa00",
            "colon": "#0000aa",
            "pound": "#00aa00",
            "host": "#00ffff bg:#444400",
            "busy": "#ff6600 italic",
        }
    )

    # 显示启动信息
    print(
        f"""
    \033[1;32m  ____ _           _          _         _               ____          _           
    / ___| |__   __ _| |_       / \\  _   _| |_ ___        / ___|___   __| | ___ _ __ 
    | |   | '_ \\ / _` | __|____ / _ \\| | | | __/ _ \\ _____| |   / _ \\ / _` |/ _ \\ '__|
    | |___| | | | (_| | ||_____/ ___ \\ |_| | || (_) |_____| |__| (_) | (_| |  __/ |   
    \\____|_| |_|\\__,_|\\__|   /_/   \\_\\__,_|\\__\\___/       \\____\\___/ \\__,_|\\___|_| 
                                                                        v{__version__}
    \033[0m"""
    )
    print(f"\033[1;34m{get_message('type_help_to_see_commands')}\033[0m\n")

    # 显示插件信息
    if plugin_manager.plugins:
        print(f"\033[1;34m{get_message('loaded_plugins_title')}\033[0m")
        for name, plugin in plugin_manager.plugins.items():
            print(f"  - {plugin.description}")
        print()

    show_help()

    # 启动后台任务（传递 session 对象以便刷新工具栏）
    background_task_coro = asyncio.create_task(background_task(stop_ev, session))

    # 主交互循环
    while True:
        task_state = task_event.get_state()
        try:
            # 根据任务状态控制是否渲染prompt
            if task_state in ["started", "running", "pending"]:
                # 任务运行中，不显示prompt，跳过此次循环
                await asyncio.sleep(0.1)
                continue
            else:
                prompt_message = [
                    ("class:username", "coding"),
                    ("class:at", "@"),
                    ("class:host", "cuscli.chat"),
                    ("class:colon", ":"),
                    ("class:path", "~"),
                    ("class:dollar", "$ "),
                ]

            if new_prompt:
                user_input = await session.prompt_async(
                    FormattedText(prompt_message), default=new_prompt, style=style
                )
                new_prompt = ""
            else:
                user_input = await session.prompt_async(
                    FormattedText(prompt_message), style=style
                )

            if user_input.strip() == "/exit":
                raise EOFError()

            # 将输入放入队列，包含完成回调
            if user_input.strip():
                await input_queue.put((user_input, set_new_prompt, session))
                task_event.set_state("pending")

        except (KeyboardInterrupt, asyncio.CancelledError):
            global_cancel.set_active_tokens()
            continue
        except CancelRequestedException:
            continue
        except EOFError:
            break
        except Exception as e:
            print(
                f"\033[91m 2. An error occurred:\033[0m \033[93m{type(e).__name__}\033[0m - {str(e)}"
            )
            if ARGS and ARGS.debug:
                import traceback

                traceback.print_exc()

    exit_msg = get_i18n_message("exit_ctrl_d")
    print(f"\n\033[93m{exit_msg}\033[0m")

    # 通知后台任务停止
    stop_ev.set()

    # 取消消费者任务
    consumer_task.cancel()
    try:
        await consumer_task
    except asyncio.CancelledError:
        pass

    # 取消后台任务
    background_task_coro.cancel()
    try:
        await background_task_coro
    except asyncio.CancelledError:
        pass

    # 清理资源
    try:
        # 关闭所有插件
        plugin_manager.shutdown_all()
        # 停止 MCP 服务器
        try:
            if get_mcp_server():
                get_mcp_server().stop()
        except Exception as e:
            pass
        # 停止引擎
        stop_engine()
    except Exception as e:
        print(
            f"\033[91m 3. An error occurred while cleaning up:\033[0m \033[93m{type(e).__name__}\033[0m - {str(e)}"
        )

    goodbye_msg = get_i18n_message("goodbye")
    print(f"\n\033[93m{goodbye_msg}\033[0m")


def main():
    global ARGS
    load_tokenizer()
    ARGS = parse_arguments()

    if ARGS.lite:
        ARGS.product_mode = "lite"

    if ARGS.pro:
        ARGS.product_mode = "pro"

    if not ARGS.quick:
        initialize_system(
            InitializeSystemRequest(
                product_mode=ARGS.product_mode,
                skip_provider_selection=ARGS.skip_provider_selection,
                debug=ARGS.debug,
                quick=ARGS.quick,
                lite=ARGS.lite,
                pro=ARGS.pro,
            )
        )

    start_engine()

    # 初始化插件系统
    plugin_manager.load_global_plugin_dirs()
    plugin_manager.add_global_plugin_directory(
        os.path.join(os.path.dirname(__file__), "plugins")
    )

    # 加载保存的运行时配置
    plugin_manager.load_runtime_cfg()

    # 自动加载内置插件
    load_builtin_plugins()

    configure(f"product_mode:{ARGS.product_mode}")

    # 运行应用
    asyncio.run(run_app())


if __name__ == "__main__":
    main()
