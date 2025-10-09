"""
Base classes for search replace patch operations
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field


class ReplaceStrategy(Enum):
    """替换策略枚举"""
    STRING = "string"
    PATCH = "patch"
    SIMILARITY = "similarity"


@dataclass
class ReplaceResult:
    """替换结果"""
    success: bool
    message: str
    new_content: Optional[str] = None
    applied_count: int = 0
    total_count: int = 0
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseReplacer(ABC):
    """文本替换器的抽象基类"""
    
    def __init__(self, strategy: ReplaceStrategy):
        self.strategy = strategy
    
    @abstractmethod
    def replace(self, content: str, search_blocks: List[Tuple[str, str]]) -> ReplaceResult:
        """
        执行文本替换操作
        
        Args:
            content: 原始文件内容
            search_blocks: 搜索替换块列表 [(search_text, replace_text), ...]
            
        Returns:
            ReplaceResult: 替换结果
        """
        pass
    
    @abstractmethod
    def can_handle(self, content: str, search_blocks: List[Tuple[str, str]]) -> bool:
        """
        检查当前替换器是否能处理给定的内容和搜索块
        
        Args:
            content: 原始文件内容
            search_blocks: 搜索替换块列表
            
        Returns:
            bool: 是否能处理
        """
        pass
    
    def get_strategy_name(self) -> str:
        """获取策略名称"""
        return self.strategy.value
    
    def validate_search_blocks(self, search_blocks: List[Tuple[str, str]]) -> bool:
        """
        验证搜索替换块的有效性
        
        Args:
            search_blocks: 搜索替换块列表
            
        Returns:
            bool: 是否有效
        """
        if not search_blocks:
            return False
        
        for search_text, replace_text in search_blocks:
            if not isinstance(search_text, str) or not isinstance(replace_text, str):
                return False
            
            # 允许空 search_text，表示"插入"操作（行级插入）
            if search_text == "":
                continue
            
            # 其他空白搜索文本仍然无效
            if not search_text.strip():
                return False
            
            # 硬约束：只支持行级替换，不支持行内替换
            if not self._is_line_level_replacement(search_text):
                return False
                
        return True
    
    def _is_line_level_replacement(self, search_text: str) -> bool:
        """
        检查是否为行级替换
        
        Args:
            search_text: 搜索文本
            
        Returns:
            bool: 是否为行级替换
        """
        # 如果搜索文本包含换行符，认为是多行替换，允许
        if '\n' in search_text:
            return True
        
        # 如果是单行文本，必须是完整的行（以换行符结尾）
        # 但我们放宽条件：允许不以换行符结尾的文本，但在实际替换时会按整行处理
        return True  # 暂时放宽，在具体替换器中实施严格约束 