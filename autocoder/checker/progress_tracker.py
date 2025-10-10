"""
进度跟踪器

管理代码检查进度，支持状态保存和中断恢复。
"""

import os
import json
import fcntl
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from autocoder.checker.types import CheckState


class ProgressTracker:
    """
    代码检查进度跟踪器

    功能：
    - 生成唯一的检查ID
    - 保存和加载检查状态
    - 跟踪文件检查进度
    - 支持中断恢复
    - 列出历史检查记录
    """

    def __init__(self, state_dir: str = ".auto-coder/codecheck/progress"):
        """
        初始化进度跟踪器

        Args:
            state_dir: 状态文件保存目录
        """
        self.state_dir = state_dir
        self._ensure_directory()

    def _ensure_directory(self) -> None:
        """确保状态目录存在"""
        os.makedirs(self.state_dir, exist_ok=True)

    def _generate_check_id(self, project_name: str = "project") -> str:
        """
        生成唯一的检查ID

        格式: {project_name}_{YYYYMMDD_HHMMSS}

        Args:
            project_name: 项目名称

        Returns:
            检查ID字符串
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{project_name}_{timestamp}"

    def _get_state_file_path(self, check_id: str) -> str:
        """
        获取状态文件路径

        Args:
            check_id: 检查ID

        Returns:
            状态文件完整路径
        """
        return os.path.join(self.state_dir, f"{check_id}.json")

    def _acquire_lock(self, file_path: str, mode: str = 'r') -> tuple:
        """
        获取文件锁（支持并发访问）

        Args:
            file_path: 文件路径
            mode: 打开模式

        Returns:
            (file_object, lock_acquired)
        """
        try:
            f = open(file_path, mode)
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return f, True
        except (IOError, OSError):
            return None, False

    def _release_lock(self, file_obj) -> None:
        """
        释放文件锁

        Args:
            file_obj: 文件对象
        """
        if file_obj:
            try:
                fcntl.flock(file_obj.fileno(), fcntl.LOCK_UN)
                file_obj.close()
            except Exception:
                pass

    def start_check(
        self,
        files: List[str],
        config: Dict[str, Any],
        project_name: str = "project"
    ) -> str:
        """
        开始新的检查任务

        Args:
            files: 待检查文件列表
            config: 检查配置
            project_name: 项目名称

        Returns:
            生成的检查ID
        """
        check_id = self._generate_check_id(project_name)
        start_time = datetime.now().isoformat()

        state = CheckState(
            check_id=check_id,
            start_time=start_time,
            config=config,
            total_files=files.copy(),
            completed_files=[],
            remaining_files=files.copy(),
            status="running"
        )

        self.save_state(check_id, state)
        return check_id

    def mark_completed(self, check_id: str, file_path: str) -> None:
        """
        标记文件已完成检查

        Args:
            check_id: 检查ID
            file_path: 文件路径
        """
        state = self.load_state(check_id)
        if not state:
            return

        # 添加到已完成列表
        if file_path not in state.completed_files:
            state.completed_files.append(file_path)

        # 从剩余列表中移除
        if file_path in state.remaining_files:
            state.remaining_files.remove(file_path)

        # 如果全部完成，更新状态
        if len(state.remaining_files) == 0:
            state.status = "completed"

        self.save_state(check_id, state)

    def get_remaining_files(self, check_id: str) -> List[str]:
        """
        获取剩余待检查的文件列表

        Args:
            check_id: 检查ID

        Returns:
            剩余文件路径列表
        """
        state = self.load_state(check_id)
        if not state:
            return []
        return state.remaining_files.copy()

    def save_state(self, check_id: str, state: CheckState) -> None:
        """
        保存检查状态到文件

        Args:
            check_id: 检查ID
            state: 检查状态对象
        """
        state_file = self._get_state_file_path(check_id)

        try:
            with open(state_file, 'w', encoding='utf-8') as f:
                # 使用 pydantic 的 dict() 方法序列化
                json.dump(state.dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise IOError(f"保存状态文件失败: {e}")

    def load_state(self, check_id: str) -> Optional[CheckState]:
        """
        从文件加载检查状态

        Args:
            check_id: 检查ID

        Returns:
            检查状态对象，如果不存在则返回 None
        """
        state_file = self._get_state_file_path(check_id)

        if not os.path.exists(state_file):
            return None

        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return CheckState(**data)
        except Exception as e:
            raise IOError(f"加载状态文件失败: {e}")

    def list_checks(self) -> List[Dict[str, Any]]:
        """
        列出所有检查记录

        Returns:
            检查记录列表，每个记录包含：
            - check_id: 检查ID
            - start_time: 开始时间
            - status: 状态
            - total: 总文件数
            - completed: 已完成数
            - remaining: 剩余数
        """
        checks = []

        if not os.path.exists(self.state_dir):
            return checks

        for filename in os.listdir(self.state_dir):
            if not filename.endswith('.json'):
                continue

            check_id = filename[:-5]  # 移除 .json 后缀
            state = self.load_state(check_id)

            if state:
                checks.append({
                    "check_id": check_id,
                    "start_time": state.start_time,
                    "status": state.status,
                    "total": len(state.total_files),
                    "completed": len(state.completed_files),
                    "remaining": len(state.remaining_files),
                    "progress": state.get_progress_percentage()
                })

        # 按开始时间降序排序
        checks.sort(key=lambda x: x["start_time"], reverse=True)
        return checks

    def delete_check(self, check_id: str) -> bool:
        """
        删除检查记录

        Args:
            check_id: 检查ID

        Returns:
            是否成功删除
        """
        state_file = self._get_state_file_path(check_id)

        if not os.path.exists(state_file):
            return False

        try:
            os.remove(state_file)
            return True
        except Exception:
            return False

    def cleanup_old_checks(self, keep_days: int = 7) -> int:
        """
        清理旧的检查记录

        Args:
            keep_days: 保留天数

        Returns:
            删除的记录数
        """
        if not os.path.exists(self.state_dir):
            return 0

        deleted_count = 0
        cutoff_time = datetime.now().timestamp() - (keep_days * 86400)

        for filename in os.listdir(self.state_dir):
            if not filename.endswith('.json'):
                continue

            file_path = os.path.join(self.state_dir, filename)
            file_mtime = os.path.getmtime(file_path)

            if file_mtime < cutoff_time:
                try:
                    os.remove(file_path)
                    deleted_count += 1
                except Exception:
                    pass

        return deleted_count

    def get_check_summary(self, check_id: str) -> Optional[Dict[str, Any]]:
        """
        获取检查摘要信息

        Args:
            check_id: 检查ID

        Returns:
            检查摘要字典，如果不存在则返回 None
        """
        state = self.load_state(check_id)
        if not state:
            return None

        return {
            "check_id": check_id,
            "start_time": state.start_time,
            "status": state.status,
            "config": state.config,
            "total_files": len(state.total_files),
            "completed_files": len(state.completed_files),
            "remaining_files": len(state.remaining_files),
            "progress_percentage": state.get_progress_percentage(),
        }
