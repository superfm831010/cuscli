"""
工具显示模块，提供格式化工具调用信息的功能。

这个模块负责生成用户友好的、国际化的工具调用显示信息，
主要用于终端运行器中展示工具调用的详细信息。
"""

import json
import yaml
import re
from typing import Dict, Callable, Type, Tuple

# Import the messages module to ensure auto-registration
from autocoder.common.international import get_message, get_message_with_format
from autocoder.common.v2.agent.agentic_edit_types import (
    BaseTool,
    ReadFileTool, WriteToFileTool, ReplaceInFileTool, ExecuteCommandTool,
    ListFilesTool, SearchFilesTool, ListCodeDefinitionNamesTool,
    AskFollowupQuestionTool, UseMcpTool, AttemptCompletionTool,
    TodoReadTool, TodoWriteTool, UseRAGTool, ACModReadTool, ACModWriteTool, ACModListTool,
    CountTokensTool, SessionStartTool, SessionInteractiveTool, SessionStopTool,
    ConversationMessageIdsWriteTool, ConversationMessageIdsReadTool, RunNamedSubagentsTool
)


def get_tool_display_message(tool: BaseTool) -> str:
    """
    生成工具调用的用户友好、国际化的字符串表示。

    Args:
        tool: 工具实例（Pydantic模型）。

    Returns:
        用于在终端中显示的格式化字符串。
    """
    tool_type = type(tool)

    # 准备特定于每种工具类型的上下文
    try:
        if isinstance(tool, ReadFileTool):
            return get_message_with_format("tool_display.read_file", path=tool.path)
            
        elif isinstance(tool, WriteToFileTool):
            snippet = tool.content[:150]
            return get_message_with_format(
                "tool_display.write_to_file",
                path=tool.path,
                content_snippet=snippet,
                ellipsis='...' if len(tool.content) > 150 else ''
            )
            
        elif isinstance(tool, ReplaceInFileTool):
            return get_message_with_format(
                "tool_display.replace_in_file",
                path=tool.path,
                diff_snippet=tool.diff,
                ellipsis=''
            )
            
        elif isinstance(tool, ExecuteCommandTool):
            return get_message_with_format(
                "tool_display.execute_command",
                command=tool.command,
                requires_approval=tool.requires_approval
            )
            
        elif isinstance(tool, ListFilesTool):
            recursive_text = get_message("tool_text.recursive") if tool.recursive else get_message("tool_text.top_level")
            return get_message_with_format(
                "tool_display.list_files",
                path=tool.path,
                recursive_text=recursive_text
            )
            
        elif isinstance(tool, SearchFilesTool):
            return get_message_with_format(
                "tool_display.search_files",
                path=tool.path,
                file_pattern=tool.file_pattern or '*',
                regex=tool.regex
            )
            
        elif isinstance(tool, ListCodeDefinitionNamesTool):
            return get_message_with_format("tool_display.list_code_definition_names", path=tool.path)
            
        elif isinstance(tool, AskFollowupQuestionTool):
            options_text = ""
            if tool.options:
                options_list = "\n".join([f"- {opt}" for opt in tool.options])
                options_label = get_message("tool_text.options")
                options_text = f"[dim]{options_label}[/dim]\n{options_list}"
            
            return get_message_with_format(
                "tool_display.ask_followup_question",
                question=tool.question,
                options_text=options_text
            )
            
        elif isinstance(tool, UseMcpTool):
            args_str = tool.query
            snippet = args_str[:100]
            return get_message_with_format(
                "tool_display.use_mcp",
                server_name=tool.server_name,
                tool_name=tool.tool_name,
                arguments_snippet=snippet,
                ellipsis='...' if len(args_str) > 100 else ''
            )
            
        elif isinstance(tool, TodoReadTool):
            return get_message("tool_display.todo_read")
            
        elif isinstance(tool, UseRAGTool):
            return get_message_with_format(
                "tool_display.use_rag",
                server_name=tool.server_name,
                query=tool.query
            )
            
        elif isinstance(tool, ACModReadTool):
            return get_message_with_format("tool_display.ac_mod_read", path=tool.path)
            
        elif isinstance(tool, ACModWriteTool):
            diff_snippet = tool.diff[:300]
            return get_message_with_format(
                "tool_display.ac_mod_write",
                path=tool.path,
                diff_snippet=diff_snippet,
                ellipsis='...' if len(tool.diff) > 300 else ''
            )
            
        elif isinstance(tool, ACModListTool):
            if tool.path:
                search_text = get_message_with_format("tool_text.search_path") + f" [green]{tool.path}[/]"
            else:
                project_root = get_message("tool_text.project_root")
                all_text = get_message("tool_text.all")
                search_text = f"[dim]{get_message('tool_text.search_path')}[/dim] [green]{project_root}[/]{all_text}"
            
            return get_message_with_format("tool_display.ac_mod_list", search_text=search_text)
            
        elif isinstance(tool, CountTokensTool):
            recursive_text = get_message("tool_text.yes") if tool.recursive else get_message("tool_text.no")
            summary_text = get_message("tool_text.yes") if tool.include_summary else get_message("tool_text.no")
            
            return get_message_with_format(
                "tool_display.count_tokens",
                path=tool.path,
                recursive_text=recursive_text,
                summary_text=summary_text
            )
            
        elif isinstance(tool, TodoWriteTool):
            return _format_todo_write_tool(tool)
            
        elif isinstance(tool, SessionStartTool):
            timeout_text = ""
            if tool.timeout:
                timeout_label = get_message("tool_text.timeout")
                timeout_text = f"[dim]{timeout_label}[/dim] {tool.timeout}s\n"
            
            cwd_text = ""
            if tool.cwd:
                cwd_label = get_message("tool_text.working_directory")
                cwd_text = f"[dim]{cwd_label}[/dim] [green]{tool.cwd}[/]\n"
            
            env_text = ""
            if tool.env:
                env_count = len(tool.env)
                env_label = get_message("tool_text.environment_variables")
                variables_label = get_message("tool_text.variables")
                env_text = f"[dim]{env_label}:[/dim] {env_count} {variables_label}\n"
            
            return get_message_with_format(
                "tool_display.session_start",
                command=tool.command,
                timeout_text=timeout_text,
                cwd_text=cwd_text,
                env_text=env_text
            )
            
        elif isinstance(tool, SessionInteractiveTool):
            input_snippet = tool.input[:100]
            prompt_text = ""
            if tool.expect_prompt and tool.prompt_regex:
                prompt_label = get_message("tool_text.expected_prompt")
                prompt_text = f"[dim]{prompt_label}[/dim] [yellow]{tool.prompt_regex}[/]"
            
            return get_message_with_format(
                "tool_display.session_interactive",
                session_id=tool.session_id,
                input_snippet=input_snippet,
                ellipsis='...' if len(tool.input) > 100 else '',
                prompt_text=prompt_text
            )
            
        elif isinstance(tool, SessionStopTool):
            force_text = get_message("tool_text.yes") if tool.force else get_message("tool_text.no")
            
            return get_message_with_format(
                "tool_display.session_stop",
                session_id=tool.session_id,
                force_text=force_text
            )
            
        elif isinstance(tool, ConversationMessageIdsReadTool):
            return get_message("tool_display.conversation_message_ids_read")
            
        elif isinstance(tool, ConversationMessageIdsWriteTool):
            message_ids_snippet = tool.message_ids[:100]
            return get_message_with_format(
                "tool_display.conversation_message_ids_write",
                action=tool.action,
                message_ids_snippet=message_ids_snippet,
                ellipsis='...' if len(tool.message_ids) > 100 else ''
            )
            
        elif isinstance(tool, RunNamedSubagentsTool):
            return _format_run_named_subagents_tool(tool)
            
        else:
            # 未专门处理的工具的通用上下文
            return get_message_with_format(
                "tool_display.unknown_tool",
                tool_type=tool_type.__name__,
                data=tool.model_dump_json(indent=2)
            )

    except Exception as e:
        # 格式化错误时的回退处理
        return get_message_with_format(
            "tool_display.format_error",
            tool_type=tool_type.__name__,
            error=str(e),
            template="unknown",
            context=str(tool.model_dump())
        )


