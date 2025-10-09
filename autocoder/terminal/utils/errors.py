"""错误处理工具函数"""

import traceback


def print_error(tag: str, exc: Exception, debug: bool = False):
    """统一的错误打印函数

    Args:
        tag: 错误标签（如 "1", "2", "3"）
        exc: 异常对象
        debug: 是否打印详细堆栈
    """
    print(
        f"\033[91m {tag}. An error occurred:\033[0m \033[93m{type(exc).__name__}\033[0m - {str(exc)}"
    )
    if debug:
        traceback.print_exc()
