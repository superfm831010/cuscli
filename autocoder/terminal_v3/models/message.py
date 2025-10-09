"""聊天消息模型"""

from datetime import datetime
from typing import List, Tuple
from prompt_toolkit.formatted_text import ANSI, to_formatted_text


class ChatMessage:
    """聊天消息类"""

    def __init__(
        self,
        content: str,
        role: str = "assistant",
        timestamp: datetime = None,
        ansi: bool = False,
    ):
        self.content = content
        self.role = role  # user, assistant, system, welcome
        self.timestamp = timestamp or datetime.now()
        self.is_ansi = ansi
        self._is_thinking: bool = False

    def to_formatted_text(self) -> List[Tuple[str, str]]:
        """转换为 FormattedText 格式"""
        if self.is_ansi:
            # 直接使用 ANSI 渲染（不加前缀圆点，避免破坏颜色布局）
            return list(to_formatted_text(ANSI(self.content))) + [("", "\n")]

        if self.role == "welcome":
            # 欢迎消息不显示时间戳
            return [("class:welcome", self.content), ("", "\n")]
        elif self.role == "system":
            return [
                ("class:system", "● "),
                ("class:system-text", self.content),
                ("", "\n"),
            ]
        elif self.role == "user":
            return [
                ("class:user-prompt", "> "),
                ("class:user-text", self.content),
                ("", "\n"),
            ]
        else:  # assistant
            return [
                ("class:assistant", "● "),
                ("class:assistant-text", self.content),
                ("", "\n"),
            ]
