# -*- coding: utf-8 -*-
"""
监控工具 - 已弃用

注意：此模块已弃用。RuleFiles 模块现在使用基于文件 MD5 的缓存失效机制，
不再依赖文件监控。为了保持向后兼容性，此模块提供空的实现。
"""

import os
from typing import Optional, List, Callable, Any
from loguru import logger


def setup_file_monitor(
    project_root: str,
    monitored_dirs: List[str],
    callback: Callable[[Any, str], None]
) -> Optional[Any]:
    """
    设置文件监控 - 已弃用
    
    注意：此函数已弃用，不再提供实际的监控功能。
    RuleFiles 模块现在使用基于文件 MD5 的缓存失效机制。
    
    Args:
        project_root: 项目根目录
        monitored_dirs: 要监控的目录列表
        callback: 文件变化时的回调函数
        
    Returns:
        None: 不再返回 FileMonitor 实例
    """
    logger.warning("setup_file_monitor 已弃用，RuleFiles 模块现在使用基于 MD5 的缓存失效机制")
    return None


def is_rule_related_change(changed_path: str, monitored_dirs: List[str]) -> bool:
    """
    检查变更是否与规则相关 - 已弃用
    
    注意：此函数已弃用，不再提供实际的检查功能。
    
    Args:
        changed_path: 发生变化的文件路径
        monitored_dirs: 监控的目录列表
        
    Returns:
        False: 始终返回 False
    """
    logger.warning("is_rule_related_change 已弃用")
    return False


def cleanup_file_monitor(file_monitor: Optional[Any], monitored_dirs: List[str]) -> None:
    """
    清理文件监控 - 已弃用
    
    注意：此函数已弃用，不再提供实际的清理功能。
    
    Args:
        file_monitor: FileMonitor 实例（忽略）
        monitored_dirs: 监控的目录列表（忽略）
    """
    logger.warning("cleanup_file_monitor 已弃用")
    pass


def create_rule_change_callback(reload_rules_func: Callable[[], None]) -> Callable[[Any, str], None]:
    """
    创建规则变化回调函数 - 已弃用
    
    注意：此函数已弃用，不再提供实际的回调功能。
    
    Args:
        reload_rules_func: 重新加载规则的函数（忽略）
        
    Returns:
        Callable: 空的回调函数
    """
    logger.warning("create_rule_change_callback 已弃用")
    
    def dummy_callback(change_type: Any, changed_path: str):
        """空的回调函数"""
        pass
    
    return dummy_callback 