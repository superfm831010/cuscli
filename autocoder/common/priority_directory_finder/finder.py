"""
优先级目录查找器核心实现

提供灵活的目录查找功能，支持多种查找策略和验证规则。
"""

import os
from typing import List, Optional, Dict, Any
from loguru import logger

from .models import (
    SearchStrategy, ValidationMode, FileTypeFilter, DirectoryConfig,
    SearchResult, FinderConfig
)


class PriorityDirectoryFinder:
    """优先级目录查找器"""
    
    def __init__(self, config: Optional[FinderConfig] = None):
        """
        初始化查找器
        
        Args:
            config: 查找器配置，如果为None则使用默认配置
        """
        self.config = config or FinderConfig()
    
    def find_directories(self, config: Optional[FinderConfig] = None) -> SearchResult:
        """
        查找目录
        
        Args:
            config: 查找配置，如果为None则使用初始化时的配置
            
        Returns:
            SearchResult: 查找结果
        """
        use_config = config or self.config
        
        result = SearchResult(
            strategy=use_config.strategy,
            success=False
        )
        
        # 获取排序后的目录列表
        directories = use_config.get_sorted_directories()
        
        if not directories:
            logger.warning("没有配置任何目录")
            if use_config.fail_on_no_match:
                result.add_error("config", "没有配置任何目录")
            return result
        
        # 验证所有目录并收集有效目录
        valid_directories = []
        for dir_config in directories:
            try:
                if dir_config.validate_directory():
                    expanded_path = dir_config.get_expanded_path()
                    valid_directories.append(expanded_path)
                    logger.debug(f"目录有效: {expanded_path} (优先级: {dir_config.priority})")
                else:
                    logger.debug(f"目录无效: {dir_config.path}")
            except Exception as e:
                error_msg = f"验证目录时发生错误: {str(e)}"
                result.add_error(dir_config.path, error_msg)
                logger.warning(f"验证目录 {dir_config.path} 时发生错误: {e}")
        
        result.all_valid_directories = valid_directories
        
        # 根据策略选择目录
        if use_config.strategy == SearchStrategy.FIRST_MATCH:
            result.selected_directories = valid_directories[:1] if valid_directories else []
        
        elif use_config.strategy == SearchStrategy.MERGE_ALL:
            result.selected_directories = valid_directories
        
        elif use_config.strategy == SearchStrategy.LIST_ALL:
            result.selected_directories = valid_directories
        
        # 如果没有找到有效目录，尝试使用回退目录
        if not result.selected_directories and use_config.default_fallback:
            fallback_path = os.path.expanduser(use_config.default_fallback)
            fallback_path = os.path.expandvars(fallback_path)
            fallback_path = os.path.abspath(fallback_path)
            
            result.selected_directories = [fallback_path]
            logger.info(f"使用回退目录: {fallback_path}")
        
        # 设置成功状态
        result.success = len(result.selected_directories) > 0
        
        if not result.success and use_config.fail_on_no_match:
            result.add_error("search", "没有找到任何有效目录")
        
        # 添加元数据
        if use_config.include_metadata:
            result.metadata.update({
                "total_configured": len(directories),
                "total_valid": len(valid_directories),
                "strategy_used": use_config.strategy.value,
                "directory_configs": [
                    {
                        "path": d.path,
                        "expanded_path": d.get_expanded_path(),
                        "priority": d.priority,
                        "description": d.description,
                        "is_valid": d.validate_directory()
                    }
                    for d in directories
                ]
            })
        
        logger.info(f"目录查找完成: 策略={use_config.strategy.value}, "
                   f"配置={len(directories)}, 有效={len(valid_directories)}, "
                   f"选择={len(result.selected_directories)}")
        
        return result
    
    def find_first_directory(self, config: Optional[FinderConfig] = None) -> Optional[str]:
        """
        查找第一个有效目录
        
        Args:
            config: 查找配置
            
        Returns:
            str: 第一个有效目录路径，如果没有找到则返回None
        """
        use_config = config or self.config
        original_strategy = use_config.strategy
        use_config.strategy = SearchStrategy.FIRST_MATCH
        
        try:
            result = self.find_directories(use_config)
            return result.primary_directory
        finally:
            use_config.strategy = original_strategy
    
    def find_all_directories(self, config: Optional[FinderConfig] = None) -> List[str]:
        """
        查找所有有效目录
        
        Args:
            config: 查找配置
            
        Returns:
            List[str]: 所有有效目录路径列表
        """
        use_config = config or self.config
        original_strategy = use_config.strategy
        use_config.strategy = SearchStrategy.LIST_ALL
        
        try:
            result = self.find_directories(use_config)
            return result.selected_directories
        finally:
            use_config.strategy = original_strategy
    
    def collect_files_from_directories(self, 
                                     directories: List[str], 
                                     file_filter: Optional[FileTypeFilter] = None) -> List[str]:
        """
        从目录列表中收集文件
        
        Args:
            directories: 目录路径列表
            file_filter: 文件过滤器
            
        Returns:
            List[str]: 收集到的文件路径列表
        """
        all_files = []
        
        for directory in directories:
            if not os.path.exists(directory) or not os.path.isdir(directory):
                continue
            
            try:
                self._collect_files_recursive(directory, all_files, file_filter)
            except (OSError, PermissionError) as e:
                logger.warning(f"无法访问目录 {directory}: {e}")
        
        return all_files
    
    def _collect_files_recursive(self, 
                               directory: str, 
                               file_list: List[str], 
                               file_filter: Optional[FileTypeFilter] = None) -> None:
        """
        递归收集文件
        
        Args:
            directory: 目录路径
            file_list: 文件列表（会被修改）
            file_filter: 文件过滤器
        """
        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            
            if os.path.isfile(item_path):
                if file_filter is None or file_filter.matches_file(item_path):
                    file_list.append(item_path)
            
            elif (os.path.isdir(item_path) and 
                  (file_filter is None or file_filter.recursive) and
                  not os.path.basename(item).startswith('.')):
                self._collect_files_recursive(item_path, file_list, file_filter)


