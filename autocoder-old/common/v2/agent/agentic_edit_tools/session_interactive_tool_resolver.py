"""
Session interactive tool resolver for interacting with active sessions.
"""

from typing import Optional
from loguru import logger

from autocoder.common.v2.agent.agentic_edit_tools.base_tool_resolver import BaseToolResolver
from autocoder.common.v2.agent.agentic_edit_types import SessionInteractiveTool, ToolResult
from autocoder.common.shell_commands import get_session_manager
from autocoder.common import AutoCoderArgs

import typing
if typing.TYPE_CHECKING:
    from autocoder.common.v2.agent.agentic_edit import AgenticEdit


class SessionInteractiveToolResolver(BaseToolResolver):
    """Resolver for interacting with active command sessions."""

    def __init__(self, agent: Optional['AgenticEdit'], tool: SessionInteractiveTool, args: AutoCoderArgs):
        super().__init__(agent, tool, args)
        self.tool: SessionInteractiveTool = tool
        self.session_manager = get_session_manager()

    def resolve(self) -> ToolResult:
        """
        Send input to a session and read output.

        Returns:
            ToolResult with session output
        """
        session_id = self.tool.session_id
        input_text = self.tool.input
        read_timeout = self.tool.read_timeout
        max_bytes = self.tool.max_bytes
        expect_prompt = self.tool.expect_prompt
        prompt_regex = self.tool.prompt_regex

        logger.debug(
            f"Sending input to session {session_id}: {input_text[:50]}...")

        # Send input to session
        result = self.session_manager.send_input(
            session_id=session_id,
            input_text=input_text,
            read_timeout=read_timeout,
            max_bytes=max_bytes,
            expect_prompt=expect_prompt,
            prompt_regex=prompt_regex
        )

        if result.success:
            # Handle both dict and string content
            output = ''
            raw_output = ''
            cleaned_length = 0
            
            if isinstance(result.content, dict):
                output = result.content.get('output', '')
                raw_output = result.content.get('raw_output', '')
                cleaned_length = result.content.get('cleaned_length', 0)
            elif isinstance(result.content, str):
                output = result.content
                raw_output = result.content
                cleaned_length = len(result.content)

            logger.debug(
                f"Session {session_id} output: {len(output)} characters")

            # Format content as readable text
            if output.strip():
                lines = output.strip().split('\n')
                line_count = len(lines)

                # Create formatted text output
                formatted_content = f"""Session ID: {session_id}
Input: {input_text}
Output ({line_count} lines):
{'-' * 50}
{output}
{'-' * 50}
Status: Success - Received {line_count} lines of output"""

                return ToolResult(
                    success=True,
                    message=f"Input sent successfully. Received {line_count} lines of output",
                    content=formatted_content
                )
            else:
                # No output case
                formatted_content = f"""Session ID: {session_id}
Input: {input_text}
Output: (no output)
Status: Success - No output received"""

                return ToolResult(
                    success=True,
                    message="Input sent successfully. No output received.",
                    content=formatted_content
                )
        else:
            # Error case - format as text as well
            formatted_content = f"""Session ID: {session_id}
Input: {input_text}
Status: Error - {result.message}"""
            
            logger.error(
                f"Failed to interact with session {session_id}: {result.message}")
            
            return ToolResult(
                success=False,
                message=result.message,
                content=formatted_content
            )
