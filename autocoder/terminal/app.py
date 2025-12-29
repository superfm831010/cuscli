"""终端应用核心类"""

import asyncio
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style
from autocoder.version import __version__
from autocoder.chat_auto_coder_lang import get_message
from autocoder.common.international import get_message as get_i18n_message
from autocoder.common.global_cancel import (
    global_cancel,
    CancelRequestedException,
)
from autocoder.events.event_manager_singleton import gengerate_event_file_path
from autocoder.terminal.tasks.task_event import TaskEvent, CancellationRegistry
from autocoder.terminal.tasks.background import background_task
from autocoder.terminal.ui.completer import EnhancedCompleter
from autocoder.terminal.ui.keybindings import setup_keybindings
from autocoder.terminal.ui.toolbar import get_bottom_toolbar_func
from autocoder.terminal.ui.session import create_session
from autocoder.terminal.command_registry import CommandRegistry
from autocoder.terminal.command_processor import CommandProcessor
from autocoder.terminal.utils.errors import print_error


def print_warning_box(message: str, width: int = 78, color: str = "\033[1;33m"):
    """
    打印带有完整边框的警告消息框(支持终端兼容性)

    Args:
        message: 要显示的消息文本
        width: 边框宽度（默认78，为80字符终端留出边距）
        color: ANSI颜色代码（默认黄色加粗）
    """
    from autocoder.common.terminal_compat import get_terminal_capability

    term = get_terminal_capability()

    # 根据终端能力选择边框字符
    if term.supports_unicode():
        # Unicode框线字符
        top_left, top_right = "╔", "╗"
        bottom_left, bottom_right = "╚", "╝"
        horizontal, vertical = "═", "║"
    else:
        # 纯ASCII字符
        top_left, top_right = "+", "+"
        bottom_left, bottom_right = "+", "+"
        horizontal, vertical = "=", "|"

    reset = "\033[0m" if term.ansi_support else ""
    text_color = "\033[1;31m" if term.ansi_support else ""  # 红色加粗用于文字
    box_color = color if term.ansi_support else ""

    # 计算内容宽度（边框占用4个字符：左边"║ "和右边" ║"）
    content_width = width - 4

    def get_char_width(char):
        """获取单个字符的显示宽度（考虑东亚宽字符）"""
        code = ord(char)
        # 东亚宽字符（中文、日文、韩文等）占2个宽度
        if (0x1100 <= code <= 0x115F or  # Hangul Jamo
            0x2E80 <= code <= 0x9FFF or  # CJK & CJK Ext A
            0xAC00 <= code <= 0xD7A3 or  # Hangul Syllables
            0xF900 <= code <= 0xFAFF or  # CJK Compatibility Ideographs
            0xFE30 <= code <= 0xFE4F or  # CJK Compatibility Forms
            0xFF00 <= code <= 0xFF60 or  # Fullwidth Forms
            0xFFE0 <= code <= 0xFFE6 or  # Fullwidth Forms
            0x20000 <= code <= 0x2FFFD or  # CJK Ext B, C, D, E
            0x30000 <= code <= 0x3FFFD):   # CJK Ext F
            return 2
        # Zero-width characters (组合字符、变音符号等)
        elif (0x0300 <= code <= 0x036F or  # Combining Diacritical Marks
              0xFE00 <= code <= 0xFE0F or  # Variation Selectors
              0xFE20 <= code <= 0xFE2F):   # Combining Half Marks
            return 0
        # 普通ASCII字符占1个宽度
        else:
            return 1

    def get_display_width(text):
        """计算文本的实际显示宽度"""
        return sum(get_char_width(char) for char in text)

    def wrap_text_by_display_width(text, max_width):
        """按显示宽度换行文本，确保不超出边框"""
        lines = []
        current_line = ""
        current_width = 0

        for char in text:
            char_width = get_char_width(char)

            # 如果加上这个字符会超出宽度，开始新行
            if current_width + char_width > max_width and current_line:
                lines.append(current_line)
                current_line = char
                current_width = char_width
            else:
                current_line += char
                current_width += char_width

        # 添加最后一行
        if current_line:
            lines.append(current_line)

        return lines

    # 使用自定义换行（按显示宽度）
    lines = []
    for line in message.split('\n'):
        if line.strip():
            wrapped = wrap_text_by_display_width(line, content_width)
            lines.extend(wrapped)

    # 打印顶部边框
    print(f"{box_color}{top_left}{horizontal * (width - 2)}{top_right}{reset}")

    # 打印每行内容（带左右边框）
    for line in lines:
        # 计算实际显示宽度
        line_display_width = get_display_width(line)
        # 计算需要填充的空格数
        padding_needed = content_width - line_display_width
        padded_line = line + ' ' * padding_needed
        print(f"{box_color}{vertical}{reset} {text_color}{padded_line}{reset} {box_color}{vertical}{reset}")

    # 打印底部边框
    print(f"{box_color}{bottom_left}{horizontal * (width - 2)}{bottom_right}{reset}")


