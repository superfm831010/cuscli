"""主应用类"""

import asyncio
from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

from .models import ConversationBuffer
from .handlers import CommandHandler
from .ui import get_styles, create_layout, create_key_bindings
from autocoder.plugins import PluginManager


class AutoCoderChatApp:
    """Auto-Coder 聊天式 TUI 应用程序"""

    def __init__(self,plugin_manager: PluginManager):
        # 初始化状态
        self.conversation_buffer = ConversationBuffer()
        self.is_processing = False
        self.current_task = ""
        self.show_shortcuts = False
        self.animation_counter = 0
        self.plugin_manager = plugin_manager

        # 创建命令处理器
        self.command_handler = CommandHandler(self.conversation_buffer, self)

        # 创建输入缓冲区
        self.input_buffer = Buffer(
            history=InMemoryHistory(),
            auto_suggest=AutoSuggestFromHistory(),
            enable_history_search=True,
            multiline=False,
            accept_handler=self._handle_input_sync,
        )

        # 创建布局
        self.layout = create_layout(
            conversation_buffer=self.conversation_buffer,
            input_buffer=self.input_buffer,
            get_prompt_text=self._get_prompt_text,
            get_right_hint=self._get_right_hint,
            get_tips_text=self._get_tips_text,
            get_shortcuts_help_text=self._get_shortcuts_help_text,
            show_shortcuts_condition=lambda: self.show_shortcuts,
            input_has_text_condition=lambda: bool(self.input_buffer.text.strip()),
        )

        # 创建键绑定
        self.key_bindings = create_key_bindings(self, self.input_buffer, self.plugin_manager)

        # 创建样式
        self.style = get_styles()

        # 创建应用程序
        self.app = Application(
            layout=self.layout,
            key_bindings=self.key_bindings,
            style=self.style,
            full_screen=True,
            mouse_support=False,
            color_depth=None,
            refresh_interval=0.5,
        )

    def _get_tips_text(self):
        """获取提示文本"""
        return [
            ("class:tips", "Tips for getting started:\n\n"),
            (
                "class:tips",
                "1. Type your questions or tasks directly - Auto-Coder will help!\n",
            ),
            ("class:tips", "2. Use /auto <query> for explicit auto command\n"),
            ("class:tips", "3. Use /exit or Ctrl+D to exit the application\n"),
            ("class:tips", "4. Be as specific as possible for the best results\n"),
        ]

    def _get_prompt_text(self):
        """获取提示符文本"""
        if self.is_processing:
            # 转圈圈动画字符
            spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
            spinner_index = (self.animation_counter // 3) % len(spinner_chars)
            return f"{spinner_chars[spinner_index]} "
        else:
            return "> "

    def _get_right_hint(self):
        """获取右侧提示信息"""
        if self.show_shortcuts:
            return "Press ? again to hide shortcuts"
        else:
            return "? for shortcuts"

    def _get_shortcuts_help_text(self):
        """底部快捷键帮助文本"""
        return [
            (
                "class:shortcuts-help",
                "┌─────────────────────── Keyboard Shortcuts ───────────────────────┐\n",
            ),
            (
                "class:shortcuts-help",
                "│  ?       Toggle this help           Enter    Submit command      │\n",
            ),
            (
                "class:shortcuts-help",
                "│  Ctrl+C  Cancel current task        ↑/↓      Navigate history   │\n",
            ),
            (
                "class:shortcuts-help",
                "│  Ctrl+D  Exit application           Ctrl+L   Clear conversation │\n",
            ),
            (
                "class:shortcuts-help",
                "└──────────────────────────────────────────────────────────────────┘",
            ),
        ]

    def invalidate(self):
        """刷新界面 - 转发到内部的 prompt_toolkit Application"""
        self.app.invalidate()

    def exit(self):
        """退出应用 - 转发到内部的 prompt_toolkit Application"""
        self.app.exit()

    def _handle_input_sync(self, buffer: Buffer) -> bool:
        """处理用户输入（同步版本）"""
        command = buffer.text.strip()
        buffer.reset()

        if not command:
            return True

        # 一旦用户输入了内容，隐藏底部帮助
        if self.show_shortcuts:
            self.show_shortcuts = False

        # 添加用户消息到对话
        self.conversation_buffer.add_user_message(command)
        self.app.invalidate()

        # 创建后台任务
        self.app.create_background_task(self._execute_command(command))

        return True

    async def _execute_command(self, command: str):
        """执行用户命令"""
        self.is_processing = True
        self.current_task = command[:30] + "..." if len(command) > 30 else command

        # 开始处理时刷新界面显示转圈圈动画
        self.app.invalidate()
        await asyncio.sleep(0.05)

        try:
            await self.command_handler.handle_command(command)
        except Exception as e:
            self.conversation_buffer.add_system_message(f"Error: {str(e)}")
        finally:
            self.is_processing = False
            self.current_task = ""
            self.animation_counter = 0
            self.app.invalidate()

    async def _animation_loop(self):
        """动画循环，定期更新界面以显示转圈圈效果"""
        while True:
            try:
                if self.is_processing:
                    self.animation_counter += 1
                    self.app.invalidate()
                    await asyncio.sleep(0.2)
                else:
                    await asyncio.sleep(1.0)
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(1.0)

    async def run(self):
        """运行 TUI 应用"""
        try:
            # 创建动画更新任务
            animation_task = asyncio.create_task(self._animation_loop())

            # 运行应用
            await self.app.run_async()
        finally:
            # 确保清理资源
            if "animation_task" in locals():
                animation_task.cancel()
                try:
                    await animation_task
                except asyncio.CancelledError:
                    pass
