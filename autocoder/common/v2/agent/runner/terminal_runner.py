"""
TerminalRunner 提供在终端环境中运行代理的功能，支持格式化输出和交互式显示。

这个模块使用 Rich 库来提供格式化的终端输出，包括颜色、样式和布局。
它处理各种代理事件并以用户友好的方式在终端中显示。
"""

import os
import json
import time
import logging
from typing import Any, Dict, Optional, List

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax

from autocoder.common.auto_coder_lang import get_message
from byzerllm.utils.types import SingleOutputMeta
from autocoder.utils import llms as llm_utils
from autocoder.common.v2.agent.agentic_edit_types import (
    AgenticEditRequest, AgentEvent, CompletionEvent, 
    LLMOutputEvent, LLMThinkingEvent, ToolCallEvent, 
    ToolResultEvent, TokenUsageEvent, ErrorEvent,
    WindowLengthChangeEvent, ConversationIdEvent,
    PlanModeRespondEvent, AttemptCompletionTool,
    ConversationAction, TodoReadTool, TodoWriteTool,
    ConversationMessageIdsWriteTool, ConversationMessageIdsReadTool
)
from .tool_display import get_tool_display_message, get_tool_title, get_tool_result_title
from .base_runner import BaseRunner
from autocoder.common.wrap_llm_hint.utils import extract_content_from_text, has_hint_in_text
from loguru import logger

