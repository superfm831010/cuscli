from typing import Dict, Any, Optional, List
from autocoder.common.v2.agent.agentic_edit_tools.base_tool_resolver import BaseToolResolver
from autocoder.common.v2.agent.agentic_edit_types import TodoReadTool, ToolResult
from loguru import logger
import typing
from autocoder.common import AutoCoderArgs

# Import the new todos module
from autocoder.common.todos.get_todo_manager import get_todo_manager
from autocoder.common.todos.exceptions import TodoManagerError

if typing.TYPE_CHECKING:
    from autocoder.common.v2.agent.agentic_edit import AgenticEdit


class TodoReadToolResolver(BaseToolResolver):
    def __init__(self, agent: Optional['AgenticEdit'], tool: TodoReadTool, args: AutoCoderArgs):
        super().__init__(agent, tool, args)
        self.tool: TodoReadTool = tool  # For type hinting
        
        # Initialize todo manager
        self.todo_manager = get_todo_manager()
    
    def _format_todo_display(self, todos: List[Dict[str, Any]]) -> str:
        """Format todos for display."""
        if not todos:
            return "No todos found for current conversation."
        
        output = []
        output.append("=== Current Conversation Todo List ===\n")
        
        # Status emoji mapping
        status_emoji = {
            'pending': '⏳',
            'in_progress': '🔄',
            'completed': '✅',
            'cancelled': '❌'
        }
        
        # Priority icon mapping
        priority_icon = {
            'high': '🔴',
            'medium': '🟡',
            'low': '🟢'
        }
        
        # Display todos in a single list with status markers
        for idx, todo in enumerate(todos, 1):
            status = todo.get('status', 'pending')
            priority = todo.get('priority', 'medium')
            todo_id = todo.get('todo_id', 'MISSING_ID')
            todo_content = todo.get('content', 'Missing content')
            
            # Log any todos with missing IDs
            if todo_id == 'MISSING_ID':
                logger.error(f"Found todo with missing ID: {todo}")
            
            # Get status emoji and priority icon
            status_mark = status_emoji.get(status, '❓')
            priority_mark = priority_icon.get(priority, '⚪')
            
            # Format each todo item
            output.append(f"{idx}. {status_mark} {priority_mark} [{todo_id}] {todo_content}")
            
            # Add notes if present
            if todo.get('notes'):
                output.append(f"   └─ 📝 {todo['notes']}")
            
            # Add dependencies if present
            if todo.get('dependencies'):
                deps = ', '.join(todo['dependencies'])
                output.append(f"   └─ 🔗 Depends on: {deps}")
        
        output.append("")
        
        # Add summary statistics using todo manager
        try:
            conversation_id = self.agent.conversation_config.conversation_id if self.agent else None
            stats = self.todo_manager.get_statistics(conversation_id=conversation_id)
            total = stats.get('total', 0)
            status_counts = {
                'pending': stats.get('pending', 0),
                'in_progress': stats.get('in_progress', 0),
                'completed': stats.get('completed', 0),
                'cancelled': stats.get('cancelled', 0)
            }
            
            summary_parts = [f"Total: {total}"]
            for status, emoji in status_emoji.items():
                if status in status_counts and status_counts[status] > 0:
                    summary_parts.append(f"{emoji} {status.replace('_', ' ').title()}: {status_counts[status]}")
            
            output.append("📊 Summary: " + " | ".join(summary_parts))
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            output.append("📊 Summary: Statistics unavailable")
        
        return "\n".join(output)

    def resolve(self) -> ToolResult:
        """
        Read the current todo list and return it in a formatted display.
        """
        try:
            logger.info("Reading current todo list")
            
            # Load todos from todo manager
            conversation_id = self.agent.conversation_config.conversation_id if self.agent else None
            todos = self.todo_manager.get_todos(conversation_id=conversation_id)
            
            # Format for display
            formatted_display = self._format_todo_display(todos)
            
            logger.info(f"Found {len(todos)} todos in current conversation")
            
            return ToolResult(
                success=True,
                message="Todo list retrieved successfully.",
                content=formatted_display
            )
            
        except TodoManagerError as e:
            logger.error(f"Todo manager error reading todo list: {e}")
            return ToolResult(
                success=False,
                message=f"Failed to read todo list: {str(e)}",
                content=None
            )
        except Exception as e:
            logger.error(f"Error reading todo list: {e}")
            return ToolResult(
                success=False,
                message=f"Failed to read todo list: {str(e)}",
                content=None
            ) 