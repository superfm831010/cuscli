"""
Terminal V3 工具显示模块
提供简洁友好的工具调用展示，类似 IDE 风格的简化显示
"""

from pathlib import Path
from typing import Optional
from autocoder.common.v2.agent.agentic_edit_types import (
    BaseTool,
    ReadFileTool,
    WriteToFileTool,
    ReplaceInFileTool,
    ExecuteCommandTool,
    ListFilesTool,
    SearchFilesTool,
    ListCodeDefinitionNamesTool,
    AskFollowupQuestionTool,
    UseMcpTool,
    AttemptCompletionTool,
    TodoReadTool,
    TodoWriteTool,
    UseRAGTool,
    ACModReadTool,
    ACModWriteTool,
    ACModListTool,
    CountTokensTool,
    SessionStartTool,
    SessionInteractiveTool,
    SessionStopTool,
    ConversationMessageIdsWriteTool,
    ConversationMessageIdsReadTool,
    RunNamedSubagentsTool,
)


def get_short_path(path: str, max_length: int = 50) -> str:
    """
    获取路径的简短版本

    Args:
        path: 完整路径
        max_length: 最大长度

    Returns:
        简化后的路径
    """
    if len(path) <= max_length:
        return path

    # 尝试只显示文件名
    p = Path(path)
    if len(p.name) <= max_length:
        return p.name

    # 如果文件名也太长，截断
    return "..." + path[-(max_length - 3) :]


def get_tool_simple_display(tool: BaseTool) -> str:
    """
    获取工具的简洁显示文本（类似 IDE 风格）

    Args:
        tool: 工具实例

    Returns:
        简洁的工具描述字符串
    """
    try:
        if isinstance(tool, ReadFileTool):
            path = get_short_path(tool.path)
            if tool.start_line and tool.end_line:
                return f"Read({path}:{tool.start_line}-{tool.end_line})"
            elif tool.query:
                return f"Search({path}, '{tool.query[:30]}...')"
            return f"Read({path})"

        elif isinstance(tool, WriteToFileTool):
            path = get_short_path(tool.path)
            mode = "Append" if tool.mode == "append" else "Write"
            lines = len(tool.content.splitlines())
            return f"{mode}({path}, {lines} lines)"

        elif isinstance(tool, ReplaceInFileTool):
            path = get_short_path(tool.path)
            # 计算修改的行数
            changes = len(
                [line for line in tool.diff.splitlines() if line.startswith(("+", "-"))]
            )
            return f"Edit({path}, ~{changes} changes)"

        elif isinstance(tool, ExecuteCommandTool):
            cmd = tool.command
            if len(cmd) > 50:
                cmd = cmd[:47] + "..."
            bg = " [bg]" if tool.background else ""
            return f"Run({cmd}){bg}"

        elif isinstance(tool, ListFilesTool):
            path = get_short_path(tool.path)
            mode = "recursive" if tool.recursive else "flat"
            return f"List({path}, {mode})"

        elif isinstance(tool, SearchFilesTool):
            path = get_short_path(tool.path)
            pattern = tool.file_pattern or "*"
            regex = tool.regex[:30] if len(tool.regex) > 30 else tool.regex
            return f"Search({path}, pattern={pattern}, regex='{regex}')"

        elif isinstance(tool, ListCodeDefinitionNamesTool):
            path = get_short_path(tool.path)
            return f"ListDefinitions({path})"

        elif isinstance(tool, AskFollowupQuestionTool):
            question = tool.question[:50]
            if len(tool.question) > 50:
                question += "..."
            options = f", {len(tool.options)} options" if tool.options else ""
            return f"Ask('{question}'{options})"

        elif isinstance(tool, UseMcpTool):
            return f"MCP({tool.server_name}.{tool.tool_name})"

        elif isinstance(tool, UseRAGTool):
            query = tool.query[:40]
            if len(tool.query) > 40:
                query += "..."
            return f"RAG({tool.server_name}, '{query}')"

        elif isinstance(tool, TodoReadTool):
            return "TodoList()"

        elif isinstance(tool, TodoWriteTool):
            action_map = {
                "create": "Create",
                "update": "Update",
                "delete": "Delete",
                "complete": "Complete",
            }
            action = action_map.get(tool.action, tool.action)
            if tool.task_id:
                return f"Todo.{action}(#{tool.task_id})"
            return f"Todo.{action}()"

        elif isinstance(tool, ACModReadTool):
            path = get_short_path(tool.path)
            return f"ACMod.Read({path})"

        elif isinstance(tool, ACModWriteTool):
            path = get_short_path(tool.path)
            changes = len(
                [line for line in tool.diff.splitlines() if line.startswith(("+", "-"))]
            )
            return f"ACMod.Write({path}, ~{changes} changes)"

        elif isinstance(tool, ACModListTool):
            if tool.path:
                path = get_short_path(tool.path)
                return f"ACMod.List({path})"
            return "ACMod.List()"

        elif isinstance(tool, CountTokensTool):
            path = get_short_path(tool.path)
            mode = "recursive" if tool.recursive else "single"
            return f"CountTokens({path}, {mode})"

        elif isinstance(tool, SessionStartTool):
            cmd = tool.command
            if len(cmd) > 40:
                cmd = cmd[:37] + "..."
            return f"Session.Start('{cmd}')"

        elif isinstance(tool, SessionInteractiveTool):
            input_text = tool.input[:30]
            if len(tool.input) > 30:
                input_text += "..."
            return f"Session.Send({tool.session_id}, '{input_text}')"

        elif isinstance(tool, SessionStopTool):
            force = " [force]" if tool.force else ""
            return f"Session.Stop({tool.session_id}){force}"

        elif isinstance(tool, ConversationMessageIdsReadTool):
            return "ConversationIds.Read()"

        elif isinstance(tool, ConversationMessageIdsWriteTool):
            return f"ConversationIds.{tool.action.capitalize()}()"

        elif isinstance(tool, RunNamedSubagentsTool):
            # 尝试统计子代理数量
            import re

            agents_count = len(re.findall(r'"name"\s*:', tool.subagents))
            if agents_count == 0:
                agents_count = len(re.findall(r"name:\s*", tool.subagents))
            if agents_count > 0:
                return f"RunSubagents({agents_count} agents)"
            return "RunSubagents()"

        elif isinstance(tool, AttemptCompletionTool):
            result = tool.result[:50] if tool.result else "Done"
            if tool.result and len(tool.result) > 50:
                result += "..."
            return f"Complete('{result}')"

        else:
            # 未知工具的通用显示
            tool_name = type(tool).__name__.replace("Tool", "")
            return f"{tool_name}(...)"

    except Exception as e:
        # 出错时返回通用格式
        tool_name = type(tool).__name__
        return f"{tool_name}(error: {str(e)[:30]})"


def get_tool_result_display(
    tool_name: str, success: bool, message: Optional[str] = None
) -> str:
    """
    获取工具结果的简洁显示

    Args:
        tool_name: 工具名称（如 ReadFileToolResolver）
        success: 是否成功
        message: 结果消息（可选）

    Returns:
        简洁的结果描述
    """
    # 清理工具名称
    base_name = tool_name
    if base_name.endswith("ToolResolver"):
        base_name = base_name[:-12]
    elif base_name.endswith("Resolver"):
        base_name = base_name[:-8]
    if base_name.endswith("Tool"):
        base_name = base_name[:-4]

    status = "✓" if success else "✗"

    if message and len(message) < 50:
        return f"{status} {base_name}: {message}"
    elif message:
        return f"{status} {base_name}: {message[:47]}..."
    else:
        return f"{status} {base_name}"
