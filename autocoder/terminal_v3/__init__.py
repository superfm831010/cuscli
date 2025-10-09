"""
Terminal V3 - 重构的终端交互模块

这个模块提供了类似 Claude Code 的 TUI 界面，
同时支持所有 auto-coder 的功能命令。
"""

from .app import AutoCoderChatApp

__all__ = ["AutoCoderChatApp"]
