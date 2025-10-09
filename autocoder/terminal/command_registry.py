"""命令注册和路由"""

from typing import Dict, Callable, Optional, Tuple, Any


class CommandRegistry:
    """命令注册器，管理所有命令的路由"""

    def __init__(self):
        self.commands: Dict[str, Callable] = {}
        self.fallback_handler: Optional[Callable] = None

    def register(self, prefix: str, handler: Callable):
        """注册一个命令处理器

        Args:
            prefix: 命令前缀（如 "/coding", "/chat"）
            handler: 处理函数
        """
        self.commands[prefix] = handler

    def set_fallback(self, handler: Callable):
        """设置兜底处理器，用于处理未匹配的命令"""
        self.fallback_handler = handler

    async def dispatch(
        self, user_input: str, context: Dict[str, Any]
    ) -> Optional[bool]:
        """分发命令到对应的处理器

        Args:
            user_input: 用户输入
            context: 上下文信息（包含 session, new_prompt_callback 等）

        Returns:
            Optional[bool]: True 表示命令已处理，False 表示未处理，None 表示需要退出
        """
        # 按前缀长度排序，优先匹配更长的前缀（如 /conf/export 优先于 /conf）
        sorted_prefixes = sorted(self.commands.keys(), key=len, reverse=True)

        for prefix in sorted_prefixes:
            if user_input.startswith(prefix):
                handler = self.commands[prefix]
                result = handler(user_input, context)
                # 如果是协程，await 它
                if hasattr(result, "__await__"):
                    result = await result
                return result

        # 没有匹配的命令，使用兜底处理器
        if self.fallback_handler:
            result = self.fallback_handler(user_input, context)
            if hasattr(result, "__await__"):
                result = await result
            return result

        return False
