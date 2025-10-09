"""
Base Tool Call Plugin

提供工具调用插件的基础实现。
"""

from typing import Any, Dict, Optional, TYPE_CHECKING
from autocoder.common.v2.agent.agentic_edit_types import BaseTool, ToolResult
from .plugin_interface import ToolCallPlugin, PluginPriority
from loguru import logger

if TYPE_CHECKING:
    from autocoder.common.v2.agent.agentic_edit import AgenticEdit


class BaseToolCallPlugin(ToolCallPlugin):
    """
    工具调用插件基础实现类
    
    提供常见功能的默认实现，插件开发者可以继承此类。
    """
    
    def __init__(self, enabled: bool = True):
        """
        初始化插件
        
        Args:
            enabled: 插件是否启用
        """
        self._enabled = enabled
        self._config = {}
    
    @property
    def enabled(self) -> bool:
        """插件是否启用"""
        return self._enabled
    
    def set_enabled(self, enabled: bool) -> None:
        """设置插件启用状态"""
        self._enabled = enabled
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """设置插件配置"""
        self._config = config
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return self._config.get(key, default)
    
    def log_info(self, message: str) -> None:
        """记录信息日志"""
        logger.info(f"[{self.name}] {message}")
    
    def log_warning(self, message: str) -> None:
        """记录警告日志"""
        logger.warning(f"[{self.name}] {message}")
    
    def log_error(self, message: str) -> None:
        """记录错误日志"""
        logger.error(f"[{self.name}] {message}")
    
    def create_context(self, **kwargs) -> Dict[str, Any]:
        """创建上下文信息"""
        context = {
            "plugin_name": self.name,
            "plugin_priority": self.priority.value,
            "timestamp": __import__("time").time()
        }
        context.update(kwargs)
        return context
    
    def should_process_tool(self, tool: BaseTool, agent: Optional['AgenticEdit']) -> bool:
        """
        判断是否应该处理这个工具
        
        默认实现：只有当插件启用时才处理
        """
        return self.enabled
    
    def before_tool_execution(
        self, 
        tool: BaseTool, 
        agent: Optional['AgenticEdit'],
        context: Optional[Dict[str, Any]] = None
    ) -> BaseTool:
        """
        工具执行前的处理
        
        默认实现：记录日志并返回原始工具
        """
        if self.enabled:
            self.log_info(f"Before execution of {type(tool).__name__}")
        return tool
    
    def after_tool_execution(
        self, 
        tool: BaseTool, 
        tool_result: ToolResult, 
        agent: Optional['AgenticEdit'],
        context: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """
        工具执行后的处理
        
        默认实现：记录日志并返回原始结果
        """
        if self.enabled:
            success_str = "successfully" if tool_result.success else "with error"
            self.log_info(f"After execution of {type(tool).__name__} {success_str}")
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
        
        默认实现：记录错误日志，不提供替代结果
        """
        if self.enabled:
            self.log_error(f"Error in {type(tool).__name__}: {str(error)}")
        return None 