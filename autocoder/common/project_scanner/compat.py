# -*- coding: utf-8 -*-
"""
兼容性接口，提供与 auto_coder_runner.py 中原有函数相同的接口
"""

from typing import List, Optional
from .scanner import get_project_scanner, SymbolItem


def create_scanner_functions(project_root: str, 
                           default_exclude_dirs: Optional[List[str]] = None,
                           get_extra_exclude_dirs_func=None):
    """
    创建与原有接口兼容的函数集合
    
    Args:
        project_root: 项目根目录
        default_exclude_dirs: 默认排除目录列表
        get_extra_exclude_dirs_func: 获取额外排除目录的函数
        
    Returns:
        包含所有兼容函数的字典
    """
    
    def _get_scanner():
        """获取或创建扫描器实例"""
        extra_exclude_dirs = []
        if get_extra_exclude_dirs_func:
            extra_exclude_dirs = get_extra_exclude_dirs_func()
        return get_project_scanner(project_root, default_exclude_dirs, extra_exclude_dirs)
    
    def get_all_file_names_in_project() -> List[str]:
        """获取项目中所有文件名"""
        scanner = _get_scanner()
        return scanner.get_all_file_names()
    
    def get_all_file_in_project() -> List[str]:
        """获取项目中所有文件的完整路径"""
        scanner = _get_scanner()
        return scanner.get_all_file_paths()
    
    def get_all_file_in_project_with_dot() -> List[str]:
        """获取项目中所有文件的相对路径（以./开头）"""
        scanner = _get_scanner()
        return scanner.get_all_file_paths_with_dot()
    
    def get_all_dir_names_in_project() -> List[str]:
        """获取项目中所有目录名"""
        scanner = _get_scanner()
        # 原始实现只返回目录名，不是完整路径
        import os
        return [os.path.basename(path) for path in scanner.get_all_dir_paths()]
    
    def get_symbol_list() -> List[SymbolItem]:
        """获取符号列表"""
        scanner = _get_scanner()
        return scanner.get_symbol_list()
    
    def find_files_in_project(patterns: List[str]) -> List[str]:
        """根据模式查找文件"""
        scanner = _get_scanner()
        return scanner.find_files(patterns)
    
    def refresh_scanner():
        """手动刷新扫描器缓存"""
        scanner = _get_scanner()
        scanner.refresh()
    
    return {
        'get_all_file_names_in_project': get_all_file_names_in_project,
        'get_all_file_in_project': get_all_file_in_project,
        'get_all_file_in_project_with_dot': get_all_file_in_project_with_dot,
        'get_all_dir_names_in_project': get_all_dir_names_in_project,
        'get_symbol_list': get_symbol_list,
        'find_files_in_project': find_files_in_project,
        'refresh_scanner': refresh_scanner
    } 