def _format_todo_write_tool(tool: TodoWriteTool) -> str:
    """格式化TodoWriteTool的显示"""
    task_details = ""

    # For create action, show the tasks being created
    if tool.action == "create" and tool.content:
        # Parse task content to show individual tasks
        task_pattern = r'<task>(.*?)</task>'
        task_matches = re.findall(task_pattern, tool.content, re.DOTALL)

        if task_matches:
            task_list = []
            for i, task_content in enumerate(task_matches, 1):
                task_content = task_content.strip()
                if task_content:
                    task_list.append(f"   {i}. {task_content}")

            if task_list:
                tasks_label = get_message("tool_text.tasks_to_create")
                task_details += f"[dim]{tasks_label}[/dim]\n"
                task_details += "\n".join(task_list) + "\n"
        else:
            # Fallback to showing raw content if no <task> tags
            lines = tool.content.strip().split('\n')
            task_list = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('<'):
                    # Remove common prefixes like "1.", "- ", "* ", etc.
                    cleaned_line = re.sub(r'^[0-9]+\.\s*|-\s*|\*\s*', '', line)
                    if cleaned_line:
                        task_list.append(f"   • {cleaned_line}")

            if task_list:
                tasks_label = get_message("tool_text.tasks_to_create")
                task_details += f"[dim]{tasks_label}[/dim]\n"
                task_details += "\n".join(task_list) + "\n"

    # For other actions, show relevant details
    if tool.task_id:
        task_id_label = get_message("tool_text.task_id")
        task_details += f"[dim]{task_id_label}[/dim] [yellow]{tool.task_id}[/]\n"

    if tool.content and tool.action != "create":
        content_snippet = tool.content[:200]
        ellipsis = "..." if len(tool.content) > 200 else ""
        content_label = get_message("tool_text.content")
        task_details += f"[dim]{content_label}[/dim] {content_snippet}{ellipsis}\n"

    if tool.priority:
        priority_icons = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        priority_icon = priority_icons.get(tool.priority, "⚪")
        priority_display = get_message(f"tool_text.priority.{tool.priority}")
        priority_label = get_message("tool_text.priority")
        task_details += f"[dim]{priority_label}[/dim] {priority_icon} {priority_display}\n"

    if tool.status:
        status_icons = {"pending": "⏳", "in_progress": "🔄", "completed": "✅"}
        status_icon = status_icons.get(tool.status, "❓")
        status_display = get_message(f"tool_text.status.{tool.status}")
        status_label = get_message("tool_text.status")
        task_details += f"[dim]{status_label}[/dim] {status_icon} {status_display}\n"

    # Notes text with better formatting
    notes_text = ""
    if tool.notes:
        notes_snippet = tool.notes[:300]
        ellipsis = "..." if len(tool.notes) > 300 else ""
        notes_label = get_message("tool_text.notes")
        notes_text = f"\n[dim]{notes_label}[/dim] 📝 {notes_snippet}{ellipsis}"

    # Add action summary at the end for better context
    action_summary = ""
    if tool.action == "create":
        task_count = len(re.findall(r'<task>.*?</task>', tool.content, re.DOTALL)) if tool.content else 0
        if task_count == 0 and tool.content:
            # Count lines as tasks if no <task> tags
            lines = [line.strip() for line in tool.content.strip().split('\n') if line.strip()]
            task_count = len(lines)
        total_tasks_label = get_message("tool_text.total_tasks")
        action_summary = f"\n[dim]{total_tasks_label}[/dim] {task_count}"

    return get_message_with_format(
        "tool_display.todo_write",
        task_details=task_details,
        notes_text=notes_text + action_summary
    )