class TerminalRunner(BaseRunner):
    """
    在终端环境中运行代理，提供格式化输出和交互式显示。
    
    这个运行器使用 Rich 库来格式化终端输出，处理各种代理事件，
    并以用户友好的方式在终端中显示。
    """
    
    def _safe_console_print(self, console: Console, renderable, fallback_content: Optional[str] = None, error_prefix: str = "Rich display"):
        """
        安全地在控制台打印内容，如果Rich markup失败则回退到纯文本。
        
        Args:
            console: Rich Console对象
            renderable: 要渲染的Rich对象（如Panel、Markdown等）
            fallback_content: 回退时显示的内容，如果为None则从renderable中提取
            error_prefix: 错误日志的前缀
        """
        try:
            console.print(renderable)
        except Exception as display_error:
            logger.warning(f"{error_prefix} error, falling back to plain text: {display_error}")
            
            # 如果没有提供fallback_content，尝试从renderable中提取
            if fallback_content is None:
                if hasattr(renderable, 'renderable') and hasattr(renderable.renderable, 'markup'):
                    # Panel with Markdown
                    fallback_content = str(renderable.renderable.markup)
                elif hasattr(renderable, 'renderable'):
                    # Panel with other content
                    fallback_content = str(renderable.renderable)
                else:
                    fallback_content = str(renderable)
            
            # 转义Rich markup字符
            safe_content = fallback_content.replace('[', '\\[').replace(']', '\\]')
            
            # 如果原来是Panel，保持Panel结构
            if hasattr(renderable, 'title') and hasattr(renderable, 'border_style'):
                console.print(Panel(
                    safe_content,
                    title=renderable.title,
                    border_style=renderable.border_style,
                    title_align=getattr(renderable, 'title_align', 'center')
                ))
            else:
                console.print(safe_content)
    
    def run(self, request: AgenticEditRequest) -> str:
        """
        Runs the agentic edit process based on the request and displays
        the interaction streamingly in the terminal using Rich.
        """        
        self.attempt_result = ""
        console = Console()
        source_dir = self.args.source_dir or "."
        project_name = os.path.basename(os.path.abspath(source_dir))

        console.rule(f"[bold cyan]Starting Agentic Edit: {project_name}[/]")
        console.print(Panel(
            f"[bold]{get_message('/agent/edit/user_query')}:[/bold]\n{request.user_input}", title=get_message("/agent/edit/objective"), border_style="blue"))

        # 用于累计TokenUsageEvent数据
        accumulated_token_usage = {
            "model_name": "",
            "input_tokens": 0,
            "output_tokens": 0,
            "input_cost": 0.0,
            "output_cost": 0.0
        }

        try:
            self.apply_pre_changes()
            event_stream = self.analyze(request)
            for event in event_stream:
                if isinstance(event, ConversationIdEvent):
                    console.print(f"[dim]Conversation ID: {event.conversation_id}[/dim]")
                    continue
                if isinstance(event, TokenUsageEvent):
                    last_meta: SingleOutputMeta = event.usage
                    # Get model info for pricing
                    model_name = ",".join(llm_utils.get_llm_names(self.llm))
                    model_info = llm_utils.get_model_info(
                        model_name, self.args.product_mode) or {}
                    input_price = model_info.get(
                        "input_price", 0.0) if model_info else 0.0
                    output_price = model_info.get(
                        "output_price", 0.0) if model_info else 0.0

                    # Calculate costs
                    input_cost = (last_meta.input_tokens_count *
                                  input_price) / 1000000  # Convert to millions
                    # Convert to millions
                    output_cost = (
                        last_meta.generated_tokens_count * output_price) / 1000000

                    # 添加日志记录
                    logger.info(f"Token Usage: Model={model_name}, Input Tokens={last_meta.input_tokens_count}, Output Tokens={last_meta.generated_tokens_count}, Input Cost=${input_cost:.6f}, Output Cost=${output_cost:.6f}")

                    # 累计token使用情况
                    accumulated_token_usage["model_name"] = model_name
                    accumulated_token_usage["input_tokens"] += last_meta.input_tokens_count
                    accumulated_token_usage["output_tokens"] += last_meta.generated_tokens_count
                    accumulated_token_usage["input_cost"] += input_cost
                    accumulated_token_usage["output_cost"] += output_cost
                    
                elif isinstance(event, WindowLengthChangeEvent):
                    # 显示当前会话的token数量
                    logger.info(f"当前会话总 tokens: {event.tokens_used}")
                    if event.tokens_used > event.pruned_tokens_used:
                        console.print(f"[dim]conversation tokens: {event.tokens_used} -> {event.pruned_tokens_used} (conversation round: {event.conversation_round})[/dim]")
                    else:
                        console.print(f"[dim]conversation tokens: {event.tokens_used} (conversation round: {event.conversation_round})[/dim]")

                    # 无论是否剪裁，都显示醒目的等待提示，让用户知道 Agent 正在长时间思考
                    thinking_notice = get_message("agent_thinking_notice")
                    console.print(f"\n[bold yellow]{thinking_notice}[/bold yellow]\n")
                    
                elif isinstance(event, LLMThinkingEvent):
                    # Render thinking within a less prominent style, maybe grey?
                    console.print(f"[grey50]{event.text}[/grey50]", end="")
                elif isinstance(event, LLMOutputEvent):
                    # Print regular LLM output, potentially as markdown if needed later
                    console.print(event.text, end="")
                elif isinstance(event, ToolCallEvent):
                    # Skip displaying AttemptCompletionTool's tool call
                    if isinstance(event.tool, AttemptCompletionTool):
                        continue  # Do not display AttemptCompletionTool tool call

                    # Special handling for ConversationMessageIds tools - only show compacting message
                    if isinstance(event.tool, (ConversationMessageIdsWriteTool, ConversationMessageIdsReadTool)):
                        # Use internationalization module to get the compacting message
                        compacting_message = get_message("conversation_compacting")
                        compacting_title = get_message("conversation_compacting_title")
                        
                        self._safe_console_print(
                            console,
                            Panel(f"[dim]{compacting_message}[/dim]", title=f"🗜️ {compacting_title}", border_style="yellow", title_align="left"),
                            fallback_content=compacting_message,
                            error_prefix="Compacting display"
                        )
                        continue

                    # Get the descriptive title for the tool
                    title = get_tool_title(event.tool)
                    
                    # Use the new internationalized display function
                    display_content = get_tool_display_message(event.tool)
                    
                    # Use cyan border for todo tools, blue for others
                    if isinstance(event.tool, (TodoReadTool, TodoWriteTool)):
                        border_style = "cyan"
                    else:
                        border_style = "blue"
                    
                    self._safe_console_print(
                        console,
                        Panel(display_content, title=f"📝 {title}", border_style=border_style, title_align="left"),
                        fallback_content=str(display_content),
                        error_prefix="Tool display"
                    )
                    
                elif isinstance(event, ToolResultEvent):
                    # Skip displaying AttemptCompletionTool's result
                    if event.tool_name == "AttemptCompletionTool":
                        continue  # Do not display AttemptCompletionTool result

                    if event.tool_name == "PlanModeRespondTool":
                        continue

                    # Skip displaying ConversationMessageIds tools' results - they are handled by the compacting message
                    if event.tool_name in ["ConversationMessageIdsWriteTool", "ConversationMessageIdsReadTool"]:
                        continue

                    result = event.result
                    
                    # Use friendly result title instead of tool name
                    result_title = get_tool_result_title(event.tool_name, result.success)
                    title_icon = "✅" if result.success else "❌"
                    title = f"{title_icon} {result_title}"
                    border_style = "green" if result.success else "red"
                    
                    # Special handling for TodoReadTool and TodoWriteTool
                    if event.tool_name in ["TodoReadTool", "TodoWriteTool","SessionStartTool","SessionInteractiveTool","SessionStopTool"]:
                        # For todo tools, display content directly without syntax highlighting
                        if result.content:
                            # The content is already nicely formatted by the resolver
                            self._safe_console_print(
                                console,
                                Panel(result.content, title=title, border_style=border_style, title_align="left"),
                                fallback_content=str(result.content),
                                error_prefix="Todo content display"
                            )
                        else:
                            # If no content, just show the message
                            status_message = f"[bold]Status:[/bold] {'Success' if result.success else 'Failure'}\n[bold]Message:[/bold] {result.message}"
                            fallback_message = f"Status: {'Success' if result.success else 'Failure'}\nMessage: {result.message}"
                            self._safe_console_print(
                                console,
                                Panel(status_message, title=title, border_style=border_style, title_align="left"),
                                fallback_content=fallback_message,
                                error_prefix="Todo message display"
                            )
                        continue  # Skip the rest of the processing for todo tools
                    
                    # Regular processing for other tools
                    base_content = f"[bold]Status:[/bold] {'Success' if result.success else 'Failure'}"
                    base_content += f"\n[bold]Message:[/bold] {result.message}"

                    def _format_content(content):
                        if len(content) > 200:
                            return f"{content[:100]}\n...\n{content[-100:]}"
                        else:
                            return content

                    # Prepare panel for base info first
                    panel_content = [base_content]
                    syntax_content = None

                    if result.content is not None:
                        content_str = ""
                        try:
                            # Remove hints from content before processing
                            processed_content = result.content
                            if isinstance(result.content, str) and has_hint_in_text(result.content):
                                processed_content = extract_content_from_text(result.content)
                            
                            if isinstance(processed_content, (dict, list)):
                                if not processed_content:
                                    continue                                
                                content_str = json.dumps(
                                    processed_content, indent=2, ensure_ascii=False)
                                syntax_content = Syntax(
                                    content_str, "json", theme="default", line_numbers=False)
                            elif isinstance(processed_content, str) and ('\n' in processed_content or processed_content.strip().startswith('<')):
                                # Heuristic for code or XML/HTML
                                lexer = "python"  # Default guess
                                if event.tool_name == "ReadFileTool" and isinstance(event.result.message, str):
                                    # Try to guess lexer from file extension in message
                                    if ".py" in event.result.message:
                                        lexer = "python"
                                    elif ".js" in event.result.message:
                                        lexer = "javascript"
                                    elif ".ts" in event.result.message:
                                        lexer = "typescript"
                                    elif ".html" in event.result.message:
                                        lexer = "html"
                                    elif ".css" in event.result.message:
                                        lexer = "css"
                                    elif ".json" in event.result.message:
                                        lexer = "json"
                                    elif ".xml" in event.result.message:
                                        lexer = "xml"
                                    elif ".md" in event.result.message:
                                        lexer = "markdown"
                                    else:
                                        lexer = "text"  # Fallback lexer
                                elif event.tool_name == "ExecuteCommandTool":
                                    lexer = "shell"
                                else:
                                    lexer = "text"

                                syntax_content = Syntax(
                                    _format_content(processed_content), lexer, theme="default", line_numbers=True)
                            else:
                                content_str = str(processed_content)
                                # Append simple string content directly
                                panel_content.append(
                                    _format_content(content_str))
                        except Exception as e:
                            logger.warning(
                                f"Error formatting tool result content: {e}")
                            panel_content.append(
                                # Fallback
                                _format_content(str(result.content)))

                    # Print the base info panel with error handling for Rich markup
                    panel_content_str = "\n".join(panel_content)
                    self._safe_console_print(
                        console,
                        Panel(panel_content_str, title=title, border_style=border_style, title_align="left"),
                        fallback_content=panel_content_str,
                        error_prefix="Tool result panel"
                    )
                    
                    # Print syntax highlighted content separately if it exists
                    if syntax_content:
                        content_fallback = f"[bold]Content:[/bold]\n{result.content}"
                        self._safe_console_print(
                            console,
                            syntax_content,
                            fallback_content=content_fallback,
                            error_prefix="Syntax highlighting"
                        )
                            
                elif isinstance(event, PlanModeRespondEvent):
                    self._safe_console_print(
                        console,
                        Panel(Markdown(event.completion.response), title="🏁 Task Completion", border_style="green", title_align="left"),
                        fallback_content=event.completion.response,
                        error_prefix="Plan mode response"
                    )

                elif isinstance(event, CompletionEvent):
                    # 在这里完成实际合并
                    try:
                        self.apply_changes()
                    except Exception as e:
                        logger.exception(
                            f"Error merging shadow changes to project: {e}")

                    self._safe_console_print(
                        console,
                        Panel(Markdown(event.completion.result), title="🏁 Task Completion", border_style="green", title_align="left"),
                        fallback_content=event.completion.result,
                        error_prefix="Task completion"
                    )
                    self.attempt_result = event.completion.result
                    if event.completion.command:
                        console.print(
                            f"[dim]Suggested command:[/dim] [bold cyan]{event.completion.command}[/]")
                elif isinstance(event, ErrorEvent):
                    console.print(Panel(
                        f"[bold red]Error:[/bold red] {event.message}", title="🔥 Error", border_style="red", title_align="left"))

                time.sleep(0.1)  # Small delay for better visual flow

            # 在处理完所有事件后打印累计的token使用情况
            if accumulated_token_usage["input_tokens"] > 0:
                self.printer.print_in_terminal(
                    "code_generation_complete",
                    duration=0.0,
                    input_tokens=accumulated_token_usage["input_tokens"],
                    output_tokens=accumulated_token_usage["output_tokens"],
                    input_cost=accumulated_token_usage["input_cost"],
                    output_cost=accumulated_token_usage["output_cost"],
                    speed=0.0,
                    model_names=accumulated_token_usage["model_name"],
                    sampling_count=1
                )            
                
        except Exception as e:
            # 在处理异常时也打印累计的token使用情况
            if accumulated_token_usage["input_tokens"] > 0:
                self.printer.print_in_terminal(
                    "code_generation_complete",
                    duration=0.0,
                    input_tokens=accumulated_token_usage["input_tokens"],
                    output_tokens=accumulated_token_usage["output_tokens"],
                    input_cost=accumulated_token_usage["input_cost"],
                    output_cost=accumulated_token_usage["output_cost"],
                    speed=0.0,
                    model_names=accumulated_token_usage["model_name"],
                    sampling_count=1
                )
                
            logger.exception(
                "An unexpected error occurred during agent execution:")
            console.print(Panel(
                f"[bold red]FATAL ERROR:[/bold red]\n{str(e)}", title="🔥 System Error", border_style="red"))
            raise e
        finally:
            console.rule("[bold cyan]Agentic Edit Finished[/]")

        return self.attempt_result    
