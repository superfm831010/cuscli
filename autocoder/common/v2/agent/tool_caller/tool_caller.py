"""
Tool Caller

工具调用器核心模块，负责工具执行和插件系统集成。
"""

import time
from typing import Dict, Type, Optional, Any, TYPE_CHECKING
from autocoder.common.v2.agent.agentic_edit_types import BaseTool, ToolResult
from autocoder.common.v2.agent.agentic_edit_tools.base_tool_resolver import BaseToolResolver
from .tool_call_plugin_manager import ToolCallPluginManager
from .default_tool_resolver_map import get_default_tool_resolver_map
from loguru import logger

if TYPE_CHECKING:
    from autocoder.common.v2.agent.agentic_edit import AgenticEdit
    from autocoder.common import AutoCoderArgs


class ToolCaller:
    """
    工具调用器
    
    负责工具的调用执行，集成插件系统，提供工具执行的拦截和修改能力。
    """
    
    def __init__(
        self,
        tool_resolver_map: Optional[Dict[Type[BaseTool], Type[BaseToolResolver]]] = None,
        agent: Optional['AgenticEdit'] = None,
        args: Optional['AutoCoderArgs'] = None,
        enable_plugins: bool = True
    ):
        """
        初始化工具调用器
        
        Args:
            tool_resolver_map: 工具类型到解析器类的映射，如果为None则使用默认映射
            agent: 代理实例
            args: 自动编码器参数
            enable_plugins: 是否启用插件系统
        """
        self.tool_resolver_map = tool_resolver_map or get_default_tool_resolver_map()
        self.agent = agent
        self.args = args
        self.plugin_manager = ToolCallPluginManager()
        self.plugin_manager.set_global_enabled(enable_plugins)
        
        # 统计信息
        self._stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "plugin_intercepted_calls": 0,
            "total_execution_time": 0.0
        }
        
        # 自动加载插件
        self._auto_load_plugins()
    
    def _auto_load_plugins(self) -> None:
        """自动加载插件"""
        try:
            # 从默认插件目录加载插件
            if self.args and hasattr(self.args, 'source_dir'):
                plugin_dirs = [
                    f"{self.args.source_dir}/.auto-coder/plugins/tool_caller",
                    f"{self.args.source_dir}/plugins/tool_caller"
                ]
                for plugin_dir in plugin_dirs:
                    if plugin_dir:
                        loaded = self.plugin_manager.load_plugins_from_directory(plugin_dir)
                        if loaded > 0:
                            logger.info(f"Auto-loaded {loaded} plugins from {plugin_dir}")
        except Exception as e:
            logger.warning(f"Failed to auto-load plugins: {str(e)}")
    
    def call_tool(
        self, 
        tool: BaseTool, 
        context: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """
        调用工具执行
        
        Args:
            tool: 工具实例
            context: 上下文信息
            
        Returns:
            ToolResult: 工具执行结果
        """
        start_time = time.time()
        self._stats["total_calls"] += 1
        
        # 创建执行上下文
        exec_context = self._create_execution_context(tool, context)
        
        try:
            # 执行前置插件钩子
            processed_tool = self.plugin_manager.execute_before_hooks(
                tool, self.agent, exec_context
            )
            
            # 检查工具是否被插件修改
            if processed_tool != tool:
                self._stats["plugin_intercepted_calls"] += 1
                logger.debug(f"Tool {type(tool).__name__} was modified by plugins")
            
            # 执行工具
            tool_result = self._execute_tool(processed_tool)
            
            # 执行后置插件钩子
            final_result = self.plugin_manager.execute_after_hooks(
                processed_tool, tool_result, self.agent, exec_context
            )
            
            # 更新统计信息
            if final_result.success:
                self._stats["successful_calls"] += 1
            else:
                self._stats["failed_calls"] += 1
            
            execution_time = time.time() - start_time
            self._stats["total_execution_time"] += execution_time
            
            # 添加执行统计到结果中
            if hasattr(final_result, 'content') and isinstance(final_result.content, dict):
                final_result.content["execution_stats"] = {
                    "execution_time": execution_time,
                    "plugins_processed": len(self.plugin_manager.enabled_plugins)
                }
            
            return final_result
            
        except Exception as e:
            # 执行错误插件钩子
            recovery_result = self.plugin_manager.execute_error_hooks(
                tool, e, self.agent, exec_context
            )
            
            if recovery_result is not None:
                logger.info(f"Plugin provided recovery result for {type(tool).__name__}")
                self._stats["successful_calls"] += 1
                return recovery_result
            
            # 没有插件提供恢复结果，返回错误
            self._stats["failed_calls"] += 1
            logger.error(f"Tool execution failed: {str(e)}")
            
            return ToolResult(
                success=False,
                message=f"Tool execution failed: {str(e)}",
                content={
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "tool_type": type(tool).__name__
                }
            )
    
    def _create_execution_context(
        self, 
        tool: BaseTool, 
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        创建执行上下文
        
        Args:
            tool: 工具实例
            context: 额外的上下文信息
            
        Returns:
            Dict[str, Any]: 执行上下文
        """
        exec_context = {
            "tool_type": type(tool).__name__,
            "tool_params": tool.model_dump() if hasattr(tool, 'model_dump') else {},
            "timestamp": time.time(),
            "call_id": f"{type(tool).__name__}_{int(time.time() * 1000)}",
            "agent_present": self.agent is not None,
            "stats": self._stats.copy()
        }
        
        if context:
            exec_context.update(context)
        
        return exec_context
    
    def _execute_tool(self, tool: BaseTool) -> ToolResult:
        """
        执行工具的核心逻辑
        
        Args:
            tool: 工具实例
            
        Returns:
            ToolResult: 工具执行结果
        """
        # 获取工具解析器类
        resolver_cls = self.tool_resolver_map.get(type(tool))
        if not resolver_cls:
            error_msg = f"No resolver implemented for tool {type(tool).__name__}"
            logger.error(error_msg)
            return ToolResult(
                success=False,
                message=error_msg,
                content=None
            )
        
        # 创建并执行解析器
        try:
            logger.info(f"Creating resolver for tool: {type(tool).__name__}")
            resolver = resolver_cls(
                agent=self.agent, 
                tool=tool, 
                args=self.args
            )
            
            logger.info(f"Executing tool: {type(tool).__name__}")
            tool_result = resolver.resolve()
            
            logger.info(f"Tool Result: Success={tool_result.success}")
            return tool_result
            
        except Exception as e:
            logger.exception(f"Error resolving tool {type(tool).__name__}: {e}")
            raise
    
    def register_plugin(self, plugin: 'ToolCallPlugin') -> bool:
        """
        注册插件
        
        Args:
            plugin: 插件实例
            
        Returns:
            bool: 注册是否成功
        """
        return self.plugin_manager.register_plugin(plugin)
    
    def unregister_plugin(self, plugin_name: str) -> bool:
        """
        注销插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 注销是否成功
        """
        return self.plugin_manager.unregister_plugin(plugin_name)
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """
        启用插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 是否成功
        """
        return self.plugin_manager.enable_plugin(plugin_name)
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """
        禁用插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 是否成功
        """
        return self.plugin_manager.disable_plugin(plugin_name)
    
    def set_plugins_enabled(self, enabled: bool) -> None:
        """
        设置插件系统启用状态
        
        Args:
            enabled: 是否启用
        """
        self.plugin_manager.set_global_enabled(enabled)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = self._stats.copy()
        stats["plugin_status"] = self.plugin_manager.get_plugin_status()
        
        # 计算成功率
        if stats["total_calls"] > 0:
            stats["success_rate"] = stats["successful_calls"] / stats["total_calls"]
            stats["average_execution_time"] = stats["total_execution_time"] / stats["total_calls"]
        else:
            stats["success_rate"] = 0.0
            stats["average_execution_time"] = 0.0
        
        return stats
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self._stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "plugin_intercepted_calls": 0,
            "total_execution_time": 0.0
        }
        logger.info("Tool caller statistics reset")
    
    def load_plugins_from_directory(self, directory: str) -> int:
        """
        从目录加载插件
        
        Args:
            directory: 插件目录路径
            
        Returns:
            int: 成功加载的插件数量
        """
        return self.plugin_manager.load_plugins_from_directory(directory)
    
    def get_plugin_status(self) -> Dict[str, Any]:
        """
        获取插件状态
        
        Returns:
            Dict[str, Any]: 插件状态信息
        """
        return self.plugin_manager.get_plugin_status() 