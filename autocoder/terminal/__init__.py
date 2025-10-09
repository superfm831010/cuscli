"""
Auto Coder Terminal - 终端交互模块

这个模块提供了 auto-coder 的终端交互界面，包括：
- 命令处理和路由
- UI 组件（补全、键盘绑定、工具栏）
- 任务管理（异步任务、后台任务）
- 插件集成
"""

from .app import TerminalApp
from .bootstrap import run_cli

__all__ = ["TerminalApp", "run_cli"]
