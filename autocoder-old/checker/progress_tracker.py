"""
进度跟踪器

管理代码检查进度，支持状态保存和中断恢复。
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from loguru import logger

# 条件导入 fcntl（仅在 Unix/Linux 上可用）
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    # Windows 系统没有 fcntl 模块
    HAS_FCNTL = False

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

    跨平台支持：
    - Unix/Linux: 使用 fcntl 文件锁防止并发冲突
    - Windows: 降级为无锁模式（适用于单用户场景）
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

        注意：
            - Unix/Linux 使用 fcntl 文件锁
            - Windows 降级为无锁模式（直接返回成功）
        """
        try:
            f = open(file_path, mode)
            # 仅在支持 fcntl 的平台上尝试加锁
            if HAS_FCNTL:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return f, True
        except (IOError, OSError):
            return None, False

    def _release_lock(self, file_obj) -> None:
        """
        释放文件锁

        Args:
            file_obj: 文件对象

        注意：
            - Unix/Linux 使用 fcntl 解锁
            - Windows 直接关闭文件
        """
        if file_obj:
            try:
                # 仅在支持 fcntl 的平台上解锁
                if HAS_FCNTL:
                    fcntl.flock(file_obj.fileno(), fcntl.LOCK_UN)
                file_obj.close()
            except Exception:
                pass

    def start_check(
        self,
        files: List[str],
        config: Dict[str, Any],
        project_name: str = "project",
        report_dir: Optional[str] = None
    ) -> str:
        """
        开始新的检查任务

        Args:
            files: 待检查文件列表
            config: 检查配置
            project_name: 项目名称
            report_dir: 报告目录路径

        Returns:
            生成的检查ID
        """
        check_id = self._generate_check_id(project_name)
        start_time = datetime.now().isoformat()

        # 创建文件结果保存目录
        results_dir = self._get_results_dir(check_id)
        os.makedirs(results_dir, exist_ok=True)

        state = CheckState(
            check_id=check_id,
            start_time=start_time,
            config=config,
            total_files=files.copy(),
            completed_files=[],
            remaining_files=files.copy(),
            status="running",
            report_dir=report_dir,
            file_results_dir=results_dir
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
        保存检查状态到文件（原子写入）

        使用原子写入模式：先写临时文件，再重命名。
        这样可以防止中断时损坏原有文件。

        Args:
            check_id: 检查ID
            state: 检查状态对象
        """
        state_file = self._get_state_file_path(check_id)
        temp_file = state_file + '.tmp'

        try:
            # 1. 先写入临时文件
            with open(temp_file, 'w', encoding='utf-8') as f:
                # 使用 pydantic 的 dict() 方法序列化
                json.dump(state.dict(), f, indent=2, ensure_ascii=False)

            # 2. 原子重命名（os.replace 在 Windows 和 Linux 上都是原子操作）
            os.replace(temp_file, state_file)

        except Exception as e:
            # 清理临时文件（如果存在）
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass
            raise IOError(f"保存状态文件失败: {e}")

    def load_state(self, check_id: str) -> Optional[CheckState]:
        """
        从文件加载检查状态（支持自动修复）

        如果 JSON 损坏，尝试自动修复。

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
        except json.JSONDecodeError as e:
            # JSON 解析失败，尝试修复
            logger.warning(f"状态文件 JSON 损坏: {e}，尝试自动修复...")
            repaired_state = self._repair_corrupted_state(check_id)
            if repaired_state:
                logger.info(f"状态文件已成功修复: {check_id}")
                # 保存修复后的状态
                self.save_state(check_id, repaired_state)
                return repaired_state
            else:
                raise IOError(f"加载状态文件失败: {e}")
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

    def _get_results_dir(self, check_id: str) -> str:
        """
        获取文件结果保存目录

        Args:
            check_id: 检查ID

        Returns:
            结果目录路径
        """
        return os.path.join(self.state_dir, f"{check_id}_results")

    def _get_result_file_path(self, check_id: str, file_path: str) -> str:
        """
        获取单个文件结果的保存路径

        Args:
            check_id: 检查ID
            file_path: 文件路径

        Returns:
            结果文件路径
        """
        # 将文件路径转换为安全的文件名
        import hashlib
        file_hash = hashlib.md5(file_path.encode()).hexdigest()[:16]
        safe_name = file_path.replace('/', '_').replace('\\', '_').replace(':', '_')
        # 限制长度，避免文件名过长
        if len(safe_name) > 100:
            safe_name = safe_name[:100] + '_' + file_hash
        else:
            safe_name = safe_name + '_' + file_hash

        results_dir = self._get_results_dir(check_id)
        return os.path.join(results_dir, f"{safe_name}.json")

    def save_file_result(self, check_id: str, result) -> None:
        """
        保存单个文件的检查结果

        Args:
            check_id: 检查ID
            result: FileCheckResult 对象

        Raises:
            IOError: 如果保存失败
        """
        from autocoder.checker.types import FileCheckResult

        if not isinstance(result, FileCheckResult):
            raise TypeError(f"result 必须是 FileCheckResult 类型，当前为: {type(result)}")

        result_file = self._get_result_file_path(check_id, result.file_path)

        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(result_file), exist_ok=True)

            # 保存结果
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result.model_dump(), f, indent=2, ensure_ascii=False)

        except Exception as e:
            raise IOError(f"保存文件结果失败 {result.file_path}: {e}")

    def load_all_results(self, check_id: str) -> List:
        """
        加载检查任务的所有文件结果

        Args:
            check_id: 检查ID

        Returns:
            FileCheckResult 对象列表

        Raises:
            IOError: 如果加载失败
        """
        from autocoder.checker.types import FileCheckResult

        results_dir = self._get_results_dir(check_id)

        if not os.path.exists(results_dir):
            return []

        results = []
        try:
            for filename in os.listdir(results_dir):
                if not filename.endswith('.json'):
                    continue

                result_file = os.path.join(results_dir, filename)
                try:
                    with open(result_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        result = FileCheckResult(**data)
                        results.append(result)
                except Exception as e:
                    # 记录错误但继续加载其他文件
                    print(f"⚠️  加载结果文件失败 {filename}: {e}")
                    continue

            return results

        except Exception as e:
            raise IOError(f"加载检查结果失败: {e}")

    def get_result_count(self, check_id: str) -> int:
        """
        获取已保存的结果数量

        Args:
            check_id: 检查ID

        Returns:
            已保存的结果文件数量
        """
        results_dir = self._get_results_dir(check_id)

        if not os.path.exists(results_dir):
            return 0

        try:
            count = 0
            for filename in os.listdir(results_dir):
                if filename.endswith('.json'):
                    count += 1
            return count
        except Exception:
            return 0

    def _repair_corrupted_state(self, check_id: str) -> Optional[CheckState]:
        """
        尝试修复损坏的状态文件

        修复策略：
        1. 读取文件内容
        2. 找到不完整的数组（末尾有逗号但缺少结束符）
        3. 补全 JSON 结构
        4. 解析并返回修复后的状态

        Args:
            check_id: 检查ID

        Returns:
            修复后的 CheckState 对象，如果无法修复则返回 None
        """
        state_file = self._get_state_file_path(check_id)

        try:
            # 读取文件内容
            with open(state_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 尝试修复：移除末尾的逗号，添加缺失的结束符
            # 常见情况：JSON 数组未闭合
            content = content.rstrip()

            # 如果末尾是逗号，说明数组未完成
            if content.endswith(','):
                content = content[:-1]  # 移除末尾逗号

            # 统计缺少的结束符
            open_brackets = content.count('[') - content.count(']')
            open_braces = content.count('{') - content.count('}')

            # 补全缺失的结束符
            for _ in range(open_brackets):
                content += '\n  ]'
            for _ in range(open_braces):
                content += '\n}'

            # 尝试解析修复后的 JSON
            data = json.loads(content)
            state = CheckState(**data)

            logger.info(
                f"成功修复状态文件 {check_id}：移除末尾逗号，补全 "
                f"{open_brackets} 个 ']' 和 {open_braces} 个 '}}'"
            )

            return state

        except Exception as e:
            logger.error(f"无法修复状态文件 {check_id}: {e}")
            return None
