"""
Auto Coder Terminal - 新的终端入口

这是重构后的终端交互入口，代码结构更清晰，职责更分明。
原有的 chat_auto_coder.py 保持不变以保证向后兼容。
"""

from loguru import logger

logger.remove()  # 把默认 sink 去掉，彻底静音

from autocoder.run_context import get_run_context, RunMode

# 设置运行模式为终端模式
get_run_context().set_mode(RunMode.TERMINAL)

from autocoder.terminal.bootstrap import run_cli


def main():
    """主入口函数"""
    run_cli()


if __name__ == "__main__":
    main()
