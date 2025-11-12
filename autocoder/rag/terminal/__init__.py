"""
RAG Terminal - RAG 系统的终端交互入口模块

这个模块提供了 RAG 系统的终端交互功能，代码结构清晰，职责分明。
"""

# 延迟导入以避免循环依赖
__all__ = ["run_cli"]


def __getattr__(name):
    """延迟导入以避免循环依赖"""
    if name == "run_cli":
        from autocoder.rag.terminal.bootstrap import run_cli

        return run_cli
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
