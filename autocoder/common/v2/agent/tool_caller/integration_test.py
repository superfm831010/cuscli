#!/usr/bin/env python3
"""
Tool Caller Integration Test

验证 ToolCaller 与 AgenticEdit 的集成是否正常工作。
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../../..'))

from unittest.mock import Mock
from autocoder.common import AutoCoderArgs
from autocoder.common.v2.agent.agentic_edit_types import ExecuteCommandTool, ToolResult
from autocoder.common.v2.agent.agentic_edit_tools.base_tool_resolver import BaseToolResolver
from autocoder.common.v2.agent.tool_caller import ToolCaller
from autocoder.common.v2.agent.tool_caller.plugins.examples import LoggingPlugin, SecurityFilterPlugin


class TestToolResolver(BaseToolResolver):
    """测试用的工具解析器"""
    
    def resolve(self) -> ToolResult:
        if isinstance(self.tool, ExecuteCommandTool):
            return ToolResult(
                success=True,
                message=f"Test: Command '{self.tool.command}' executed",
                content={"output": f"Mock output for: {self.tool.command}"}
            )
        else:
            return ToolResult(
                success=False,
                message=f"Test: Unsupported tool type {type(self.tool).__name__}"
            )


def test_tool_caller_basic():
    """测试 ToolCaller 基本功能"""
    print("Testing ToolCaller basic functionality...")
    
    # 创建工具解析器映射
    tool_resolver_map = {
        ExecuteCommandTool: TestToolResolver
    }
    
    # 创建 ToolCaller
    args = AutoCoderArgs(source_dir=".")
    tool_caller = ToolCaller(
        tool_resolver_map=tool_resolver_map,
        args=args,
        enable_plugins=True
    )
    
    # 测试工具调用
    tool = ExecuteCommandTool(command="echo 'test'", requires_approval=False)
    result = tool_caller.call_tool(tool)
    
    assert result.success, f"Tool call failed: {result.message}"
    print("✓ Basic tool calling works")
    
    return tool_caller


def test_plugin_system(tool_caller):
    """测试插件系统"""
    print("Testing plugin system...")
    
    # 注册插件
    logging_plugin = LoggingPlugin(enabled=True)
    security_plugin = SecurityFilterPlugin(enabled=True)
    
    assert tool_caller.register_plugin(logging_plugin), "Failed to register logging plugin"
    assert tool_caller.register_plugin(security_plugin), "Failed to register security plugin"
    print("✓ Plugin registration works")
    
    # 检查插件状态
    status = tool_caller.get_plugin_status()
    assert status["total_plugins"] == 2, f"Expected 2 plugins, got {status['total_plugins']}"
    assert status["enabled_plugins"] == 2, f"Expected 2 enabled plugins, got {status['enabled_plugins']}"
    print("✓ Plugin status reporting works")
    
    # 测试插件功能
    safe_tool = ExecuteCommandTool(command="echo 'safe'", requires_approval=False)
    result = tool_caller.call_tool(safe_tool)
    assert result.success, "Safe tool call failed"
    print("✓ Safe tool call with plugins works")
    
    # 测试安全过滤
    dangerous_tool = ExecuteCommandTool(command="rm -rf /", requires_approval=False)
    result = tool_caller.call_tool(dangerous_tool)
    assert result.success, "Dangerous tool should be blocked but return success"
    print("✓ Security filtering works")
    
    # 检查统计
    log_stats = logging_plugin.get_statistics()
    assert log_stats["total_logged_calls"] > 0, "No calls logged"
    print("✓ Logging plugin statistics work")
    
    filter_stats = security_plugin.get_filter_statistics()
    assert filter_stats["blocked_count"] > 0, "No dangerous commands blocked"
    print("✓ Security filter statistics work")


def test_integration_with_mock_agent():
    """测试与模拟代理的集成"""
    print("Testing integration with mock agent...")
    
    # 创建模拟代理
    mock_agent = Mock()
    
    # 创建工具解析器映射
    tool_resolver_map = {
        ExecuteCommandTool: TestToolResolver
    }
    
    # 创建 ToolCaller
    args = AutoCoderArgs(source_dir=".")
    tool_caller = ToolCaller(
        tool_resolver_map=tool_resolver_map,
        agent=mock_agent,
        args=args,
        enable_plugins=True
    )
    
    # 测试工具调用
    tool = ExecuteCommandTool(command="echo 'integration test'", requires_approval=False)
    result = tool_caller.call_tool(tool)
    
    assert result.success, f"Integration test failed: {result.message}"
    print("✓ Integration with mock agent works")
    
    # 测试统计信息
    stats = tool_caller.get_stats()
    assert stats["total_calls"] > 0, "No calls recorded"
    assert stats["success_rate"] == 1.0, f"Expected 100% success rate, got {stats['success_rate']}"
    print("✓ Statistics collection works")


def main():
    """主测试函数"""
    print("=" * 60)
    print("Tool Caller Integration Test")
    print("=" * 60)
    
    try:
        # 基本功能测试
        tool_caller = test_tool_caller_basic()
        
        # 插件系统测试
        test_plugin_system(tool_caller)
        
        # 集成测试
        test_integration_with_mock_agent()
        
        print("\n" + "=" * 60)
        print("✓ All integration tests passed!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 