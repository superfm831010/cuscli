"""
Security Filter Plugin Example

安全过滤插件，用于拦截和过滤敏感信息。
"""

import re
from copy import deepcopy
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from autocoder.common.v2.agent.agentic_edit_types import BaseTool, ToolResult, ExecuteCommandTool
from ..base_plugin import BaseToolCallPlugin
from ..plugin_interface import PluginPriority

if TYPE_CHECKING:
    from autocoder.common.v2.agent.agentic_edit import AgenticEdit


class SecurityFilterPlugin(BaseToolCallPlugin):
    """
    安全过滤插件
    
    过滤敏感信息，如密码、API密钥等，防止在工具执行过程中泄露。
    """
    
    def __init__(self, enabled: bool = True):
        """
        初始化安全过滤插件
        
        Args:
            enabled: 插件是否启用
        """
        super().__init__(enabled)
        
        # 敏感信息正则模式
        self.sensitive_patterns = [
            (r'password\s*[=:]\s*["\']?([^"\'\s]+)["\']?', 'password=***'),
            (r'passwd\s*[=:]\s*["\']?([^"\'\s]+)["\']?', 'passwd=***'),
            (r'api_key\s*[=:]\s*["\']?([^"\'\s]+)["\']?', 'api_key=***'),
            (r'secret\s*[=:]\s*["\']?([^"\'\s]+)["\']?', 'secret=***'),
            (r'token\s*[=:]\s*["\']?([^"\'\s]+)["\']?', 'token=***'),
            (r'--password\s+([^\s]+)', '--password ***'),
            (r'-p\s+([^\s]+)', '-p ***'),
        ]
        
        # 危险命令模式
        self.dangerous_commands = [
            r'rm\s+-rf\s+/',
            r'sudo\s+rm\s+-rf',
            r'format\s+c:',
            r'del\s+/q\s+/s\s+c:\\',
            r'shutdown\s+(-s|-r|-h)',
            r'halt',
            r'reboot',
        ]
        
        self.filtered_count = 0
        self.blocked_count = 0
    
    @property
    def name(self) -> str:
        return "security_filter"
    
    @property
    def priority(self) -> PluginPriority:
        return PluginPriority.HIGHEST  # 安全过滤应该最先执行
    
    @property
    def description(self) -> str:
        return "Filters sensitive information and blocks dangerous commands"
    
    def should_process_tool(self, tool: BaseTool, agent: Optional['AgenticEdit']) -> bool:
        """只处理执行命令工具和其他可能包含敏感信息的工具"""
        return self.enabled and isinstance(tool, (ExecuteCommandTool,))
    
    def before_tool_execution(
        self, 
        tool: BaseTool, 
        agent: Optional['AgenticEdit'],
        context: Optional[Dict[str, Any]] = None
    ) -> BaseTool:
        """在工具执行前过滤敏感信息"""
        if not self.should_process_tool(tool, agent):
            return tool
        
        # 创建工具的副本以避免修改原始工具
        filtered_tool = deepcopy(tool)
        
        if isinstance(filtered_tool, ExecuteCommandTool):
            original_command = filtered_tool.command
            
            # 检查危险命令
            if self._is_dangerous_command(original_command):
                self.blocked_count += 1
                self.log_warning(f"Blocked dangerous command: {original_command}")
                # 创建一个安全的替代命令
                filtered_tool.command = "echo 'BLOCKED: Potentially dangerous command detected'"
                return filtered_tool
            
            # 过滤敏感信息
            filtered_command = self._filter_sensitive_info(original_command)
            if filtered_command != original_command:
                self.filtered_count += 1
                self.log_info(f"Filtered sensitive information from command")
                filtered_tool.command = filtered_command
        
        return filtered_tool
    
    def after_tool_execution(
        self, 
        tool: BaseTool, 
        tool_result: ToolResult, 
        agent: Optional['AgenticEdit'],
        context: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """在工具执行后过滤结果中的敏感信息"""
        if not self.should_process_tool(tool, agent):
            return tool_result
        
        # 创建结果的副本
        filtered_result = ToolResult(
            success=tool_result.success,
            message=self._filter_sensitive_info(tool_result.message),
            content=self._filter_result_content(tool_result.content)
        )
        
        return filtered_result
    
    def _is_dangerous_command(self, command: str) -> bool:
        """检查是否为危险命令"""
        command_lower = command.lower().strip()
        
        for pattern in self.dangerous_commands:
            if re.search(pattern, command_lower, re.IGNORECASE):
                return True
        
        return False
    
    def _filter_sensitive_info(self, text: str) -> str:
        """过滤文本中的敏感信息"""
        if not text:
            return text
        
        filtered_text = text
        
        for pattern, replacement in self.sensitive_patterns:
            filtered_text = re.sub(pattern, replacement, filtered_text, flags=re.IGNORECASE)
        
        return filtered_text
    
    def _filter_result_content(self, content: Any) -> Any:
        """过滤结果内容中的敏感信息"""
        if content is None:
            return content
        
        if isinstance(content, str):
            return self._filter_sensitive_info(content)
        
        elif isinstance(content, dict):
            filtered_content = {}
            for key, value in content.items():
                if isinstance(value, str):
                    filtered_content[key] = self._filter_sensitive_info(value)
                else:
                    filtered_content[key] = value
            return filtered_content
        
        elif isinstance(content, list):
            return [
                self._filter_sensitive_info(item) if isinstance(item, str) else item
                for item in content
            ]
        
        return content
    
    def add_sensitive_pattern(self, pattern: str, replacement: str) -> None:
        """添加新的敏感信息模式"""
        self.sensitive_patterns.append((pattern, replacement))
        self.log_info(f"Added new sensitive pattern: {pattern}")
    
    def add_dangerous_command(self, pattern: str) -> None:
        """添加新的危险命令模式"""
        self.dangerous_commands.append(pattern)
        self.log_info(f"Added new dangerous command pattern: {pattern}")
    
    def get_filter_statistics(self) -> Dict[str, Any]:
        """获取过滤统计信息"""
        return {
            "filtered_count": self.filtered_count,
            "blocked_count": self.blocked_count,
            "sensitive_patterns_count": len(self.sensitive_patterns),
            "dangerous_patterns_count": len(self.dangerous_commands)
        }
    
    def reset_statistics(self) -> None:
        """重置统计信息"""
        self.filtered_count = 0
        self.blocked_count = 0
        self.log_info("Filter statistics reset") 