"""路径相关工具函数，使用 pathlib 确保跨平台兼容"""

from pathlib import Path


def get_history_path(cwd: Path = None) -> Path:
    """获取命令历史文件路径"""
    if cwd is None:
        cwd = Path.cwd()
    history_path = (
        cwd / ".auto-coder" / "auto-coder.chat" / "history" / "command_history.txt"
    )
    history_path.parent.mkdir(parents=True, exist_ok=True)
    return history_path


def get_async_agent_meta_dir() -> Path:
    """获取异步代理元数据目录"""
    return Path.home() / ".auto-coder" / "async_agent" / "meta"
