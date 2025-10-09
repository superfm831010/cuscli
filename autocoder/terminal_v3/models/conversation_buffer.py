"""对话缓冲区管理"""

import os
from typing import List, Optional
from .message import ChatMessage
from autocoder.common.v2.agent.agentic_edit_types import (
    ConversationIdEvent,
    TokenUsageEvent,
    WindowLengthChangeEvent,
    LLMThinkingEvent,
    LLMOutputEvent,
    ToolCallEvent,
    ToolResultEvent,
    PlanModeRespondEvent,
    PreCommitEvent,
    CommitEvent,
    PullRequestEvent,
    CompletionEvent,
    ErrorEvent,
)


class ConversationBuffer:
    """对话缓冲区，类似聊天应用的消息列表"""

    def __init__(self, max_messages: int = 200):
        self.max_messages = max_messages
        self.messages: List[ChatMessage] = []
        self.welcome_messages: List[ChatMessage] = []
        self.token_stats = {"input_tokens": 0, "output_tokens": 0, "model": ""}

        # 强类型属性定义
        self._thinking_buffer: Optional[str] = None
        self._current_response: Optional[str] = None

        self._init_welcome_messages()

    def _init_welcome_messages(self):
        """初始化欢迎消息"""
        self.welcome_messages.append(
            ChatMessage("✦ Welcome to Auto-Coder.Chat!", "welcome")
        )
        self.welcome_messages.append(ChatMessage("", "welcome"))
        self.welcome_messages.append(
            ChatMessage("/help for help, /status to view current setup", "welcome")
        )
        self.welcome_messages.append(ChatMessage("", "welcome"))
        cwd = os.getcwd()
        self.welcome_messages.append(ChatMessage(f"cwd: {cwd}", "welcome"))
        self.welcome_messages.append(ChatMessage("", "welcome"))

    def get_welcome_text(self):
        """获取欢迎消息的格式化文本"""
        result = []
        for msg in self.welcome_messages:
            result.extend(msg.to_formatted_text())
        return result

    def add_user_message(self, content: str):
        """添加用户消息"""
        self.messages.append(ChatMessage(content, "user"))
        self._trim_messages()

    def add_assistant_message(self, content: str):
        """添加助手消息"""
        self.messages.append(ChatMessage(content, "assistant"))
        self._trim_messages()

    def add_system_message(self, content: str, ansi: bool = False):
        """添加系统消息"""
        self.messages.append(ChatMessage(content, "system", ansi=ansi))
        self._trim_messages()

    def add_event(self, event):
        """处理 SdkRunner 事件 - 参考 terminal_runner.py 的格式化方式"""
        if isinstance(event, ConversationIdEvent):
            # 对话ID事件静默处理，不显示
            pass

        elif isinstance(event, TokenUsageEvent):
            meta = event.usage
            self.token_stats["input_tokens"] += meta.input_tokens_count
            self.token_stats["output_tokens"] += meta.generated_tokens_count
            # SingleOutputMeta 没有 model_name 属性，保持原有逻辑
            # 模型名称通过其他方式获取

        elif isinstance(event, WindowLengthChangeEvent):
            # 显示 token 使用情况
            if event.tokens_used > event.pruned_tokens_used:
                self.add_system_message(
                    f"Conversation tokens: {event.tokens_used} -> {event.pruned_tokens_used} "
                    f"(round: {event.conversation_round})"
                )

        elif isinstance(event, LLMThinkingEvent):
            # 实时显示思考过程（灰色显示）
            if self._thinking_buffer is not None:
                self._thinking_buffer += event.text
                # 更新最后一条思考消息
                if self.messages and self.messages[-1]._is_thinking:
                    self.messages[-1].content = self._thinking_buffer
                else:
                    msg = ChatMessage(self._thinking_buffer, "system")
                    msg._is_thinking = True
                    self.messages.append(msg)
            else:
                self._thinking_buffer = event.text
                msg = ChatMessage(self._thinking_buffer, "system")
                msg._is_thinking = True
                self.messages.append(msg)

        elif isinstance(event, LLMOutputEvent):
            # 清除思考缓冲区（如果有）
            if self._thinking_buffer is not None:
                self._thinking_buffer = None

            # LLM 输出直接添加为助手消息（流式更新）
            if self._current_response is not None:
                self._current_response += event.text
                if self.messages and self.messages[-1].role == "assistant":
                    self.messages[-1].content = self._current_response
                else:
                    self.messages.append(
                        ChatMessage(self._current_response, "assistant")
                    )
            else:
                self._current_response = event.text
                self.messages.append(ChatMessage(self._current_response, "assistant"))

        elif isinstance(event, ToolCallEvent):
            # 使用简洁的工具调用显示
            from .tool_display import get_tool_simple_display

            tool_display = get_tool_simple_display(event.tool)
            self.add_system_message(f"🔧 {tool_display}")

        elif isinstance(event, ToolResultEvent):
            # 显示工具结果（简洁版本）
            from .tool_display import get_tool_result_display

            result = event.result
            result_display = get_tool_result_display(
                event.tool_name,
                result.success,
                result.message if not result.success else None,
            )
            self.add_system_message(result_display)

        elif isinstance(event, PlanModeRespondEvent):
            try:
                response_text = event.completion.response
                if response_text:
                    self.add_assistant_message(response_text)
            except Exception:
                pass

        elif isinstance(event, PreCommitEvent):
            if event.commit_result:
                self.add_system_message("📦 Changes staged")

        elif isinstance(event, CommitEvent):
            if event.commit_result and event.commit_result.success:
                self.add_system_message(
                    f"✅ Committed: {event.commit_result.commit_hash[:8]}"
                )

        elif isinstance(event, PullRequestEvent):
            if event.pull_request_result and event.pull_request_result.success:
                self.add_system_message(
                    f"🎉 PR #{event.pull_request_result.pr_number} created"
                )

        elif isinstance(event, CompletionEvent):
            # 清除思考和响应缓冲区
            if self._thinking_buffer is not None:
                self._thinking_buffer = None

            if self._current_response is not None:
                if self.messages and self.messages[-1].role == "assistant":
                    self.messages[-1].content = self._current_response
                else:
                    self.add_assistant_message(self._current_response)
                self._current_response = None
            else:
                try:
                    result_text = event.completion.result
                    if result_text:
                        self.add_assistant_message(result_text)
                except Exception:
                    pass

        elif isinstance(event, ErrorEvent):
            self.add_system_message(f"❌ Error: {event.message}")

    def _trim_messages(self):
        """保持消息数量在限制内"""
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages :]

    def get_formatted_text(self):
        """获取格式化的文本用于显示"""
        if not self.messages:
            return [("", "")]

        result = []
        for message in self.messages:
            result.extend(message.to_formatted_text())
        return result

    def clear_conversation(self):
        """清空对话历史"""
        self.messages = []
        self._current_response = None
        self._thinking_buffer = None
