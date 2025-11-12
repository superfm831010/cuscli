"""
Auto-Coder AutoCoderArgs 参数解析模块

提供 AutoCoderArgs 参数的高级解析功能，包括：
- 支持多种数据类型的统一解析
- Token 数量单位解析（k, m, g 等）
- 数学表达式计算
- 基于模型配置的动态解析
"""

from .parser import AutoCoderArgsParser
from .token_parser import TokenParser

__all__ = ["AutoCoderArgsParser", "TokenParser"] 