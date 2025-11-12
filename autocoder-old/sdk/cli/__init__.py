"""
Auto-Coder CLI 模块

提供命令行接口，允许用户通过终端使用 Auto-Coder 的核心功能。
"""

def main():
    """CLI主入口点函数"""
    from .main import AutoCoderCLI
    return AutoCoderCLI.main()

__all__ = ["main"]
