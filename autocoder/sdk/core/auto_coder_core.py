"""
Auto-Coder SDK 核心封装类

提供统一的查询接口，处理同步和异步调用。
"""

from typing import AsyncIterator, Optional, Dict, Any, Iterator, List
import asyncio
import os
import time
from concurrent.futures import ThreadPoolExecutor
import json

# Rich 渲染相关导入
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..models.options import AutoCodeOptions
from ..models.responses import StreamEvent, CodeModificationResult
from ..exceptions import BridgeError
from .bridge import AutoCoderBridge
from autocoder.common.wrap_llm_hint.utils import (
    extract_content_from_text,
    has_hint_in_text,
)


class AutoCoderCore:
    """AutoCoder核心封装类"""

    def __init__(self, options: AutoCodeOptions):
        """
        初始化AutoCoderCore

        Args:
            options: 配置选项
        """
        self.options = options
        cwd_str = str(options.cwd) if options.cwd is not None else os.getcwd()
        self.bridge = AutoCoderBridge(cwd_str, options)
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._console = Console()

        # 用于累计TokenUsageEvent数据
        self._accumulated_token_usage = {
            "model_name": "",
            "input_tokens": 0,
            "output_tokens": 0,
            "input_cost": 0.0,
            "output_cost": 0.0,
        }

    def _render_stream_event(
        self, event: StreamEvent, show_terminal: bool = True
    ) -> None:
        """
        渲染流式事件到终端

        Args:
            event: 流式事件
            show_terminal: 是否显示到终端
        """
        if not show_terminal:
            return

        # 如果输出格式是 JSON 相关，输出 JSON 格式
        if self.options.output_format in ["json", "stream-json"]:
            self._render_json_event(event)
            return

        # 原有的文本渲染逻辑保持不变
        try:
            # 处理新的事件类型（动态检查以避免导入依赖）
            event_class_name = type(event).__name__

            # 处理 TokenUsageEvent 和 WindowLengthChangeEvent
            if "TokenUsageEvent" in event_class_name:
                usage = getattr(event, "usage", None)
                if usage:
                    self._process_token_usage_event(usage)
                return

            elif "WindowLengthChangeEvent" in event_class_name:
                tokens_used = getattr(event, "tokens_used", 0)
                if tokens_used > 0:
                    self._console.print(f"[dim]当前会话总 tokens: {tokens_used}[/dim]")
                return

            elif "LLMThinkingEvent" in event_class_name:
                text = getattr(event, "text", "")
                if text.strip():
                    self._console.print(f"[grey50]{text}[/grey50]", end="")
                return

            elif "LLMOutputEvent" in event_class_name:
                text = getattr(event, "text", "")
                if text.strip():
                    self._console.print(text, end="")
                return

            elif "ToolCallEvent" in event_class_name:
                # 跳过 AttemptCompletionTool 的工具调用显示
                tool = getattr(event, "tool", None)
                if tool and "AttemptCompletionTool" in type(tool).__name__:
                    return

                tool_name = type(tool).__name__ if tool else "Unknown Tool"

                # 特殊处理 ConversationMessageIds 工具 - 只显示 compacting 消息
                if tool and tool_name in [
                    "ConversationMessageIdsWriteTool",
                    "ConversationMessageIdsReadTool",
                ]:
                    # 使用国际化的 compacting 消息
                    try:
                        from autocoder.common.auto_coder_lang import get_system_language

                        lang = get_system_language()
                        compacting_message = (
                            "compacting..." if lang == "en" else "压缩中..."
                        )
                    except:
                        compacting_message = "compacting..."

                    self._console.print(
                        Panel(
                            f"[dim]{compacting_message}[/dim]",
                            title="🗜️ Compacting",
                            border_style="yellow",
                            title_align="left",
                        )
                    )
                    return

                try:
                    # 尝试使用 get_tool_display_message 函数
                    from autocoder.common.v2.agent.agentic_edit_types import (
                        get_tool_display_message,
                    )

                    display_content = get_tool_display_message(tool)
                except:
                    # 如果导入失败，使用简单的显示
                    display_content = f"Tool: {tool_name}"
                    if hasattr(tool, "__dict__"):
                        for key, value in tool.__dict__.items():
                            if not key.startswith("_"):
                                display_content += f"\n{key}: {value}"

                self._console.print(
                    Panel(
                        display_content,
                        title=f"🛠️ Action: {tool_name}",
                        border_style="blue",
                        title_align="left",
                    )
                )
                return

            elif "ToolResultEvent" in event_class_name:
                # 跳过 AttemptCompletionTool 和 PlanModeRespondTool 的结果显示
                tool_name = getattr(event, "tool_name", "Unknown")
                if tool_name in ["AttemptCompletionTool", "PlanModeRespondTool"]:
                    return

                # 跳过 ConversationMessageIds 工具的结果显示 - 已由 compacting 消息处理
                if tool_name in [
                    "ConversationMessageIdsWriteTool",
                    "ConversationMessageIdsReadTool",
                ]:
                    return

                result = getattr(event, "result", None)
                if result:
                    success = getattr(result, "success", True)
                    message = getattr(result, "message", "")
                    content = getattr(result, "content", None)

                    title = (
                        f"✅ Tool Result: {tool_name}"
                        if success
                        else f"❌ Tool Result: {tool_name}"
                    )
                    border_style = "green" if success else "red"

                    base_content = (
                        f"[bold]Status:[/bold] {'Success' if success else 'Failure'}\n"
                    )
                    base_content += f"[bold]Message:[/bold] {message}\n"

                    # 处理内容显示
                    if content is not None:
                        formatted_content = self._format_tool_result_content(
                            content, tool_name
                        )
                        if isinstance(formatted_content, Syntax):
                            self._console.print(
                                Panel(
                                    base_content,
                                    title=title,
                                    border_style=border_style,
                                    title_align="left",
                                )
                            )
                            self._console.print(formatted_content)
                        else:
                            base_content += f"\n{formatted_content}"
                            self._console.print(
                                Panel(
                                    base_content,
                                    title=title,
                                    border_style=border_style,
                                    title_align="left",
                                )
                            )
                    else:
                        self._console.print(
                            Panel(
                                base_content,
                                title=title,
                                border_style=border_style,
                                title_align="left",
                            )
                        )
                return

            elif "CompletionEvent" in event_class_name:
                completion = getattr(event, "completion", None)
                if completion:
                    result = getattr(
                        completion, "result", "Task completed successfully"
                    )
                    command = getattr(completion, "command", None)

                    self._console.print(
                        Panel(
                            Markdown(result),
                            title="🏁 Task Completion",
                            border_style="green",
                            title_align="left",
                        )
                    )
                    if command:
                        self._console.print(
                            f"[dim]Suggested command:[/dim] [bold cyan]{command}[/]"
                        )
                return

            elif "PlanModeRespondEvent" in event_class_name:
                completion = getattr(event, "completion", None)
                if completion:
                    response = getattr(completion, "response", "Plan completed")
                    self._console.print(
                        Panel(
                            Markdown(response),
                            title="🏁 Plan Completion",
                            border_style="green",
                            title_align="left",
                        )
                    )
                return

            elif "ErrorEvent" in event_class_name:
                message = getattr(event, "message", "Unknown error")
                self._console.print(
                    Panel(
                        f"[bold red]Error:[/bold red] {message}",
                        title="🔥 Error",
                        border_style="red",
                        title_align="left",
                    )
                )
                return

            elif "ConversationIdEvent" in event_class_name:
                conversation_id = getattr(event, "conversation_id", "")
                if conversation_id:
                    self._console.print(
                        f"[dim]Conversation ID: {conversation_id}[/dim]"
                    )
                return

            elif "PreCommitEvent" in event_class_name:
                # event.commit_result 一定存在
                commit_result = event.commit_result
                success = (
                    commit_result.success
                    if hasattr(commit_result, "success")
                    else False
                )
                message = (
                    commit_result.message
                    if hasattr(commit_result, "message")
                    else "Pre-commit operation completed"
                )

                title = "✅ Pre-Commit Success" if success else "❌ Pre-Commit Failed"
                border_style = "yellow" if success else "red"

                self._console.print(
                    Panel(
                        f"[bold]Status:[/bold] {'Success' if success else 'Failed'}\n[bold]Message:[/bold] {message}",
                        title=title,
                        border_style=border_style,
                        title_align="left",
                    )
                )
                return

            elif "CommitEvent" in event_class_name:
                # event.commit_result 一定存在
                commit_result = event.commit_result
                success = (
                    commit_result.success
                    if hasattr(commit_result, "success")
                    else False
                )
                message = (
                    commit_result.message
                    if hasattr(commit_result, "message")
                    else "Commit operation completed"
                )
                commit_hash = (
                    commit_result.commit_hash
                    if hasattr(commit_result, "commit_hash")
                    else ""
                )

                title = "✅ Commit Success" if success else "❌ Commit Failed"
                border_style = "green" if success else "red"

                content = f"[bold]Status:[/bold] {'Success' if success else 'Failed'}\n[bold]Message:[/bold] {message}"
                if commit_hash:
                    content += f"\n[bold]Commit Hash:[/bold] {commit_hash}"

                self._console.print(
                    Panel(
                        content,
                        title=title,
                        border_style=border_style,
                        title_align="left",
                    )
                )
                return

            elif "PullRequestEvent" in event_class_name:
                # event.pull_request_result 一定存在
                pr_result = event.pull_request_result
                success = pr_result.success if hasattr(pr_result, "success") else False
                pr_number = (
                    pr_result.pr_number if hasattr(pr_result, "pr_number") else None
                )
                pr_url = pr_result.pr_url if hasattr(pr_result, "pr_url") else ""
                error_message = (
                    pr_result.error_message
                    if hasattr(pr_result, "error_message")
                    else ""
                )
                platform = (
                    pr_result.platform if hasattr(pr_result, "platform") else "Unknown"
                )

                title = (
                    "✅ Pull Request Created" if success else "❌ Pull Request Failed"
                )
                border_style = "cyan" if success else "red"

                if success:
                    content = f"[bold]Status:[/bold] Success\n[bold]Platform:[/bold] {platform}"
                    if pr_number:
                        content += f"\n[bold]PR Number:[/bold] #{pr_number}"
                    if pr_url:
                        content += f"\n[bold]PR URL:[/bold] {pr_url}"
                else:
                    content = f"[bold]Status:[/bold] Failed\n[bold]Platform:[/bold] {platform}"
                    if error_message:
                        content += f"\n[bold]Error:[/bold] {error_message}"

                self._console.print(
                    Panel(
                        content,
                        title=title,
                        border_style=border_style,
                        title_align="left",
                    )
                )
                return

            # 处理旧格式的事件类型
            if event.event_type == "start":
                project_name = os.path.basename(
                    os.path.abspath(self.options.cwd or os.getcwd())
                )
                self._console.rule(f"[bold cyan]Starting Auto-Coder: {project_name}[/]")
                query = event.data.get("query", "")
                if query:
                    self._console.print(
                        Panel(
                            f"[bold]Query:[/bold]\n{query}",
                            title="🎯 Objective",
                            border_style="blue",
                        )
                    )

            elif event.event_type == "llm_thinking":
                text = event.data.get("text", "")
                if text.strip():
                    self._console.print(f"[grey50]{text}[/grey50]", end="")

            elif event.event_type == "llm_output":
                text = event.data.get("text", "")
                if text.strip():
                    self._console.print(text, end="")

            elif event.event_type == "tool_call":
                tool_name = event.data.get("tool_name", "Unknown Tool")

                # 特殊处理 ConversationMessageIds 工具 - 只显示 compacting 消息
                if tool_name in [
                    "ConversationMessageIdsWriteTool",
                    "ConversationMessageIdsReadTool",
                ]:
                    # 使用国际化的 compacting 消息
                    try:
                        from autocoder.common.auto_coder_lang import get_system_language

                        lang = get_system_language()
                        compacting_message = (
                            "compacting..." if lang == "en" else "压缩中..."
                        )
                    except:
                        compacting_message = "compacting..."

                    self._console.print(
                        Panel(
                            f"[dim]{compacting_message}[/dim]",
                            title="🗜️ Compacting",
                            border_style="yellow",
                            title_align="left",
                        )
                    )
                else:
                    tool_args = event.data.get("args", {})
                    display_content = self._format_tool_display(tool_name, tool_args)
                    self._console.print(
                        Panel(
                            display_content,
                            title=f"🛠️ Action: {tool_name}",
                            border_style="blue",
                            title_align="left",
                        )
                    )

            elif event.event_type == "tool_result":
                tool_name = event.data.get("tool_name", "Unknown Tool")

                # 跳过 ConversationMessageIds 工具的结果显示 - 已由 compacting 消息处理
                if tool_name in [
                    "ConversationMessageIdsWriteTool",
                    "ConversationMessageIdsReadTool",
                ]:
                    return

                success = event.data.get("success", True)
                message = event.data.get("message", "")
                content = event.data.get("content")

                title = (
                    f"✅ Tool Result: {tool_name}"
                    if success
                    else f"❌ Tool Result: {tool_name}"
                )
                border_style = "green" if success else "red"

                base_content = (
                    f"[bold]Status:[/bold] {'Success' if success else 'Failure'}\n"
                )
                base_content += f"[bold]Message:[/bold] {message}\n"

                # 处理内容显示
                if content is not None:
                    formatted_content = self._format_tool_result_content(
                        content, tool_name
                    )
                    if isinstance(formatted_content, Syntax):
                        self._console.print(
                            Panel(
                                base_content,
                                title=title,
                                border_style=border_style,
                                title_align="left",
                            )
                        )
                        self._console.print(formatted_content)
                    else:
                        base_content += f"\n{formatted_content}"
                        self._console.print(
                            Panel(
                                base_content,
                                title=title,
                                border_style=border_style,
                                title_align="left",
                            )
                        )
                else:
                    self._console.print(
                        Panel(
                            base_content,
                            title=title,
                            border_style=border_style,
                            title_align="left",
                        )
                    )

            elif event.event_type == "completion":
                result = event.data.get("result", "Task completed successfully")
                self._console.print(
                    Panel(
                        Markdown(result),
                        title="🏁 Task Completion",
                        border_style="green",
                        title_align="left",
                    )
                )

            elif event.event_type == "plan_mode_respond":
                result = event.data.get("result", "Plan completed")
                self._console.print(
                    Panel(
                        Markdown(result),
                        title="🏁 Plan Completion",
                        border_style="green",
                        title_align="left",
                    )
                )

            elif event.event_type == "token_usage":
                usage = event.data.get("usage")
                if usage:
                    self._process_token_usage_event(usage)

            elif event.event_type == "window_change":
                tokens_used = event.data.get("tokens_used", 0)
                if tokens_used > 0:
                    self._console.print(f"[dim]当前会话总 tokens: {tokens_used}[/dim]")

            elif event.event_type == "conversation_id":
                conversation_id = event.data.get("conversation_id", "")
                if conversation_id:
                    self._console.print(
                        f"[dim]Conversation ID: {conversation_id}[/dim]"
                    )

            elif event.event_type == "content":
                content = event.data.get("content", "")
                if content.strip():
                    # 检查是否是思考过程（通常包含特定标记）
                    if any(
                        marker in content.lower()
                        for marker in ["thinking", "analyzing", "考虑", "分析"]
                    ):
                        self._console.print(f"[grey50]{content}[/grey50]", end="")
                    else:
                        self._console.print(content, end="")

            elif event.event_type == "file_modified":
                files = event.data.get("files", [])
                if files:
                    files_str = "\n".join([f"  - {f}" for f in files])
                    self._console.print(
                        Panel(
                            f"[bold]Modified Files:[/bold]\n{files_str}",
                            title="📝 File Changes",
                            border_style="yellow",
                            title_align="left",
                        )
                    )

            elif event.event_type == "file_created":
                files = event.data.get("files", [])
                if files:
                    files_str = "\n".join([f"  - {f}" for f in files])
                    self._console.print(
                        Panel(
                            f"[bold]Created Files:[/bold]\n{files_str}",
                            title="📄 New Files",
                            border_style="green",
                            title_align="left",
                        )
                    )

            elif event.event_type == "file_deleted":
                files = event.data.get("files", [])
                if files:
                    files_str = "\n".join([f"  - {f}" for f in files])
                    self._console.print(
                        Panel(
                            f"[bold]Deleted Files:[/bold]\n{files_str}",
                            title="🗑️ Removed Files",
                            border_style="red",
                            title_align="left",
                        )
                    )

            elif event.event_type == "end":
                status = event.data.get("status", "completed")
                if status == "completed":
                    self._console.rule(
                        "[bold green]Auto-Coder Finished Successfully[/]"
                    )
                else:
                    self._console.rule(f"[bold yellow]Auto-Coder Finished: {status}[/]")

            elif event.event_type == "error":
                error = event.data.get("error", "Unknown error")
                error_type = event.data.get("error_type", "Error")
                self._console.print(
                    Panel(
                        f"[bold red]Error Type:[/bold red] {error_type}\n[bold red]Message:[/bold red] {error}",
                        title="🔥 Error",
                        border_style="red",
                        title_align="left",
                    )
                )

        except Exception as e:
            # 渲染错误不应该影响主流程
            self._console.print(f"[dim red]Render error: {str(e)}[/dim red]")

    def _render_json_event(self, event: StreamEvent) -> None:
        """
        以 JSON 格式渲染流式事件

        Args:
            event: 流式事件
        """
        try:
            # 构建事件的 JSON 表示
            event_json = self._convert_event_to_json(event)
            print(json.dumps(event_json, ensure_ascii=False), flush=True)
        except Exception as e:
            # 如果 JSON 序列化失败，输出错误事件
            error_json = {
                "event_type": "json_render_error",
                "data": {
                    "error": str(e),
                    "original_event_type": getattr(event, "event_type", "unknown"),
                },
                "timestamp": time.time(),
            }
            print(json.dumps(error_json, ensure_ascii=False), flush=True)

    def _convert_event_to_json(self, event: StreamEvent) -> dict:
        """
        将流式事件转换为 JSON 字典

        Args:
            event: 流式事件

        Returns:
            dict: JSON 字典表示
        """
        # 处理新格式的事件类型（动态检查以避免导入依赖）
        event_class_name = type(event).__name__

        # 基础事件信息
        base_json = {
            "timestamp": time.time(),
        }

        try:
            if "TokenUsageEvent" in event_class_name:
                usage = getattr(event, "usage", None)
                base_json.update(
                    {
                        "event_type": "token_usage",
                        "data": {
                            "usage": (
                                self._serialize_usage_object(usage) if usage else None
                            )
                        },
                    }
                )
            elif "WindowLengthChangeEvent" in event_class_name:
                tokens_used = getattr(event, "tokens_used", 0)
                base_json.update(
                    {
                        "event_type": "window_change",
                        "data": {"tokens_used": tokens_used},
                    }
                )
            elif "LLMThinkingEvent" in event_class_name:
                text = getattr(event, "text", "")
                base_json.update({"event_type": "llm_thinking", "data": {"text": text}})
            elif "LLMOutputEvent" in event_class_name:
                text = getattr(event, "text", "")
                base_json.update({"event_type": "llm_output", "data": {"text": text}})
            elif "ToolCallEvent" in event_class_name:
                tool = getattr(event, "tool", None)
                tool_name = type(tool).__name__ if tool else "Unknown Tool"
                tool_args = self._serialize_tool_object(tool) if tool else {}
                base_json.update(
                    {
                        "event_type": "tool_call",
                        "data": {"tool_name": tool_name, "args": tool_args},
                    }
                )
            elif "ToolResultEvent" in event_class_name:
                tool_name = getattr(event, "tool_name", "Unknown")
                result = getattr(event, "result", None)
                result_data = self._serialize_tool_result(result) if result else {}
                base_json.update(
                    {
                        "event_type": "tool_result",
                        "data": {"tool_name": tool_name, **result_data},
                    }
                )
            elif "CompletionEvent" in event_class_name:
                completion = getattr(event, "completion", None)
                completion_data = (
                    self._serialize_completion_object(completion) if completion else {}
                )
                base_json.update({"event_type": "completion", "data": completion_data})
            elif "PlanModeRespondEvent" in event_class_name:
                completion = getattr(event, "completion", None)
                response = (
                    getattr(completion, "response", "Plan completed")
                    if completion
                    else "Plan completed"
                )
                base_json.update(
                    {"event_type": "plan_mode_respond", "data": {"result": response}}
                )
            elif "ErrorEvent" in event_class_name:
                message = getattr(event, "message", "Unknown error")
                base_json.update(
                    {
                        "event_type": "error",
                        "data": {"error": message, "error_type": "Error"},
                    }
                )
            elif "ConversationIdEvent" in event_class_name:
                conversation_id = getattr(event, "conversation_id", "")
                base_json.update(
                    {
                        "event_type": "conversation_id",
                        "data": {"conversation_id": conversation_id},
                    }
                )
            elif "PreCommitEvent" in event_class_name:
                # event.commit_result 和 event.tpe 一定存在
                commit_result = event.commit_result
                commit_data = self._serialize_commit_result(commit_result)
                base_json.update(
                    {
                        "event_type": "pre_commit",
                        "data": {"commit_result": commit_data, "tpe": event.tpe},
                    }
                )
            elif "CommitEvent" in event_class_name:
                # event.commit_result 和 event.tpe 一定存在
                commit_result = event.commit_result
                commit_data = self._serialize_commit_result(commit_result)
                base_json.update(
                    {
                        "event_type": "commit",
                        "data": {"commit_result": commit_data, "tpe": event.tpe},
                    }
                )
            elif "PullRequestEvent" in event_class_name:
                # event.pull_request_result 一定存在
                pr_result = event.pull_request_result
                pr_data = self._serialize_pr_result(pr_result)
                base_json.update(
                    {
                        "event_type": "pull_request",
                        "data": {"pull_request_result": pr_data},
                    }
                )
            else:
                # 处理旧格式的事件（有 event_type 和 data 属性）
                if hasattr(event, "event_type") and hasattr(event, "data"):
                    base_json.update(
                        {
                            "event_type": event.event_type,
                            "data": (
                                event.data
                                if isinstance(event.data, dict)
                                else {"content": str(event.data)}
                            ),
                        }
                    )
                else:
                    # 未知事件类型，尝试序列化所有属性
                    base_json.update(
                        {
                            "event_type": "unknown",
                            "data": self._serialize_object_attributes(event),
                        }
                    )
        except Exception as e:
            # 如果序列化失败，返回基本信息
            base_json.update(
                {
                    "event_type": "serialization_error",
                    "data": {"error": str(e), "original_class": event_class_name},
                }
            )

        return base_json

    def _serialize_usage_object(self, usage) -> dict:
        """序列化使用情况对象"""
        try:
            return {
                "input_tokens_count": getattr(usage, "input_tokens_count", 0),
                "generated_tokens_count": getattr(usage, "generated_tokens_count", 0),
                "total_tokens": getattr(usage, "input_tokens_count", 0)
                + getattr(usage, "generated_tokens_count", 0),
            }
        except:
            return {"error": "Failed to serialize usage object"}

    def _serialize_tool_object(self, tool) -> dict:
        """序列化工具对象"""
        try:
            if hasattr(tool, "__dict__"):
                result = {}
                for key, value in tool.__dict__.items():
                    if not key.startswith("_"):
                        try:
                            # 尝试序列化值，如果失败则转为字符串
                            json.dumps(value)
                            result[key] = value
                        except:
                            result[key] = str(value)
                return result
            else:
                return {"tool": str(tool)}
        except:
            return {"error": "Failed to serialize tool object"}

    def _serialize_tool_result(self, result) -> dict:
        """序列化工具结果对象"""
        try:
            return {
                "success": getattr(result, "success", True),
                "message": getattr(result, "message", ""),
                "content": self._serialize_content(getattr(result, "content", None)),
            }
        except:
            return {"error": "Failed to serialize tool result"}

    def _serialize_completion_object(self, completion) -> dict:
        """序列化完成对象"""
        try:
            return {
                "result": getattr(completion, "result", "Task completed successfully"),
                "command": getattr(completion, "command", None),
            }
        except:
            return {"error": "Failed to serialize completion object"}

    def _serialize_content(self, content) -> Any:
        """序列化内容，确保可以 JSON 序列化"""
        try:
            if content is None:
                return None
            # 尝试 JSON 序列化测试
            json.dumps(content)
            return content
        except:
            # 如果不能序列化，转为字符串
            return str(content)

    def _serialize_object_attributes(self, obj) -> dict:
        """序列化对象的所有属性"""
        try:
            result = {}
            if hasattr(obj, "__dict__"):
                for key, value in obj.__dict__.items():
                    if not key.startswith("_"):
                        result[key] = self._serialize_content(value)
            return result
        except:
            return {"error": "Failed to serialize object attributes"}

    def _serialize_commit_result(self, commit_result) -> dict:
        """序列化 Git 提交结果对象"""
        try:
            return {
                "success": (
                    commit_result.success
                    if hasattr(commit_result, "success")
                    else False
                ),
                "message": (
                    commit_result.message if hasattr(commit_result, "message") else ""
                ),
                "commit_hash": (
                    commit_result.commit_hash
                    if hasattr(commit_result, "commit_hash")
                    else ""
                ),
                "files_changed": (
                    commit_result.files_changed
                    if hasattr(commit_result, "files_changed")
                    else []
                ),
                "error": (
                    commit_result.error if hasattr(commit_result, "error") else None
                ),
            }
        except:
            return {"error": "Failed to serialize commit result"}

    def _serialize_pr_result(self, pr_result) -> dict:
        """序列化 Pull Request 结果对象"""
        try:
            return {
                "success": (
                    pr_result.success if hasattr(pr_result, "success") else False
                ),
                "pr_number": (
                    pr_result.pr_number if hasattr(pr_result, "pr_number") else None
                ),
                "pr_url": pr_result.pr_url if hasattr(pr_result, "pr_url") else "",
                "pr_id": pr_result.pr_id if hasattr(pr_result, "pr_id") else None,
                "error_message": (
                    pr_result.error_message
                    if hasattr(pr_result, "error_message")
                    else None
                ),
                "error_code": (
                    pr_result.error_code if hasattr(pr_result, "error_code") else None
                ),
                "platform": (
                    pr_result.platform if hasattr(pr_result, "platform") else None
                ),
                "raw_response": self._serialize_content(
                    pr_result.raw_response
                    if hasattr(pr_result, "raw_response")
                    else None
                ),
                "retry_after": (
                    pr_result.retry_after if hasattr(pr_result, "retry_after") else None
                ),
            }
        except:
            return {"error": "Failed to serialize pull request result"}

    def _format_tool_display(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """
        格式化工具调用显示内容

        Args:
            tool_name: 工具名称
            tool_args: 工具参数

        Returns:
            str: 格式化后的显示内容
        """
        if not tool_args:
            return f"[bold]Tool:[/bold] {tool_name}"

        content_parts = [f"[bold]Tool:[/bold] {tool_name}"]

        for key, value in tool_args.items():
            if isinstance(value, str) and len(value) > 100:
                value = f"{value[:50]}...{value[-50:]}"
            content_parts.append(f"[bold]{key}:[/bold] {value}")

        return "\n".join(content_parts)

    def _process_token_usage_event(self, usage):
        """
        处理 TokenUsageEvent，累计 token 使用情况

        Args:
            usage: SingleOutputMeta 对象
        """
        try:
            # 正确提取 SingleOutputMeta 对象的属性
            input_tokens = getattr(usage, "input_tokens_count", 0)
            output_tokens = getattr(usage, "generated_tokens_count", 0)

            # 获取模型信息用于定价
            try:
                from autocoder.utils import llms as llm_utils

                # 这里需要获取 LLM 实例，但在 SDK 中可能不直接可用
                # 暂时使用默认模型名称
                model_name = self.options.model or "unknown"
                model_info = llm_utils.get_model_info(model_name, "lite") or {}
                input_price = model_info.get("input_price", 0.0)
                output_price = model_info.get("output_price", 0.0)
            except:
                # 如果获取模型信息失败，使用默认值
                model_name = self.options.model or "unknown"
                input_price = 0.0
                output_price = 0.0

            # 计算成本
            input_cost = (input_tokens * input_price) / 1000000  # 转换为百万token单位
            output_cost = (output_tokens * output_price) / 1000000

            # 累计token使用情况
            self._accumulated_token_usage["model_name"] = model_name
            self._accumulated_token_usage["input_tokens"] += input_tokens
            self._accumulated_token_usage["output_tokens"] += output_tokens
            self._accumulated_token_usage["input_cost"] += input_cost
            self._accumulated_token_usage["output_cost"] += output_cost

            # 显示当前的 token 使用情况
            total_tokens = input_tokens + output_tokens
            self._console.print(
                f"[dim]Token usage: Input={input_tokens}, Output={output_tokens}, Total={total_tokens}[/dim]"
            )

        except Exception as e:
            self._console.print(
                f"[dim red]Error processing token usage: {str(e)}[/dim red]"
            )

    def _print_final_token_usage(self):
        """
        打印最终的累计 token 使用情况
        """
        try:
            if self._accumulated_token_usage["input_tokens"] > 0:
                from autocoder.common.printer import Printer

                printer = Printer()
                printer.print_in_terminal(
                    "code_generation_complete",
                    duration=0.0,
                    input_tokens=self._accumulated_token_usage["input_tokens"],
                    output_tokens=self._accumulated_token_usage["output_tokens"],
                    input_cost=self._accumulated_token_usage["input_cost"],
                    output_cost=self._accumulated_token_usage["output_cost"],
                    speed=0.0,
                    model_names=self._accumulated_token_usage["model_name"],
                    sampling_count=1,
                )
        except Exception as e:
            # 如果打印失败，使用简单的格式
            total_tokens = (
                self._accumulated_token_usage["input_tokens"]
                + self._accumulated_token_usage["output_tokens"]
            )
            total_cost = (
                self._accumulated_token_usage["input_cost"]
                + self._accumulated_token_usage["output_cost"]
            )
            self._console.print(
                Panel(
                    f"总计 Token 使用: {total_tokens} (输入: {self._accumulated_token_usage['input_tokens']}, 输出: {self._accumulated_token_usage['output_tokens']})\n"
                    f"总计成本: ${total_cost:.6f}",
                    title="📊 Token 使用统计",
                    border_style="cyan",
                )
            )

    def _reset_token_usage(self):
        """
        重置累计的 token 使用情况
        """
        self._accumulated_token_usage = {
            "model_name": "",
            "input_tokens": 0,
            "output_tokens": 0,
            "input_cost": 0.0,
            "output_cost": 0.0,
        }

    def _format_tool_result_content(
        self, content: Any, tool_name: str = ""
    ) -> str | Syntax:
        """
        格式化工具结果内容

        Args:
            content: 结果内容
            tool_name: 工具名称（用于推断语法类型）

        Returns:
            str | Syntax: 格式化后的内容或语法高亮对象
        """

        def _truncate_content(content_str: str) -> str:
            if len(content_str) > 500:
                return f"{content_str[:200]}\n...\n{content_str[-200:]}"
            return content_str

        try:
            # Remove hints from content before processing
            processed_content = content
            if isinstance(content, str) and has_hint_in_text(content):
                processed_content = extract_content_from_text(content)

            if isinstance(processed_content, (dict, list)):
                import json

                content_str = json.dumps(
                    processed_content, indent=2, ensure_ascii=False
                )
                return Syntax(
                    _truncate_content(content_str),
                    "json",
                    theme="default",
                    line_numbers=False,
                )

            elif isinstance(processed_content, str):
                # 检查是否是多行内容或代码
                if (
                    "\n" in processed_content
                    or processed_content.strip().startswith("<")
                    or len(processed_content) > 200
                ):
                    # 推断语法类型
                    lexer = "text"
                    if "ReadFile" in tool_name:
                        if any(ext in processed_content for ext in [".py", "python"]):
                            lexer = "python"
                        elif any(
                            ext in processed_content for ext in [".js", "javascript"]
                        ):
                            lexer = "javascript"
                        elif any(
                            ext in processed_content for ext in [".ts", "typescript"]
                        ):
                            lexer = "typescript"
                        elif any(
                            ext in processed_content
                            for ext in [".html", "<!DOCTYPE", "<html"]
                        ):
                            lexer = "html"
                        elif any(ext in processed_content for ext in [".css", "{"]):
                            lexer = "css"
                        elif any(ext in processed_content for ext in [".json", "{"]):
                            lexer = "json"
                        elif any(ext in processed_content for ext in [".xml", "<?xml"]):
                            lexer = "xml"
                        elif any(ext in processed_content for ext in [".md", "#"]):
                            lexer = "markdown"
                    elif "ExecuteCommand" in tool_name or "Shell" in tool_name:
                        lexer = "shell"
                    elif processed_content.strip().startswith(
                        "{"
                    ) or processed_content.strip().startswith("["):
                        lexer = "json"

                    return Syntax(
                        _truncate_content(processed_content),
                        lexer,
                        theme="default",
                        line_numbers=True,
                    )
                else:
                    return _truncate_content(processed_content)
            else:
                return _truncate_content(str(processed_content))

        except Exception:
            return _truncate_content(str(content))

    async def query_stream(
        self, prompt: str, show_terminal: Optional[bool] = None
    ) -> AsyncIterator[StreamEvent]:
        """
        异步流式查询 - 使用 run_auto_command

        Args:
            prompt: 查询提示
            show_terminal: 是否显示到终端，None时使用配置中的verbose设置

        Yields:
            StreamEvent: 响应事件流

        Raises:
            BridgeError: 桥接层错误
        """
        # 如果没有明确指定show_terminal，使用verbose配置
        if show_terminal is None:
            show_terminal = self.options.verbose

        # 如果verbose为False，则强制show_terminal为False
        if not self.options.verbose:
            show_terminal = False

        try:
            # 重置累计的 token 使用情况
            self._reset_token_usage()

            # 先返回用户消息
            user_message = StreamEvent(event_type="start", data={"query": prompt})
            yield user_message

            # 在线程池中执行同步调用
            loop = asyncio.get_event_loop()

            # 使用 run_auto_command 进行代码修改，传递 cancel_token
            event_stream = await loop.run_in_executor(
                self._executor,
                self._sync_run_auto_command,
                prompt,
                False,  # pre_commit
                None,  # pr (使用默认值)
                None,  # extra_args
            )

            # 处理事件流并转换为消息
            for event in event_stream:
                # 渲染事件到终端
                self._render_stream_event(event, show_terminal)
                yield event

            # 打印最终的累计 token 使用情况
            if show_terminal:
                self._print_final_token_usage()

        except Exception as e:
            # 在异常时也打印累计的 token 使用情况
            if show_terminal:
                self._print_final_token_usage()
            raise e

    def query_sync(
        self, prompt: str, show_terminal: Optional[bool] = None
    ) -> List[StreamEvent]:
        """
        同步查询 - 通过调用 query_stream 实现

        Args:
            prompt: 查询提示
            show_terminal: 是否显示到终端，None时使用配置中的verbose设置

        Returns:
            List[StreamEvent]: 事件列表，包含用户查询和响应事件

        Raises:
            BridgeError: 桥接层错误
        """
        try:
            # 收集所有事件
            events = []

            # 运行异步查询流并收集结果
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:

                async def collect_events():
                    async for event in self.query_stream(prompt, show_terminal):
                        events.append(event)

                loop.run_until_complete(collect_events())
            finally:
                loop.close()

            return events

        except Exception as e:
            raise e

    def _sync_run_auto_command(
        self,
        prompt: str,
        pre_commit: bool = False,
        pr: Optional[bool] = None,
        extra_args: Optional[Dict[str, Any]] = None,
    ) -> Iterator[StreamEvent]:
        """
        内部同步调用 run_auto_command

        Args:
            prompt: 查询提示
            pre_commit: 是否预提交
            pr: 是否创建 PR，如果为None则使用配置中的值
            extra_args: 额外参数

        Returns:
            Iterator[StreamEvent]: 事件流
        """
        # 如果没有明确指定pr参数，使用配置中的值
        if pr is None:
            pr = self.options.pr

        return self.bridge.call_run_auto_command(
            query=prompt,
            pre_commit=pre_commit,
            pr=pr,
            cancel_token=self.options.cancel_token,
            extra_args=extra_args or {},
            stream=True,
        )

    def get_project_memory(self) -> Dict[str, Any]:
        """
        获取项目内存状态

        Returns:
            Dict[str, Any]: 项目内存数据
        """
        return self.bridge.get_memory()

    def save_project_memory(self, memory_data: Dict[str, Any]) -> None:
        """
        保存项目内存状态

        Args:
            memory_data: 内存数据
        """
        self.bridge.save_memory(memory_data)

    def get_project_config(self) -> Dict[str, Any]:
        """
        获取项目配置

        Returns:
            Dict[str, Any]: 项目配置
        """
        return self.bridge.get_project_config()

    def run_workflow(
        self,
        workflow: str,
        prompt: Optional[str] = None,
        vars_override: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        运行指定的 workflow

        Args:
            workflow: workflow 名称或文件路径
            prompt: 可选的提示内容，会注入到 workflow 的 vars.query 中
            vars_override: 可选的变量覆盖字典

        Returns:
            WorkflowResult: workflow 执行结果

        Raises:
            BridgeError: 桥接层错误
        """
        return self.bridge.run_workflow(
            workflow=workflow,
            prompt=prompt,
            model=self.options.model,
            vars_override=vars_override,
        )

    def __del__(self):
        """清理资源"""
        if hasattr(self, "_executor"):
            self._executor.shutdown(wait=False)
