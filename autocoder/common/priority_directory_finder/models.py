"""
优先级目录查找器的数据模型

定义了查找策略、验证规则、结果类型等核心数据结构。
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Callable, Any, Union
from pathlib import Path


class SearchStrategy(Enum):
    """查找策略枚举"""
    FIRST_MATCH = "first_match"  # 顺序查找，找到第一个有效目录就返回
    MERGE_ALL = "merge_all"      # 合并查找，合并所有有效目录的内容
    LIST_ALL = "list_all"        # 全部查找，返回所有有效目录列表


class ValidationMode(Enum):
    """验证模式枚举"""
    EXISTS = "exists"                    # 目录存在即可
    HAS_FILES = "has_files"             # 目录包含文件
    HAS_SPECIFIC_FILES = "has_specific_files"  # 目录包含特定类型文件
    CUSTOM = "custom"                   # 自定义验证函数


@dataclass
class FileTypeFilter:
    """文件类型过滤器"""
    extensions: Set[str] = field(default_factory=set)  # 文件扩展名，如 {'.md', '.txt'}
    patterns: Set[str] = field(default_factory=set)    # 文件名模式，如 {'*.yml', 'config.*'}
    include_hidden: bool = False                        # 是否包含隐藏文件
    recursive: bool = True                              # 是否递归搜索子目录
    min_count: int = 1                                  # 最小文件数量
    max_count: Optional[int] = None                     # 最大文件数量
    
    def matches_file(self, file_path: str) -> bool:
        """检查文件是否匹配过滤器"""
        import fnmatch
        
        file_name = os.path.basename(file_path)
        
        # 检查隐藏文件
        if not self.include_hidden and file_name.startswith('.'):
            return False
        
        # 检查扩展名和模式匹配（OR逻辑：满足任一条件即可）
        extension_matches = False
        pattern_matches = False
        
        # 检查扩展名
        if self.extensions:
            _, ext = os.path.splitext(file_name)
            # 将扩展名转换为小写并检查是否在集合中（扩展名集合应该都是小写的）
            ext_lower = ext.lower()
            # 同时检查原始扩展名和小写扩展名（为了兼容性）
            extension_matches = ext_lower in self.extensions or ext in self.extensions
        
        # 检查模式匹配
        if self.patterns:
            pattern_matches = any(fnmatch.fnmatch(file_name, pattern) for pattern in self.patterns)
        
        # 如果设置了扩展名或模式，则至少要匹配其中一个
        if self.extensions or self.patterns:
            return extension_matches or pattern_matches
        
        # 如果既没有设置扩展名也没有设置模式，则匹配所有文件
        return True


@dataclass
class DirectoryConfig:
    """目录配置"""
    path: str                                           # 目录路径（支持环境变量和~展开）
    priority: int = 0                                   # 优先级（数字越小优先级越高）
    validation_mode: ValidationMode = ValidationMode.HAS_FILES
    file_filter: Optional[FileTypeFilter] = None
    custom_validator: Optional[Callable[[str], bool]] = None
    description: str = ""                               # 目录描述
    
    def get_expanded_path(self) -> str:
        """获取展开后的路径"""
        expanded = os.path.expanduser(self.path)
        expanded = os.path.expandvars(expanded)
        return os.path.abspath(expanded)
    
    def validate_directory(self) -> bool:
        """验证目录是否有效"""
        expanded_path = self.get_expanded_path()
        
        if not os.path.exists(expanded_path) or not os.path.isdir(expanded_path):
            return False
        
        if self.validation_mode == ValidationMode.EXISTS:
            return True
        
        elif self.validation_mode == ValidationMode.HAS_FILES:
            return self._has_any_files(expanded_path)
        
        elif self.validation_mode == ValidationMode.HAS_SPECIFIC_FILES:
            if self.file_filter is None:
                return False
            return self._has_matching_files(expanded_path)
        
        elif self.validation_mode == ValidationMode.CUSTOM:
            if self.custom_validator is None:
                return False
            return self.custom_validator(expanded_path)
        
        return False
    
    def _has_any_files(self, directory: str) -> bool:
        """检查目录是否包含任何文件"""
        try:
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                if os.path.isfile(item_path):
                    return True
                if os.path.isdir(item_path) and self._has_any_files(item_path):
                    return True
            return False
        except (OSError, PermissionError):
            return False
    
    def _has_matching_files(self, directory: str) -> bool:
        """检查目录是否包含匹配的文件"""
        if self.file_filter is None:
            return False
        
        matching_files = []
        
        try:
            self._collect_matching_files(directory, matching_files)
            
            file_count = len(matching_files)
            if file_count < self.file_filter.min_count:
                return False
            
            if self.file_filter.max_count is not None and file_count > self.file_filter.max_count:
                return False
            
            return True
            
        except (OSError, PermissionError):
            return False
    
    def _collect_matching_files(self, directory: str, matching_files: List[str]) -> None:
        """收集匹配的文件"""
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            
            if os.path.isfile(item_path) and self.file_filter.matches_file(item_path):
                matching_files.append(item_path)
            
            elif (os.path.isdir(item_path) and 
                  self.file_filter.recursive and 
                  not os.path.basename(item).startswith('.')):
                self._collect_matching_files(item_path, matching_files)


@dataclass
class SearchResult:
    """查找结果"""
    strategy: SearchStrategy
    success: bool
    selected_directories: List[str] = field(default_factory=list)
    all_valid_directories: List[str] = field(default_factory=list)
    errors: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def primary_directory(self) -> Optional[str]:
        """获取主要目录（第一个选中的目录）"""
        return self.selected_directories[0] if self.selected_directories else None
    
    @property
    def has_errors(self) -> bool:
        """是否有错误"""
        return len(self.errors) > 0
    
    def add_error(self, path: str, error_message: str) -> None:
        """添加错误信息"""
        self.errors[path] = error_message


@dataclass
class FinderConfig:
    """查找器配置"""
    directories: List[DirectoryConfig] = field(default_factory=list)
    strategy: SearchStrategy = SearchStrategy.FIRST_MATCH
    sort_by_priority: bool = True                       # 是否按优先级排序
    include_metadata: bool = True                       # 是否包含元数据
    fail_on_no_match: bool = False                      # 没有匹配时是否失败
    default_fallback: Optional[str] = None              # 默认回退目录
    
    def add_directory(self, path: str, priority: int = 0, **kwargs) -> 'FinderConfig':
        """添加目录配置"""
        config = DirectoryConfig(path=path, priority=priority, **kwargs)
        self.directories.append(config)
        return self
    
    def add_standard_paths(self, base_name: str, current_dir: Optional[str] = None) -> 'FinderConfig':
        """添加标准路径配置"""
        if current_dir is None:
            current_dir = os.getcwd()
        
        # 项目级目录
        self.add_directory(
            path=os.path.join(current_dir, base_name),
            priority=1,
            description=f"项目级{base_name}目录"
        )
        
        # 项目.auto-coder目录
        self.add_directory(
            path=os.path.join(current_dir, ".auto-coder", base_name),
            priority=2,
            description=f"项目.auto-coder/{base_name}目录"
        )
        
        # 全局目录
        self.add_directory(
            path=f"~/.auto-coder/{base_name}",
            priority=3,
            description=f"全局{base_name}目录"
        )
        
        return self
    
    def get_sorted_directories(self) -> List[DirectoryConfig]:
        """获取排序后的目录列表"""
        if self.sort_by_priority:
            return sorted(self.directories, key=lambda d: d.priority)
        return self.directories.copy() 