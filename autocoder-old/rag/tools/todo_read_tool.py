"""
TodoReadTool 模块

该模块实现了 TodoReadTool 和 TodoReadToolResolver 类，用于在 BaseAgent 框架中
提供 TODO 列表读取功能。
"""

from typing import Dict, Any, List, Optional

import byzerllm
from loguru import logger

from autocoder.agent.base_agentic.types import BaseTool, ToolResult
from autocoder.agent.base_agentic.tool_registry import ToolRegistry
from autocoder.agent.base_agentic.tools.base_tool_resolver import BaseToolResolver
from autocoder.agent.base_agentic.types import ToolDescription, ToolExample
from autocoder.common.todos.get_todo_manager import get_todo_manager
from autocoder.common.todos.exceptions import TodoManagerError


class TodoReadTool(BaseTool):
    """读取TODO列表工具"""
    pass  # 不需要参数


class TodoReadToolResolver(BaseToolResolver):
    """TODO读取工具解析器，实现读取逻辑"""
    def __init__(self, agent, tool, args):
        super().__init__(agent, tool, args)
        self.tool: TodoReadTool = tool
        
        # 初始化 todo 管理器
        self.todo_manager = get_todo_manager()
    
    def _format_todo_display(self, todos: List[Dict[str, Any]]) -> str:
        """格式化 TODO 显示"""
        if not todos:
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
        for idx, todo in enumerate(todos, 1):
            status = todo.get('status', 'pending')
            priority = todo.get('priority', 'medium')
            todo_id = todo.get('todo_id', 'MISSING_ID')
            todo_content = todo.get('content', '缺少内容')
            
            # 记录任何缺少 ID 的 todos
            if todo_id == 'MISSING_ID':
                logger.error(f"发现缺少 ID 的 TODO: {todo}")
            
            # 获取状态表情符号和优先级图标
            status_mark = status_emoji.get(status, '❓')
            priority_mark = priority_icon.get(priority, '⚪')
            
            # 格式化每个 todo 项
            output.append(f"{idx}. {status_mark} {priority_mark} [{todo_id}] {todo_content}")
            
            # 如果存在，添加备注
            if todo.get('notes'):
                output.append(f"   └─ 📝 {todo['notes']}")
            
            # 如果存在，添加依赖
            if todo.get('dependencies'):
                deps = ', '.join(todo['dependencies'])
                output.append(f"   └─ 🔗 依赖于: {deps}")
        
        output.append("")
        
        # 使用 todo 管理器添加摘要统计
        try:
            # 获取当前会话 ID
            conversation_id = None
            if hasattr(self.agent, 'conversation_config') and self.agent.conversation_config:
                conversation_id = self.agent.conversation_config.conversation_id
            
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
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            output.append("📊 摘要: 统计信息不可用")
        
        return "\n".join(output)

    def resolve(self) -> ToolResult:
        """实现 TODO 读取工具的解析逻辑"""
        try:
            logger.info("读取当前 TODO 列表")
            
            # 从 todo 管理器加载 todos
            conversation_id = None
            if hasattr(self.agent, 'conversation_config') and self.agent.conversation_config:
                conversation_id = self.agent.conversation_config.conversation_id
            
            todos = self.todo_manager.get_todos(conversation_id=conversation_id)
            
            # 格式化显示
            formatted_display = self._format_todo_display(todos)
            
            logger.info(f"在当前会话中找到 {len(todos)} 个 TODO 项")
            
            return ToolResult(
                success=True,
                message="成功检索 TODO 列表。",
                content=formatted_display
            )
            
        except TodoManagerError as e:
            logger.error(f"TODO 管理器读取 TODO 列表时出错: {e}")
            return ToolResult(
                success=False,
                message=f"读取 TODO 列表失败: {str(e)}",
                content=None
            )
        except Exception as e:
            logger.error(f"读取 TODO 列表时出错: {e}")
            import traceback
            return ToolResult(
                success=False,
                message=f"读取 TODO 列表失败: {str(e)}",
                content=traceback.format_exc()
            )


class TodoReadToolDescGenerator:
    def __init__(self, params: Dict[str, Any]):
        self.params = params

    @byzerllm.prompt()
    def todo_read_description(self) -> Dict:
        """
        Description: Request to read and display the current session's TODO list. Use this tool when you need to check the current status of tasks, track progress, or see what work remains to be completed in the current conversation session.
        Parameters:
        No parameters required
        Usage:
        <todo_read>
        </todo_read>
        """
        return self.params


def register_todo_read_tool():
    """Register TODO read tool"""
    desc_gen = TodoReadToolDescGenerator({})
    
    # 准备工具描述
    description = ToolDescription(
        description=desc_gen.todo_read_description.prompt()
    )
    
    # 准备工具示例
    example = ToolExample(
        title="TODO read tool usage example",
        body="""<todo_read>
</todo_read>"""
    )
    
    # 注册工具
    ToolRegistry.register_tool(
        tool_tag="todo_read",  # XML标签名
        tool_cls=TodoReadTool,  # 工具类
        resolver_cls=TodoReadToolResolver,  # 解析器类
        description=description,  # 工具描述
        example=example,  # 工具示例
        use_guideline="Use this tool to read and display the current session's TODO list, helping you track task progress and understand outstanding work. Ideal for checking task status and understanding project progress during complex multi-step operations."  # 使用指南
    )