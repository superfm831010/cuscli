import os
from typing import Dict, Any, Optional, List
from autocoder.common.v2.agent.agentic_edit_types import WriteToFileTool, ToolResult
from autocoder.common.v2.agent.agentic_edit_tools.linter_enabled_tool_resolver import LinterEnabledToolResolver
from loguru import logger
from autocoder.common import AutoCoderArgs
from autocoder.common.file_checkpoint.models import FileChange as CheckpointFileChange
import typing

if typing.TYPE_CHECKING:
    from autocoder.common.v2.agent.agentic_edit import AgenticEdit

class WriteToFileToolResolver(LinterEnabledToolResolver):
    def __init__(self, agent: Optional['AgenticEdit'], tool: WriteToFileTool, args: AutoCoderArgs):
        super().__init__(agent, tool, args)
        self.tool: WriteToFileTool = tool  # For type hinting
        self.args = args

    def write_file_normal(self, file_path: str, content: str, source_dir: str, abs_project_dir: str, abs_file_path: str, mode: str = "write") -> ToolResult:
        """Write file directly without using shadow manager"""
        try:
            os.makedirs(os.path.dirname(abs_file_path), exist_ok=True)

            is_new = not os.path.exists(abs_file_path)
            new_content_to_write = content
            if mode == "append" and not is_new:
                try:
                    with open(abs_file_path, 'r', encoding='utf-8') as f:
                        existing_content = f.read()
                except Exception:
                    existing_content = ""
                new_content_to_write = f"{existing_content}{content}"

            if self.agent:
                rel_path = os.path.relpath(abs_file_path, abs_project_dir)
                change_type = "added" if is_new else "modified"
                self.agent.record_file_change(rel_path, change_type, diff=None, content=new_content_to_write)

            if self.agent and self.agent.checkpoint_manager:
                changes = {
                    file_path: CheckpointFileChange(
                        file_path=file_path,
                        content=new_content_to_write,
                        is_deletion=False,
                        is_new=is_new
                    )
                }
                change_group_id = self.args.event_file
                                                              
                conversation_id = self.agent.conversation_config.conversation_id if self.agent else None
                if conversation_id:
                    first_message_id, last_message_id = self.agent.get_conversation_message_range()
                    self.agent.checkpoint_manager.apply_changes_with_conversation(
                                changes=changes,
                                conversation_id=conversation_id,
                                first_message_id=first_message_id,
                                last_message_id=last_message_id,
                                change_group_id=change_group_id,
                                metadata={"event_file": self.args.event_file}
                            )
            else:
                open_mode = 'a' if (mode == "append" and not is_new) else 'w'
                with open(abs_file_path, open_mode, encoding='utf-8') as f:
                    f.write(content if open_mode == 'a' else new_content_to_write)

            action_text = "appended to" if (mode == "append" and not is_new) else "wrote to"
            logger.info(f"Successfully {action_text} file: {file_path}")
            
            # 构建成功消息
            final_message = f"Successfully {action_text} file: {file_path}"
            
            # Run linter check if enabled
            result = ToolResult(success=True, message=final_message)
            if self.should_lint(file_path) and self.linter_config and self.linter_config.check_after_modification:
                logger.info(f"Running linter check on {action_text} file: {file_path}")
                lint_report = self.lint_files([abs_file_path])
                if lint_report:
                    result = self.handle_lint_results(result, lint_report)
            
            return result
        except Exception as e:
            logger.error(f"Error writing to file '{file_path}': {str(e)}")
            return ToolResult(success=False, message=f"An error occurred while writing to the file: {str(e)}")

    def resolve(self) -> ToolResult:
        """Resolve the write file tool by calling the appropriate implementation"""
        # Check if we are in plan mode
        if self.args.agentic_mode == "plan":
            return ToolResult(
                success=False, 
                message="Currently in plan mode, modification tools are disabled. "
            )
            
        file_path = self.tool.path
        content = self.tool.content
        # Determine mode; default to 'write'
        tool_mode = self.tool.mode or "write"
        mode_value = tool_mode
        source_dir = self.args.source_dir or "."
        abs_project_dir = os.path.abspath(source_dir)
        abs_file_path = os.path.abspath(os.path.join(source_dir, file_path))

        # Security check: ensure the path is within the source directory
        if not abs_file_path.startswith(abs_project_dir):
            return ToolResult(success=False, message=f"Error: Access denied. Attempted to write file outside the project directory: {file_path}")
                
        return self.write_file_normal(file_path, content, source_dir, abs_project_dir, abs_file_path, mode=mode_value)