def _format_run_named_subagents_tool(tool: RunNamedSubagentsTool) -> str:
    """格式化RunNamedSubagentsTool的显示"""
    # Parse subagents configuration and extract display info
    try:
        # Try to parse as JSON first
        try:
            subagents_data = json.loads(tool.subagents)
            if isinstance(subagents_data, list):
                execution_mode = "parallel"
                subagents_list = subagents_data
            else:
                execution_mode = "parallel"
                subagents_list = []
        except json.JSONDecodeError:
            # Try to parse as YAML
            try:
                subagents_data = yaml.safe_load(tool.subagents)
                if isinstance(subagents_data, dict):
                    execution_mode = subagents_data.get("mode", "parallel")
                    subagents_list = subagents_data.get("subagents", [])
                elif isinstance(subagents_data, list):
                    execution_mode = "parallel"
                    subagents_list = subagents_data
                else:
                    execution_mode = "unknown"
                    subagents_list = []
            except yaml.YAMLError:
                execution_mode = "unknown"
                subagents_list = []
        
        # Translate execution mode
        execution_mode_display = get_message(f"tool_text.execution_mode.{execution_mode}")
        
        # Build subagent details
        subagent_details = ""
        if subagents_list:
            detail_lines = []
            for i, subagent in enumerate(subagents_list[:3], 1):  # Show max 3 subagents
                if isinstance(subagent, dict):
                    name = subagent.get("name", "unnamed")
                    task = subagent.get("task", "no task specified")
                    # Truncate task if too long
                    task_display = task[:80] + "..." if len(task) > 80 else task
                    
                    agent_label = get_message("tool_text.agent")
                    task_label = get_message("tool_text.task")
                    detail_lines.append(f"  {i}. [green]{name}[/] ({agent_label})")
                    detail_lines.append(f"     [dim]{task_label}:[/dim] {task_display}")
            
            if len(subagents_list) > 3:
                more_count = len(subagents_list) - 3
                more_label = get_message_with_format("tool_text.and_more", count=more_count)
                detail_lines.append(f"  [dim]{more_label}[/dim]")
            
            subagent_details = "\n".join(detail_lines)
        else:
            # No subagents found
            no_agents_msg = get_message("tool_text.no_agents_configured")
            subagent_details = f"[dim]{no_agents_msg}[/dim]"
        
        return get_message_with_format(
            "tool_display.run_named_subagents",
            execution_mode=execution_mode_display,
            subagent_count=len(subagents_list),
            subagent_details=subagent_details
        )
        
    except Exception as e:
        # Fallback to showing raw content if parsing fails
        snippet = tool.subagents[:200]
        ellipsis = "..." if len(tool.subagents) > 200 else ""
        raw_label = get_message("tool_text.raw_config")
        unknown_text = get_message("tool_text.unknown")
        subagent_details = f"[dim]{raw_label}:[/dim] {snippet}{ellipsis}"
        
        return get_message_with_format(
            "tool_display.run_named_subagents",
            execution_mode=unknown_text,
            subagent_count=unknown_text,
            subagent_details=subagent_details
        )


