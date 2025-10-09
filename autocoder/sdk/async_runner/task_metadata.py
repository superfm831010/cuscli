"""
任务元数据管理模块

用于管理异步代理运行器中每个任务的元数据信息。
"""

import json
import os
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List


@dataclass
class TaskMetadata:
    """任务元数据"""
    
    task_id: str                           # 任务ID（通常是worktree名称）
    user_query: str                        # 用户查询内容
    worktree_path: str                     # 对应的worktree路径    
    created_at: datetime                   # 创建时间
    original_project_path: str = ""        # 原始项目路径
    completed_at: Optional[datetime] = None # 完成时间
    status: str = "running"                # 任务状态: running, completed, failed
    model: str = ""                        # 使用的模型
    split_mode: str = ""                   # 分割模式
    background_mode: bool = False          # 是否后台运行
    pull_request: bool = False             # 是否创建PR
    log_file: str = ""                     # 日志文件路径
    error_message: str = ""                # 错误信息
    execution_result: Optional[Dict[str, Any]] = None  # 执行结果
    pid: int = 0                           # 运行任务所在进程的PID (main.py进程)
    sub_pid: int = 0                       # 子进程PID (auto-coder.run进程)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        # 将datetime对象转换为ISO格式字符串
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskMetadata":
        """从字典创建实例"""
        # 转换时间字符串为datetime对象
        if 'created_at' in data and data['created_at']:
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'completed_at' in data and data['completed_at']:
            data['completed_at'] = datetime.fromisoformat(data['completed_at'])
        
        return cls(**data)
    
    def update_status(self, status: str, error_message: str = "") -> None:
        """更新任务状态"""
        self.status = status
        if error_message:
            self.error_message = error_message
        
        if status in ["completed", "failed"]:
            self.completed_at = datetime.now()
    
    def update_sub_pid(self, sub_pid: int) -> None:
        """更新子进程PID"""
        self.sub_pid = sub_pid


class TaskMetadataManager:
    """任务元数据管理器"""
    
    def __init__(self, meta_dir: str):
        """
        初始化元数据管理器
        
        Args:
            meta_dir: 元数据目录路径
        """
        self.meta_dir = Path(meta_dir)
        self.meta_dir.mkdir(parents=True, exist_ok=True)
    
    def create_task_metadata(
        self,
        task_id: str,
        user_query: str,
        worktree_path: str,
        original_project_path: str = "",
        model: str = "",
        split_mode: str = "",
        background_mode: bool = False,
        pull_request: bool = False
    ) -> TaskMetadata:
        """
        创建新的任务元数据
        
        Args:
            task_id: 任务ID
            user_query: 用户查询
            worktree_path: worktree路径
            original_project_path: 原始项目路径
            model: 模型名称
            split_mode: 分割模式
            background_mode: 是否后台运行
            pull_request: 是否创建PR
            
        Returns:
            TaskMetadata: 创建的任务元数据
        """
        metadata = TaskMetadata(
            task_id=task_id,
            user_query=user_query,
            worktree_path=worktree_path,
            original_project_path=original_project_path,
            created_at=datetime.now(),
            model=model,
            split_mode=split_mode,
            background_mode=background_mode,
            pull_request=pull_request,
            pid=os.getpid()  # 获取当前进程的PID
        )
        
        self.save_task_metadata(metadata)
        return metadata
    
    def save_task_metadata(self, metadata: TaskMetadata) -> None:
        """
        保存任务元数据到文件
        
        Args:
            metadata: 任务元数据
        """
        meta_file = self.meta_dir / f"{metadata.task_id}.json"
        
        try:
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(metadata.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存任务元数据失败 {metadata.task_id}: {e}")
    
    def load_task_metadata(self, task_id: str) -> Optional[TaskMetadata]:
        """
        加载任务元数据
        
        Args:
            task_id: 任务ID
            
        Returns:
            TaskMetadata: 任务元数据，如果不存在则返回None
        """
        meta_file = self.meta_dir / f"{task_id}.json"
        
        if not meta_file.exists():
            return None
        
        try:
            with open(meta_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return TaskMetadata.from_dict(data)
        except Exception as e:
            print(f"加载任务元数据失败 {task_id}: {e}")
            return None
    
    def update_task_status(
        self,
        task_id: str,
        status: str,
        error_message: str = "",
        execution_result: Optional[Dict[str, Any]] = None,
        log_file: str = ""
    ) -> bool:
        """
        更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态
            error_message: 错误信息
            execution_result: 执行结果
            log_file: 日志文件路径
            
        Returns:
            bool: 是否更新成功
        """
        metadata = self.load_task_metadata(task_id)
        if not metadata:
            return False
        
        metadata.update_status(status, error_message)
        
        if execution_result is not None:
            metadata.execution_result = execution_result
        
        if log_file:
            metadata.log_file = log_file
        
        self.save_task_metadata(metadata)
        return True
    
    def update_sub_pid(self, task_id: str, sub_pid: int) -> bool:
        """
        更新任务的子进程PID
        
        Args:
            task_id: 任务ID
            sub_pid: 子进程PID
            
        Returns:
            bool: 是否更新成功
        """
        metadata = self.load_task_metadata(task_id)
        if not metadata:
            return False
        
        metadata.update_sub_pid(sub_pid)
        self.save_task_metadata(metadata)
        return True
    
    def list_tasks(self, status_filter: Optional[str] = None) -> List[TaskMetadata]:
        """
        列出所有任务
        
        Args:
            status_filter: 状态过滤器，如果指定则只返回该状态的任务
            
        Returns:
            List[TaskMetadata]: 任务列表
        """
        tasks = []
        
        for meta_file in self.meta_dir.glob("*.json"):
            metadata = self.load_task_metadata(meta_file.stem)
            if metadata:
                if status_filter is None or metadata.status == status_filter:
                    tasks.append(metadata)
        
        # 按创建时间排序
        tasks.sort(key=lambda x: x.created_at, reverse=True)
        return tasks
    
    def cleanup_completed_tasks(self, keep_days: int = 7) -> int:
        """
        清理完成的任务元数据
        
        Args:
            keep_days: 保留天数
            
        Returns:
            int: 清理的任务数量
        """
        cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 3600)
        cleaned_count = 0
        
        for meta_file in self.meta_dir.glob("*.json"):
            metadata = self.load_task_metadata(meta_file.stem)
            if metadata and metadata.status in ["completed", "failed"]:
                if metadata.completed_at and metadata.completed_at.timestamp() < cutoff_time:
                    try:
                        meta_file.unlink()
                        cleaned_count += 1
                    except Exception as e:
                        print(f"清理任务元数据失败 {meta_file.stem}: {e}")
        
        return cleaned_count
    
    def get_task_summary(self) -> Dict[str, Any]:
        """
        获取任务汇总信息
        
        Returns:
            Dict[str, Any]: 汇总信息
        """
        all_tasks = self.list_tasks()
        
        summary = {
            "total": len(all_tasks),
            "running": len([t for t in all_tasks if t.status == "running"]),
            "completed": len([t for t in all_tasks if t.status == "completed"]),
            "failed": len([t for t in all_tasks if t.status == "failed"]),
            "latest_tasks": all_tasks[:5]  # 最近5个任务
        }
        
        return summary 