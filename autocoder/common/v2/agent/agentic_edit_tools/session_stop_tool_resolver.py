"""
Session stop tool resolver for stopping interactive command sessions.
"""

from typing import Optional
from loguru import logger

from autocoder.common.v2.agent.agentic_edit_tools.base_tool_resolver import BaseToolResolver
from autocoder.common.v2.agent.agentic_edit_types import SessionStopTool, ToolResult
from autocoder.common.shell_commands import get_session_manager
from autocoder.common import AutoCoderArgs

import typing
if typing.TYPE_CHECKING:
    from autocoder.common.v2.agent.agentic_edit import AgenticEdit


class SessionStopToolResolver(BaseToolResolver):
    """Resolver for stopping interactive command sessions."""
    
    def __init__(self, agent: Optional['AgenticEdit'], tool: SessionStopTool, args: AutoCoderArgs):
        super().__init__(agent, tool, args)
        self.tool: SessionStopTool = tool
        self.session_manager = get_session_manager()
    
    def resolve(self) -> ToolResult:
        """
        Stop an interactive session.
        
        Returns:
            ToolResult indicating success with formatted text output
        """
        session_id = self.tool.session_id
        force = self.tool.force or False
        
        logger.info(f"Stopping interactive session {session_id} (force={force})")
        
        # Terminate the session
        result = self.session_manager.terminate_session(
            session_id=session_id,
            force=force
        )
        
        # Format the result as readable text and return new ToolResult
        if result.success:
            logger.info(f"Interactive session {session_id} stopped successfully")
            
            # Create formatted text output
            force_text = "Force termination" if force else "Graceful termination"
            content = f"""Session ID: {session_id}
Termination Method: {force_text}
Status: Successfully stopped

✅ Session successfully terminated and cleaned up"""
            
            return ToolResult(
                success=True,
                message=f"Interactive session {session_id} stopped successfully",
                content=content
            )
        else:
            logger.error(f"Failed to stop interactive session {session_id}: {result.message}")
            
            # Create formatted error text
            force_text = "Force termination" if force else "Graceful termination"
            content = f"""Session ID: {session_id}
Termination Method: {force_text}
Status: Failed to stop

❌ Error Message: {result.message}"""
            
            return ToolResult(
                success=False,
                message=result.message,
                content=content
            ) 