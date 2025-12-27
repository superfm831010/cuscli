"""
异步兼容的 prompt 工具模块 - 完全向后兼容版本

自动检测运行环境，在 asyncio 中使用线程池执行同步调用。

使用方式：
    # 原来的
    from prompt_toolkit import prompt
    from prompt_toolkit import PromptSession

    # 改为
    from autocoder.common.async_prompt import prompt, PromptSession

这样所有现有代码无需修改逻辑，只需替换 import 即可。
"""

import asyncio
from typing import Any
from concurrent.futures import ThreadPoolExecutor
from prompt_toolkit import PromptSession as _PromptSession
from prompt_toolkit import prompt as _prompt

# 全局线程池，用于在 async 环境中执行同步 prompt
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="prompt_thread")


def _is_in_async_context() -> bool:
    """检测当前是否在 asyncio 事件循环中"""
    try:
        loop = asyncio.get_running_loop()
        return loop is not None
    except RuntimeError:
        return False


def prompt(message: Any = "", **kwargs) -> str:
    """
    兼容 prompt_toolkit.prompt 的函数

    如果在 asyncio 事件循环中调用，会在线程池中执行以避免阻塞事件循环。
    如果不在事件循环中，直接调用原始的 prompt。
    """
    if _is_in_async_context():
        # 在线程池中执行同步 prompt
        future = _executor.submit(_prompt, message, **kwargs)
        return future.result()
    return _prompt(message, **kwargs)


class PromptSession:
    """
    兼容 prompt_toolkit.PromptSession 的包装类

    自动处理 asyncio 环境，在需要时使用线程池执行同步调用。
    """

    def __init__(self, *args, **kwargs):
        self._session = _PromptSession(*args, **kwargs)
        self._args = args
        self._kwargs = kwargs

    def prompt(self, message: Any = None, **kwargs) -> str:
        """
        同步 prompt 方法 - 自动处理 asyncio 环境

        如果在 asyncio 事件循环中调用，会在线程池中创建新的 session 并执行。
        """
        if _is_in_async_context():
            # 在线程池中创建新的 session 并执行
            # 因为 prompt_toolkit session 不能跨线程使用
            def _run_in_thread():
                thread_session = _PromptSession(*self._args, **self._kwargs)
                if message is not None:
                    return thread_session.prompt(message, **kwargs)
                return thread_session.prompt(**kwargs)

            future = _executor.submit(_run_in_thread)
            return future.result()

        if message is not None:
            return self._session.prompt(message, **kwargs)
        return self._session.prompt(**kwargs)

    async def prompt_async(self, message: Any = None, **kwargs) -> str:
        """
        异步 prompt 方法

        直接使用 prompt_toolkit 原生的 prompt_async。
        """
        if message is not None:
            return await self._session.prompt_async(message, **kwargs)
        return await self._session.prompt_async(**kwargs)

    def __getattr__(self, name):
        """代理其他属性到原始 session"""
        return getattr(self._session, name)
