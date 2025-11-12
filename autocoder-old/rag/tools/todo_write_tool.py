"""
TodoWriteTool 模块

该模块实现了 TodoWriteTool 和 TodoWriteToolResolver 类，用于在 BaseAgent 框架中
提供 TODO 列表写入和管理功能。
"""

from typing import Dict, Any, List, Optional

import byzerllm
from loguru import logger

from autocoder.agent.base_agentic.types import BaseTool, ToolResult
from autocoder.agent.base_agentic.tool_registry import ToolRegistry
from autocoder.agent.base_agentic.tools.base_tool_resolver import BaseToolResolver
from autocoder.agent.base_agentic.types import ToolDescription, ToolExample
from autocoder.common.todos.get_todo_manager import get_todo_manager
from autocoder.common.todos.exceptions import TodoManagerError, TodoNotFoundError


class TodoWriteTool(BaseTool):
    """TODO 写入工具，用于创建和管理任务列表"""
    action: str  # 操作类型：create, add_task, update, mark_progress, mark_completed
    task_id: Optional[str] = None  # 任务 ID（用于更新操作）
    content: Optional[str] = None  # 任务内容
    priority: Optional[str] = None  # 优先级：high, medium, low
    status: Optional[str] = None  # 状态：pending, in_progress, completed
    notes: Optional[str] = None  # 备注


