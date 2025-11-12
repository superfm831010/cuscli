"""
Auto-Coder SDK 格式化工具 - 向后兼容代理

此模块已被弃用，请使用 autocoder.sdk.formatters
"""

import warnings

# 在模块导入时发出弃用警告
warnings.warn(
    "autocoder.sdk.utils.formatters is deprecated, use autocoder.sdk.formatters instead",
    DeprecationWarning,
    stacklevel=2
)

# 从新位置导入所有内容
from ..formatters import (
    format_output,
    format_stream_output,
    format_table_output,
    format_error_output,
    format_progress_output,
)

__all__ = [
    "format_output",
    "format_stream_output",
    "format_table_output",
    "format_error_output",
    "format_progress_output",
]

















