
import os
import json
import uuid
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
from loguru import logger as global_logger


class QueueTaskStatus(Enum):
    """队列任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class QueueTask:
    """队列任务数据结构"""
    task_id: str
    user_query: str  # 用户需求而非命令
    model: str  # 使用的模型
    status: QueueTaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[str] = None
    error_message: Optional[str] = None
    priority: int = 0  # 优先级，数字越大优先级越高
    worktree_name: Optional[str] = None  # worktree 名称
    # 兼容旧版本
    command: Optional[str] = None  # 保留以兼容旧数据
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        # 处理datetime和enum类型
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat() if self.created_at else None
        data['started_at'] = self.started_at.isoformat() if self.started_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueueTask':
        """从字典创建任务对象"""
        # 处理datetime和enum类型
        data['status'] = QueueTaskStatus(data['status'])
        data['created_at'] = datetime.fromisoformat(data['created_at']) if data.get('created_at') else None
        data['started_at'] = datetime.fromisoformat(data['started_at']) if data.get('started_at') else None
        data['completed_at'] = datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None
        
        # 兼容旧版本数据
        if 'command' in data and 'user_query' not in data:
            data['user_query'] = data['command']
        if 'model' not in data:
            data['model'] = 'auto'
        
        # 只传递存在的字段
        valid_fields = {'task_id', 'user_query', 'model', 'status', 'created_at', 
                       'started_at', 'completed_at', 'result', 'error_message', 
                       'priority', 'worktree_name', 'command'}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        
        return cls(**filtered_data)


class QueueManager:
    """队列管理器"""
    
    def __init__(self, queue_dir: Optional[str] = None):
        """
        初始化队列管理器
        
        Args:
            queue_dir: 队列数据存储目录，默认为 ~/.auto-coder/queue
        """
        if queue_dir is None:
            self.queue_dir = Path.home() / ".auto-coder" / "queue"
        else:
            self.queue_dir = Path(queue_dir)
        
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        self.queue_file = self.queue_dir / "tasks.json"
        self._lock = threading.Lock()
        
        # 初始化队列文件
        if not self.queue_file.exists():
            self._save_tasks([])
    
    def _load_tasks(self) -> List[QueueTask]:
        """加载所有任务"""
        try:
            with open(self.queue_file, 'r', encoding='utf-8') as f:
                tasks_data = json.load(f)
                return [QueueTask.from_dict(task_data) for task_data in tasks_data]
        except (FileNotFoundError, json.JSONDecodeError) as e:
            global_logger.warning(f"Failed to load tasks: {e}")
            return []
    
    def _save_tasks(self, tasks: List[QueueTask]) -> None:
        """保存所有任务"""
        try:
            tasks_data = [task.to_dict() for task in tasks]
            with open(self.queue_file, 'w', encoding='utf-8') as f:
                json.dump(tasks_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            global_logger.error(f"Failed to save tasks: {e}")
            raise
    
    def add_task(self, user_query: str = None, model: str = "auto", priority: int = 0, command: str = None, worktree_name: str = None) -> str:
        """
        添加新任务到队列
        
        Args:
            user_query: 用户需求
            model: 使用的模型
            priority: 任务优先级，数字越大优先级越高
            command: 旧版本兼容参数
            worktree_name: 自定义 worktree 名称
            
        Returns:
            str: 任务ID
        """
        with self._lock:
            task_id = str(uuid.uuid4())[:8]  # 使用8位UUID作为任务ID
            
            # 兼容旧版本
            if command and not user_query:
                user_query = command
            
            task = QueueTask(
                task_id=task_id,
                user_query=user_query,
                model=model,
                status=QueueTaskStatus.PENDING,
                created_at=datetime.now(),
                priority=priority,
                worktree_name=worktree_name,
                command=command  # 兼容字段
            )
            
            tasks = self._load_tasks()
            tasks.append(task)
            
            # 按优先级和创建时间排序（优先级高的在前，同优先级按创建时间排序）
            tasks.sort(key=lambda t: (-t.priority, t.created_at))
            
            self._save_tasks(tasks)
            global_logger.info(f"Added task {task_id}: {user_query[:100]}..." if len(user_query) > 100 else f"Added task {task_id}: {user_query}")
            return task_id
    
    def get_task(self, task_id: str) -> Optional[QueueTask]:
        """
        获取指定任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            QueueTask: 任务对象，如果不存在返回None
        """
        tasks = self._load_tasks()
        for task in tasks:
            if task.task_id == task_id:
                return task
        return None
    
    def list_tasks(self, status_filter: Optional[QueueTaskStatus] = None) -> List[QueueTask]:
        """
        列出所有任务
        
        Args:
            status_filter: 状态过滤器，只返回指定状态的任务
            
        Returns:
            List[QueueTask]: 任务列表
        """
        tasks = self._load_tasks()
        if status_filter:
            tasks = [task for task in tasks if task.status == status_filter]
        return tasks
    
    def remove_task(self, task_id: str) -> bool:
        """
        移除指定任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功移除
        """
        with self._lock:
            tasks = self._load_tasks()
            original_count = len(tasks)
            
            # 只允许移除非运行状态的任务
            tasks = [task for task in tasks if not (
                task.task_id == task_id and task.status != QueueTaskStatus.RUNNING
            )]
            
            if len(tasks) < original_count:
                self._save_tasks(tasks)
                global_logger.info(f"Removed task {task_id}")
                return True
            else:
                global_logger.warning(f"Task {task_id} not found or is running")
                return False
    
    def update_task_status(self, task_id: str, status: QueueTaskStatus, 
                          result: Optional[str] = None, 
                          error_message: Optional[str] = None) -> bool:
        """
        更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态
            result: 执行结果
            error_message: 错误信息
            
        Returns:
            bool: 是否更新成功
        """
        with self._lock:
            tasks = self._load_tasks()
            for task in tasks:
                if task.task_id == task_id:
                    task.status = status
                    
                    if status == QueueTaskStatus.RUNNING and task.started_at is None:
                        task.started_at = datetime.now()
                    elif status in [QueueTaskStatus.COMPLETED, QueueTaskStatus.FAILED, QueueTaskStatus.CANCELLED]:
                        task.completed_at = datetime.now()
                    
                    if result is not None:
                        task.result = result
                    if error_message is not None:
                        task.error_message = error_message
                    
                    self._save_tasks(tasks)
                    global_logger.info(f"Updated task {task_id} status to {status.value}")
                    return True
            
            global_logger.warning(f"Task {task_id} not found")
            return False
    
    def get_next_pending_task(self) -> Optional[QueueTask]:
        """
        获取下一个待执行的任务（优先级最高的pending任务）
        
        Returns:
            QueueTask: 下一个待执行的任务，如果没有返回None
        """
        tasks = self._load_tasks()
        pending_tasks = [task for task in tasks if task.status == QueueTaskStatus.PENDING]
        
        if not pending_tasks:
            return None
        
        # 返回优先级最高的任务（已经按优先级排序）
        return pending_tasks[0]
    
    def get_running_tasks(self) -> List[QueueTask]:
        """
        获取所有正在运行的任务
        
        Returns:
            List[QueueTask]: 正在运行的任务列表
        """
        return self.list_tasks(QueueTaskStatus.RUNNING)
    
    def clear_completed_tasks(self) -> int:
        """
        清理已完成的任务
        
        Returns:
            int: 清理的任务数量
        """
        with self._lock:
            tasks = self._load_tasks()
            original_count = len(tasks)
            
            # 保留未完成的任务
            tasks = [task for task in tasks if task.status not in [
                QueueTaskStatus.COMPLETED, 
                QueueTaskStatus.FAILED, 
                QueueTaskStatus.CANCELLED
            ]]
            
            removed_count = original_count - len(tasks)
            if removed_count > 0:
                self._save_tasks(tasks)
                global_logger.info(f"Cleared {removed_count} completed tasks")
            
            return removed_count
    
    def get_queue_statistics(self) -> Dict[str, int]:
        """
        获取队列统计信息
        
        Returns:
            Dict[str, int]: 统计信息
        """
        tasks = self._load_tasks()
        stats = {
            'total': len(tasks),
            'pending': 0,
            'running': 0,
            'completed': 0,
            'failed': 0,
            'cancelled': 0
        }
        
        for task in tasks:
            stats[task.status.value] += 1
        
        return stats
