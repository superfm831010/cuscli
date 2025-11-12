
"""
WrapLLMHint - 核心文本提示包装器

提供给定文本添加提示信息的功能，采用标准化的格式。
参考 agentic_conversation_pruner.py 中的实现模式。
"""

from typing import Optional, Dict, Any, List, Union
import re
from dataclasses import dataclass


@dataclass
class HintConfig:
    """提示配置类"""
    separator: str = "\n---\n"
    prefix: str = "[["
    suffix: str = "]]"
    allow_empty_hint: bool = False
    strip_whitespace: bool = True


class WrapLLMHint:
    """
    LLM提示包装器类
    
    用于给文本内容添加提示信息，采用标准化的分隔符格式。
    支持多种配置选项和批量处理功能。
    """
    
    def __init__(self, config: Optional[HintConfig] = None):
        """
        初始化提示包装器
        
        Args:
            config: 提示配置，如果为None则使用默认配置
        """
        self.config = config or HintConfig()
        
    def add_hint(self, content: str, hint: str) -> str:
        """
        给文本内容添加提示信息
        
        Args:
            content: 原始文本内容
            hint: 要添加的提示信息
            
        Returns:
            添加提示后的文本内容
            
        Raises:
            ValueError: 当提示为空且不允许空提示时
        """
        if not isinstance(content, str):
            raise TypeError("content must be a string")
        
        if not isinstance(hint, str):
            raise TypeError("hint must be a string")
            
        # 处理空提示
        if not hint.strip() and not self.config.allow_empty_hint:
            raise ValueError("hint cannot be empty when allow_empty_hint is False")
            
        # 处理空内容
        if not content.strip():
            content = ""
            
        # 处理提示内容
        processed_hint = hint
        if self.config.strip_whitespace:
            processed_hint = hint.strip()
            
        # 添加前缀和后缀
        if self.config.prefix:
            processed_hint = self.config.prefix + processed_hint
        if self.config.suffix:
            processed_hint = processed_hint + self.config.suffix
            
        # 组合最终结果
        if not processed_hint and self.config.allow_empty_hint:
            return content
            
        return content + self.config.separator + processed_hint
    
    def add_hint_safe(self, content: str, hint: str, fallback_hint: str = "") -> str:
        """
        安全地添加提示信息，出错时使用备用提示
        
        Args:
            content: 原始文本内容
            hint: 要添加的提示信息
            fallback_hint: 备用提示信息
            
        Returns:
            添加提示后的文本内容
        """
        try:
            return self.add_hint(content, hint)
        except (ValueError, TypeError):
            if fallback_hint:
                try:
                    return self.add_hint(content, fallback_hint)
                except (ValueError, TypeError):
                    return content
            return content
    
    def add_multiple_hints(self, content: str, hints: List[str]) -> str:
        """
        添加多个提示信息
        
        Args:
            content: 原始文本内容
            hints: 提示信息列表
            
        Returns:
            添加所有提示后的文本内容
        """
        if not hints:
            return content
            
        result = content
        for hint in hints:
            if hint.strip() or self.config.allow_empty_hint:
                result = self.add_hint(result, hint)
        
        return result
    
    def extract_hint(self, wrapped_content: str) -> Optional[str]:
        """
        从包装后的内容中提取提示信息
        
        Args:
            wrapped_content: 包装后的文本内容
            
        Returns:
            提取的提示信息，如果没有找到则返回None
        """
        if not isinstance(wrapped_content, str):
            return None
            
        separator = self.config.separator
        if separator not in wrapped_content:
            return None
            
        # 找到最后一个分隔符的位置
        last_separator_pos = wrapped_content.rfind(separator)
        if last_separator_pos == -1:
            return None
            
        # 提取提示部分
        hint_part = wrapped_content[last_separator_pos + len(separator):]
        
        if self.config.strip_whitespace:
            hint_part = hint_part.strip()
            
        # 去除前缀和后缀（如果存在）
        if hint_part and self.config.prefix and hint_part.startswith(self.config.prefix):
            hint_part = hint_part[len(self.config.prefix):]
        if hint_part and self.config.suffix and hint_part.endswith(self.config.suffix):
            hint_part = hint_part[:-len(self.config.suffix)]
            
        if self.config.strip_whitespace:
            hint_part = hint_part.strip()
            
        return hint_part if hint_part else None
    
    def extract_content(self, wrapped_content: str) -> str:
        """
        从包装后的内容中提取原始内容（去除提示部分）
        
        Args:
            wrapped_content: 包装后的文本内容
            
        Returns:
            原始文本内容
        """
        if not isinstance(wrapped_content, str):
            return ""
            
        separator = self.config.separator
        if separator not in wrapped_content:
            return wrapped_content
            
        # 找到最后一个分隔符的位置
        last_separator_pos = wrapped_content.rfind(separator)
        if last_separator_pos == -1:
            return wrapped_content
            
        # 提取内容部分
        content_part = wrapped_content[:last_separator_pos]
        
        if self.config.strip_whitespace:
            content_part = content_part.rstrip()
            
        return content_part
    
    def has_hint(self, content: str) -> bool:
        """
        检查内容是否包含提示信息
        
        Args:
            content: 要检查的文本内容
            
        Returns:
            如果包含提示信息返回True，否则返回False
        """
        if not isinstance(content, str):
            return False
            
        return self.config.separator in content
    
    def append_hint(self, content: str, hint: str) -> str:
        """
        追加提示信息到现有内容
        
        如果内容已经包含提示信息，则在现有提示后追加新提示；
        如果内容不包含提示信息，则等同于 add_hint 方法。
        
        Args:
            content: 原始文本内容（可能已经包含提示）
            hint: 要追加的提示信息
            
        Returns:
            追加提示后的文本内容
            
        Raises:
            ValueError: 当提示为空且不允许空提示时
            TypeError: 当输入参数类型不正确时
            
        Example:
            >>> wrapper = WrapLLMHint()
            >>> content = "Hello\\n---\\n[[hint1]]"
            >>> result = wrapper.append_hint(content, "hint2")
            >>> print(result)
            Hello
            ---
            [[hint1
            hint2]]
        """
        if not isinstance(content, str):
            raise TypeError("content must be a string")
        
        if not isinstance(hint, str):
            raise TypeError("hint must be a string")
            
        # 处理空提示
        if not hint.strip() and not self.config.allow_empty_hint:
            raise ValueError("hint cannot be empty when allow_empty_hint is False")
            
        # 处理提示内容
        processed_hint = hint
        if self.config.strip_whitespace:
            processed_hint = hint.strip()
            
        # 如果处理后的提示为空且允许空提示，直接返回原内容
        if not processed_hint and self.config.allow_empty_hint:
            return content
        
        # 检查内容是否已经包含提示
        if self.has_hint(content):
            # 提取现有的内容和提示
            original_content = self.extract_content(content)
            existing_hint = self.extract_hint(content)
            
            # 组合新的提示内容
            if existing_hint:
                combined_hint = existing_hint + "\n" + processed_hint
            else:
                combined_hint = processed_hint
                
            # 重新添加提示
            return self.add_hint(original_content, combined_hint)
        else:
            # 如果没有现有提示，等同于 add_hint
            return self.add_hint(content, processed_hint)
    
    def replace_hint(self, wrapped_content: str, new_hint: str) -> str:
        """
        替换现有的提示信息
        
        Args:
            wrapped_content: 包装后的文本内容
            new_hint: 新的提示信息
            
        Returns:
            替换提示后的文本内容
        """
        original_content = self.extract_content(wrapped_content)
        return self.add_hint(original_content, new_hint)
    
    def get_statistics(self, wrapped_content: str) -> Dict[str, Any]:
        """
        获取包装内容的统计信息
        
        Args:
            wrapped_content: 包装后的文本内容
            
        Returns:
            包含统计信息的字典
        """
        if not isinstance(wrapped_content, str):
            return {
                "total_length": 0,
                "content_length": 0,
                "hint_length": 0,
                "has_hint": False,
                "separator_count": 0
            }
            
        content = self.extract_content(wrapped_content)
        hint = self.extract_hint(wrapped_content)
        separator_count = wrapped_content.count(self.config.separator)
        
        return {
            "total_length": len(wrapped_content),
            "content_length": len(content),
            "hint_length": len(hint) if hint else 0,
            "has_hint": hint is not None,
            "separator_count": separator_count,
            "separator": self.config.separator
        }