class QuickFinder:
    """快速查找器 - 提供简化的API"""
    
    @staticmethod
    def find_standard_directories(base_name: str, 
                                current_dir: Optional[str] = None,
                                file_extensions: Optional[List[str]] = None,
                                strategy: SearchStrategy = SearchStrategy.FIRST_MATCH) -> SearchResult:
        """
        查找标准目录结构
        
        Args:
            base_name: 基础目录名（如 ".autocodercommands"）
            current_dir: 当前目录，如果为None则使用os.getcwd()
            file_extensions: 要查找的文件扩展名列表
            strategy: 查找策略
            
        Returns:
            SearchResult: 查找结果
        """
        config = FinderConfig(strategy=strategy)
        config.add_standard_paths(base_name, current_dir)
        
        # 设置文件过滤器
        if file_extensions:
            file_filter = FileTypeFilter(
                extensions=set(f".{ext.lstrip('.')}" for ext in file_extensions),
                recursive=True
            )
            
            for dir_config in config.directories:
                dir_config.validation_mode = ValidationMode.HAS_SPECIFIC_FILES
                dir_config.file_filter = file_filter
        
        finder = PriorityDirectoryFinder(config)
        return finder.find_directories()
    
    @staticmethod
    def find_command_directories(current_dir: Optional[str] = None) -> SearchResult:
        """
        查找命令目录（.autocodercommands）
        
        Args:
            current_dir: 当前目录
            
        Returns:
            SearchResult: 查找结果
        """
        return QuickFinder.find_standard_directories(
            base_name=".autocodercommands",
            current_dir=current_dir,
            file_extensions=["md"],
            strategy=SearchStrategy.FIRST_MATCH
        )
    
    @staticmethod
    def find_config_directories(current_dir: Optional[str] = None) -> SearchResult:
        """
        查找配置目录
        
        Args:
            current_dir: 当前目录
            
        Returns:
            SearchResult: 查找结果
        """
        return QuickFinder.find_standard_directories(
            base_name=".auto-coder",
            current_dir=current_dir,
            file_extensions=["yml", "yaml", "json"],
            strategy=SearchStrategy.FIRST_MATCH
        ) 