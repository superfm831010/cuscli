from typing import Dict, Any, Optional, List
from autocoder.common.v2.agent.agentic_edit_tools.base_tool_resolver import BaseToolResolver
from autocoder.common.v2.agent.agentic_edit_types import TodoWriteTool, ToolResult
from loguru import logger
import typing
from autocoder.common import AutoCoderArgs

# Import the new todos module
from autocoder.common.todos.get_todo_manager import get_todo_manager
from autocoder.common.todos.exceptions import TodoManagerError, TodoNotFoundError

if typing.TYPE_CHECKING:
    from autocoder.common.v2.agent.agentic_edit import AgenticEdit


class TodoWriteToolResolver(BaseToolResolver):
    def __init__(self, agent: Optional['AgenticEdit'], tool: TodoWriteTool, args: AutoCoderArgs):
        super().__init__(agent, tool, args)
        self.tool: TodoWriteTool = tool  # For type hinting
        
        # Initialize todo manager
        self.todo_manager = get_todo_manager()

    def _format_todo_response(self, todos: List[Dict[str, Any]], action_performed: str) -> str:
        """Format the response message after todo operations."""
        if not todos:
            return f"Operation completed: {action_performed}"

        output = [f"Operation completed: {action_performed}\n"]

        if action_performed.startswith("Created"):
            # For creation operations, show newly created tasks
            output.append("📝 Newly created todos:")
            for todo in todos:
                priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                    todo.get('priority', 'medium'), "⚪")
                status_icon = {"pending": "⏳", "in_progress": "🔄", "completed": "✅"}.get(
                    todo.get('status', 'pending'), "⏳")
                todo_id = todo.get('todo_id', 'MISSING_ID')
                todo_content = todo.get('content', 'Missing content')

                # Log any todos with missing IDs
                if todo_id == 'MISSING_ID':
                    logger.error(f"Found todo with missing ID: {todo}")

                output.append(
                    f"  {priority_icon} {status_icon} [{todo_id}] {todo_content}")

            total_todos = len(todos)
            pending_count = len(
                [t for t in todos if t.get('status') == 'pending'])
            in_progress_count = len(
                [t for t in todos if t.get('status') == 'in_progress'])
            completed_count = len(
                [t for t in todos if t.get('status') == 'completed'])

            output.append(
                f"\n📊 Current summary: Total {total_todos} items | Pending {pending_count} | In Progress {in_progress_count} | Completed {completed_count}")
        else:
            # For update operations, show complete TODO list
            output.append(self._format_full_todo_list())

        return "\n".join(output)

    def _format_full_todo_list(self) -> str:
        """Format the complete todo list using the same format as todo_read_tool_resolver."""
        try:
            # Get all todos from the current conversation
            conversation_id = self.agent.conversation_config.conversation_id if self.agent else None
            all_todos = self.todo_manager.get_todos(conversation_id=conversation_id)

            if not all_todos:
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
            for idx, todo in enumerate(all_todos, 1):
                status = todo.get('status', 'pending')
                priority = todo.get('priority', 'medium')
                todo_id = todo.get('todo_id', 'MISSING_ID')
                todo_content = todo.get('content', 'Missing content')

                # Log any todos with missing IDs
                if todo_id == 'MISSING_ID':
                    logger.error(
                        f"Found todo with missing ID in full list: {todo}")

                # Get status emoji and priority icon
                status_mark = status_emoji.get(status, '❓')
                priority_mark = priority_icon.get(priority, '⚪')

                # Format each todo item
                output.append(
                    f"{idx}. {status_mark} {priority_mark} [{todo_id}] {todo_content}")

                # Add notes if present
                if todo.get('notes'):
                    output.append(f"   └─ 📝 {todo['notes']}")

                # Add dependencies if present
                if todo.get('dependencies'):
                    deps = ', '.join(todo['dependencies'])
                    output.append(f"   └─ 🔗 Depends on: {deps}")

            output.append("")

            # Add summary statistics
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
                    summary_parts.append(
                        f"{emoji} {status.replace('_', ' ').title()}: {status_counts[status]}")

            output.append("📊 Summary: " + " | ".join(summary_parts))

            return "\n".join(output)
            
        except Exception as e:
            logger.error(f"Failed to format full todo list: {e}")
            return "Error retrieving todo list."

    def resolve(self) -> ToolResult:
        """
        Create and manage a structured task list based on the action specified.
        """
        try:
            action = self.tool.action.lower()
            logger.info(f"Performing todo action: {action}")

            if action == "create":
                if not self.tool.content:
                    return ToolResult(
                        success=False,
                        message="Error: Content is required for creating todos.",
                        content=None
                    )

                # Create new todos using the todo manager
                try:
                    conversation_id = self.agent.conversation_config.conversation_id if self.agent else None
                    todo_ids = self.todo_manager.create_todos(
                        content=self.tool.content,
                        conversation_id=conversation_id,
                        priority=self.tool.priority or "medium",
                        notes=self.tool.notes
                    )
                    
                    # Get the created todos for display
                    created_todos = []
                    conversation_id = self.agent.conversation_config.conversation_id if self.agent else None
                    all_todos = self.todo_manager.get_todos(conversation_id=conversation_id)
                    for todo in all_todos:
                        if todo.get('todo_id') in todo_ids:
                            created_todos.append(todo)
                    
                    response = self._format_todo_response(
                        created_todos, f"Created {len(todo_ids)} new todo items")
                    return ToolResult(
                        success=True,
                        message="Todo list created successfully.",
                        content=response
                    )
                    
                except TodoManagerError as e:
                    return ToolResult(
                        success=False,
                        message=f"Failed to create todos: {str(e)}",
                        content=None
                    )

            elif action == "add_task":
                if not self.tool.content:
                    return ToolResult(
                        success=False,
                        message="Error: Content is required for adding a task.",
                        content=None
                    )

                try:
                    conversation_id = self.agent.conversation_config.conversation_id if self.agent else None
                    todo_id = self.todo_manager.add_todo(
                        content=self.tool.content,
                        conversation_id=conversation_id,
                        status=self.tool.status or "pending",
                        priority=self.tool.priority or "medium",
                        notes=self.tool.notes
                    )
                    
                    # Get the created todo for display
                    conversation_id = self.agent.conversation_config.conversation_id if self.agent else None
                    all_todos = self.todo_manager.get_todos(conversation_id=conversation_id)
                    new_todo = next((t for t in all_todos if t.get('todo_id') == todo_id), None)
                    
                    if new_todo:
                        response = self._format_todo_response(
                            [new_todo], f"Added new task: {new_todo['content']}")
                    else:
                        response = f"Added new task with ID: {todo_id}"
                    
                    return ToolResult(
                        success=True,
                        message="Task added successfully.",
                        content=response
                    )
                    
                except TodoManagerError as e:
                    return ToolResult(
                        success=False,
                        message=f"Failed to add task: {str(e)}",
                        content=None
                    )

            elif action in ["update", "mark_progress", "mark_completed"]:
                if not self.tool.task_id:
                    return ToolResult(
                        success=False,
                        message="Error: Task ID is required for update operations.",
                        content=None
                    )

                try:
                    # Prepare update parameters
                    update_kwargs = {}
                    action_msg = ""
                    
                    if action == "mark_progress":
                        update_kwargs['status'] = "in_progress"
                        action_msg = "Marked task as in progress"
                    elif action == "mark_completed":
                        update_kwargs['status'] = "completed"
                        action_msg = "Marked task as completed"
                    else:  # update
                        if self.tool.content:
                            update_kwargs['content'] = self.tool.content
                        if self.tool.status:
                            update_kwargs['status'] = self.tool.status
                        if self.tool.priority:
                            update_kwargs['priority'] = self.tool.priority
                        if self.tool.notes:
                            update_kwargs['notes'] = self.tool.notes
                        action_msg = "Updated task"
                    
                    # Update the todo
                    conversation_id = self.agent.conversation_config.conversation_id if self.agent else None
                    success = self.todo_manager.update_todo(
                        todo_id=self.tool.task_id,
                        conversation_id=conversation_id,
                        **update_kwargs
                    )
                    
                    if success:
                        # Get the updated todo for display
                        conversation_id = self.agent.conversation_config.conversation_id if self.agent else None
                        all_todos = self.todo_manager.get_todos(conversation_id=conversation_id)
                        updated_todo = next((t for t in all_todos if t.get('todo_id') == self.tool.task_id), None)
                        
                        if updated_todo:
                            full_action_msg = f"{action_msg}: {updated_todo['content']}"
                            response = self._format_todo_response([updated_todo], full_action_msg)
                        else:
                            response = f"{action_msg} with ID: {self.tool.task_id}"
                        
                        return ToolResult(
                            success=True,
                            message="Task updated successfully.",
                            content=response
                        )
                    else:
                        return ToolResult(
                            success=False,
                            message=f"Task with ID '{self.tool.task_id}' not found.",
                            content=None
                        )
                        
                except TodoNotFoundError:
                    return ToolResult(
                        success=False,
                        message=f"Error: Task with ID '{self.tool.task_id}' not found.",
                        content=None
                    )
                except TodoManagerError as e:
                    return ToolResult(
                        success=False,
                        message=f"Failed to update task: {str(e)}",
                        content=None
                    )

            else:
                return ToolResult(
                    success=False,
                    message=f"Error: Unknown action '{action}'. Supported actions: create, add_task, update, mark_progress, mark_completed.",
                    content=None
                )

        except Exception as e:
            logger.error(f"Error in todo write operation: {e}")
            return ToolResult(
                success=False,
                message=f"Failed to perform todo operation: {str(e)}",
                content=None
            )