class TerminalApp:
    """终端应用主类"""

    def __init__(
        self,
        plugin_manager,
        wrapped_functions,
        configure_func,
        show_help_func,
        base_completer,
        get_mode_func,
        get_human_as_model_string_func,
        get_agentic_mode_string_func,
        cycle_mode_func,
        toggle_human_as_model_func,
        toggle_agentic_mode_func,
        voice_input_func,
        get_mcp_server_func,
        stop_engine_func,
        debug=False,
    ):
        self.plugin_manager = plugin_manager
        self.wrapped_functions = wrapped_functions
        self.configure = configure_func
        self.show_help = show_help_func
        self.base_completer = base_completer
        self.get_mode = get_mode_func
        self.get_human_as_model_string = get_human_as_model_string_func
        self.get_agentic_mode_string = get_agentic_mode_string_func
        self.cycle_mode = cycle_mode_func
        self.toggle_human_as_model = toggle_human_as_model_func
        self.toggle_agentic_mode = toggle_agentic_mode_func
        self.voice_input = voice_input_func
        self.get_mcp_server = get_mcp_server_func
        self.stop_engine = stop_engine_func
        self.debug = debug

        # 初始化组件
        self.task_event = TaskEvent()
        self.registry = CancellationRegistry()
        self.input_queue = asyncio.Queue()
        self.busy_event = asyncio.Event()
        self.busy_event.set()  # 初始状态为空闲

        # 创建命令处理器
        self.command_processor = CommandProcessor(
            plugin_manager=plugin_manager,
            wrapped_functions=wrapped_functions,
            configure_func=configure_func,
            global_cancel=global_cancel,
            show_help_func=show_help_func,
            debug=debug,
        )

        # 创建命令注册表
        self.command_registry = CommandRegistry()
        self._register_commands()

        # UI 组件（稍后初始化）
        self.session = None
        self.consumer_task = None
        self.background_task_coro = None
        self.stop_ev = asyncio.Event()

    def _register_commands(self):
        """注册所有命令"""
        # 注意：按前缀长度排序，优先匹配更长的前缀
        self.command_registry.register(
            "/conf/export", self.command_processor.handle_conf_export
        )
        self.command_registry.register(
            "/index/query", self.command_processor.handle_index_query
        )
        self.command_registry.register(
            "/index/build", self.command_processor.handle_index_build
        )
        self.command_registry.register(
            "/index/export", self.command_processor.handle_index_export
        )
        self.command_registry.register(
            "/index/import", self.command_processor.handle_index_import
        )

        self.command_registry.register(
            "/voice_input", self.command_processor.handle_voice_input_command
        )
        self.command_registry.register("/clear", self.command_processor.handle_clear)
        self.command_registry.register("/cls", self.command_processor.handle_clear)
        self.command_registry.register(
            "/add_files", self.command_processor.handle_add_files
        )
        self.command_registry.register(
            "/remove_files", self.command_processor.handle_remove_files
        )
        self.command_registry.register(
            "/list_files", self.command_processor.handle_list_files
        )
        self.command_registry.register("/models", self.command_processor.handle_models)
        self.command_registry.register("/mode", self.command_processor.handle_mode)
        self.command_registry.register(
            "/plugins", self.command_processor.handle_plugins
        )
        self.command_registry.register("/conf", self.command_processor.handle_conf)
        self.command_registry.register("/revert", self.command_processor.handle_revert)
        self.command_registry.register("/commit", self.command_processor.handle_commit)
        self.command_registry.register("/help", self.command_processor.handle_help)
        self.command_registry.register(
            "/exclude_dirs", self.command_processor.handle_exclude_dirs
        )
        self.command_registry.register(
            "/exclude_files", self.command_processor.handle_exclude_files
        )
        self.command_registry.register("/exit", self.command_processor.handle_exit)
        self.command_registry.register("/coding", self.command_processor.handle_coding)
        self.command_registry.register("/chat", self.command_processor.handle_chat)
        self.command_registry.register("/design", self.command_processor.handle_design)
        self.command_registry.register("/summon", self.command_processor.handle_summon)
        self.command_registry.register("/lib", self.command_processor.handle_lib)
        self.command_registry.register("/rules", self.command_processor.handle_rules)
        self.command_registry.register("/mcp", self.command_processor.handle_mcp)
        self.command_registry.register(
            "/active_context", self.command_processor.handle_active_context
        )
        self.command_registry.register("/auto", self.command_processor.handle_auto)
        self.command_registry.register("/debug", self.command_processor.handle_debug)
        self.command_registry.register(
            "/shell", self.command_processor.handle_shell_command
        )
        self.command_registry.register(
            "/workflow", self.command_processor.handle_workflow
        )
        self.command_registry.register("/remote", self.command_processor.handle_remote)

        # 兜底处理器
        self.command_registry.set_fallback(
            self.command_processor.handle_unknown_or_fallback
        )

    async def process_user_input(
        self, user_input: str, new_prompt_callback, session=None
    ):
        """处理用户输入的异步函数"""
        try:
            # 预处理输入
            user_input = self.command_processor.preprocess_input(user_input)

            # 1. 如果用户输入 /shell（无参数），启动一个子 shell
            if user_input == "/shell":
                await self.command_processor.handle_shell_enter(
                    user_input, {"session": session}
                )
                return

            # 2. 如果以 ! 开头，当作单行 shell 命令执行
            if user_input.startswith("!"):
                await self.command_processor.handle_shell_single(
                    user_input, {"session": session}
                )
                return

            # 3. 如果以 $ 开头，当作 workflow 快捷命令执行
            if user_input.startswith("$"):
                await self.command_processor.handle_workflow_shortcut(
                    user_input, {"session": session}
                )
                return

            # 4. 尝试插件处理
            context = {"session": session, "new_prompt_callback": new_prompt_callback}
            if self.command_processor.handle_plugin_command(user_input, context):
                return

            # 5. Shell 模式处理
            if await self.command_processor.handle_shell_mode(user_input, context):
                return

            # 6. 自动检测模式
            if self.command_processor.handle_auto_detect_mode(user_input, context):
                return

            # 7. 语音输入模式
            if self.command_processor.handle_voice_input_mode(user_input, context):
                return

            # 8. 使用命令注册表分发命令
            await self.command_registry.dispatch(user_input, context)

        except EOFError:
            # 重新抛出这些异常，让主循环处理
            raise
        except asyncio.CancelledError:
            # 原生取消，向上抛出让上层统一处理
            raise
        except (CancelRequestedException, KeyboardInterrupt):
            pass
        except Exception as e:
            print_error("1", e, self.debug)

    async def consumer_loop(self):
        """后台处理用户输入的消费者协程"""
        while True:
            is_queue_geted = False
            event_file = None
            try:
                # 给队列获取操作添加超时，让消费者有机会响应取消请求
                try:
                    user_input, new_prompt_callback, session = await asyncio.wait_for(
                        self.input_queue.get(), timeout=1.0
                    )
                    is_queue_geted = True
                except asyncio.TimeoutError:
                    # 超时后短暂休眠，然后继续循环等待
                    await asyncio.sleep(0.1)
                    continue

                # 设置任务状态为已开始
                self.task_event.set_state("started")
                self.busy_event.clear()  # 标记为忙碌

                # 设置任务状态为运行中
                self.task_event.set_state("running")

                # 为每个请求创建 Task 并注册
                event_file, _ = gengerate_event_file_path()
                global_cancel.register_token(event_file)

                task = asyncio.create_task(
                    self.process_user_input(user_input, new_prompt_callback, session)
                )
                self.registry.register(event_file, task)

                try:
                    await task
                except asyncio.CancelledError:
                    # Task 被取消，向上传播
                    raise
                except CancelRequestedException:
                    # 兼容旧的取消机制
                    pass
                finally:
                    self.registry.unregister(event_file)
                    global_cancel.reset_token(event_file)

                # 触发任务完成回调（虽然当前为空，但保持与原代码一致）
                # await trigger_task_completion_callbacks()

                # 设置任务状态为已完成
                self.task_event.set_state("completed")

            except KeyboardInterrupt:
                # 消费者收到 KeyboardInterrupt（不太可能直接收到，但保持兼容）
                # 设置取消标志并清理状态
                global_cancel.set_active_tokens()
                self.task_event.set_state("completed")
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.debug:
                    import traceback

                    traceback.print_exc()
                continue
            finally:
                self.busy_event.set()  # 标记为空闲
                if is_queue_geted:
                    self.input_queue.task_done()
                # 确保任务状态最终被重置
                if self.task_event.get_state() != "completed":
                    self.task_event.set_state("completed")

    async def run(self):
        """运行终端应用"""
        # 创建 UI 组件
        kb = setup_keybindings(
            self.plugin_manager,
            self.voice_input,
            self.cycle_mode,
            self.toggle_human_as_model,
            self.toggle_agentic_mode,
            self.configure,
        )

        toolbar_func = get_bottom_toolbar_func(
            self.get_mode,
            self.get_human_as_model_string,
            self.get_agentic_mode_string,
            self.plugin_manager,
        )

        enhanced_completer = EnhancedCompleter(self.base_completer, self.plugin_manager)

        self.session = create_session(enhanced_completer, kb, toolbar_func)

        # 启动消费者协程
        self.consumer_task = asyncio.create_task(self.consumer_loop())

        # 启动后台任务
        self.background_task_coro = asyncio.create_task(
            background_task(self.stop_ev, self.session, self.debug)
        )

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
            f"""\033[1;32m  ██████╗██╗   ██╗███████╗          ██████╗██╗     ██╗
 ██╔════╝██║   ██║██╔════╝         ██╔════╝██║     ██║
 ██║     ██║   ██║███████╗ ██████  ██║     ██║     ██║
 ██║     ██║   ██║╚════██║         ██║     ██║     ██║
 ╚██████╗╚██████╔╝███████║         ╚██████╗███████╗██║
  ╚═════╝ ╚═════╝ ╚══════╝          ╚═════╝╚══════╝╚═╝
                                             {__version__}
                            Produced by 黄埔海关科技处\033[0m"""
        )
        print(f"\033[1;34m{get_message('type_help_to_see_commands')}\033[0m\n")

        # 显示插件信息
        if self.plugin_manager.plugins:
            print(f"\033[1;34m{get_message('loaded_plugins_title')}\033[0m")
            for name, plugin in self.plugin_manager.plugins.items():
                print(f"  - {plugin.description}")
            print()

        # 显示模型能力要求警告（醒目格式）
        print()
        print_warning_box(
            "⚠️  重要提示：自动编程和智能代理（Agentic Agent）功能对 AI 模型能力要求极高，"
            "请务必配置 DeepSeek V3.1（128K 上下文窗口）或后续能力更强的模型，"
            "低于此标准的模型将导致功能异常，无法正常工作！",
            width=78,
            color="\033[1;33m"
        )
        print()

        self.show_help()

        # 用于设置新提示的回调函数
        new_prompt = ""

        def set_new_prompt(prompt):
            nonlocal new_prompt
            new_prompt = prompt

        # 主交互循环
        while True:
            task_state = self.task_event.get_state()
            try:
                # 根据任务状态控制是否渲染prompt
                if task_state in ["started", "running", "pending"]:
                    # 任务运行中，不显示prompt，跳过此次循环
                    # 使用 sleep 让循环有机会响应 Ctrl+C
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
                    user_input = await self.session.prompt_async(
                        FormattedText(prompt_message), default=new_prompt, style=style
                    )
                    new_prompt = ""
                else:
                    user_input = await self.session.prompt_async(
                        FormattedText(prompt_message), style=style
                    )

                if user_input.strip() == "/exit":
                    raise EOFError()

                # 将输入放入队列
                if user_input.strip():
                    await self.input_queue.put(
                        (user_input, set_new_prompt, self.session)
                    )
                    self.task_event.set_state("pending")

            except (KeyboardInterrupt, asyncio.CancelledError):
                # 按 Ctrl+C 取消当前任务
                global_cancel.set_active_tokens()
                continue
            except CancelRequestedException:
                continue
            except EOFError:
                break
            except Exception as e:
                print_error("2", e, self.debug)

        # 清理
        await self.shutdown()

    async def shutdown(self):
        """关闭应用并清理资源"""
        exit_msg = get_i18n_message("exit_ctrl_d")
        print(f"\n\033[93m{exit_msg}\033[0m")

        # 通知后台任务停止
        self.stop_ev.set()

        # 取消消费者任务
        if self.consumer_task:
            self.consumer_task.cancel()
            try:
                await self.consumer_task
            except asyncio.CancelledError:
                pass

        # 取消后台任务
        if self.background_task_coro:
            self.background_task_coro.cancel()
            try:
                await self.background_task_coro
            except asyncio.CancelledError:
                pass

        # 清理资源
        try:
            # 关闭所有插件
            self.plugin_manager.shutdown_all()
            # 停止 MCP 服务器
            try:
                if self.get_mcp_server():
                    self.get_mcp_server().stop()
            except Exception:
                pass
            # 停止引擎
            self.stop_engine()
        except Exception as e:
            print_error("3 (cleanup)", e, self.debug)

        goodbye_msg = get_i18n_message("goodbye")
        print(f"\n\033[93m{goodbye_msg}\033[0m")
