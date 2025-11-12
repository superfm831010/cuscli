"""
Logging Plugin Example

记录工具调用日志的示例插件。
"""

import json
from typing import Optional, Dict, Any, TYPE_CHECKING
from autocoder.common.v2.agent.agentic_edit_types import BaseTool, ToolResult
from ..base_plugin import BaseToolCallPlugin
from ..plugin_interface import PluginPriority

if TYPE_CHECKING:
    from autocoder.common.v2.agent.agentic_edit import AgenticEdit


class LoggingPlugin(BaseToolCallPlugin):
    """
    日志记录插件
    
    记录所有工具调用的详细信息，包括参数、执行时间和结果。
    """
    
    def __init__(self, enabled: bool = True, detailed_logging: bool = False):
        """
        初始化日志插件
        
        Args:
            enabled: 插件是否启用
            detailed_logging: 是否记录详细日志（包括工具参数和结果内容）
        """
        super().__init__(enabled)
        self.detailed_logging = detailed_logging
        self.call_history = []
    
    @property
    def name(self) -> str:
        return "logging"
    
    @property
    def priority(self) -> PluginPriority:
        return PluginPriority.LOW  # 记录日志通常优先级较低
    
    @property 
    def description(self) -> str:
        return "Records detailed logs of all tool calls and executions"
    
    def before_tool_execution(
        self, 
        tool: BaseTool, 
        agent: Optional['AgenticEdit'],
        context: Optional[Dict[str, Any]] = None
    ) -> BaseTool:
        """记录工具执行前的信息"""
        if not self.enabled:
            return tool
        
        call_info = {
            "tool_name": type(tool).__name__,
            "timestamp": context.get("timestamp") if context else None,
            "call_id": context.get("call_id") if context else None,
            "phase": "before_execution"
        }
        
        if self.detailed_logging:
            call_info["tool_params"] = tool.model_dump() if hasattr(tool, 'model_dump') else str(tool)
        
        self.call_history.append(call_info)
        self.log_info(f"Starting execution of {type(tool).__name__}")
        
        if self.detailed_logging:
            self.log_info(f"Tool parameters: {json.dumps(call_info.get('tool_params', {}), indent=2)}")
        
        return tool
    
    def after_tool_execution(
        self, 
        tool: BaseTool, 
        tool_result: ToolResult, 
        agent: Optional['AgenticEdit'],
        context: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """记录工具执行后的信息"""
        if not self.enabled:
            return tool_result
        
        call_info = {
            "tool_name": type(tool).__name__,
            "timestamp": context.get("timestamp") if context else None,
            "call_id": context.get("call_id") if context else None,
            "phase": "after_execution",
            "success": tool_result.success,
            "message": tool_result.message
        }
        
        if self.detailed_logging and tool_result.content:
            # 只记录前500个字符，避免日志过长
            content_str = str(tool_result.content)
            if len(content_str) > 500:
                content_str = content_str[:500] + "..."
            call_info["result_content"] = content_str
        
        self.call_history.append(call_info)
        
        status = "successfully" if tool_result.success else "with error"
        self.log_info(f"Completed execution of {type(tool).__name__} {status}")
        
        if not tool_result.success:
            self.log_warning(f"Tool execution failed: {tool_result.message}")
        
        if self.detailed_logging:
            self.log_info(f"Result: {json.dumps(call_info, indent=2, default=str)}")
        
        return tool_result
    
    def on_tool_error(
        self, 
        tool: BaseTool, 
        error: Exception, 
        agent: Optional['AgenticEdit'],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[ToolResult]:
        """记录工具执行错误"""
        if not self.enabled:
            return None
        
        call_info = {
            "tool_name": type(tool).__name__,
            "timestamp": context.get("timestamp") if context else None,
            "call_id": context.get("call_id") if context else None,
            "phase": "error",
            "error_type": type(error).__name__,
            "error_message": str(error)
        }
        
        self.call_history.append(call_info)
        self.log_error(f"Tool {type(tool).__name__} failed with {type(error).__name__}: {str(error)}")
        
        # 不提供恢复结果，只记录错误
        return None
    
    def get_call_history(self) -> list:
        """获取调用历史"""
        return self.call_history.copy()
    
    def clear_history(self) -> None:
        """清空调用历史"""
        self.call_history.clear()
        self.log_info("Call history cleared")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_calls = len([call for call in self.call_history if call["phase"] == "after_execution"])
        successful_calls = len([call for call in self.call_history 
                              if call["phase"] == "after_execution" and call.get("success", False)])
        error_calls = len([call for call in self.call_history if call["phase"] == "error"])
        
        return {
            "total_logged_calls": total_calls,
            "successful_calls": successful_calls,
            "error_calls": error_calls,
            "success_rate": successful_calls / total_calls if total_calls > 0 else 0.0,
            "detailed_logging": self.detailed_logging
        } 