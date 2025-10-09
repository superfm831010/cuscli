"""会话管理"""

from pathlib import Path
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory


def create_session(completer, key_bindings, bottom_toolbar_func):
    """创建 PromptSession

    Args:
        completer: 补全器
        key_bindings: 键盘绑定
        bottom_toolbar_func: 底部工具栏函数

    Returns:
        PromptSession: 配置好的会话对象
    """
    # 定义历史文件路径，使用 pathlib
    history_file_path = (
        Path.cwd()
        / ".auto-coder"
        / "auto-coder.chat"
        / "history"
        / "command_history.txt"
    )
    history_file_path.parent.mkdir(parents=True, exist_ok=True)

    # 创建会话
    session = PromptSession(
        history=FileHistory(str(history_file_path)),
        auto_suggest=AutoSuggestFromHistory(),
        enable_history_search=False,
        completer=completer,
        complete_while_typing=False,
        key_bindings=key_bindings,
        bottom_toolbar=bottom_toolbar_func,
    )

    return session
