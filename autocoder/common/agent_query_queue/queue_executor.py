import os
import platform
import shutil
import threading
import time
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Callable, TYPE_CHECKING, Dict

# 仅用于类型提示，避免循环导入
if TYPE_CHECKING:
    from autocoder.common.agent_query_queue.queue_manager import QueueManager
from loguru import logger as global_logger


def _get_command_path(command: str) -> str:
    """获取命令的完整路径，确保 Windows 兼容性"""
    if os.path.isabs(command):
        return command
    full_path = shutil.which(command)
    if full_path:
        return full_path
    if platform.system() == "Windows":
        full_path = shutil.which(f"{command}.exe")
        if full_path:
            return full_path
    return command


def _build_env() -> Dict[str, str]:
    """构建子进程环境变量，在 Windows 上自动配置 UTF-8"""
    env = os.environ.copy()
    if platform.system() == "Windows":
        env.update(
            {
                "PYTHONIOENCODING": "utf-8",
                "LANG": "zh_CN.UTF-8",
                "LC_ALL": "zh_CN.UTF-8",
            }
        )
    return env


class QueueExecutor:
    """队列执行器 - 负责在 worktree 中执行队列中的任务"""

    def __init__(
        self,
        queue_manager: Optional["QueueManager"] = None,
        max_concurrent_tasks: int = 1,
        execution_callback: Optional[Callable] = None,
    ):
        """
        初始化队列执行器

        Args:
            queue_manager: 队列管理器实例，如果为None则创建新实例
            max_concurrent_tasks: 最大并发任务数
            execution_callback: 任务执行回调函数
        """
        # 延迟导入以避免循环依赖
        from autocoder.common.agent_query_queue.queue_manager import QueueManager

        self.queue_manager = queue_manager or QueueManager()
        self.max_concurrent_tasks = max_concurrent_tasks
        self.execution_callback = execution_callback
        self._running = False
        self._thread = None
        self._current_tasks = {}  # task_id -> thread

        # 初始化 worktree 管理器
        self._init_worktree_manager()

    def _init_worktree_manager(self) -> None:
        """初始化 worktree 管理器"""
        # 获取项目名称
        self.project_name = self._get_project_name()
        self.worktree_name = f"{self.project_name}"

        # 创建 worktree 管理器 - 延迟导入
        from autocoder.sdk.async_runner.worktree_manager import WorktreeManager

        async_agent_dir = Path.home() / ".auto-coder" / "queue_agent"
        self.worktree_manager = WorktreeManager(
            base_work_dir=str(async_agent_dir), original_project_path=os.getcwd()
        )

    def _get_project_name(self) -> str:
        """获取项目名称"""
        # 从当前目录名获取项目名
        current_dir = Path.cwd()
        project_name = current_dir.name

        # 如果是 git 仓库，尝试从远程 URL 获取项目名
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                url = result.stdout.strip()
                # 从 URL 提取项目名
                if "/" in url:
                    repo_part = url.split("/")[-1]
                    if repo_part.endswith(".git"):
                        repo_part = repo_part[:-4]
                    if repo_part:
                        project_name = repo_part
        except Exception:
            pass

        # 清理项目名，只保留字母数字和下划线
        project_name = "".join(
            c if c.isalnum() or c == "_" else "_" for c in project_name
        )
        return project_name or "project"

    def start(self) -> None:
        """启动队列执行器"""
        if self._running:
            global_logger.warning("Queue executor is already running")
            return

        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        global_logger.info("Queue executor started")

    def stop(self) -> None:
        """停止队列执行器"""
        if not self._running:
            return

        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        global_logger.info("Queue executor stopped")

    def _run_loop(self) -> None:
        """主执行循环"""
        while self._running:
            try:
                # 清理已完成的任务线程
                self._cleanup_completed_tasks()

                # 检查是否可以启动新任务
                if len(self._current_tasks) < self.max_concurrent_tasks:
                    next_task = self.queue_manager.get_next_pending_task()
                    if next_task:
                        self._start_task_execution(next_task)

                # 短暂休眠避免过度占用CPU
                time.sleep(1)

            except Exception as e:
                global_logger.error(f"Error in queue executor loop: {e}")
                time.sleep(5)  # 出错时等待更长时间

    def _cleanup_completed_tasks(self) -> None:
        """清理已完成的任务线程"""
        completed_task_ids = []
        for task_id, thread in self._current_tasks.items():
            if not thread.is_alive():
                completed_task_ids.append(task_id)

        for task_id in completed_task_ids:
            del self._current_tasks[task_id]

    def _start_task_execution(self, task) -> None:
        """启动任务执行"""
        thread = threading.Thread(target=self._execute_task, args=(task,), daemon=True)
        self._current_tasks[task.task_id] = thread
        thread.start()
        global_logger.info(f"Started execution of task {task.task_id}")

    def _execute_task(self, task) -> None:
        """在 worktree 中执行单个任务"""
        task_id = task.task_id
        user_query = task.user_query
        model = task.model or "auto"

        # 使用任务指定的 worktree_name 或默认名称
        task_worktree_name = task.worktree_name or self.worktree_name
        task.worktree_name = task_worktree_name

        try:
            # 更新任务状态为运行中，并设置 worktree_name
            from autocoder.common.agent_query_queue.queue_manager import QueueTaskStatus

            self.queue_manager.update_task_status(task_id, QueueTaskStatus.RUNNING)

            global_logger.info(
                f"Executing task {task_id} in worktree {task_worktree_name}"
            )

            # 调用执行回调（如果有）
            if self.execution_callback:
                try:
                    self.execution_callback(task, "started")
                except Exception as e:
                    global_logger.error(f"Error in execution callback: {e}")

            # 创建或复用 worktree
            worktree_info = self._ensure_worktree(task_worktree_name)

            # 创建临时文件保存用户需求
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False, encoding="utf-8"
            ) as tmp_file:
                tmp_file.write(user_query)
                tmp_file_path = tmp_file.name

            try:
                # 构建执行命令（跨平台兼容，不使用 cat | 管道）
                cmd_args = [
                    _get_command_path("auto-coder.run"),
                    "--model",
                    model,
                    "--verbose",
                    "--continue",
                ]

                # 读取临时文件内容
                with open(tmp_file_path, "r", encoding="utf-8") as f:
                    input_content = f.read()

                # 在 worktree 中执行命令
                result = subprocess.run(
                    cmd_args,
                    input=input_content,
                    cwd=worktree_info.path,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    env=_build_env(),
                    timeout=1800,  # 30分钟超时
                )

                if result.returncode == 0:
                    # 执行成功
                    output = (
                        result.stdout.strip()
                        if result.stdout
                        else "Task executed successfully"
                    )
                    from autocoder.common.agent_query_queue.queue_manager import (
                        QueueTaskStatus,
                    )

                    self.queue_manager.update_task_status(
                        task_id, QueueTaskStatus.COMPLETED, result=output
                    )
                    global_logger.info(f"Task {task_id} completed successfully")

                    # 调用执行回调
                    if self.execution_callback:
                        try:
                            self.execution_callback(task, "completed", output)
                        except Exception as e:
                            global_logger.error(f"Error in execution callback: {e}")

                else:
                    # 执行失败
                    error_msg = (
                        result.stderr.strip()
                        if result.stderr
                        else f"Command failed with return code {result.returncode}"
                    )
                    from autocoder.common.agent_query_queue.queue_manager import (
                        QueueTaskStatus,
                    )

                    self.queue_manager.update_task_status(
                        task_id, QueueTaskStatus.FAILED, error_message=error_msg
                    )
                    global_logger.error(f"Task {task_id} failed: {error_msg}")

                    # 调用执行回调
                    if self.execution_callback:
                        try:
                            self.execution_callback(task, "failed", error_msg)
                        except Exception as e:
                            global_logger.error(f"Error in execution callback: {e}")

            finally:
                # 删除临时文件
                try:
                    os.remove(tmp_file_path)
                except:
                    pass

        except subprocess.TimeoutExpired:
            # 超时
            error_msg = "Task execution timed out (30 minutes)"
            from autocoder.common.agent_query_queue.queue_manager import QueueTaskStatus

            self.queue_manager.update_task_status(
                task_id, QueueTaskStatus.FAILED, error_message=error_msg
            )
            global_logger.error(f"Task {task_id} timed out")

            # 调用执行回调
            if self.execution_callback:
                try:
                    self.execution_callback(task, "timeout", error_msg)
                except Exception as e:
                    global_logger.error(f"Error in execution callback: {e}")

        except Exception as e:
            # 其他异常
            error_msg = f"Unexpected error: {str(e)}"
            from autocoder.common.agent_query_queue.queue_manager import QueueTaskStatus

            self.queue_manager.update_task_status(
                task_id, QueueTaskStatus.FAILED, error_message=error_msg
            )
            global_logger.error(f"Task {task_id} failed with exception: {e}")

            # 调用执行回调
            if self.execution_callback:
                try:
                    self.execution_callback(task, "error", error_msg)
                except Exception as e:
                    global_logger.error(f"Error in execution callback: {e}")

    def _ensure_worktree(self, worktree_name: str = None):
        """确保 worktree 存在"""
        # 使用传入的 worktree_name 或默认的 worktree_name
        name_to_use = worktree_name or self.worktree_name

        # 检查 worktree 是否已存在
        if self.worktree_manager.worktree_exists(name_to_use):
            global_logger.info(f"Reusing existing worktree: {name_to_use}")
            return self.worktree_manager.get_worktree_info(name_to_use)

        # 创建新的 worktree
        global_logger.info(f"Creating new worktree: {name_to_use}")
        return self.worktree_manager.create_worktree(
            name=name_to_use, user_query="Queue job worktree", model="auto"
        )

    def get_running_tasks_count(self) -> int:
        """获取当前运行的任务数量"""
        return len(self._current_tasks)

    def is_running(self) -> bool:
        """检查执行器是否正在运行"""
        return self._running


# 全局队列执行器实例
_global_executor = None


def get_global_queue_executor() -> QueueExecutor:
    """获取全局队列执行器实例"""
    global _global_executor
    if _global_executor is None:
        _global_executor = QueueExecutor()
    return _global_executor


def start_global_queue_executor() -> None:
    """启动全局队列执行器"""
    executor = get_global_queue_executor()
    executor.start()


def stop_global_queue_executor() -> None:
    """停止全局队列执行器"""
    global _global_executor
    if _global_executor:
        _global_executor.stop()
        _global_executor = None
