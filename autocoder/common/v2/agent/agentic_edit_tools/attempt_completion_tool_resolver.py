from typing import Dict, Any, Optional
from autocoder.common.v2.agent.agentic_edit_tools.base_tool_resolver import BaseToolResolver
from autocoder.common.v2.agent.agentic_edit_types import AttemptCompletionTool, ToolResult # Import ToolResult from types
from loguru import logger
import typing
from autocoder.common import AutoCoderArgs

if typing.TYPE_CHECKING:
    from autocoder.common.v2.agent.agentic_edit import AgenticEdit

class AttemptCompletionToolResolver(BaseToolResolver):
    def __init__(self, agent: Optional['AgenticEdit'], tool: AttemptCompletionTool, args: AutoCoderArgs):
        super().__init__(agent, tool, args)
        self.tool: AttemptCompletionTool = tool # For type hinting

    def resolve(self) -> ToolResult:
        """
        Packages the completion result and optional command to signal task completion.
        """
        result_text = self.tool.result
        command = self.tool.command

        logger.info(f"Resolving AttemptCompletionTool: Result='{result_text[:100]}...', Command='{command}'")

        if not result_text:
             return ToolResult(success=False, message="Error: Completion result cannot be empty.")

        # The actual presentation of the result happens outside the resolver.
        result_content = {
            "result": result_text,
            "command": command
        }

        # Indicate success in preparing the completion data
        return ToolResult(success=True, message="Task completion attempted.", content=result_content)
