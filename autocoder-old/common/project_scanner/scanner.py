# -*- coding: utf-8 -*-
"""
Project Scanner Module

提供项目文件和目录扫描功能，支持文件监控和忽略规则。
"""

import os
import json
import threading
import queue
import time
from pathlib import Path
from typing import List, Dict, Optional, Set, Any
from dataclasses import dataclass, field
from loguru import logger

from autocoder.common.file_monitor import FileMonitor
from autocoder.common.file_monitor.monitor import Change
from autocoder.common.ignorefiles import should_ignore
from autocoder.index.symbols_utils import extract_symbols, SymbolType


@dataclass
class SymbolItem:
    """符号信息数据类"""
    symbol_name: str
    symbol_type: SymbolType
    file_name: str


@dataclass
class ScanResult:
    """扫描结果数据类"""
    file_names: List[str] = field(default_factory=list)
    file_paths: List[str] = field(default_factory=list)
    file_paths_with_dot: List[str] = field(default_factory=list)
    dir_paths: List[str] = field(default_factory=list)
    symbols: List[SymbolItem] = field(default_factory=list)


class ProjectScanner:
    """
    项目扫描器，提供文件和目录扫描功能。
    
    特性：
    - 单例模式确保全局唯一实例
    - 自动监控文件变化并更新缓存
    - 集成忽略规则过滤
    - 线程安全的缓存访问
    """
    
    _instance = None
    _instance_lock = threading.Lock()
    
    def __new__(cls, project_root: Optional[str] = None, 
                default_exclude_dirs: Optional[List[str]] = None,
                extra_exclude_dirs: Optional[List[str]] = None):
        """实现单例模式"""
        with cls._instance_lock:
            if cls._instance is None:
                if project_root is None:
                    raise ValueError("First initialization requires project_root")
                cls._instance = super(ProjectScanner, cls).__new__(cls)
                cls._instance._initialized = False
            elif project_root and cls._instance._project_root != os.path.abspath(project_root):
                logger.warning(f"ProjectScanner already initialized with {cls._instance._project_root}")
        return cls._instance
    
    def __init__(self, project_root: str, 
                 default_exclude_dirs: Optional[List[str]] = None,
                 extra_exclude_dirs: Optional[List[str]] = None):
        """初始化扫描器"""
        if hasattr(self, '_initialized') and self._initialized:            
            if set(extra_exclude_dirs) != set(self._extra_exclude_dirs):                
                self._extra_exclude_dirs = extra_exclude_dirs
                self._scan_project()
            else:                
                self._extra_exclude_dirs = extra_exclude_dirs
            return
            
        self._project_root = os.path.abspath(project_root)
        self._default_exclude_dirs = default_exclude_dirs or [
            ".git", "node_modules", "dist", "build", "__pycache__", ".auto-coder"
        ]
        self._extra_exclude_dirs = extra_exclude_dirs or []
        
        # 缓存扫描结果
        self._cache = ScanResult()
        self._cache_lock = threading.RLock()
        
        # 扫描任务队列管理
        self._scan_queue = queue.Queue()
        self._scan_thread_running = False
        self._scan_thread_lock = threading.Lock()
        self._scan_worker_thread = None
        
        # 文件监控器
        self._file_monitor = None
        self._setup_file_monitor()
        
        # 初始扫描
        self._scan_project()
        
        # 启动扫描任务处理线程
        self._start_scan_worker()
        
        self._initialized = True
        logger.info(f"ProjectScanner initialized for {self._project_root}")
    
    @classmethod
    def get_instance(cls) -> Optional['ProjectScanner']:
        """获取单例实例"""
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """重置单例实例"""
        with cls._instance_lock:
            if cls._instance is not None:
                # 停止扫描工作线程
                if hasattr(cls._instance, '_scan_thread_running'):
                    cls._instance._scan_thread_running = False
                    if hasattr(cls._instance, '_scan_worker_thread') and cls._instance._scan_worker_thread:
                        try:
                            # 等待工作线程结束，最多等待3秒
                            cls._instance._scan_worker_thread.join(timeout=3.0)
                        except:
                            pass
                    # 清空队列
                    if hasattr(cls._instance, '_scan_queue'):
                        try:
                            while not cls._instance._scan_queue.empty():
                                cls._instance._scan_queue.get_nowait()
                                cls._instance._scan_queue.task_done()
                        except:
                            pass
                            
                # 停止文件监控
                if cls._instance._file_monitor:
                    try:
                        cls._instance._file_monitor.stop()
                    except:
                        pass
                cls._instance = None
                logger.info("ProjectScanner singleton reset")
    
    def _setup_file_monitor(self):
        """设置文件监控"""
        try:
            self._file_monitor = FileMonitor(self._project_root)
            # 监控整个项目目录
            self._file_monitor.register(self._project_root, self._on_file_changed)
            # 监控符号索引文件
            index_file = os.path.join(self._project_root, ".auto-coder", "index.json")
            if os.path.exists(os.path.dirname(index_file)):
                self._file_monitor.register(index_file, self._on_index_changed)
            
            # 启动监控
            if not self._file_monitor.is_running():
                self._file_monitor.start()
                logger.info("File monitoring started for project scanner")
        except Exception as e:
            logger.error(f"Failed to setup file monitor: {e}")
    
    def _start_scan_worker(self):
        """启动扫描任务工作线程"""
        with self._scan_thread_lock:
            if not self._scan_thread_running:
                self._scan_thread_running = True
                self._scan_worker_thread = threading.Thread(
                    target=self._scan_worker, 
                    daemon=True, 
                    name="ProjectScanner-Worker"
                )
                self._scan_worker_thread.start()
                logger.debug("Scan worker thread started")
    
    def _scan_worker(self):
        """扫描任务工作线程主循环"""
        while self._scan_thread_running:
            try:
                # 阻塞等待任务，超时1秒检查是否需要停止
                task = self._scan_queue.get(timeout=1.0)
                
                # 清空队列中的其他待处理任务，只处理最新的
                latest_task = task
                while True:
                    try:
                        # 非阻塞获取，如果没有更多任务则跳出循环
                        latest_task = self._scan_queue.get_nowait()
                        # 标记之前的任务为完成（虽然没有实际执行）
                        self._scan_queue.task_done()
                    except queue.Empty:
                        break
                
                # 执行最新的扫描任务
                logger.debug("Executing scan task")
                if latest_task == "scan_project":
                    self._scan_project()
                elif latest_task == "scan_symbols":
                    self._load_symbols()
                
                # 标记任务完成
                self._scan_queue.task_done()
                
            except queue.Empty:
                # 超时，继续循环检查是否需要停止
                continue
            except Exception as e:
                logger.error(f"Error in scan worker: {e}")
                # 继续运行，不要因为单个错误而停止工作线程
                continue
    
    def _schedule_scan(self, task_type: str = "scan_project"):
        """将扫描任务添加到队列"""
        try:
            # 非阻塞添加任务，如果队列满了会抛出异常
            self._scan_queue.put_nowait(task_type)
            logger.debug(f"Scheduled scan task: {task_type}")
        except queue.Full:
            logger.warning("Scan queue is full, dropping task")
    
    def _on_file_changed(self, change_type: Change, changed_path: str):
        """文件变化回调"""
        # 检查是否需要更新缓存
        need_update = False
        
        if change_type == Change.added:
            # 新增文件/目录
            if not self._should_ignore(changed_path):
                need_update = True
        elif change_type == Change.deleted:
            # 删除文件/目录
            with self._cache_lock:
                abs_path = os.path.abspath(changed_path)
                if abs_path in self._cache.file_paths:
                    need_update = True
                elif abs_path in self._cache.dir_paths:
                    need_update = True
        elif change_type == Change.modified:
            # 文件修改通常不需要重新扫描，除非是目录结构变化
            pass
        
        if need_update:
            logger.debug(f"Project structure changed: {change_type.name} - {changed_path}")
            # 将扫描任务添加到队列，避免阻塞文件监控
            self._schedule_scan("scan_project")
    
    def _on_index_changed(self, change_type: Change, changed_path: str):
        """索引文件变化回调"""
        if change_type in [Change.added, Change.modified]:
            logger.debug("Symbol index changed, reloading symbols")
            self._schedule_scan("scan_symbols")
    
    def _should_ignore(self, path: str) -> bool:
        """检查路径是否应被忽略"""
        # 使用 ignorefiles 模块的规则
        if should_ignore(path, self._project_root):
            return True
            
        # 检查默认和额外的排除目录
        all_exclude_dirs = self._default_exclude_dirs + self._extra_exclude_dirs
        abs_path = os.path.abspath(path)
        
        for exclude_dir in all_exclude_dirs:
            # 检查路径是否包含排除的目录名
            parts = abs_path.split(os.sep)
            if exclude_dir in parts:
                return True
                
        return False
    
    def _scan_project(self):
        """扫描整个项目"""        
        new_cache = ScanResult()
        
        try:
            for root, dirs, files in os.walk(self._project_root, followlinks=True):
                # 过滤目录
                dirs[:] = [d for d in dirs if not self._should_ignore(os.path.join(root, d))]
                
                # 收集目录路径
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    if not self._should_ignore(dir_path):
                        new_cache.dir_paths.append(dir_path)
                
                # 收集文件
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    if not self._should_ignore(file_path):
                        new_cache.file_names.append(file_name)
                        new_cache.file_paths.append(file_path)
                        # 相对路径（以.开头）
                        rel_path = os.path.relpath(file_path, self._project_root)
                        new_cache.file_paths_with_dot.append(f"./{rel_path}")
            
            # 加载符号信息
            self._load_symbols_to_cache(new_cache)
            
            # 更新缓存
            with self._cache_lock:
                self._cache = new_cache                            
                       
        except Exception as e:
            logger.error(f"Error during project scan: {e}")
    
    def _load_symbols(self):
        """仅重新加载符号信息"""
        with self._cache_lock:
            self._load_symbols_to_cache(self._cache)
    
    def _load_symbols_to_cache(self, cache: ScanResult):
        """加载符号信息到缓存"""
        cache.symbols.clear()
        
        index_file = os.path.join(self._project_root, ".auto-coder", "index.json")
        if not os.path.exists(index_file):
            return
            
        try:
            with open(index_file, "r", encoding="utf-8") as f:
                index_data = json.load(f)
                
            for item in index_data.values():
                symbols_str = item.get("symbols", "")
                module_name = item.get("module_name", "")
                
                if not symbols_str or not module_name:
                    continue
                    
                info = extract_symbols(symbols_str)
                
                # 添加类符号
                for name in info.classes:
                    cache.symbols.append(SymbolItem(
                        symbol_name=name,
                        symbol_type=SymbolType.CLASSES,
                        file_name=module_name
                    ))
                
                # 添加函数符号
                for name in info.functions:
                    cache.symbols.append(SymbolItem(
                        symbol_name=name,
                        symbol_type=SymbolType.FUNCTIONS,
                        file_name=module_name
                    ))
                
                # 添加变量符号
                for name in info.variables:
                    cache.symbols.append(SymbolItem(
                        symbol_name=name,
                        symbol_type=SymbolType.VARIABLES,
                        file_name=module_name
                    ))
                    
        except Exception as e:
            logger.error(f"Error loading symbols: {e}")
    
    def refresh(self):
        """手动刷新扫描结果"""
        self._schedule_scan("scan_project")
    
    def update_extra_exclude_dirs(self, extra_exclude_dirs: List[str]):
        """更新额外的排除目录"""
        self._extra_exclude_dirs = extra_exclude_dirs
        self._schedule_scan("scan_project")
    
    # 公共接口方法
    def get_all_file_names(self) -> List[str]:
        """获取所有文件名（不含路径）"""
        with self._cache_lock:
            return self._cache.file_names.copy()
    
    def get_all_file_paths(self) -> List[str]:
        """获取所有文件的绝对路径"""
        with self._cache_lock:
            return self._cache.file_paths.copy()
    
    def get_all_file_paths_with_dot(self) -> List[str]:
        """获取所有文件的相对路径（以./开头）"""
        with self._cache_lock:
            return self._cache.file_paths_with_dot.copy()
    
    def get_all_dir_paths(self) -> List[str]:
        """获取所有目录的绝对路径"""
        with self._cache_lock:
            return self._cache.dir_paths.copy()
    
    def get_symbol_list(self) -> List[SymbolItem]:
        """获取符号列表"""
        with self._cache_lock:
            return self._cache.symbols.copy()
    
    def find_files(self, patterns: List[str]) -> List[str]:
        """根据模式查找文件"""
        import glob
        import fnmatch
        
        matched_files = []
        
        for pattern in patterns:
            if "*" in pattern or "?" in pattern:
                # 使用 glob 匹配
                for file_path in glob.glob(pattern, recursive=True):
                    if os.path.isfile(file_path):
                        abs_path = os.path.abspath(file_path)
                        if not self._should_ignore(abs_path):
                            matched_files.append(abs_path)
            else:
                # 精确匹配或部分匹配
                pattern_abs = os.path.abspath(pattern)
                found = False
                
                with self._cache_lock:
                    # 检查文件名匹配
                    for file_path in self._cache.file_paths:
                        file_name = os.path.basename(file_path)
                        if pattern == file_name or pattern_abs == file_path or pattern in file_path:
                            matched_files.append(file_path)
                            found = True
                
                # 如果在项目内没找到，检查是否是外部文件
                if not found and os.path.exists(pattern):
                    matched_files.append(os.path.abspath(pattern))
        
        return list(set(matched_files))  # 去重


def get_project_scanner(project_root: str, 
                       default_exclude_dirs: Optional[List[str]] = None,
                       extra_exclude_dirs: Optional[List[str]] = None) -> ProjectScanner:
    """获取项目扫描器实例"""
    return ProjectScanner(project_root, default_exclude_dirs, extra_exclude_dirs) 