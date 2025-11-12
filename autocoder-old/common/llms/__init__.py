"""
Auto-Coder LLM 管理模块

提供统一的大语言模型管理功能，包括：
- 模型配置管理
- API 密钥管理
- 模型实例化
- 价格管理
- 成本估算
"""

from .manager import LLMManager
from .schema import LLMModel

__all__ = ["LLMManager", "LLMModel"] 