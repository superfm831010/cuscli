"""
Git 文件获取辅助模块

提供 Git 仓库文件信息获取的统一接口，支持暂存区、工作区、
历史 commit 和 diff 文件的获取。

主要用于 CodeChecker 插件的 Git 集成功能。
"""

from typing import List, Optional, Dict
import os
from git import Repo, GitCommandError, BadName
from loguru import logger


class GitFileHelper:
    """
    Git 文件操作辅助类

    提供获取 Git 仓库中不同状态文件的方法，包括：
    - 暂存区文件（已 add 但未 commit）
    - 工作区修改文件（已修改但未 add）
    - 历史 commit 的变更文件
    - 两个 commit 间的差异文件

    Attributes:
        repo_path: Git 仓库根目录的绝对路径
        repo: GitPython 的 Repo 对象
    """

    def __init__(self, repo_path: str = "."):
        """
        初始化 GitFileHelper

        Args:
            repo_path: Git 仓库路径，默认当前目录

        Raises:
            RuntimeError: 如果不是有效的 Git 仓库
        """
        self.repo_path = os.path.abspath(repo_path)

        try:
            self.repo = Repo(self.repo_path)
        except Exception as e:
            raise RuntimeError(
                f"不是有效的 Git 仓库: {self.repo_path}\n"
                f"错误: {e}\n"
                f"请确保在 Git 仓库中执行此命令"
            )

        logger.info(f"GitFileHelper 初始化成功: {self.repo_path}")

    def get_staged_files(self) -> List[str]:
        """
        获取暂存区文件列表（已 add 但未 commit）

        Returns:
            文件路径列表（绝对路径）

        Example:
            >>> helper = GitFileHelper()
            >>> files = helper.get_staged_files()
            >>> print(files)
            ['/path/to/repo/src/main.py', '/path/to/repo/src/utils.py']
        """
        try:
            # 获取暂存区与 HEAD 的差异（包括新增、修改的文件）
            # 使用 repo.head.commit.diff() 来获取HEAD与暂存区的差异
            # 这种方法能正确识别新增文件（new_file=True）
            try:
                diff_index = self.repo.head.commit.diff()
            except (GitCommandError, BadName, ValueError):
                # 如果没有HEAD（初始仓库），获取所有暂存的文件
                logger.debug("没有HEAD，获取所有暂存文件")
                # 这种情况下所有在index中的文件都算暂存文件
                staged_entries = [
                    entry[0] for entry in self.repo.index.entries.keys()
                ]
                files = [
                    os.path.join(self.repo_path, path)
                    for path in staged_entries
                    if os.path.exists(os.path.join(self.repo_path, path))
                ]
                logger.info(f"暂存区文件: {len(files)} 个")
                return files

            files = []
            for diff_item in diff_index:
                # 跳过删除的文件
                if diff_item.deleted_file:
                    logger.debug(f"跳过删除的文件: {diff_item.a_path}")
                    continue

                # 新增文件或修改文件，使用 b_path（变更后的路径）
                # 对于新增文件，a_path 和 b_path 相同
                file_path = diff_item.b_path or diff_item.a_path

                # 转换为绝对路径
                abs_path = os.path.join(self.repo_path, file_path)

                # 确保文件存在（应该存在于工作区）
                if os.path.exists(abs_path):
                    files.append(abs_path)
                else:
                    logger.warning(f"文件不存在: {abs_path}")

            logger.info(f"暂存区文件: {len(files)} 个")
            return files

        except GitCommandError as e:
            logger.error(f"获取暂存区文件失败: {e}")
            raise RuntimeError(f"获取暂存区文件失败: {e}")

    def get_unstaged_files(self) -> List[str]:
        """
        获取工作区修改文件列表（已修改但未 add）

        Returns:
            文件路径列表（绝对路径）

        Example:
            >>> helper = GitFileHelper()
            >>> files = helper.get_unstaged_files()
            >>> print(files)
            ['/path/to/repo/src/main.py']
        """
        try:
            # 获取工作区与暂存区的差异
            diff_working = self.repo.index.diff(None)

            files = []
            for diff_item in diff_working:
                # 跳过删除的文件
                if diff_item.deleted_file:
                    logger.debug(f"跳过删除的文件: {diff_item.a_path}")
                    continue

                file_path = diff_item.a_path
                abs_path = os.path.join(self.repo_path, file_path)

                if os.path.exists(abs_path):
                    files.append(abs_path)
                else:
                    logger.warning(f"文件不存在: {abs_path}")

            logger.info(f"工作区修改文件: {len(files)} 个")
            return files

        except GitCommandError as e:
            logger.error(f"获取工作区文件失败: {e}")
            raise RuntimeError(f"获取工作区文件失败: {e}")

    def get_commit_files(self, commit_hash: str) -> List[str]:
        """
        获取指定 commit 的变更文件

        Args:
            commit_hash: commit 哈希值（完整或短哈希均可）

        Returns:
            文件路径列表（相对于仓库根目录的相对路径）

        Raises:
            ValueError: commit 不存在

        Example:
            >>> helper = GitFileHelper()
            >>> files = helper.get_commit_files("abc1234")
            >>> print(files)
            ['src/main.py', 'src/utils.py']
        """
        try:
            # 解析 commit（支持短哈希）
            commit = self.repo.commit(commit_hash)

            logger.info(
                f"Commit 信息: {commit.hexsha[:7]} - "
                f"{commit.message.splitlines()[0]}"
            )

            # 如果是初始 commit，没有父节点
            if not commit.parents:
                logger.warning(f"Commit {commit_hash} 是初始提交，无父节点")
                # 返回该 commit 中的所有文件
                files = []
                for item in commit.tree.traverse():
                    if item.type == 'blob':  # 只要文件，不要目录
                        files.append(item.path)
                logger.info(f"初始 Commit 文件: {len(files)} 个")
                return files

            # 与父节点对比
            parent = commit.parents[0]
            diff = parent.diff(commit)

            files = []
            for diff_item in diff:
                # 跳过删除的文件
                if diff_item.deleted_file:
                    logger.debug(f"跳过删除的文件: {diff_item.a_path}")
                    continue

                # 使用变更后的路径
                file_path = diff_item.b_path or diff_item.a_path
                files.append(file_path)

            logger.info(f"Commit {commit_hash[:7]} 变更文件: {len(files)} 个")
            return files

        except (ValueError, BadName):
            raise ValueError(f"Commit 不存在: {commit_hash}")
        except GitCommandError as e:
            logger.error(f"获取 commit 文件失败: {e}")
            raise RuntimeError(f"获取 commit 文件失败: {e}")

    def get_diff_files(self, commit1: str, commit2: str = "HEAD") -> List[str]:
        """
        获取两个 commit 之间的差异文件

        Args:
            commit1: 起始 commit（哈希值、分支名或标签）
            commit2: 结束 commit（默认 HEAD）

        Returns:
            文件路径列表（相对于仓库根目录的相对路径）

        Example:
            >>> helper = GitFileHelper()
            >>> files = helper.get_diff_files("main", "dev")
            >>> print(files)
            ['src/feature.py', 'tests/test_feature.py']
        """
        try:
            c1 = self.repo.commit(commit1)
            c2 = self.repo.commit(commit2)

            logger.info(f"对比: {c1.hexsha[:7]}...{c2.hexsha[:7]}")

            diff = c1.diff(c2)

            files = []
            for diff_item in diff:
                # 跳过删除的文件
                if diff_item.deleted_file:
                    logger.debug(f"跳过删除的文件: {diff_item.a_path}")
                    continue

                file_path = diff_item.b_path or diff_item.a_path
                files.append(file_path)

            logger.info(f"Diff 文件: {len(files)} 个")
            return files

        except ValueError as e:
            raise ValueError(f"Commit 不存在: {e}")
        except GitCommandError as e:
            raise RuntimeError(f"获取 diff 文件失败: {e}")

    def get_file_content_at_commit(
        self,
        file_path: str,
        commit_hash: str,
        max_size: int = 10 * 1024 * 1024  # 10MB
    ) -> Optional[str]:
        """
        获取文件在指定 commit 时的内容

        Args:
            file_path: 文件路径（相对于仓库根目录）
            commit_hash: commit 哈希值
            max_size: 最大文件大小（字节），默认 10MB

        Returns:
            文件内容字符串，如果失败或文件过大返回 None

        Example:
            >>> helper = GitFileHelper()
            >>> content = helper.get_file_content_at_commit("src/main.py", "abc1234")
            >>> print(content[:50])
            'import os\nimport sys\n\ndef main():\n    pass'
        """
        try:
            # 先检查文件大小（Phase 3: 大文件过滤）
            commit = self.repo.commit(commit_hash)
            try:
                blob = commit.tree / file_path
                if blob.size > max_size:
                    logger.warning(
                        f"文件过大，跳过: {file_path} "
                        f"({blob.size / 1024 / 1024:.2f}MB > {max_size / 1024 / 1024}MB)"
                    )
                    return None
            except KeyError:
                # 文件不存在于该 commit（可能是删除操作）
                logger.debug(f"文件不存在于 commit: {file_path}@{commit_hash}")
                return None

            # 使用 git show 命令获取文件内容
            content = self.repo.git.show(f"{commit_hash}:{file_path}")
            return content

        except GitCommandError as e:
            logger.warning(
                f"无法获取文件内容: {file_path}@{commit_hash}, {e}"
            )
            return None
        except Exception as e:
            logger.error(
                f"获取文件内容时发生错误: {file_path}@{commit_hash}, {e}"
            )
            return None

    def is_binary_file(
        self,
        file_path: str,
        commit_hash: Optional[str] = None
    ) -> bool:
        """
        判断是否为二进制文件

        Args:
            file_path: 文件路径（相对于仓库根目录）
            commit_hash: 如果指定，检查该 commit 时的文件；否则检查工作区文件

        Returns:
            True 表示二进制文件，False 表示文本文件

        Example:
            >>> helper = GitFileHelper()
            >>> helper.is_binary_file("image.png")
            True
            >>> helper.is_binary_file("src/main.py")
            False
        """
        try:
            if commit_hash:
                # 历史文件：使用 git 检查
                # Git 会自动检测二进制文件
                # 尝试 show，如果包含 NULL 字节则为二进制
                content = self.get_file_content_at_commit(file_path, commit_hash)
                if content is None:
                    return True
                return '\x00' in content
            else:
                # 工作区文件：读取文件头判断
                abs_path = os.path.join(self.repo_path, file_path)
                if not os.path.exists(abs_path):
                    return False

                with open(abs_path, 'rb') as f:
                    chunk = f.read(1024)
                    if not chunk:
                        return False
                    return b'\x00' in chunk

        except Exception as e:
            logger.warning(f"检测二进制文件失败: {file_path}, {e}")
            return True  # 保守起见，当作二进制

    def get_commit_info(self, commit_hash: str) -> Dict[str, str]:
        """
        获取 commit 详细信息

        Args:
            commit_hash: commit 哈希值

        Returns:
            包含 commit 信息的字典:
            {
                'hash': '完整哈希',
                'short_hash': '短哈希',
                'message': '提交信息',
                'author': '作者',
                'date': '提交日期（ISO 8601格式）',
                'files_changed': 变更文件数
            }

        Example:
            >>> helper = GitFileHelper()
            >>> info = helper.get_commit_info("abc1234")
            >>> print(info['message'])
            'feat: add new feature'
        """
        try:
            commit = self.repo.commit(commit_hash)

            files_changed = 0
            if commit.parents:
                diff = commit.parents[0].diff(commit)
                files_changed = len(list(diff))
            else:
                # 初始 commit，计算所有文件
                files_changed = sum(1 for item in commit.tree.traverse()
                                    if item.type == 'blob')

            return {
                'hash': commit.hexsha,
                'short_hash': commit.hexsha[:7],
                'message': commit.message.strip(),
                'author': f"{commit.author.name} <{commit.author.email}>",
                'date': commit.committed_datetime.isoformat(),
                'files_changed': files_changed
            }

        except Exception as e:
            logger.error(f"获取 commit 信息失败: {e}")
            return {}


