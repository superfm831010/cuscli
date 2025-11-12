"""
Auto-Coder SDK API Functions

包含所有主要的公共 API 函数，包括新的清晰 API、工具函数和向后兼容的旧 API。
"""

import warnings
from typing import AsyncIterator, Iterator, Optional, Dict, Any
from .core.auto_coder_core import AutoCoderCore
from .models.options import AutoCodeOptions
from .models.responses import StreamEvent, CodeModificationResult
from autocoder.auto_coder_runner import init_project_if_required as init_project_if_required_buildin
from autocoder.auto_coder_runner import (
    configure as configure_buildin,
    load_tokenizer,
    start as start_engine,
    commit as commit_buildin
)
from autocoder.rag.variable_holder import VariableHolder
from autocoder.utils.llms import get_single_llm


# ===== 新的清晰 API 命名 =====

async def auto_code_stream(
    prompt: str, 
    options: Optional[AutoCodeOptions] = None,
    show_terminal: Optional[bool] = None,
    cancel_token: Optional[str] = None
) -> AsyncIterator[StreamEvent]:
    """
    异步流式代码生成接口
    
    Args:
        prompt: 代码生成提示
        options: 配置选项
        show_terminal: 是否在终端显示友好的渲染输出，None时使用配置中的verbose设置
        cancel_token: 取消令牌，用于中断执行
        
    Yields:
        StreamEvent: 响应事件流
        
    Example:
        >>> import asyncio
        >>> from autocoder.sdk import auto_code_stream, AutoCodeOptions
        >>> 
        >>> async def main():
        ...     options = AutoCodeOptions(max_turns=3)
        ...     async for event in auto_code_stream("Write a hello world function", options):
        ...         print(f"[{event.event_type}] {event.data}")
        >>> 
        >>> asyncio.run(main())
    """
    if options is None:
        options = AutoCodeOptions()
    
    # 如果直接传递了 cancel_token 参数，优先使用它
    if cancel_token is not None:
        options = options.copy(cancel_token=cancel_token)
    
    core = AutoCoderCore(options)
    async for event in core.query_stream(prompt, show_terminal):
        yield event


def auto_code(
    prompt: str, 
    options: Optional[AutoCodeOptions] = None,
    show_terminal: Optional[bool] = None,
    cancel_token: Optional[str] = None
) -> str:
    """
    同步代码生成接口
    
    Args:
        prompt: 代码生成提示
        options: 配置选项
        show_terminal: 是否在终端显示友好的渲染输出，None时使用配置中的verbose设置
        cancel_token: 取消令牌，用于中断执行
        
    Returns:
        str: 生成的代码内容
        
    Example:
        >>> from autocoder.sdk import auto_code, AutoCodeOptions
        >>> 
        >>> options = AutoCodeOptions(max_turns=1)
        >>> response = auto_code("Write a simple calculator function", options)
        >>> print(response)
    """
    if options is None:
        options = AutoCodeOptions()
    
    # 如果直接传递了 cancel_token 参数，优先使用它
    if cancel_token is not None:
        options = options.copy(cancel_token=cancel_token)
    
    core = AutoCoderCore(options)
    events = core.query_sync(prompt, show_terminal)
    
    # 从事件流中提取最终结果
    result_content = ""
    for event in events:
        if event.event_type == "completion":
            result_content = event.data.get("result", "")
            break
        elif event.event_type == "llm_output":
            result_content += event.data.get("text", "")
    
    return result_content


async def auto_code_events_stream(
    prompt: str, 
    options: Optional[AutoCodeOptions] = None,
    show_terminal: bool = False,
    cancel_token: Optional[str] = None
) -> AsyncIterator[StreamEvent]:
    """
    异步流式代码生成接口，返回详细事件流
    
    Args:
        prompt: 代码生成提示
        options: 配置选项
        show_terminal: 是否在终端显示友好的渲染输出（默认为False，避免重复显示）
        cancel_token: 取消令牌，用于中断执行
        
    Yields:
        StreamEvent: 原始事件流，包含详细的执行过程信息
        
    Example:
        >>> import asyncio
        >>> from autocoder.sdk import auto_code_events_stream, AutoCodeOptions
        >>> 
        >>> async def main():
        ...     options = AutoCodeOptions(max_turns=3)
        ...     async for event in auto_code_events_stream("Write a hello world function", options):
        ...         print(f"[{event.event_type}] {event.data}")
        >>> 
        >>> asyncio.run(main())
    """
    if options is None:
        options = AutoCodeOptions()
    
    # 如果直接传递了 cancel_token 参数，优先使用它
    if cancel_token is not None:
        options = options.copy(cancel_token=cancel_token)
    
    core = AutoCoderCore(options)
    
    # 使用桥接层直接获取事件流
    import asyncio
    loop = asyncio.get_event_loop()
    
    # 在线程池中执行同步调用
    event_stream = await loop.run_in_executor(
        core._executor,
        core._sync_run_auto_command,
        prompt
    )
    
    # 直接返回事件流
    for event in event_stream:
        # 可选择性地渲染到终端
        if show_terminal:
            core._render_stream_event(event, show_terminal)
        yield event


