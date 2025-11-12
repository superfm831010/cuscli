"""
RAG Terminal 输出格式化器模块

提供三种输出格式：
- text: 纯文本，只输出答案
- json: JSON格式，包含完整结果和元数据
- stream-json: 流式JSON，实时输出每个处理步骤
"""

from .text import TextFormatter
from .json_format import JSONFormatter
from .stream_json import StreamJSONFormatter
from .base import format_rag_output

__all__ = [
    "TextFormatter",
    "JSONFormatter",
    "StreamJSONFormatter",
    "format_rag_output",
]
