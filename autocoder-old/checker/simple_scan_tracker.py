"""
简单扫描状态跟踪器

用于跟踪 Git 仓库的代码扫描状态，实现增量扫描功能。

核心功能：
- 管理 .check 目录和 .checked 文件
- 记录文件扫描状态（checked/unchecked）
- 基于 Git diff 检测变更文件
- 支持增量扫描和全量扫描

文件格式：
- {branch}.checked: 文本格式，每行记录一个文件的状态
- .last_commits: JSON 格式，记录上次扫描的 commit

作者: Claude AI
创建时间: 2025-10-17
"""

import os
import json
from typing import Dict, List, Optional, Tuple, Set
from pathlib import Path
from datetime import datetime
from loguru import logger

from git import Repo, GitCommandError


class SimpleScanTracker:
    """
    简单的扫描状态跟踪器

    使用文本文件记录每个文件的扫描状态（checked/unchecked），
    基于 Git diff 自动检测变更文件，实现增量扫描。

    Attributes:
        repo_path: Git 仓库路径
        check_dir: .check 目录路径
    """

    def __init__(self, repo_path: str):
        """
        初始化扫描状态跟踪器

        Args:
            repo_path: Git 仓库根目录路径
        """
        self.repo_path = os.path.abspath(repo_path)
        self.check_dir = os.path.join(self.repo_path, ".check")
        self._ensure_check_dir()

    def _ensure_check_dir(self):
        """确保 .check 目录存在"""
        if not os.path.exists(self.check_dir):
            os.makedirs(self.check_dir, exist_ok=True)
            logger.info(f"创建扫描状态目录: {self.check_dir}")

    def get_checked_file(self, version: str) -> str:
        """
        获取指定版本的 .checked 文件路径

        Args:
            version: 分支名/标签名/commit hash

        Returns:
            .checked 文件的绝对路径
        """
        # 清理版本名称中的特殊字符
        safe_name = version.replace('/', '_').replace('\\', '_')
        return os.path.join(self.check_dir, f"{safe_name}.checked")

    def get_last_commits_file(self) -> str:
        """获取 .last_commits 文件路径"""
        return os.path.join(self.check_dir, ".last_commits")

    def has_scan_record(self, version: str) -> bool:
        """
        检查是否存在扫描记录

        Args:
            version: 分支名/标签名/commit hash

        Returns:
            True 如果存在扫描记录
        """
        checked_file = self.get_checked_file(version)
        return os.path.exists(checked_file)

    def load_file_states(self, version: str) -> Dict[str, str]:
        """
        加载文件扫描状态

        Args:
            version: 分支名/标签名/commit hash

        Returns:
            {file_path: 'checked'|'unchecked'} 状态字典
        """
        checked_file = self.get_checked_file(version)

        if not os.path.exists(checked_file):
            logger.debug(f"扫描记录不存在: {checked_file}")
            return {}

        states = {}

        try:
            with open(checked_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()

                    # 跳过注释和空行
                    if not line or line.startswith('#'):
                        continue

                    # 解析：状态|文件路径[|变化类型]
                    parts = line.split('|')
                    if len(parts) >= 2:
                        status = parts[0]
                        file_path = parts[1]
                        states[file_path] = status

            logger.info(f"加载扫描状态: {len(states)} 个文件 (版本: {version})")
            return states

        except Exception as e:
            logger.error(f"加载扫描状态失败: {e}", exc_info=True)
            return {}

    def save_file_states(
        self,
        version: str,
        states: Dict[str, str],
        commit_info: Optional[Dict[str, str]] = None
    ):
        """
        保存文件扫描状态

        Args:
            version: 分支名/标签名/commit hash
            states: {file_path: 'checked'|'unchecked'} 状态字典
            commit_info: 可选的 commit 信息（hash, message, author, date）
        """
        checked_file = self.get_checked_file(version)

        try:
            with open(checked_file, 'w', encoding='utf-8') as f:
                # 写入元信息
                f.write(f"# Last scan: {datetime.now().isoformat()}\n")

                if commit_info:
                    f.write(f"# Commit: {commit_info.get('hash', 'unknown')}\n")
                    f.write(f"# Message: {commit_info.get('message', '')}\n")

                f.write(f"# Total: {len(states)} files\n")
                f.write(f"#\n")

                # 写入文件状态（按路径排序）
                for file_path in sorted(states.keys()):
                    status = states[file_path]
                    f.write(f"{status}|{file_path}\n")

            logger.info(f"保存扫描状态: {len(states)} 个文件 (版本: {version})")

        except Exception as e:
            logger.error(f"保存扫描状态失败: {e}", exc_info=True)
            raise RuntimeError(f"保存扫描状态失败: {e}")

    def get_last_commit(self, version: str) -> Optional[str]:
        """
        获取上次扫描的 commit hash

        Args:
            version: 分支名/标签名/commit hash

        Returns:
            上次扫描的 commit hash，如果不存在返回 None
        """
        last_commits_file = self.get_last_commits_file()

        if not os.path.exists(last_commits_file):
            return None

        try:
            with open(last_commits_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get(version)

        except Exception as e:
            logger.warning(f"读取 .last_commits 失败: {e}")
            return None

    def update_last_commit(self, version: str, commit_hash: str):
        """
        更新上次扫描的 commit hash

        Args:
            version: 分支名/标签名/commit hash
            commit_hash: 完整的 commit hash
        """
        last_commits_file = self.get_last_commits_file()

        # 加载现有数据
        data = {}
        if os.path.exists(last_commits_file):
            try:
                with open(last_commits_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception as e:
                logger.warning(f"读取 .last_commits 失败，将创建新文件: {e}")

        # 更新
        data[version] = commit_hash

        # 保存
        try:
            with open(last_commits_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            logger.info(f"更新上次扫描 commit: {version} -> {commit_hash[:7]}")

        except Exception as e:
            logger.error(f"保存 .last_commits 失败: {e}")
            raise RuntimeError(f"保存 .last_commits 失败: {e}")

    def get_changed_files(
        self,
        last_commit: str,
        current_commit: str
    ) -> Dict[str, str]:
        """
        获取两个 commit 之间的变更文件

        Args:
            last_commit: 上次扫描的 commit hash
            current_commit: 当前 commit hash

        Returns:
            {file_path: change_type} 变更类型字典
            change_type 可以是：'added', 'modified', 'deleted'
        """
        try:
            repo = Repo(self.repo_path)

            # 执行 git diff --name-status
            diff_output = repo.git.diff(
                last_commit,
                current_commit,
                name_status=True
            )

            changes = {}

            for line in diff_output.split('\n'):
                line = line.strip()
                if not line:
                    continue

                # 解析格式：状态\t文件路径
                # 状态：A(added), M(modified), D(deleted), R(renamed)
                parts = line.split('\t')
                if len(parts) < 2:
                    continue

                status_code = parts[0][0]  # 取第一个字符
                file_path = parts[1]

                # 映射状态
                if status_code == 'A':
                    changes[file_path] = 'added'
                elif status_code == 'M':
                    changes[file_path] = 'modified'
                elif status_code == 'D':
                    changes[file_path] = 'deleted'
                elif status_code == 'R':
                    # 重命名视为修改
                    changes[file_path] = 'modified'
                else:
                    # 其他情况视为修改
                    changes[file_path] = 'modified'

            logger.info(
                f"检测到 {len(changes)} 个变更文件 "
                f"({last_commit[:7]}...{current_commit[:7]})"
            )

            return changes

        except Exception as e:
            logger.error(f"获取变更文件失败: {e}", exc_info=True)
            raise RuntimeError(f"获取变更文件失败: {e}")

    def mark_changed_files(
        self,
        version: str,
        changes: Dict[str, str]
    ) -> int:
        """
        标记变更文件为 unchecked

        Args:
            version: 分支名/标签名/commit hash
            changes: {file_path: change_type} 变更字典

        Returns:
            标记为 unchecked 的文件数量
        """
        # 加载现有状态
        states = self.load_file_states(version)

        unchecked_count = 0

        for file_path, change_type in changes.items():
            if change_type == 'deleted':
                # 删除文件：从状态中移除
                if file_path in states:
                    del states[file_path]
                    logger.debug(f"移除已删除文件: {file_path}")
            else:
                # 新增或修改文件：标记为 unchecked
                states[file_path] = 'unchecked'
                unchecked_count += 1
                logger.debug(f"标记为 unchecked: {file_path} ({change_type})")

        # 保存更新后的状态
        self.save_file_states(version, states)

        logger.info(f"标记了 {unchecked_count} 个文件为 unchecked")
        return unchecked_count

    def get_unchecked_files(self, version: str) -> List[str]:
        """
        获取所有 unchecked 文件

        Args:
            version: 分支名/标签名/commit hash

        Returns:
            unchecked 文件路径列表（相对路径）
        """
        states = self.load_file_states(version)

        unchecked = [
            file_path
            for file_path, status in states.items()
            if status == 'unchecked'
        ]

        logger.info(f"找到 {len(unchecked)} 个 unchecked 文件")
        return unchecked

    def mark_as_checked(
        self,
        version: str,
        files: List[str],
        commit_info: Optional[Dict[str, str]] = None
    ):
        """
        标记文件为 checked

        Args:
            version: 分支名/标签名/commit hash
            files: 文件路径列表（相对路径）
            commit_info: 可选的 commit 信息
        """
        # 加载现有状态
        states = self.load_file_states(version)

        # 更新状态
        for file_path in files:
            states[file_path] = 'checked'

        # 保存
        self.save_file_states(version, states, commit_info)

        logger.info(f"标记了 {len(files)} 个文件为 checked")

    def initialize_full_scan(
        self,
        version: str,
        files: List[str],
        commit_info: Optional[Dict[str, str]] = None
    ):
        """
        初始化全量扫描（首次扫描或强制全量）

        将所有文件标记为 checked

        Args:
            version: 分支名/标签名/commit hash
            files: 所有文件路径列表（相对路径）
            commit_info: 可选的 commit 信息
        """
        states = {file_path: 'checked' for file_path in files}

        self.save_file_states(version, states, commit_info)

        logger.info(f"初始化全量扫描: {len(files)} 个文件标记为 checked")

    def get_scan_summary(self, version: str) -> Optional[Dict]:
        """
        获取扫描状态摘要

        Args:
            version: 分支名/标签名/commit hash

        Returns:
            包含扫描状态摘要的字典，不存在返回 None
        """
        if not self.has_scan_record(version):
            return None

        states = self.load_file_states(version)
        last_commit = self.get_last_commit(version)

        checked_count = sum(1 for s in states.values() if s == 'checked')
        unchecked_count = sum(1 for s in states.values() if s == 'unchecked')

        # 尝试从 .checked 文件读取元信息
        checked_file = self.get_checked_file(version)
        last_scan_time = None
        commit_hash = None
        commit_message = None

        try:
            with open(checked_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('# Last scan:'):
                        last_scan_time = line.split(':', 1)[1].strip()
                    elif line.startswith('# Commit:'):
                        commit_hash = line.split(':', 1)[1].strip()
                    elif line.startswith('# Message:'):
                        commit_message = line.split(':', 1)[1].strip()
        except Exception as e:
            logger.debug(f"读取元信息失败: {e}")

        return {
            'version': version,
            'total_files': len(states),
            'checked': checked_count,
            'unchecked': unchecked_count,
            'last_scan_time': last_scan_time,
            'last_commit': last_commit or commit_hash,
            'commit_message': commit_message
        }

    def reset(self, version: str):
        """
        清除扫描记录

        删除 .checked 文件和 .last_commits 中的记录

        Args:
            version: 分支名/标签名/commit hash
        """
        # 删除 .checked 文件
        checked_file = self.get_checked_file(version)
        if os.path.exists(checked_file):
            os.remove(checked_file)
            logger.info(f"删除扫描记录: {checked_file}")

        # 从 .last_commits 中移除
        last_commits_file = self.get_last_commits_file()
        if os.path.exists(last_commits_file):
            try:
                with open(last_commits_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if version in data:
                    del data[version]

                    with open(last_commits_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2)

                    logger.info(f"从 .last_commits 中移除: {version}")

            except Exception as e:
                logger.warning(f"更新 .last_commits 失败: {e}")

    def to_absolute_paths(self, files: List[str]) -> List[str]:
        """
        将相对路径转换为绝对路径

        Args:
            files: 相对路径列表

        Returns:
            绝对路径列表
        """
        return [os.path.join(self.repo_path, f) for f in files]

    def to_relative_paths(self, files: List[str]) -> List[str]:
        """
        将绝对路径转换为相对路径

        Args:
            files: 绝对路径列表

        Returns:
            相对路径列表
        """
        rel_paths = []
        for abs_path in files:
            try:
                rel_path = os.path.relpath(abs_path, self.repo_path)
                # 标准化路径分隔符（Git 使用正斜杠）
                rel_path = rel_path.replace(os.sep, '/')
                rel_paths.append(rel_path)
            except ValueError:
                # 跨盘符等情况，保留绝对路径
                logger.warning(f"无法转换为相对路径: {abs_path}")
                rel_paths.append(abs_path)

        return rel_paths
