"""样式定义"""

from prompt_toolkit.styles import Style


def get_styles() -> Style:
    """获取应用样式 - 接近 Claude 的配色"""
    return Style.from_dict(
        {
            # 背景色
            "dialog": "bg:#f7f7f8",
            # 主内容区域
            "main-content": "bg:#f7f7f8",
            # 欢迎面板
            "welcome-panel": "bg:#f7f7f8 #2d2d30",
            "welcome-border": "#e3e3e6",
            "welcome": "#2d2d30 bold",
            # 提示部分
            "tips": "bg:#f7f7f8 #666666",
            # 对话区域
            "conversation": "bg:#ffffff #2d2d30",
            # 消息样式
            "system": "#ff6b6b",
            "system-text": "#666666",
            "user-prompt": "#2d2d30 bold",
            "user-text": "#2d2d30",
            "assistant": "#2d2d30 bold",
            "assistant-text": "#2d2d30",
            # 输入区域
            "input-separator": "#e3e3e6",
            "prompt": "bg:#ffffff #2d2d30 bold",
            "input": "bg:#ffffff #2d2d30",
            "hint-right": "bg:#ffffff #999999",
            "shortcuts-help": "bg:#ffffff #666666",
            # 默认
            "default": "#2d2d30",
            # 滚动条样式
            "scrollbar": "bg:#e3e3e6 #666666",
            "scrollbar.background": "bg:#f7f7f8",
            "scrollbar.button": "bg:#e3e3e6 #666666",
            "scrollbar.arrow": "#2d2d30",
        }
    )