def auto_code_events(
    prompt: str, 
    options: Optional[AutoCodeOptions] = None,
    show_terminal: bool = False,
    cancel_token: Optional[str] = None
) -> Iterator[StreamEvent]:
    """
    同步代码生成接口，返回详细事件流生成器
    
    Args:
        prompt: 代码生成提示
        options: 配置选项
        show_terminal: 是否在终端显示友好的渲染输出（默认为False，避免重复显示）
        cancel_token: 取消令牌，用于中断执行
        
    Returns:
        Iterator[StreamEvent]: 原始事件流生成器，包含详细的执行过程信息
        
    Example:
        >>> from autocoder.sdk import auto_code_events, AutoCodeOptions
        >>> 
        >>> options = AutoCodeOptions(max_turns=1)
        >>> for event in auto_code_events("Write a simple calculator function", options):
        ...     print(f"[{event.event_type}] {event.data}")
    """
    if options is None:
        options = AutoCodeOptions()
    
    # 如果直接传递了 cancel_token 参数，优先使用它
    if cancel_token is not None:
        options = options.copy(cancel_token=cancel_token)
    
    core = AutoCoderCore(options)
    
    # 直接调用同步方法获取事件流
    event_stream = core._sync_run_auto_command(prompt)
    
    # 直接返回事件流
    for event in event_stream:
        # 可选择性地渲染到终端
        if show_terminal:
            core._render_stream_event(event, show_terminal)
        yield event


# ===== 工具函数 =====

def initialize_project(target_dir: str, project_type: str = ".py,.ts"):
    """
    初始化项目环境
    
    Args:
        target_dir: 目标目录
        project_type: 项目类型，以逗号分隔的文件扩展名
    """
    init_project_if_required_buildin(target_dir, project_type)
    if not VariableHolder.TOKENIZER_MODEL:
        load_tokenizer()
    start_engine()


def configure_model(key: str, value: str):
    """
    配置模型参数
    
    Args:
        key: 配置键
        value: 配置值
    """
    configure_buildin(f"{key}:{value}")


def get_language_model(model: str, product_mode: str = "lite"):
    """
    获取语言模型实例
    
    Args:
        model: 模型名称
        product_mode: 产品模式
        
    Returns:
        语言模型实例
    """
    return get_single_llm(model, product_mode)


def commit_changes(query: Optional[str] = None):
    """
    根据代码变化自动生成commit信息并提交
    
    Args:
        query: 提交信息的生成提示（可选）
    """
    commit_buildin(query)


def cancel_task(cancel_token: str, context: Optional[Dict[str, Any]] = None):
    """
    取消指定的任务
    
    Args:
        cancel_token: 要取消的任务令牌
        context: 取消上下文信息（可选）
        
    Example:
        >>> from autocoder.sdk import cancel_task
        >>> 
        >>> # 取消指定任务
        >>> cancel_task("my-cancel-token-123")
        >>> 
        >>> # 带上下文信息的取消
        >>> cancel_task("my-token", {"reason": "user_requested", "timestamp": "2024-01-01"})
    """
    try:
        from autocoder.common.global_cancel import global_cancel
        global_cancel.set(cancel_token, context)
    except ImportError:
        # 如果无法导入，提供一个简单的警告
        print(f"Warning: Unable to cancel task {cancel_token} - global_cancel module not available")


# ===== 向后兼容的旧 API（带弃用警告）=====

def query(*args, **kwargs):
    """已弃用，请使用 auto_code_stream"""
    warnings.warn(
        "query() is deprecated, use auto_code_stream() instead", 
        DeprecationWarning, 
        stacklevel=2
    )
    return auto_code_stream(*args, **kwargs)


def query_sync(*args, **kwargs):
    """已弃用，请使用 auto_code"""
    warnings.warn(
        "query_sync() is deprecated, use auto_code() instead", 
        DeprecationWarning, 
        stacklevel=2
    )
    return auto_code(*args, **kwargs)


def query_with_events(*args, **kwargs):
    """已弃用，请使用 auto_code_events_stream"""
    warnings.warn(
        "query_with_events() is deprecated, use auto_code_events_stream() instead", 
        DeprecationWarning, 
        stacklevel=2
    )
    return auto_code_events_stream(*args, **kwargs)


def query_with_events_sync(*args, **kwargs):
    """已弃用，请使用 auto_code_events"""
    warnings.warn(
        "query_with_events_sync() is deprecated, use auto_code_events() instead", 
        DeprecationWarning, 
        stacklevel=2
    )
    return auto_code_events(*args, **kwargs)


def init_project_if_required(*args, **kwargs):
    """已弃用，请使用 initialize_project"""
    warnings.warn(
        "init_project_if_required() is deprecated, use initialize_project() instead", 
        DeprecationWarning, 
        stacklevel=2
    )
    return initialize_project(*args, **kwargs)


def configure(*args, **kwargs):
    """已弃用，请使用 configure_model"""
    warnings.warn(
        "configure() is deprecated, use configure_model() instead", 
        DeprecationWarning, 
        stacklevel=2
    )
    return configure_model(*args, **kwargs)


def get_llm(*args, **kwargs):
    """已弃用，请使用 get_language_model"""
    warnings.warn(
        "get_llm() is deprecated, use get_language_model() instead", 
        DeprecationWarning, 
        stacklevel=2
    )
    return get_language_model(*args, **kwargs)


def commit(*args, **kwargs):
    """已弃用，请使用 commit_changes"""
    warnings.warn(
        "commit() is deprecated, use commit_changes() instead", 
        DeprecationWarning, 
        stacklevel=2
    )
    return commit_changes(*args, **kwargs) 