class TodoWriteToolResolver(BaseToolResolver):
    """TODO 写入工具解析器，实现写入逻辑"""
    def __init__(self, agent, tool, args):
        super().__init__(agent, tool, args)
        self.tool: TodoWriteTool = tool
        
        # 初始化 todo 管理器
        self.todo_manager = get_todo_manager()

    def _format_todo_response(self, todos: List[Dict[str, Any]], action_performed: str) -> str:
        """格式化 TODO 操作后的响应消息"""
        if not todos:
            return f"操作已完成: {action_performed}"

        output = [f"操作已完成: {action_performed}\n"]

        if action_performed.startswith("创建"):
            # 对于创建操作，显示新创建的任务
            output.append("📝 新创建的 TODO 项:")
            for todo in todos:
                priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                    todo.get('priority', 'medium'), "⚪")
                status_icon = {"pending": "⏳", "in_progress": "🔄", "completed": "✅"}.get(
                    todo.get('status', 'pending'), "⏳")
                todo_id = todo.get('todo_id', 'MISSING_ID')
                todo_content = todo.get('content', '缺少内容')

                # 记录任何缺少 ID 的 todos
                if todo_id == 'MISSING_ID':
                    logger.error(f"发现缺少 ID 的 TODO: {todo}")

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
                f"\n📊 当前摘要: 总计 {total_todos} 项 | 待处理 {pending_count} | 进行中 {in_progress_count} | 已完成 {completed_count}")
        else:
            # 对于更新操作，显示完整的 TODO 列表
            output.append(self._format_full_todo_list())

        return "\n".join(output)

    def _format_full_todo_list(self) -> str:
        """格式化完整的 TODO 列表"""
        try:
            # 从当前会话获取所有 todos
            conversation_id = None
            if hasattr(self.agent, 'conversation_config') and self.agent.conversation_config:
                conversation_id = self.agent.conversation_config.conversation_id
            
            all_todos = self.todo_manager.get_todos(conversation_id=conversation_id)

            if not all_todos:
                return "当前会话没有找到 TODO 项。"

            output = []
            output.append("=== 当前会话 TODO 列表 ===\n")

            # 状态表情符号映射
            status_emoji = {
                'pending': '⏳',
                'in_progress': '🔄',
                'completed': '✅',
                'cancelled': '❌'
            }

            # 优先级图标映射
            priority_icon = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢'
            }

            # 显示带状态标记的单个列表中的 todos
            for idx, todo in enumerate(all_todos, 1):
                status = todo.get('status', 'pending')
                priority = todo.get('priority', 'medium')
                todo_id = todo.get('todo_id', 'MISSING_ID')
                todo_content = todo.get('content', '缺少内容')

                # 记录任何缺少 ID 的 todos
                if todo_id == 'MISSING_ID':
                    logger.error(
                        f"在完整列表中发现缺少 ID 的 TODO: {todo}")

                # 获取状态表情符号和优先级图标
                status_mark = status_emoji.get(status, '❓')
                priority_mark = priority_icon.get(priority, '⚪')

                # 格式化每个 todo 项
                output.append(
                    f"{idx}. {status_mark} {priority_mark} [{todo_id}] {todo_content}")

                # 如果存在，添加备注
                if todo.get('notes'):
                    output.append(f"   └─ 📝 {todo['notes']}")

                # 如果存在，添加依赖
                if todo.get('dependencies'):
                    deps = ', '.join(todo['dependencies'])
                    output.append(f"   └─ 🔗 依赖于: {deps}")

            output.append("")

            # 添加摘要统计
            stats = self.todo_manager.get_statistics(conversation_id=conversation_id)
            total = stats.get('total', 0)
            status_counts = {
                'pending': stats.get('pending', 0),
                'in_progress': stats.get('in_progress', 0),
                'completed': stats.get('completed', 0),
                'cancelled': stats.get('cancelled', 0)
            }

            summary_parts = [f"总计: {total}"]
            for status, emoji in status_emoji.items():
                if status in status_counts and status_counts[status] > 0:
                    status_label = {
                        'pending': '待处理',
                        'in_progress': '进行中',
                        'completed': '已完成',
                        'cancelled': '已取消'
                    }.get(status, status)
                    summary_parts.append(f"{emoji} {status_label}: {status_counts[status]}")

            output.append("📊 摘要: " + " | ".join(summary_parts))

            return "\n".join(output)
            
        except Exception as e:
            logger.error(f"格式化完整 TODO 列表失败: {e}")
            return "检索 TODO 列表时出错。"

    def resolve(self) -> ToolResult:
        """
        根据指定的操作创建和管理结构化任务列表。
        """
        try:
            action = self.tool.action.lower()
            logger.info(f"执行 TODO 操作: {action}")

            # 获取会话 ID
            conversation_id = None
            if hasattr(self.agent, 'conversation_config') and self.agent.conversation_config:
                conversation_id = self.agent.conversation_config.conversation_id

            if action == "create":
                if not self.tool.content:
                    return ToolResult(
                        success=False,
                        message="错误：创建 TODO 需要内容。",
                        content=None
                    )

                # 使用 todo 管理器创建新的 todos
                try:
                    todo_ids = self.todo_manager.create_todos(
                        content=self.tool.content,
                        conversation_id=conversation_id,
                        priority=self.tool.priority or "medium",
                        notes=self.tool.notes
                    )
                    
                    # 获取创建的 todos 以供显示
                    created_todos = []
                    all_todos = self.todo_manager.get_todos(conversation_id=conversation_id)
                    for todo in all_todos:
                        if todo.get('todo_id') in todo_ids:
                            created_todos.append(todo)
                    
                    response = self._format_todo_response(
                        created_todos, f"创建了 {len(todo_ids)} 个新的 TODO 项")
                    return ToolResult(
                        success=True,
                        message="TODO 列表创建成功。",
                        content=response
                    )
                    
                except TodoManagerError as e:
                    return ToolResult(
                        success=False,
                        message=f"创建 TODO 失败: {str(e)}",
                        content=None
                    )

            elif action == "add_task":
                if not self.tool.content:
                    return ToolResult(
                        success=False,
                        message="错误：添加任务需要内容。",
                        content=None
                    )

                try:
                    todo_id = self.todo_manager.add_todo(
                        content=self.tool.content,
                        conversation_id=conversation_id,
                        status=self.tool.status or "pending",
                        priority=self.tool.priority or "medium",
                        notes=self.tool.notes
                    )
                    
                    # 获取创建的 todo 以供显示
                    all_todos = self.todo_manager.get_todos(conversation_id=conversation_id)
                    new_todo = next((t for t in all_todos if t.get('todo_id') == todo_id), None)
                    
                    if new_todo:
                        response = self._format_todo_response(
                            [new_todo], f"添加了新任务: {new_todo['content']}")
                    else:
                        response = f"添加了 ID 为 {todo_id} 的新任务"
                    
                    return ToolResult(
                        success=True,
                        message="任务添加成功。",
                        content=response
                    )
                    
                except TodoManagerError as e:
                    return ToolResult(
                        success=False,
                        message=f"添加任务失败: {str(e)}",
                        content=None
                    )

            elif action in ["update", "mark_progress", "mark_completed"]:
                if not self.tool.task_id:
                    return ToolResult(
                        success=False,
                        message="错误：更新操作需要任务 ID。",
                        content=None
                    )

                try:
                    # 准备更新参数
                    update_kwargs = {}
                    action_msg = ""
                    
                    if action == "mark_progress":
                        update_kwargs['status'] = "in_progress"
                        action_msg = "将任务标记为进行中"
                    elif action == "mark_completed":
                        update_kwargs['status'] = "completed"
                        action_msg = "将任务标记为已完成"
                    else:  # update
                        if self.tool.content:
                            update_kwargs['content'] = self.tool.content
                        if self.tool.status:
                            update_kwargs['status'] = self.tool.status
                        if self.tool.priority:
                            update_kwargs['priority'] = self.tool.priority
                        if self.tool.notes:
                            update_kwargs['notes'] = self.tool.notes
                        action_msg = "更新了任务"
                    
                    # 更新 todo
                    success = self.todo_manager.update_todo(
                        todo_id=self.tool.task_id,
                        conversation_id=conversation_id,
                        **update_kwargs
                    )
                    
                    if success:
                        # 获取更新的 todo 以供显示
                        all_todos = self.todo_manager.get_todos(conversation_id=conversation_id)
                        updated_todo = next((t for t in all_todos if t.get('todo_id') == self.tool.task_id), None)
                        
                        if updated_todo:
                            full_action_msg = f"{action_msg}: {updated_todo['content']}"
                            response = self._format_todo_response([updated_todo], full_action_msg)
                        else:
                            response = f"{action_msg}，ID: {self.tool.task_id}"
                        
                        return ToolResult(
                            success=True,
                            message="任务更新成功。",
                            content=response
                        )
                    else:
                        return ToolResult(
                            success=False,
                            message=f"未找到 ID 为 '{self.tool.task_id}' 的任务。",
                            content=None
                        )
                        
                except TodoNotFoundError:
                    return ToolResult(
                        success=False,
                        message=f"错误：未找到 ID 为 '{self.tool.task_id}' 的任务。",
                        content=None
                    )
                except TodoManagerError as e:
                    return ToolResult(
                        success=False,
                        message=f"更新任务失败: {str(e)}",
                        content=None
                    )

            else:
                return ToolResult(
                    success=False,
                    message=f"错误：未知操作 '{action}'。支持的操作：create, add_task, update, mark_progress, mark_completed。",
                    content=None
                )

        except Exception as e:
            logger.error(f"TODO 写入操作出错: {e}")
            import traceback
            return ToolResult(
                success=False,
                message=f"执行 TODO 操作失败: {str(e)}",
                content=traceback.format_exc()
            )


