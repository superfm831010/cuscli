"""
Search Replace Patch Module

提供三种文本替换策略：
1. 正则表达式替换 (RegexReplacer)
2. 补丁库替换 (PatchReplacer)
3. 文本相似度替换 (SimilarityReplacer)
"""

from .base import BaseReplacer, ReplaceResult, ReplaceStrategy
from .string_replacer import StringReplacer
from .patch_replacer import PatchReplacer
from .similarity_replacer import SimilarityReplacer
from .manager import SearchReplaceManager

__all__ = [
    'BaseReplacer',
    'ReplaceResult',
    'ReplaceStrategy',
    'StringReplacer',
    'PatchReplacer',
    'SimilarityReplacer',
    'SearchReplaceManager',
] 