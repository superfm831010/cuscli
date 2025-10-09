"""布局定义"""

from prompt_toolkit.layout.containers import (
    HSplit,
    VSplit,
    Window,
    WindowAlign,
    ConditionalContainer,
)
from prompt_toolkit.layout.controls import FormattedTextControl, BufferControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.dimension import Dimension as D
from prompt_toolkit.filters import Condition
from prompt_toolkit.widgets import Frame


def create_layout(
    conversation_buffer,
    input_buffer,
    get_prompt_text,
    get_right_hint,
    get_tips_text,
    get_shortcuts_help_text,
    show_shortcuts_condition,
    input_has_text_condition,
):
    """创建应用布局"""

    # 创建对话历史控件
    conversation_control = FormattedTextControl(
        text=conversation_buffer.get_formatted_text,
        show_cursor=False,
        focusable=False,
    )

    # 创建输入控件
    input_control = BufferControl(
        buffer=input_buffer, search_buffer_control=None, focus_on_click=True
    )

    # 创建欢迎面板
    welcome_content = Window(
        content=FormattedTextControl(
            text=conversation_buffer.get_welcome_text, show_cursor=False
        ),
        style="class:welcome-panel",
    )

    welcome_panel = Frame(body=welcome_content, title="", style="class:welcome-border")

    # 对话历史窗口
    conversation_window = Window(
        content=conversation_control,
        wrap_lines=True,
        style="class:conversation",
        always_hide_cursor=True,
        height=D(min=5),
        dont_extend_height=False,
        scroll_offsets=None,
    )

    # 主要内容区域
    main_content = VSplit(
        [
            # 左侧留白
            Window(width=D(min=2, max=2)),
            # 中间内容
            HSplit(
                [
                    # 欢迎面板
                    welcome_panel,
                    # Tips 部分
                    Window(
                        content=FormattedTextControl(
                            text=get_tips_text, show_cursor=False
                        ),
                        height=D(min=7, max=7),
                        style="class:tips",
                    ),
                    # 对话历史区域
                    conversation_window,
                ]
            ),
            # 右侧留白
            Window(width=D(min=2, max=2)),
        ]
    )

    # 输入区域
    input_area = VSplit(
        [
            # 输入提示符
            Window(
                content=FormattedTextControl(text=get_prompt_text),
                width=D(min=2, max=4),
                style="class:prompt",
            ),
            # 输入框
            Window(content=input_control, style="class:input", height=D(min=1, max=1)),
            # 右侧提示信息
            Window(
                content=FormattedTextControl(text=get_right_hint),
                width=D(min=30, max=30),
                style="class:hint-right",
                align=WindowAlign.RIGHT,
            ),
        ],
        height=D(min=1, max=1),
    )

    # 创建布局
    root_container = HSplit(
        [
            # 主内容区域
            HSplit([main_content]),
            # 底部分隔
            Window(height=D(min=1, max=1)),
            # 输入区域边框
            Window(height=D(min=1, max=1), char="─", style="class:input-separator"),
            # 输入区域
            input_area,
            # 底部快捷键帮助
            ConditionalContainer(
                content=Window(
                    content=FormattedTextControl(
                        text=get_shortcuts_help_text, show_cursor=False
                    ),
                    height=D(min=5, max=5),
                    style="class:shortcuts-help",
                ),
                filter=Condition(
                    lambda: show_shortcuts_condition()
                    and not input_has_text_condition()
                ),
            ),
            # 底部空白
            Window(height=D(min=1, max=1)),
        ]
    )

    return Layout(root_container, focused_element=input_buffer)