class TodoWriteToolDescGenerator:
    def __init__(self, params: Dict[str, Any]):
        self.params = params

    @byzerllm.prompt()
    def todo_write_description(self) -> Dict:
        """
        Description: Request to create and manage structured task lists. Use this tool when you need to organize complex multi-step tasks, track progress, or manage task priorities and statuses during your work session.
        Parameters:
        - action: (required) The operation type - 'create', 'add_task', 'update', 'mark_progress', or 'mark_completed'
        - task_id: (optional) Task ID for update operations
        - content: (optional) Task content or description
        - priority: (optional) Priority level - 'high', 'medium', or 'low'
        - status: (optional) Task status - 'pending', 'in_progress', 'completed', or 'cancelled'
        - notes: (optional) Additional notes or comments for the task
        Usage:
        <todo_write>
        <action>create</action>
        <content>Your task content here</content>
        <priority>medium</priority>
        </todo_write>
        """
        return self.params


def register_todo_write_tool():
    """Register TODO write tool"""
    desc_gen = TodoWriteToolDescGenerator({})
    
    # 准备工具描述
    description = ToolDescription(
        description=desc_gen.todo_write_description.prompt()
    )
    
    # 准备工具示例
    example = ToolExample(
        title="TODO write tool usage example",
        body="""<todo_write>
<action>create</action>
<content>
<task>Analyze existing codebase structure</task>
<task>Design new feature architecture</task>
<task>Implement core functionality</task>
<task>Add comprehensive tests</task>
<task>Update documentation</task>
</content>
<priority>high</priority>
</todo_write>"""
    )
    
    # 注册工具
    ToolRegistry.register_tool(
        tool_tag="todo_write",  # XML标签名
        tool_cls=TodoWriteTool,  # 工具类
        resolver_cls=TodoWriteToolResolver,  # 解析器类
        description=description,  # 工具描述
        example=example,  # 工具示例
        use_guideline="Use this tool to create and manage structured task lists for tracking complex task progress. Ideal for organizing multi-step operations, clarifying task priorities and statuses, and maintaining visibility into work that needs to be completed."  # 使用指南
    )