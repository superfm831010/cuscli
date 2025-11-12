#!/usr/bin/env python3
"""
Tool Caller Usage Example

展示如何使用 tool_caller 模块进行工具调用和插件管理。
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../../..'))

from autocoder.common import AutoCoderArgs
from autocoder.common.v2.agent.agentic_edit_types import ExecuteCommandTool, ReadFileTool, ToolResult
from autocoder.common.v2.agent.agentic_edit_tools.base_tool_resolver import BaseToolResolver
from autocoder.common.v2.agent.tool_caller import ToolCaller
from autocoder.common.v2.agent.tool_caller.plugins.examples import LoggingPlugin, SecurityFilterPlugin


class DemoToolResolver(BaseToolResolver):
    """演示用的简单工具解析器"""
    
    def resolve(self) -> ToolResult:
        """简化的工具解析实现"""
        if isinstance(self.tool, ExecuteCommandTool):
            return ToolResult(
                success=True,
                message=f"Demo: Command '{self.tool.command}' executed",
                content={"output": f"Mock output for: {self.tool.command}"}
            )
        elif isinstance(self.tool, ReadFileTool):
            return ToolResult(
                success=True,
                message=f"Demo: File '{self.tool.path}' read",
                content={"content": f"Mock content of {self.tool.path}"}
            )
        else:
            return ToolResult(
                success=False,
                message=f"Demo: Unsupported tool type {type(self.tool).__name__}"
            )


def main():
    """主演示函数"""
    print("=" * 60)
    print("Tool Caller Module Usage Example")
    print("=" * 60)
    
    # 1. 创建工具解析器映射
    print("\n1. Setting up tool resolver mapping...")
    tool_resolver_map = {
        ExecuteCommandTool: DemoToolResolver,
        ReadFileTool: DemoToolResolver
    }
    
    # 2. 创建工具调用器
    print("2. Creating ToolCaller instance...")
    args = AutoCoderArgs(source_dir=".")
    tool_caller = ToolCaller(
        tool_resolver_map=tool_resolver_map,
        args=args,
        enable_plugins=True
    )
    
    # 3. 注册插件
    print("3. Registering plugins...")
    logging_plugin = LoggingPlugin(enabled=True, detailed_logging=True)
    security_plugin = SecurityFilterPlugin(enabled=True)
    
    tool_caller.register_plugin(logging_plugin)
    tool_caller.register_plugin(security_plugin)
    
    print(f"   - Registered logging plugin (priority: {logging_plugin.priority.value})")
    print(f"   - Registered security filter plugin (priority: {security_plugin.priority.value})")
    
    # 4. 获取插件状态
    print("\n4. Plugin system status:")
    status = tool_caller.get_plugin_status()
    print(f"   - Total plugins: {status['total_plugins']}")
    print(f"   - Enabled plugins: {status['enabled_plugins']}")
    for plugin_info in status['plugins']:
        print(f"   - {plugin_info['name']}: priority={plugin_info['priority']}, enabled={plugin_info['enabled']}")
    
    # 5. 执行一些工具调用
    print("\n5. Executing tool calls...")
    
    # 安全命令
    safe_tool = ExecuteCommandTool(command="echo 'Hello World'", requires_approval=False)
    print(f"\n   Executing safe command: {safe_tool.command}")
    result = tool_caller.call_tool(safe_tool)
    print(f"   Result: {result.success} - {result.message}")
    
    # 包含敏感信息的命令（会被过滤）
    sensitive_tool = ExecuteCommandTool(command="mysql -u root -p secret123", requires_approval=False)
    print(f"\n   Executing sensitive command: {sensitive_tool.command}")
    result = tool_caller.call_tool(sensitive_tool)
    print(f"   Result: {result.success} - {result.message}")
    
    # 危险命令（会被阻止）
    dangerous_tool = ExecuteCommandTool(command="rm -rf /", requires_approval=False)
    print(f"\n   Executing dangerous command: {dangerous_tool.command}")
    result = tool_caller.call_tool(dangerous_tool)
    print(f"   Result: {result.success} - {result.message}")
    
    # 文件读取
    read_tool = ReadFileTool(path="example.txt")
    print(f"\n   Reading file: {read_tool.path}")
    result = tool_caller.call_tool(read_tool)
    print(f"   Result: {result.success} - {result.message}")
    
    # 6. 查看统计信息
    print("\n6. Tool execution statistics:")
    stats = tool_caller.get_stats()
    print(f"   - Total calls: {stats['total_calls']}")
    print(f"   - Successful calls: {stats['successful_calls']}")
    print(f"   - Failed calls: {stats['failed_calls']}")
    print(f"   - Success rate: {stats['success_rate']:.2%}")
    print(f"   - Plugin intercepted calls: {stats['plugin_intercepted_calls']}")
    print(f"   - Average execution time: {stats['average_execution_time']:.3f}s")
    
    # 7. 查看插件统计
    print("\n7. Plugin statistics:")
    
    # 日志插件统计
    log_stats = logging_plugin.get_statistics()
    print(f"   Logging plugin:")
    print(f"     - Total logged calls: {log_stats['total_logged_calls']}")
    print(f"     - Success rate: {log_stats['success_rate']:.2%}")
    print(f"     - Call history entries: {len(logging_plugin.get_call_history())}")
    
    # 安全过滤插件统计
    filter_stats = security_plugin.get_filter_statistics()
    print(f"   Security filter plugin:")
    print(f"     - Filtered count: {filter_stats['filtered_count']}")
    print(f"     - Blocked count: {filter_stats['blocked_count']}")
    print(f"     - Sensitive patterns: {filter_stats['sensitive_patterns_count']}")
    print(f"     - Dangerous patterns: {filter_stats['dangerous_patterns_count']}")
    
    # 8. 插件管理演示
    print("\n8. Plugin management demo:")
    
    # 禁用日志插件
    print("   Disabling logging plugin...")
    tool_caller.disable_plugin("logging")
    
    # 执行一个命令（不会被日志插件记录）
    test_tool = ExecuteCommandTool(command="echo 'test without logging'", requires_approval=False)
    old_history_length = len(logging_plugin.get_call_history())
    result = tool_caller.call_tool(test_tool)
    new_history_length = len(logging_plugin.get_call_history())
    
    print(f"   Command executed, logging plugin did not record it")
    print(f"   History length before: {old_history_length}, after: {new_history_length}")
    
    # 重新启用日志插件
    print("   Re-enabling logging plugin...")
    tool_caller.enable_plugin("logging")
    
    # 9. 全局插件控制
    print("\n9. Global plugin control demo:")
    print("   Disabling all plugins globally...")
    tool_caller.set_plugins_enabled(False)
    
    # 执行命令（所有插件都被禁用）
    test_tool2 = ExecuteCommandTool(command="rm -rf /tmp", requires_approval=False)  # 通常会被安全插件阻止
    result = tool_caller.call_tool(test_tool2)
    print(f"   Dangerous command executed without plugin protection: {result.success}")
    
    # 重新启用插件系统
    print("   Re-enabling plugin system...")
    tool_caller.set_plugins_enabled(True)
    
    # 10. 最终统计
    print("\n10. Final statistics:")
    final_stats = tool_caller.get_stats()
    print(f"   - Total calls in demo: {final_stats['total_calls']}")
    print(f"   - Overall success rate: {final_stats['success_rate']:.2%}")
    
    print("\n" + "=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 