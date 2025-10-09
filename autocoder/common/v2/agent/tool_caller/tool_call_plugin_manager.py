"""
Tool Call Plugin Manager

工具调用插件管理器，负责管理和协调插件的执行。
"""

import os
import importlib
import importlib.util
import inspect
from typing import List, Dict, Optional, Any, TYPE_CHECKING
from autocoder.common.v2.agent.agentic_edit_types import BaseTool, ToolResult
from .plugins.plugin_interface import ToolCallPlugin, PluginPriority
from loguru import logger

if TYPE_CHECKING:
    from autocoder.common.v2.agent.agentic_edit import AgenticEdit


class ToolCallPluginManager:
    """
    工具调用插件管理器
    
    负责插件的注册、管理和执行流程控制。
    """
    
    def __init__(self):
        """初始化插件管理器"""
        self._plugins: List[ToolCallPlugin] = []
        self._plugin_registry: Dict[str, ToolCallPlugin] = {}
        self._global_enabled = True
        
    @property
    def plugins(self) -> List[ToolCallPlugin]:
        """获取所有插件（按优先级排序）"""
        return sorted(self._plugins, key=lambda p: p.priority.value)
    
    @property
    def enabled_plugins(self) -> List[ToolCallPlugin]:
        """获取所有启用的插件（按优先级排序）"""
        if not self._global_enabled:
            return []
        return [p for p in self.plugins if p.enabled]
    
    @property
    def global_enabled(self) -> bool:
        """插件系统是否全局启用"""
        return self._global_enabled
    
    def set_global_enabled(self, enabled: bool) -> None:
        """设置插件系统全局启用状态"""
        self._global_enabled = enabled
        logger.info(f"Plugin system globally {'enabled' if enabled else 'disabled'}")
    
    def register_plugin(self, plugin: ToolCallPlugin) -> bool:
        """
        注册插件
        
        Args:
            plugin: 插件实例
            
        Returns:
            bool: 注册是否成功
        """
        try:
            if plugin.name in self._plugin_registry:
                logger.warning(f"Plugin '{plugin.name}' already registered, replacing")
                self.unregister_plugin(plugin.name)
            
            self._plugins.append(plugin)
            self._plugin_registry[plugin.name] = plugin
            
            logger.info(f"Registered plugin: {plugin.name} (priority: {plugin.priority.value})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register plugin {plugin.name}: {str(e)}")
            return False
    
    def unregister_plugin(self, plugin_name: str) -> bool:
        """
        注销插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 注销是否成功
        """
        try:
            if plugin_name not in self._plugin_registry:
                logger.warning(f"Plugin '{plugin_name}' not found")
                return False
            
            plugin = self._plugin_registry[plugin_name]
            self._plugins.remove(plugin)
            del self._plugin_registry[plugin_name]
            
            logger.info(f"Unregistered plugin: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister plugin {plugin_name}: {str(e)}")
            return False
    
    def get_plugin(self, plugin_name: str) -> Optional[ToolCallPlugin]:
        """
        获取插件实例
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            Optional[ToolCallPlugin]: 插件实例，如果不存在则返回None
        """
        return self._plugin_registry.get(plugin_name)
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """
        启用插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 是否成功
        """
        plugin = self.get_plugin(plugin_name)
        if plugin and hasattr(plugin, 'set_enabled'):
            plugin.set_enabled(True)
            logger.info(f"Enabled plugin: {plugin_name}")
            return True
        return False
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """
        禁用插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 是否成功
        """
        plugin = self.get_plugin(plugin_name)
        if plugin and hasattr(plugin, 'set_enabled'):
            plugin.set_enabled(False)
            logger.info(f"Disabled plugin: {plugin_name}")
            return True
        return False
    
    def load_plugins_from_directory(self, directory: str) -> int:
        """
        从指定目录加载插件
        
        Args:
            directory: 插件目录路径
            
        Returns:
            int: 成功加载的插件数量
        """
        if not os.path.exists(directory):
            logger.warning(f"Plugin directory not found: {directory}")
            return 0
        
        loaded_count = 0
        
        for filename in os.listdir(directory):
            if filename.endswith('.py') and not filename.startswith('__'):
                module_name = filename[:-3]
                try:
                    # 动态导入模块
                    spec = importlib.util.spec_from_file_location(
                        module_name, 
                        os.path.join(directory, filename)
                    )
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # 查找插件类
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, ToolCallPlugin) and 
                            obj != ToolCallPlugin):
                            
                            # 实例化并注册插件
                            plugin_instance = obj()
                            if self.register_plugin(plugin_instance):
                                loaded_count += 1
                                
                except Exception as e:
                    logger.error(f"Failed to load plugin from {filename}: {str(e)}")
        
        logger.info(f"Loaded {loaded_count} plugins from {directory}")
        return loaded_count
    
    def execute_before_hooks(
        self, 
        tool: BaseTool, 
        agent: Optional['AgenticEdit'],
        context: Optional[Dict[str, Any]] = None
    ) -> BaseTool:
        """
        执行工具执行前的钩子
        
        Args:
            tool: 工具实例
            agent: 代理实例
            context: 上下文信息
            
        Returns:
            BaseTool: 处理后的工具实例
        """
        if not self._global_enabled:
            return tool
        
        current_tool = tool
        processed_plugins = []
        
        for plugin in self.enabled_plugins:
            try:
                if plugin.should_process_tool(current_tool, agent):
                    current_tool = plugin.before_tool_execution(current_tool, agent, context)
                    processed_plugins.append(plugin.name)
            except Exception as e:
                logger.error(f"Error in plugin {plugin.name} before_tool_execution: {str(e)}")
        
        if processed_plugins:
            logger.debug(f"Before hooks executed by plugins: {', '.join(processed_plugins)}")
        
        return current_tool
    
    def execute_after_hooks(
        self, 
        tool: BaseTool, 
        tool_result: ToolResult, 
        agent: Optional['AgenticEdit'],
        context: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """
        执行工具执行后的钩子
        
        Args:
            tool: 工具实例
            tool_result: 工具执行结果
            agent: 代理实例
            context: 上下文信息
            
        Returns:
            ToolResult: 处理后的工具执行结果
        """
        if not self._global_enabled:
            return tool_result
        
        current_result = tool_result
        processed_plugins = []
        
        for plugin in self.enabled_plugins:
            try:
                if plugin.should_process_tool(tool, agent):
                    current_result = plugin.after_tool_execution(tool, current_result, agent, context)
                    processed_plugins.append(plugin.name)
            except Exception as e:
                logger.error(f"Error in plugin {plugin.name} after_tool_execution: {str(e)}")
        
        if processed_plugins:
            logger.debug(f"After hooks executed by plugins: {', '.join(processed_plugins)}")
        
        return current_result
    
    def execute_error_hooks(
        self, 
        tool: BaseTool, 
        error: Exception, 
        agent: Optional['AgenticEdit'],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[ToolResult]:
        """
        执行工具执行错误的钩子
        
        Args:
            tool: 工具实例
            error: 异常信息
            agent: 代理实例
            context: 上下文信息
            
        Returns:
            Optional[ToolResult]: 如果某个插件提供了替代结果，则返回该结果
        """
        if not self._global_enabled:
            return None
        
        for plugin in self.enabled_plugins:
            try:
                if plugin.should_process_tool(tool, agent):
                    result = plugin.on_tool_error(tool, error, agent, context)
                    if result is not None:
                        logger.info(f"Plugin {plugin.name} provided error recovery result")
                        return result
            except Exception as e:
                logger.error(f"Error in plugin {plugin.name} on_tool_error: {str(e)}")
        
        return None
    
    def get_plugin_status(self) -> Dict[str, Any]:
        """
        获取插件系统状态
        
        Returns:
            Dict[str, Any]: 插件系统状态信息
        """
        return {
            "global_enabled": self._global_enabled,
            "total_plugins": len(self._plugins),
            "enabled_plugins": len(self.enabled_plugins),
            "plugins": [
                {
                    "name": plugin.name,
                    "priority": plugin.priority.value,
                    "enabled": plugin.enabled,
                    "description": plugin.description
                }
                for plugin in self.plugins
            ]
        }
    
    def clear_plugins(self) -> None:
        """清空所有插件"""
        self._plugins.clear()
        self._plugin_registry.clear()
        logger.info("All plugins cleared") 