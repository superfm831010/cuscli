"""
代码检查模块

提供基于大模型的代码规范检查功能，支持前后端代码检查。
"""

from autocoder.checker.types import (
    Severity,
    Rule,
    Issue,
    FileCheckResult,
    BatchCheckResult,
    CheckState,
    CodeChunk,
    FileFilters,
)

__all__ = [
    "Severity",
    "Rule",
    "Issue",
    "FileCheckResult",
    "BatchCheckResult",
    "CheckState",
    "CodeChunk",
    "FileFilters",
]

__version__ = "0.9.1b0"
