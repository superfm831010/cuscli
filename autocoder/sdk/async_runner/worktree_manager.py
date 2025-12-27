"""
Git Worktree 管理器模块

提供 Git worktree 的创建、管理和清理功能。
"""

import os
import subprocess
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Any
from autocoder.common.international import get_message, get_message_with_format
from .task_metadata import TaskMetadataManager


@dataclass
class WorktreeInfo:
    """Worktree 信息"""

    name: str
    path: str
    branch: str
    temp_file: str = ""


class WorktreeManager:
    """Git Worktree 管理器，用于创建和管理 Git worktree"""

    def __init__(
        self, base_work_dir: str, from_branch: str = "", original_project_path: str = ""
    ):
        """
        初始化 worktree 管理器

        Args:
            base_work_dir: 基础工作目录（将在其中创建tasks和meta子目录）
            from_branch: 基础分支
            original_project_path: 原始项目路径
        """
        self.base_work_dir = Path(base_work_dir)
        self.tasks_dir = self.base_work_dir / "tasks"
        self.meta_dir = self.base_work_dir / "meta"
        self.from_branch = from_branch
        self.original_project_path = original_project_path or os.getcwd()

        # 创建必要的目录
        self.base_work_dir.mkdir(parents=True, exist_ok=True)
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        self.meta_dir.mkdir(parents=True, exist_ok=True)

        # 初始化元数据管理器
        self.metadata_manager = TaskMetadataManager(str(self.meta_dir))

    @property
    def work_dir(self) -> str:
        """保持兼容性的work_dir属性"""
        return str(self.tasks_dir)

    def create_worktree(
        self, name: str, user_query: str = "", model: str = "", split_mode: str = ""
    ) -> WorktreeInfo:
        """
        创建新的 git worktree 并记录元数据

        Args:
            name: worktree 名称
            user_query: 用户查询内容
            model: 使用的模型
            split_mode: 分割模式

        Returns:
            WorktreeInfo: worktree 信息

        Raises:
            Exception: 创建失败时抛出异常
        """
        # 在tasks目录中创建worktree
        full_path = self.tasks_dir / name

        # 检查目录是否已存在
        if full_path.exists():
            print(
                get_message_with_format(
                    "reusing_existing_worktree", path=str(full_path)
                )
            )

            # 尝试获取现有目录的分支信息
            current_branch = name  # 默认使用 name 作为分支
            try:
                # 尝试获取当前分支
                result = subprocess.run(
                    ["git", "branch", "--show-current"],
                    cwd=str(full_path),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    check=False,
                )
                if result.returncode == 0 and result.stdout.strip():
                    current_branch = result.stdout.strip()
            except Exception:
                # 如果获取分支失败，使用默认值
                pass

            # 直接创建 WorktreeInfo 对象，复用现有目录
            worktree_info = WorktreeInfo(
                name=name, path=str(full_path), branch=current_branch
            )
        else:
            # 目录不存在，创建新的 git worktree
            # 确定基础分支
            base_branch = self.from_branch
            if not base_branch:
                # 如果没有指定分支，自动检测默认分支
                base_branch = self._detect_default_branch()

            # 创建 git worktree
            try:
                cmd = [
                    "git",
                    "worktree",
                    "add",
                    str(full_path),
                    "-b",
                    name,
                    base_branch,
                ]
                result = subprocess.run(
                    cmd,
                    check=True,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )

                print(get_message_with_format("create_git_worktree", name=name))
                if result.stdout:
                    print(result.stdout)

            except subprocess.CalledProcessError as e:
                error_msg = get_message_with_format(
                    "create_git_worktree_failed", error=str(e)
                )
                if e.stderr:
                    error_msg += f"\n{e.stderr}"
                raise Exception(error_msg)

            worktree_info = WorktreeInfo(name=name, path=str(full_path), branch=name)

        # 创建任务元数据
        if user_query:  # 只有提供了查询内容才创建元数据
            self.metadata_manager.create_task_metadata(
                task_id=name,
                user_query=user_query,
                worktree_path=str(full_path),
                original_project_path=self.original_project_path,
                model=model,
                split_mode=split_mode,
            )

        return worktree_info

    def _detect_default_branch(self) -> str:
        """
        自动检测 git 仓库的默认分支

        Returns:
            默认分支名称

        Raises:
            Exception: 无法检测到分支时抛出异常
        """
        # 首先尝试获取当前分支
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            current_branch = result.stdout.strip()
            if current_branch:
                print(
                    get_message_with_format(
                        "using_current_branch", branch=current_branch
                    )
                )
                return current_branch
        except subprocess.CalledProcessError:
            pass

        # 如果无法获取当前分支，检查本地分支中是否有 main 或 master
        try:
            result = subprocess.run(
                ["git", "branch", "--list"],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            branches = []
            for line in result.stdout.split("\n"):
                branch = line.strip().lstrip("*").strip()
                if branch:
                    branches.append(branch)

            print(get_message_with_format("detected_branches", branches=str(branches)))

            # 优先查找 main 或 master
            if "main" in branches:
                print(get_message("using_main_branch"))
                return "main"
            if "master" in branches:
                print(get_message("using_master_branch"))
                return "master"

            # 如果找不到 main 或 master，返回第一个分支
            if branches:
                first_branch = branches[0]
                print(
                    get_message_with_format(
                        "using_first_available_branch", branch=first_branch
                    )
                )
                return first_branch

        except subprocess.CalledProcessError as e:
            print(get_message_with_format("get_branch_list_failed", error=str(e)))

        # 最后尝试使用 git symbolic-ref 获取默认分支
        try:
            result = subprocess.run(
                ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            ref = result.stdout.strip()
            if ref.startswith("refs/remotes/origin/"):
                default_branch = ref.replace("refs/remotes/origin/", "")
                print(
                    get_message_with_format(
                        "using_remote_default_branch", branch=default_branch
                    )
                )
                return default_branch
        except subprocess.CalledProcessError:
            pass

        raise Exception(get_message("cannot_detect_any_branch"))

    def cleanup_worktree(self, info: WorktreeInfo) -> None:
        """
        清理指定的 worktree

        Args:
            info: worktree 信息

        Raises:
            Exception: 清理失败时抛出异常
        """
        # 删除 worktree
        try:
            subprocess.run(
                ["git", "worktree", "remove", info.path, "--force"],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except subprocess.CalledProcessError:
            # 如果命令失败，尝试手动删除目录
            try:
                shutil.rmtree(info.path)
            except OSError as e:
                raise Exception(
                    get_message_with_format("cleanup_worktree_failed", error=str(e))
                )

        # 删除分支（如果存在）
        try:
            subprocess.run(
                ["git", "branch", "-D", info.branch],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except subprocess.CalledProcessError:
            # 忽略错误，因为分支可能不存在
            pass

    def list_worktrees(self) -> List[WorktreeInfo]:
        """
        列出所有 worktree

        Returns:
            WorktreeInfo 列表

        Raises:
            Exception: 获取列表失败时抛出异常
        """
        try:
            result = subprocess.run(
                ["git", "worktree", "list", "--porcelain"],
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except subprocess.CalledProcessError as e:
            raise Exception(
                get_message_with_format("get_worktree_list_failed", error=str(e))
            )

        worktrees = []
        lines = result.stdout.split("\n")

        current = WorktreeInfo(name="", path="", branch="")
        for line in lines:
            line = line.strip()
            if not line:
                if current.path:
                    worktrees.append(current)
                    current = WorktreeInfo(name="", path="", branch="")
                continue

            if line.startswith("worktree "):
                current.path = line.replace("worktree ", "", 1)
                current.name = Path(current.path).name
            elif line.startswith("branch "):
                current.branch = line.replace("branch ", "", 1)

        # 添加最后一个 worktree（如果有）
        if current.path:
            worktrees.append(current)

        return worktrees

    def cleanup_all_worktrees(self, pattern: str = "") -> None:
        """
        清理所有匹配模式的 worktree

        Args:
            pattern: 匹配模式，为空时清理所有
        """
        try:
            worktrees = self.list_worktrees()
        except Exception as e:
            print(get_message_with_format("get_worktree_list_failed", error=str(e)))
            return

        for wt in worktrees:
            # 只清理在我们工作目录中的 worktree
            if wt.path.startswith(self.work_dir):
                if not pattern or pattern in wt.name:
                    print(get_message_with_format("cleaning_worktree", name=wt.name))
                    try:
                        self.cleanup_worktree(wt)
                    except Exception as e:
                        print(
                            get_message_with_format(
                                "cleanup_worktree_warning", error=str(e)
                            )
                        )

    def write_content_to_worktree(
        self, info: WorktreeInfo, filename: str, content: str
    ) -> None:
        """
        在 worktree 中写入内容到文件

        Args:
            info: worktree 信息
            filename: 文件名
            content: 文件内容

        Raises:
            Exception: 写入失败时抛出异常
        """
        file_path = Path(info.path) / filename

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            info.temp_file = filename
        except OSError as e:
            raise Exception(get_message_with_format("write_file_failed", error=str(e)))

    def get_managed_worktrees(self) -> List[WorktreeInfo]:
        """
        获取由此管理器管理的 worktree（在工作目录中的）

        Returns:
            管理的 WorktreeInfo 列表
        """
        try:
            all_worktrees = self.list_worktrees()
            managed = []

            for wt in all_worktrees:
                if wt.path.startswith(self.work_dir):
                    managed.append(wt)

            return managed
        except Exception:
            return []

    def worktree_exists(self, name: str) -> bool:
        """
        检查指定名称的 worktree 是否存在

        Args:
            name: worktree 名称

        Returns:
            是否存在
        """
        full_path = Path(self.work_dir) / name
        return full_path.exists()

    def get_worktree_info(self, name: str) -> Optional[WorktreeInfo]:
        """
        获取指定名称的 worktree 信息

        Args:
            name: worktree 名称

        Returns:
            WorktreeInfo 或 None
        """
        try:
            worktrees = self.list_worktrees()
            for wt in worktrees:
                if wt.name == name and wt.path.startswith(self.work_dir):
                    return wt
        except Exception:
            pass

        return None

    def update_task_status(
        self,
        task_id: str,
        status: str,
        error_message: str = "",
        log_file: str = "",
        execution_result: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        更新任务状态

        Args:
            task_id: 任务ID
            status: 新状态
            error_message: 错误信息
            log_file: 日志文件路径
            execution_result: 执行结果

        Returns:
            bool: 是否更新成功
        """
        return self.metadata_manager.update_task_status(
            task_id=task_id,
            status=status,
            error_message=error_message,
            log_file=log_file,
            execution_result=execution_result,
        )

    def get_task_metadata(self, task_id: str):
        """获取任务元数据"""
        return self.metadata_manager.load_task_metadata(task_id)

    def list_all_tasks(self, status_filter: Optional[str] = None):
        """列出所有任务"""
        return self.metadata_manager.list_tasks(status_filter)

    def get_tasks_summary(self):
        """获取任务汇总"""
        return self.metadata_manager.get_task_summary()