class TempFileManager:
    """
    临时文件管理器，用于批量管理从 Git 历史中提取的临时文件

    用于 Check Git Phase 3: 支持检查历史 commit 中不在工作区的文件。
    将 Git 对象中的文件内容提取到临时目录，检查完成后自动清理。

    Attributes:
        temp_dir: 临时目录路径
        temp_files: 原始路径 -> 临时路径的映射字典

    Example:
        >>> with TempFileManager() as manager:
        ...     temp_path = manager.create_temp_file("src/main.py", "print('hello')")
        ...     # 使用 temp_path 进行检查
        ...     # 退出时自动清理
    """

    # 大文件限制：10MB
    MAX_FILE_SIZE = 10 * 1024 * 1024

    def __init__(self):
        """初始化临时文件管理器，创建临时目录"""
        import tempfile
        self.temp_dir = tempfile.mkdtemp(prefix="codechecker_git_")
        self.temp_files: Dict[str, str] = {}  # 原始路径 -> 临时路径
        logger.info(f"创建临时目录: {self.temp_dir}")

    def create_temp_file(self, file_path: str, content: str) -> str:
        """
        创建临时文件并保留目录结构

        Args:
            file_path: 原始文件路径（相对路径）
            content: 文件内容

        Returns:
            临时文件绝对路径

        Raises:
            OSError: 文件创建失败

        Example:
            >>> manager = TempFileManager()
            >>> temp_path = manager.create_temp_file("src/main.py", "code...")
            >>> print(temp_path)
            '/tmp/codechecker_git_xxx/src/main.py'
        """
        # 保留目录结构以避免文件名冲突
        # 例如: src/main.py -> temp_dir/src/main.py
        # 清理路径中的特殊字符
        relative_path = file_path.replace('..', '_').replace(':', '_')

        # Windows 路径兼容：统一使用正斜杠
        relative_path = relative_path.replace('\\', '/')

        temp_file = os.path.join(self.temp_dir, relative_path)

        try:
            # 创建父目录
            parent_dir = os.path.dirname(temp_file)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)

            # 写入文件（明确指定 UTF-8 编码）
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(content)

            # 保存映射
            self.temp_files[file_path] = temp_file
            logger.debug(f"创建临时文件: {file_path} -> {temp_file}")
            return temp_file

        except PermissionError as e:
            logger.error(f"无权限写入临时文件: {temp_file}, {e}")
            raise OSError(f"无权限创建临时文件: {file_path}")
        except Exception as e:
            logger.error(f"创建临时文件失败: {file_path}, {e}")
            raise OSError(f"创建临时文件失败: {file_path}, {e}")

    def get_temp_path(self, file_path: str) -> Optional[str]:
        """
        获取文件的临时路径

        Args:
            file_path: 原始文件路径

        Returns:
            临时文件路径，如果不存在返回 None
        """
        return self.temp_files.get(file_path)

    def get_original_path(self, temp_path: str) -> Optional[str]:
        """
        根据临时路径反查原始路径

        Args:
            temp_path: 临时文件路径

        Returns:
            原始文件路径，如果不存在返回 None
        """
        # 反向查找
        for orig, temp in self.temp_files.items():
            if temp == temp_path:
                return orig
        return None

    def cleanup(self):
        """
        清理所有临时文件

        删除临时目录及其所有内容。
        如果清理失败，只记录警告日志，不抛出异常。
        """
        import shutil
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info(f"清理临时目录: {self.temp_dir}")
        except PermissionError as e:
            logger.warning(f"清理临时目录失败（权限问题）: {self.temp_dir}, {e}")
        except Exception as e:
            logger.error(f"清理临时目录失败: {self.temp_dir}, {e}")

    def __enter__(self):
        """Context manager 入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager 退出，自动清理"""
        self.cleanup()
        # 不抑制异常
        return False

    def __len__(self) -> int:
        """返回管理的临时文件数量"""
        return len(self.temp_files)
