"""
Auto-Coder SDK

为第三方开发者提供的 Python SDK，允许通过命令行工具和 Python API 两种方式使用 Auto-Coder 的核心功能。
"""

# 导入数据模型和异常
from .models.options import AutoCodeOptions
from .models.responses import StreamEvent, CodeModificationResult
from .exceptions import (
    AutoCoderSDKError,
    SessionNotFoundError,
    InvalidOptionsError,
    BridgeError,
    ValidationError
)

# 导入所有 API 函数
from .api import (
    # 新的清晰 API
    auto_code_stream,
    auto_code,
    auto_code_events_stream, 
    auto_code_events,
    
    # 工具函数
    initialize_project,
    configure_model,
    get_language_model,
    commit_changes,
    cancel_task,
    
    # 向后兼容的旧 API（带弃用警告）
    query,
    query_sync,
    query_with_events,
    query_with_events_sync,
    init_project_if_required,
    configure,
    get_llm,
    commit,
)


__version__ = "1.7.7"
__all__ = [
    # 新的清晰 API
    "auto_code_stream",
    "auto_code",
    "auto_code_events_stream", 
    "auto_code_events",
    "initialize_project",
    "configure_model",
    "get_language_model",
    "commit_changes",
    "cancel_task",
    
    # 数据模型和异常
    "AutoCodeOptions",
    "StreamEvent",
    "CodeModificationResult",
    "AutoCoderSDKError",
    "SessionNotFoundError",
    "InvalidOptionsError",
    "BridgeError",
    "ValidationError",
    
    # 向后兼容的旧 API（将在未来版本移除）
    "query",
    "query_sync",
    "query_with_events",
    "query_with_events_sync",
    "init_project_if_required",
    "configure",
    "get_llm",
    "commit",
]    