def get_tool_title(tool: BaseTool) -> str:
    """
    获取工具的标题，用于在 Panel 标题中显示。

    Args:
        tool: 工具实例

    Returns:
        适合显示在标题栏的简短描述
    """
    tool_type = type(tool)
    
    # Special handling for TodoWriteTool to show action-specific titles
    if isinstance(tool, TodoWriteTool) and tool.action:
        try:
            return get_message(f"tool_title.todo_write.{tool.action}")
        except:
            pass  # Fall back to generic title

    # Map tool types to message keys
    tool_type_to_key = {
        ReadFileTool: "tool_title.read_file",
        WriteToFileTool: "tool_title.write_to_file",
        ReplaceInFileTool: "tool_title.replace_in_file",
        ExecuteCommandTool: "tool_title.execute_command",
        ListFilesTool: "tool_title.list_files",
        SearchFilesTool: "tool_title.search_files",
        ListCodeDefinitionNamesTool: "tool_title.list_code_definition_names",
        AskFollowupQuestionTool: "tool_title.ask_followup_question",
        UseMcpTool: "tool_title.use_mcp",
        UseRAGTool: "tool_title.use_rag",
        ACModReadTool: "tool_title.ac_mod_read",
        ACModWriteTool: "tool_title.ac_mod_write",
        ACModListTool: "tool_title.ac_mod_list",
        CountTokensTool: "tool_title.count_tokens",
        TodoReadTool: "tool_title.todo_read",
        TodoWriteTool: "tool_title.todo_write",
        SessionStartTool: "tool_title.session_start",
        SessionInteractiveTool: "tool_title.session_interactive",
        SessionStopTool: "tool_title.session_stop",
        ConversationMessageIdsReadTool: "tool_title.conversation_message_ids_read",
        ConversationMessageIdsWriteTool: "tool_title.conversation_message_ids_write",
        RunNamedSubagentsTool: "tool_title.run_named_subagents"
    }
    
    message_key = tool_type_to_key.get(tool_type)
    if message_key:
        try:
            return get_message(message_key)
        except:
            pass  # Fall back to generic title
    
    # Fallback to generic message
    return f"AutoCoder is using {tool_type.__name__}"


def get_tool_result_title(tool_name: str, success: bool) -> str:
    """
    获取工具结果的标题，用于在 Panel 标题中显示。

    Args:
        tool_name: 工具名称（如 TodoWriteToolResolver）
        success: 操作是否成功

    Returns:
        适合显示在结果标题栏的描述
    """
    # Remove "ToolResolver" suffix and "Resolver" suffix to get base name
    base_name = tool_name
    if base_name.endswith("ToolResolver"):
        base_name = base_name[:-12]  # Remove "ToolResolver"
    elif base_name.endswith("Resolver"):
        base_name = base_name[:-8]   # Remove "Resolver"

    # Add "Tool" back if it was part of the resolver name but not the base name
    if not base_name.endswith("Tool"):
        base_name += "Tool"

    # Convert tool name to message key format (e.g., "TodoWriteTool" -> "todo_write")
    # Split camelCase and convert to lowercase with underscores
    tool_key = re.sub(r'(?<!^)(?=[A-Z])', '_', base_name).lower()
    if tool_key.endswith("_tool"):
        tool_key = tool_key[:-5]  # Remove "_tool" suffix

    # Try to get specific message for this tool
    result_type = "success" if success else "failure"
    message_key = f"tool_result.{tool_key}.{result_type}"
    
    try:
        return get_message(message_key)
    except:
        # Fallback to generic messages
        fallback_key = f"tool_result.{result_type}_generic"
        try:
            return get_message(fallback_key)
        except:
            # Final fallback
            if success:
                return "Operation completed successfully"
            else:
                return "Operation failed"
