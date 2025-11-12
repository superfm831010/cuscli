"""键盘绑定设置"""

from prompt_toolkit.key_binding import KeyBindings
from autocoder.common.terminal_paste import register_paste_handler


def setup_keybindings(
    plugin_manager,
    voice_input_func,
    cycle_mode_func,
    toggle_human_as_model_func,
    toggle_agentic_mode_func,
    configure_func,
):
    """设置所有键盘绑定

    Args:
        plugin_manager: 插件管理器
        voice_input_func: 语音输入函数
        cycle_mode_func: 模式切换函数
        toggle_human_as_model_func: 切换 human_as_model 函数
        toggle_agentic_mode_func: 切换 agentic_mode 函数
        configure_func: 配置函数

    Returns:
        KeyBindings: 配置好的键盘绑定对象
    """
    kb = KeyBindings()

    # 捕获 Ctrl+C 和 Ctrl+D
    @kb.add("c-c")
    def _(event):
        # 如果正在搜索，只重置搜索状态
        if event.app.layout.is_searching:
            event.app.current_buffer.history_search_text = None
            event.app.current_buffer.reset()
        

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
        transcription = voice_input_func()
        if transcription:
            event.app.current_buffer.insert_text(transcription)

    @kb.add("c-k")
    def _(event):
        cycle_mode_func()
        event.app.invalidate()

    @kb.add("c-n")
    def _(event):
        new_status_bool = toggle_human_as_model_func()
        new_status = "true" if new_status_bool else "false"
        configure_func(f"human_as_model:{new_status}", skip_print=True)
        event.app.invalidate()
    
    # 注册粘贴处理器
    register_paste_handler(kb)

    # 应用插件的键盘绑定
    plugin_manager.apply_keybindings(kb)

    return kb
