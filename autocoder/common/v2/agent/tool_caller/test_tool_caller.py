"""
Tool Caller Test

测试 ToolCaller 和插件系统的基本功能。
"""

import pytest
import tempfile
from unittest.mock import Mock, MagicMock
from autocoder.common import AutoCoderArgs
from autocoder.common.v2.agent.agentic_edit_types import BaseTool, ToolResult, ExecuteCommandTool
from autocoder.common.v2.agent.agentic_edit_tools.base_tool_resolver import BaseToolResolver
try:
    from .tool_caller import ToolCaller
    from .plugins.examples.logging_plugin import LoggingPlugin
    from .plugins.examples.security_filter_plugin import SecurityFilterPlugin
except ImportError:
    # 当直接运行测试文件时的导入方式
    from tool_caller import ToolCaller
    from plugins.examples.logging_plugin import LoggingPlugin
    from plugins.examples.security_filter_plugin import SecurityFilterPlugin


class MockTool(BaseTool):
    """测试用的模拟工具"""
    value: str = "test"


class MockToolResolver(BaseToolResolver):
    """测试用的模拟工具解析器"""
    
    def resolve(self) -> ToolResult:
        # 根据工具类型返回不同的结果
        if isinstance(self.tool, ExecuteCommandTool):
            return ToolResult(
                success=True,
                message="Mock command executed successfully",
                content={"result": "mock_result", "command": self.tool.command}
            )
        elif hasattr(self.tool, 'value'):
            return ToolResult(
                success=True,
                message="Mock tool executed successfully",
                content={"result": "mock_result", "value": self.tool.value}
            )
        else:
            return ToolResult(
                success=True,
                message="Mock tool executed successfully",
                content={"result": "mock_result", "tool_type": type(self.tool).__name__}
            )


