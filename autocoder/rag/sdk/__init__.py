"""
AutoCoder RAG SDK

一个便于在Python代码中调用auto-coder.rag run功能的SDK。

基本用法:
    >>> from autocoder.rag.sdk import AutoCoderRAGClient
    >>>
    >>> client = AutoCoderRAGClient(doc_dir="/path/to/docs")
    >>> answer = client.query("如何使用这个项目?")
    >>> print(answer)

流式用法:
    >>> for chunk in client.query_stream("如何使用这个项目?"):
    ...     print(chunk, end="", flush=True)
"""

from .client import AutoCoderRAGClient
from .models import (
    RAGConfig,
    RAGQueryOptions,
    RAGResponse,
    Message,
    MessageType,
    StageType,
    TokenInfo,
    RAGError,
    ValidationError,
    ExecutionError,
    RAGEnvVars,
    append_path,
    prepend_path,
)
from .utils import (
    format_contexts_for_display,
    validate_doc_dir,
    print_response_summary,
    create_simple_config,
)

__version__ = "1.0.0"
__author__ = "AutoCoder Team"

__all__ = [
    # 核心类
    "AutoCoderRAGClient",
    # 数据模型
    "RAGConfig",
    "RAGQueryOptions",
    "RAGResponse",
    "Message",
    "MessageType",
    "StageType",
    "TokenInfo",
    "RAGEnvVars",
    # 异常
    "RAGError",
    "ValidationError",
    "ExecutionError",
    # 工具函数
    "format_contexts_for_display",
    "validate_doc_dir",
    "print_response_summary",
    "create_simple_config",
    "append_path",
    "prepend_path",
    # 元数据
    "__version__",
]
