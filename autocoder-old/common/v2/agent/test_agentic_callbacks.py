
import pytest
from typing import List
from unittest.mock import Mock

from .agentic_callbacks import (
    AgenticCallBacks,
    AgenticCallbackPoint,
    AgenticContext,
    AgenticCallbackFunction,
    get_global_callbacks,
    register_global_callback,
    execute_global_callbacks
)


class TestAgenticCallBacks:
    """测试 AgenticCallBacks 类的功能"""
    
    def setup_method(self):
        """每个测试方法执行前的设置"""
        self.callbacks = AgenticCallBacks()
        self.context = AgenticContext()
        
        # 创建测试用的回调函数
        self.mock_callback1 = Mock()
        self.mock_callback2 = Mock()
        self.mock_callback3 = Mock()
    
    def test_enum_values(self):
        """测试枚举值是否正确定义"""
        expected_values = {
            "conversation_start",
            "conversation_end", 
            "pre_tool_call",
            "post_tool_call",
            "api_request_start",
            "api_request_end",
            "tool_generated_started",
            "tool_generated_end"
        }
        
        actual_values = {point.value for point in AgenticCallbackPoint}
        assert actual_values == expected_values
    
    def test_register_callback(self):
        """测试注册回调函数"""
        # 测试成功注册
        result = self.callbacks.register(
            AgenticCallbackPoint.CONVERSATION_START, 
            self.mock_callback1
        )
        assert result is True
        assert self.callbacks.get_callback_count(AgenticCallbackPoint.CONVERSATION_START) == 1
        
        # 测试重复注册同一个函数
        result = self.callbacks.register(
            AgenticCallbackPoint.CONVERSATION_START, 
            self.mock_callback1
        )
        assert result is False
        assert self.callbacks.get_callback_count(AgenticCallbackPoint.CONVERSATION_START) == 1
        
        # 测试注册不同函数到同一回调点
        result = self.callbacks.register(
            AgenticCallbackPoint.CONVERSATION_START, 
            self.mock_callback2
        )
        assert result is True
        assert self.callbacks.get_callback_count(AgenticCallbackPoint.CONVERSATION_START) == 2
    
    def test_unregister_callback(self):
        """测试注销回调函数"""
        # 先注册两个回调函数
        self.callbacks.register(AgenticCallbackPoint.PRE_TOOL_CALL, self.mock_callback1)
        self.callbacks.register(AgenticCallbackPoint.PRE_TOOL_CALL, self.mock_callback2)
        assert self.callbacks.get_callback_count(AgenticCallbackPoint.PRE_TOOL_CALL) == 2
        
        # 测试成功注销
        result = self.callbacks.unregister(AgenticCallbackPoint.PRE_TOOL_CALL, self.mock_callback1)
        assert result is True
        assert self.callbacks.get_callback_count(AgenticCallbackPoint.PRE_TOOL_CALL) == 1
        
        # 测试注销不存在的函数
        result = self.callbacks.unregister(AgenticCallbackPoint.PRE_TOOL_CALL, self.mock_callback3)
        assert result is False
        assert self.callbacks.get_callback_count(AgenticCallbackPoint.PRE_TOOL_CALL) == 1
    
    def test_execute_callbacks(self):
        """测试执行回调函数"""
        # 注册多个回调函数
        self.callbacks.register(AgenticCallbackPoint.POST_TOOL_CALL, self.mock_callback1)
        self.callbacks.register(AgenticCallbackPoint.POST_TOOL_CALL, self.mock_callback2)
        
        # 执行回调函数
        errors = self.callbacks.execute_callbacks(AgenticCallbackPoint.POST_TOOL_CALL, self.context)
        
        # 验证所有回调函数都被调用
        assert len(errors) == 0
        self.mock_callback1.assert_called_once_with(self.context)
        self.mock_callback2.assert_called_once_with(self.context)
    
    def test_execute_callbacks_with_exception(self):
        """测试执行回调函数时处理异常"""
        # 创建会抛出异常的回调函数
        def error_callback(context: AgenticContext):
            raise ValueError("测试异常")
        
        self.callbacks.register(AgenticCallbackPoint.API_REQUEST_START, error_callback)
        self.callbacks.register(AgenticCallbackPoint.API_REQUEST_START, self.mock_callback1)
        
        # 执行回调函数
        errors = self.callbacks.execute_callbacks(AgenticCallbackPoint.API_REQUEST_START, self.context)
        
        # 验证异常被捕获，但其他回调函数仍然执行
        assert len(errors) == 1
        assert isinstance(errors[0], ValueError)
        assert str(errors[0]) == "测试异常"
        self.mock_callback1.assert_called_once_with(self.context)
    
    def test_execute_callbacks_with_none_context(self):
        """测试使用 None 上下文执行回调函数"""
        self.callbacks.register(AgenticCallbackPoint.CONVERSATION_END, self.mock_callback1)
        
        # 传入 None 上下文
        errors = self.callbacks.execute_callbacks(AgenticCallbackPoint.CONVERSATION_END, None)
        
        # 验证自动创建了空上下文
        assert len(errors) == 0
        self.mock_callback1.assert_called_once()
        call_args = self.mock_callback1.call_args[0]
        assert isinstance(call_args[0], AgenticContext)
    
    def test_get_callback_count(self):
        """测试获取回调函数数量"""
        # 初始状态应该为0
        assert self.callbacks.get_callback_count(AgenticCallbackPoint.TOOL_GENERATED_STARTED) == 0
        
        # 注册回调函数后数量应该增加
        self.callbacks.register(AgenticCallbackPoint.TOOL_GENERATED_STARTED, self.mock_callback1)
        assert self.callbacks.get_callback_count(AgenticCallbackPoint.TOOL_GENERATED_STARTED) == 1
        
        self.callbacks.register(AgenticCallbackPoint.TOOL_GENERATED_STARTED, self.mock_callback2)
        assert self.callbacks.get_callback_count(AgenticCallbackPoint.TOOL_GENERATED_STARTED) == 2
    
    def test_get_all_callback_counts(self):
        """测试获取所有回调点的回调函数数量"""
        # 注册一些回调函数
        self.callbacks.register(AgenticCallbackPoint.CONVERSATION_START, self.mock_callback1)
        self.callbacks.register(AgenticCallbackPoint.CONVERSATION_START, self.mock_callback2)
        self.callbacks.register(AgenticCallbackPoint.PRE_TOOL_CALL, self.mock_callback1)
        
        counts = self.callbacks.get_all_callback_counts()
        
        assert counts["conversation_start"] == 2
        assert counts["pre_tool_call"] == 1
        assert counts["conversation_end"] == 0
    
    def test_clear_callbacks(self):
        """测试清除指定回调点的回调函数"""
        # 注册一些回调函数
        self.callbacks.register(AgenticCallbackPoint.API_REQUEST_END, self.mock_callback1)
        self.callbacks.register(AgenticCallbackPoint.API_REQUEST_END, self.mock_callback2)
        assert self.callbacks.get_callback_count(AgenticCallbackPoint.API_REQUEST_END) == 2
        
        # 清除回调函数
        cleared_count = self.callbacks.clear_callbacks(AgenticCallbackPoint.API_REQUEST_END)
        assert cleared_count == 2
        assert self.callbacks.get_callback_count(AgenticCallbackPoint.API_REQUEST_END) == 0
    
    def test_clear_all_callbacks(self):
        """测试清除所有回调函数"""
        # 注册一些回调函数到不同回调点
        self.callbacks.register(AgenticCallbackPoint.CONVERSATION_START, self.mock_callback1)
        self.callbacks.register(AgenticCallbackPoint.PRE_TOOL_CALL, self.mock_callback2)
        self.callbacks.register(AgenticCallbackPoint.POST_TOOL_CALL, self.mock_callback3)
        
        total_cleared = self.callbacks.clear_all_callbacks()
        assert total_cleared == 3
        
        # 验证所有回调点都被清空
        counts = self.callbacks.get_all_callback_counts()
        for count in counts.values():
            assert count == 0
    
    def test_has_callbacks(self):
        """测试检查回调点是否有回调函数"""
        # 初始状态应该没有回调函数
        assert self.callbacks.has_callbacks(AgenticCallbackPoint.TOOL_GENERATED_END) is False
        
        # 注册回调函数后应该返回 True
        self.callbacks.register(AgenticCallbackPoint.TOOL_GENERATED_END, self.mock_callback1)
        assert self.callbacks.has_callbacks(AgenticCallbackPoint.TOOL_GENERATED_END) is True
        
        # 清除后应该返回 False
        self.callbacks.clear_callbacks(AgenticCallbackPoint.TOOL_GENERATED_END)
        assert self.callbacks.has_callbacks(AgenticCallbackPoint.TOOL_GENERATED_END) is False