class TestToolCaller:
    """ToolCaller 测试类"""
    
    def setup_method(self):
        """测试前的设置"""
        self.mock_agent = Mock()
        self.temp_dir = tempfile.mkdtemp()
        self.args = AutoCoderArgs(source_dir=self.temp_dir)
        
        # 创建工具解析器映射
        self.tool_resolver_map = {
            MockTool: MockToolResolver,
            ExecuteCommandTool: MockToolResolver  # 简化测试
        }
        
        # 创建工具调用器
        self.tool_caller = ToolCaller(
            tool_resolver_map=self.tool_resolver_map,
            agent=self.mock_agent,
            args=self.args,
            enable_plugins=True
        )
    
    def teardown_method(self):
        """测试后的清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_basic_tool_execution(self):
        """测试基本工具执行"""
        tool = MockTool(value="test_value")
        result = self.tool_caller.call_tool(tool)
        
        assert result.success is True
        assert "successfully" in result.message
        assert result.content["value"] == "test_value"
    
    def test_tool_execution_without_plugins(self):
        """测试禁用插件时的工具执行"""
        self.tool_caller.set_plugins_enabled(False)
        
        tool = MockTool(value="no_plugins")
        result = self.tool_caller.call_tool(tool)
        
        assert result.success is True
        assert result.content["value"] == "no_plugins"
    
    def test_logging_plugin(self):
        """测试日志插件"""
        # 注册日志插件
        logging_plugin = LoggingPlugin(enabled=True, detailed_logging=True)
        assert self.tool_caller.register_plugin(logging_plugin) is True
        
        # 执行工具
        tool = MockTool(value="with_logging")
        result = self.tool_caller.call_tool(tool)
        
        assert result.success is True
        
        # 检查日志插件的记录
        history = logging_plugin.get_call_history()
        assert len(history) >= 2  # before 和 after 两条记录
        
        # 检查记录内容
        before_records = [h for h in history if h["phase"] == "before_execution"]
        after_records = [h for h in history if h["phase"] == "after_execution"]
        
        assert len(before_records) >= 1
        assert len(after_records) >= 1
        assert before_records[0]["tool_name"] == "MockTool"
        assert after_records[0]["success"] is True
    
    def test_security_filter_plugin(self):
        """测试安全过滤插件"""
        # 注册安全过滤插件
        security_plugin = SecurityFilterPlugin(enabled=True)
        assert self.tool_caller.register_plugin(security_plugin) is True
        
        # 测试过滤敏感命令
        dangerous_tool = ExecuteCommandTool(
            command="rm -rf /",
            requires_approval=False
        )
        result = self.tool_caller.call_tool(dangerous_tool)
        
        # 应该被过滤阻止
        assert result.success is True  # 因为被替换为安全命令
        assert security_plugin.get_filter_statistics()["blocked_count"] >= 1
        
        # 测试过滤敏感信息
        sensitive_tool = ExecuteCommandTool(
            command="echo password=secret123",
            requires_approval=False
        )
        result = self.tool_caller.call_tool(sensitive_tool)
        
        assert result.success is True
        stats = security_plugin.get_filter_statistics()
        assert stats["filtered_count"] >= 1
    
    def test_plugin_priority(self):
        """测试插件优先级"""
        # 注册两个插件
        security_plugin = SecurityFilterPlugin(enabled=True)  # HIGHEST 优先级
        logging_plugin = LoggingPlugin(enabled=True)  # LOW 优先级
        
        self.tool_caller.register_plugin(security_plugin)
        self.tool_caller.register_plugin(logging_plugin)
        
        # 获取插件状态
        status = self.tool_caller.get_plugin_status()
        plugins = status["plugins"]
        
        # 安全插件应该排在前面（优先级更高）
        assert plugins[0]["name"] == "security_filter"
        assert plugins[1]["name"] == "logging"
    
    def test_plugin_management(self):
        """测试插件管理功能"""
        logging_plugin = LoggingPlugin()
        
        # 注册插件
        assert self.tool_caller.register_plugin(logging_plugin) is True
        
        # 检查插件状态
        status = self.tool_caller.get_plugin_status()
        assert status["total_plugins"] == 1
        assert status["enabled_plugins"] == 1
        
        # 禁用插件
        assert self.tool_caller.disable_plugin("logging") is True
        status = self.tool_caller.get_plugin_status()
        assert status["enabled_plugins"] == 0
        
        # 启用插件
        assert self.tool_caller.enable_plugin("logging") is True
        status = self.tool_caller.get_plugin_status()
        assert status["enabled_plugins"] == 1
        
        # 注销插件
        assert self.tool_caller.unregister_plugin("logging") is True
        status = self.tool_caller.get_plugin_status()
        assert status["total_plugins"] == 0
    
    def test_statistics(self):
        """测试统计功能"""
        # 执行几个工具调用
        for i in range(3):
            tool = MockTool(value=f"test_{i}")
            self.tool_caller.call_tool(tool)
        
        # 检查统计信息
        stats = self.tool_caller.get_stats()
        assert stats["total_calls"] == 3
        assert stats["successful_calls"] == 3
        assert stats["failed_calls"] == 0
        assert stats["success_rate"] == 1.0
        
        # 重置统计
        self.tool_caller.reset_stats()
        stats = self.tool_caller.get_stats()
        assert stats["total_calls"] == 0
    
    def test_error_handling(self):
        """测试错误处理"""
        # 创建一个会抛出异常的解析器
        class ErrorToolResolver(BaseToolResolver):
            def resolve(self) -> ToolResult:
                raise ValueError("Test error")
        
        # 临时替换解析器
        original_resolver = self.tool_caller.tool_resolver_map[MockTool]
        self.tool_caller.tool_resolver_map[MockTool] = ErrorToolResolver
        
        try:
            tool = MockTool(value="error_test")
            result = self.tool_caller.call_tool(tool)
            
            assert result.success is False
            assert "Test error" in result.message
            
            # 检查统计
            stats = self.tool_caller.get_stats()
            assert stats["failed_calls"] > 0
            
        finally:
            # 恢复原始解析器
            self.tool_caller.tool_resolver_map[MockTool] = original_resolver


def test_integration():
    """集成测试"""
    args = AutoCoderArgs(source_dir=".")
    
    # 创建简单的工具解析器映射
    tool_resolver_map = {
        MockTool: MockToolResolver
    }
    
    # 创建工具调用器
    tool_caller = ToolCaller(
        tool_resolver_map=tool_resolver_map,
        args=args,
        enable_plugins=True
    )
    
    # 注册插件
    logging_plugin = LoggingPlugin()
    tool_caller.register_plugin(logging_plugin)
    
    # 执行工具
    tool = MockTool(value="integration_test")
    result = tool_caller.call_tool(tool)
    
    assert result.success is True
    assert logging_plugin.get_call_history()


if __name__ == "__main__":
    # 运行简单的测试
    test_integration()
    print("Integration test passed!")
    
    # 运行完整测试需要 pytest
    print("Run 'pytest test_tool_caller.py -v' for full test suite") 