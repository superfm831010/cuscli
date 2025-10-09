"""任务事件和取消注册表"""

import asyncio
from typing import Dict


class TaskEvent:
    """任务事件状态管理器"""

    def __init__(self):
        self.state = "idle"  # idle, pending, started, running, completed
        self._event = asyncio.Event()
        self._event.set()  # 初始状态为可用

    def set_state(self, state: str):
        """设置任务状态"""
        self.state = state
        if state == "completed":
            self._event.set()
        else:
            self._event.clear()

    def get_state(self) -> str:
        """获取当前状态"""
        return self.state

    def is_completed(self) -> bool:
        """检查是否完成"""
        return self.state == "completed"

    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self.state in ["started", "running"]

    async def wait(self):
        """等待任务完成"""
        await self._event.wait()

    def clear(self):
        """清除完成状态，重置为pending"""
        self.set_state("idle")


class CancellationRegistry:
    """任务取消注册表，用于集中管理和取消活跃的异步任务"""

    def __init__(self) -> None:
        self._tasks: Dict[str, asyncio.Task] = {}

    def register(self, token: str, task: asyncio.Task) -> None:
        """注册一个任务"""
        self._tasks[token] = task

    def unregister(self, token: str) -> None:
        """注销一个任务"""
        self._tasks.pop(token, None)

    async def cancel_all(self) -> None:
        """取消所有活跃任务"""
        for t in list(self._tasks.values()):
            if not t.done():
                t.cancel()
        # 等待所有任务完成（吞掉 CancelledError）
        for token, t in list(self._tasks.items()):
            try:
                await t
            except asyncio.CancelledError:
                pass
            finally:
                self._tasks.pop(token, None)