class TestGlobalCallbacks:
    """测试全局回调函数功能"""
    
    def setup_method(self):
        """每个测试方法执行前的设置"""
        # 清除全局回调函数，避免测试间相互影响
        get_global_callbacks().clear_all_callbacks()
        self.mock_callback = Mock()
    
    def test_register_global_callback(self):
        """测试注册全局回调函数"""
        result = register_global_callback(AgenticCallbackPoint.CONVERSATION_START, self.mock_callback)
        assert result is True
        
        global_callbacks = get_global_callbacks()
        assert global_callbacks.has_callbacks(AgenticCallbackPoint.CONVERSATION_START) is True
    
    def test_execute_global_callbacks(self):
        """测试执行全局回调函数"""
        register_global_callback(AgenticCallbackPoint.CONVERSATION_END, self.mock_callback)
        
        context = AgenticContext()
        errors = execute_global_callbacks(AgenticCallbackPoint.CONVERSATION_END, context)
        
        assert len(errors) == 0
        self.mock_callback.assert_called_once_with(context)


class TestAgenticContext:
    """测试 AgenticContext 类"""
    
    def test_create_empty_context(self):
        """测试创建空的上下文"""
        context = AgenticContext()
        assert isinstance(context, AgenticContext)
        
        # 验证可以序列化
        data = context.model_dump()
        assert isinstance(data, dict)


def test_callback_function_signature():
    """测试回调函数签名的类型检查"""
    def valid_callback(context: AgenticContext) -> None:
        """有效的回调函数"""
        pass
    
    def invalid_callback(wrong_param: str) -> None:
        """无效的回调函数（参数类型错误）"""
        pass
    
    callbacks = AgenticCallBacks()
    
    # 注册有效的回调函数应该成功
    result = callbacks.register(AgenticCallbackPoint.CONVERSATION_START, valid_callback)
    assert result is True
    
    # 注册无效的回调函数也会成功（Python的动态特性），但执行时可能出错
    # 这里主要测试类型提示的正确性
    result = callbacks.register(AgenticCallbackPoint.CONVERSATION_START, invalid_callback)
    assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

