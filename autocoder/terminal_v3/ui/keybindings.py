from typing import TYPE_CHECKING
from pluggy import PluginManager
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters import has_focus
from autocoder.common.global_cancel import global_cancel
from prompt_toolkit.buffer import Buffer
from autocoder.common.terminal_paste import register_paste_handler
if TYPE_CHECKING:
    from ..app import AutoCoderChatApp


def create_key_bindings(app_instance: "AutoCoderChatApp", input_buffer: Buffer, plugin_manager: PluginManager):
    """创建键盘绑定"""
    kb = KeyBindings()

    @kb.add("c-c")
    def _(event):
        """Ctrl+C - 取消当前任务"""        
        if app_instance.is_processing:
            global_cancel.set_active_tokens()
            app_instance.is_processing = False
            app_instance.current_task = ""
            app_instance.animation_counter = 0
            app_instance.conversation_buffer.add_system_message("The user tried to cancel the task")
            app_instance.app.invalidate()

    @kb.add("c-d")
    def _(event):
        """Ctrl+D - 退出应用"""
        event.app.exit()

    @kb.add("c-l")
    def _(event):
        """Ctrl+L - 清空对话"""
        app_instance.conversation_buffer.clear_conversation()
        app_instance.app.invalidate()

    @kb.add("?")
    def _(event):
        """? - 显示/隐藏快捷键帮助"""
        if not input_buffer.text:
            app_instance.show_shortcuts = not app_instance.show_shortcuts
            app_instance.app.invalidate()

    @kb.add("enter", filter=has_focus(input_buffer))
    def _(event):
        """Enter - 提交输入"""
        event.current_buffer.validate_and_handle()
    
    # 注册粘贴处理器
    register_paste_handler(kb)

    # 应用插件的键盘绑定
    plugin_manager.apply_keybindings(kb)

    return kb
