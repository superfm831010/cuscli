"""
Tool Call Plugin Interface

定义工具调用插件的接口和协议。
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional, TYPE_CHECKING
from autocoder.common.v2.agent.agentic_edit_types import BaseTool, ToolResult

if TYPE_CHECKING:
    from autocoder.common.v2.agent.agentic_edit import AgenticEdit


class PluginPriority(Enum):
    """插件优先级枚举"""
    HIGHEST = 0     # 最高优先级
    HIGH = 10       # 高优先级
    NORMAL = 50     # 普通优先级
    LOW = 100       # 低优先级
    LOWEST = 200    # 最低优先级


class ToolCallPlugin(ABC):
    """
    工具调用插件接口
    
    插件可以拦截和修改工具的输入参数和输出结果。
    插件按优先级顺序执行，优先级数值越小越先执行。
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """插件名称"""
        pass
    
    @property
    @abstractmethod
    def priority(self) -> PluginPriority:
        """插件优先级"""
        pass
    
    @property
    def description(self) -> str:
        """插件描述"""
        return f"{self.name} plugin"
    
    @property
    def enabled(self) -> bool:
        """插件是否启用"""
        return True
    
    def should_process_tool(self, tool: BaseTool, agent: Optional['AgenticEdit']) -> bool:
        """
        判断是否应该处理这个工具
        
        Args:
            tool: 工具实例
            agent: 代理实例
            
        Returns:
            bool: 是否应该处理
        """
        return True
    
    def before_tool_execution(
        self, 
        tool: BaseTool, 
        agent: Optional['AgenticEdit'],
        context: Optional[Dict[str, Any]] = None
    ) -> BaseTool:
        """
        工具执行前的拦截处理
        
        Args:
            tool: 原始工具实例
            agent: 代理实例
            context: 上下文信息
            
        Returns:
            BaseTool: 处理后的工具实例（可以是修改后的副本）
        """
        return tool
    
    def after_tool_execution(
        self, 
        tool: BaseTool, 
        tool_result: ToolResult, 
        agent: Optional['AgenticEdit'],
        context: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """
        工具执行后的拦截处理
        
        Args:
            tool: 工具实例
            tool_result: 原始工具执行结果
            agent: 代理实例
            context: 上下文信息
            
        Returns:
            ToolResult: 处理后的工具执行结果
        """
        return tool_result
    
    def on_tool_error(
        self, 
        tool: BaseTool, 
        error: Exception, 
        agent: Optional['AgenticEdit'],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[ToolResult]:
        """
        工具执行出错时的处理
        
        Args:
            tool: 工具实例
            error: 异常信息
            agent: 代理实例
            context: 上下文信息
            
        Returns:
            Optional[ToolResult]: 如果返回非None，则使用这个结果代替错误
        """
        return None
    
    def get_plugin_config(self) -> Dict[str, Any]:
        """
        获取插件配置信息
        
        Returns:
            Dict[str, Any]: 配置信息
        """
        return {
            "name": self.name,
            "priority": self.priority.value,
            "description": self.description,
            "enabled": self.enabled
        } 