"""
Auto Coder RAG - RAG 系统的终端入口

这是重构后的 RAG 终端交互入口，代码结构更清晰，职责更分明。
具体实现逻辑已拆分到 autocoder.rag.terminal 模块中。
"""

import logging

logging.getLogger("ppocr").setLevel(logging.WARNING)

from autocoder.rag.terminal.bootstrap import run_cli


def main(input_args=None):
    """主入口函数"""
    run_cli(input_args)


if __name__ == "__main__":
    main()
