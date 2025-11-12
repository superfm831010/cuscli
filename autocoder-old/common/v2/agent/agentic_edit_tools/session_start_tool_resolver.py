"""
Session start tool resolver for starting interactive command sessions.
"""

import time
from typing import Optional
from loguru import logger

from autocoder.common.v2.agent.agentic_edit_tools.base_tool_resolver import BaseToolResolver
from autocoder.common.v2.agent.agentic_edit_types import SessionStartTool, ToolResult
from autocoder.common.shell_commands import get_session_manager
from autocoder.common.v2.agent.agentic_edit_tools.dangerous_command_checker import DangerousCommandChecker
from autocoder.common import AutoCoderArgs

import typing
if typing.TYPE_CHECKING:
    from autocoder.common.v2.agent.agentic_edit import AgenticEdit


class SessionStartToolResolver(BaseToolResolver):
    """Resolver for starting interactive command sessions."""
    
    def __init__(self, agent: Optional['AgenticEdit'], tool: SessionStartTool, args: AutoCoderArgs):
        super().__init__(agent, tool, args)
        self.tool: SessionStartTool = tool
        self.session_manager = get_session_manager()
        self.danger_checker = DangerousCommandChecker()
    
    def resolve(self) -> ToolResult:
        """
        Start a new interactive session.
        
        Returns:
            ToolResult with session information
        """
        command = self.tool.command
        timeout = self.tool.timeout
        cwd = self.tool.cwd or self.args.source_dir
        env = self.tool.env
        
        # Security check for dangerous commands
        if self.args.enable_agentic_dangerous_command_check:
            is_safe, danger_reason = self.danger_checker.check_command_safety(
                command, allow_whitelist_bypass=True)
            
            if not is_safe:
                recommendations = self.danger_checker.get_safety_recommendations(command)
                error_message = f"检测到危险命令: {danger_reason}"
                if recommendations:
                    error_message += f"\n安全建议:\n" + "\n".join(f"- {rec}" for rec in recommendations)
                
                logger.warning(f"阻止启动危险交互式命令: {command}, 原因: {danger_reason}")
                return ToolResult(success=False, message=error_message, content=f"""Command: {command}
Status: Error - Dangerous command detected
Reason: {danger_reason}
Safety Recommendations: {recommendations if recommendations else 'None'}""")
        
        # Create the session
        logger.info(f"Starting interactive session: {command}")
        
        result = self.session_manager.create_session(
            command=command,
            cwd=cwd,
            env=env,
            timeout=timeout,
            use_pexpect=True
        )
        
        if result.success:
            # Extract session_id from content - handle both dict and string content
            session_id = 'unknown'
            if isinstance(result.content, dict):
                session_id = result.content.get('session_id', 'unknown')
            elif isinstance(result.content, str):
                # Try to parse session_id from string if possible
                import re
                match = re.search(r'session_id[:\s]+(\w+)', result.content)
                if match:
                    session_id = match.group(1)
                    
            logger.info(f"Interactive session started successfully: {session_id}")
            
            # Wait 10 seconds for initial output
            logger.debug(f"Waiting 10 seconds for initial output from session {session_id}")
            time.sleep(10)
            
            # Read initial output using progressive method
            initial_output = ""
            try:
                initial_result = self.session_manager.read_output_progressive(
                    session_id=session_id,
                    read_timeout=5,  # Initial timeout of 5 seconds
                    max_bytes=4096,
                    expect_prompt=False,
                    prompt_regex=None
                )
                
                if initial_result.success and initial_result.content:
                    # Handle both dict and string content
                    if isinstance(initial_result.content, dict):
                        initial_output = initial_result.content.get('output', '')
                        read_cycles = initial_result.content.get('read_cycles', 0)
                        total_duration = initial_result.content.get('total_duration', 0)
                    else:
                        initial_output = str(initial_result.content)
                        read_cycles = 0
                        total_duration = 0
                    
                    logger.debug(f"Progressive read completed: {len(initial_output)} characters, "
                               f"{read_cycles} cycles, {total_duration:.1f}s total")
                else:
                    logger.debug("No initial output available")
                    
            except Exception as e:
                logger.warning(f"Failed to read initial output: {e}")
                initial_output = f"Error reading initial output: {e}"
            
            # Format as readable text
            if initial_output.strip():
                lines = initial_output.strip().split('\n')
                line_count = len(lines)
                
                # Extract potential prompt pattern from the last line
                last_line = lines[-1] if lines else ""
                prompt_hint = ""
                if last_line.strip():
                    # Pre-calculate values for the hint
                    clean_last_line = last_line.strip()
                    escaped_prompt = clean_last_line.replace('$', '\\$').replace('>', '\\>').replace('?', '\\?')
                    
                    # Build multi-line prompt hint
                    prompt_hint = (
                        f"\n\n📌 IMPORTANT: The last line appears to be a prompt: '{clean_last_line}'\n"
                        f"   When using session_interactive tool later, consider setting:\n"
                        f"   - expect_prompt: true\n"
                        f"   - prompt_regex: '{escaped_prompt} ?$'\n"
                        f"   \n"
                        f"   💡 TIP: For better output capture, consider using read_output_progressive method\n"
                        f"   which intelligently waits for all content to be available."
                    )
                
                formatted_content = f"""Session ID: {session_id}
Command: {command}
Working Directory: {cwd}
Environment: {env if env else 'Default'}
Initial Output ({line_count} lines):
{'-' * 50}
{initial_output}
{'-' * 50}
Status: Success - Session started and initial output captured{prompt_hint}"""
                
                return ToolResult(
                    success=True,
                    message=f"Interactive session started successfully. Initial output: {line_count} lines",
                    content=formatted_content
                )
            else:
                formatted_content = f"""Session ID: {session_id}
Command: {command}
Working Directory: {cwd}
Environment: {env if env else 'Default'}
Initial Output: (no output after 10 seconds)
Status: Success - Session started but no initial output

📌 IMPORTANT: No initial output detected. When using session_interactive tool later:
   - Try sending a simple command first to see the prompt
   - Then set expect_prompt and prompt_regex accordingly
   
   💡 TIP: Use read_output_progressive method for better output capture
   which intelligently waits for all content and handles timing automatically."""
                
                return ToolResult(
                    success=True,
                    message="Interactive session started successfully. No initial output.",
                    content=formatted_content
                )
                
        else:
            logger.error(f"Failed to start interactive session: {result.message}")
            # Format error as readable text
            formatted_content = f"""Command: {command}
Working Directory: {cwd}
Environment: {env if env else 'Default'}
Status: Error - {result.message}"""
            
            return ToolResult(
                success=False,
                message=result.message,
                content=formatted_content
            ) 