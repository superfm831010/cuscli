"""
优先级目录查找器模块

一个灵活的目录查找工具，支持多种查找策略和验证规则，
用于在多个优先级目录中查找有效的目录。

主要功能：
- 多种查找策略：顺序查找、合并查找、全部查找
- 可配置的验证规则：文件类型、数量等
- 灵活的路径配置：支持环境变量和用户主目录展开
- 标准路径模式：项目级、项目.auto-coder、全局目录
"""

from .models import (
    SearchStrategy,
    ValidationMode,
    FileTypeFilter,
    DirectoryConfig,
    SearchResult,
    FinderConfig
)

from .finder import (
    PriorityDirectoryFinder,
    QuickFinder
)

# 版本信息
__version__ = "1.0.0"

# 导出的主要类和函数
__all__ = [
    # 枚举类型
    "SearchStrategy",
    "ValidationMode",
    
    # 数据模型
    "FileTypeFilter",
    "DirectoryConfig", 
    "SearchResult",
    "FinderConfig",
    
    # 核心类
    "PriorityDirectoryFinder",
    "QuickFinder",
    
    # 便捷函数
    "find_command_directories",
    "find_config_directories",
    "find_standard_directories",
    "create_file_filter",
    "create_directory_config",
]


def find_command_directories(current_dir=None):
    """
    查找命令目录的便捷函数
    
    Args:
        current_dir: 当前目录，如果为None则使用os.getcwd()
        
    Returns:
        SearchResult: 查找结果
    """
    return QuickFinder.find_command_directories(current_dir)


def find_config_directories(current_dir=None):
    """
    查找配置目录的便捷函数
    
    Args:
        current_dir: 当前目录
        
    Returns:
        SearchResult: 查找结果
    """
    return QuickFinder.find_config_directories(current_dir)


def find_standard_directories(base_name, current_dir=None, file_extensions=None, strategy=SearchStrategy.FIRST_MATCH):
    """
    查找标准目录结构的便捷函数
    
    Args:
        base_name: 基础目录名
        current_dir: 当前目录
        file_extensions: 要查找的文件扩展名列表
        strategy: 查找策略
        
    Returns:
        SearchResult: 查找结果
    """
    return QuickFinder.find_standard_directories(base_name, current_dir, file_extensions, strategy)


def create_file_filter(extensions=None, patterns=None, min_count=1, recursive=True, include_hidden=False):
    """
    创建文件类型过滤器的便捷函数
    
    Args:
        extensions: 文件扩展名列表
        patterns: 文件名模式列表
        min_count: 最小文件数量
        recursive: 是否递归搜索
        include_hidden: 是否包含隐藏文件
        
    Returns:
        FileTypeFilter: 文件过滤器
    """
    return FileTypeFilter(
        extensions=set(extensions or []),
        patterns=set(patterns or []),
        min_count=min_count,
        recursive=recursive,
        include_hidden=include_hidden
    )


def create_directory_config(path, priority=0, validation_mode=ValidationMode.HAS_FILES, 
                          file_filter=None, description=""):
    """
    创建目录配置的便捷函数
    
    Args:
        path: 目录路径
        priority: 优先级
        validation_mode: 验证模式
        file_filter: 文件过滤器
        description: 描述
        
    Returns:
        DirectoryConfig: 目录配置
    """
    return DirectoryConfig(
        path=path,
        priority=priority,
        validation_mode=validation_mode,
        file_filter=file_filter,
        description=description
    ) 