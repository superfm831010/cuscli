"""
Tool Caller Module

提供工具调用和插件管理功能的AC模块。
支持工具执行的插件机制，允许插件拦截和修改工具的输入参数和输出结果。
"""

from .tool_caller import ToolCaller
from .tool_call_plugin_manager import ToolCallPluginManager
from .plugins.plugin_interface import ToolCallPlugin, PluginPriority
from .plugins.base_plugin import BaseToolCallPlugin
from .default_tool_resolver_map import get_default_tool_resolver_map, DEFAULT_TOOL_RESOLVER_MAP

__all__ = [
    "ToolCaller",
    "ToolCallPluginManager", 
    "ToolCallPlugin",
    "BaseToolCallPlugin",
    "PluginPriority",
    "get_default_tool_resolver_map",
    "DEFAULT_TOOL_RESOLVER_MAP"
]

__version__ = "1.0.0" 