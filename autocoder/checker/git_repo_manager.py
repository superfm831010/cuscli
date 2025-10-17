"""
Git 远程仓库管理模块

提供远程 Git 仓库的克隆、更新、认证等功能，
用于支持 CodeChecker 的远程仓库检查功能。

主要功能：
- 克隆或更新远程仓库
- 使用现有 Git 平台配置进行认证
- 版本切换（branch/tag/commit）
- 获取仓库信息和差异文件

作者: Claude AI
创建时间: 2025-10-17
"""

import os
import re
import subprocess
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urlparse, urlunparse
from pathlib import Path

from git import Repo, GitCommandError
from loguru import logger

from autocoder.common.git_platform_config import GitPlatformManager, GitPlatformConfig
from autocoder.checker.git_helper import GitFileHelper
from autocoder.checker.types import FileDiffInfo


class GitRepoManager:
    """
    Git 远程仓库管理器

    负责管理远程 Git 仓库的克隆、更新、认证等操作。

    Attributes:
        platform_manager: Git 平台配置管理器
    """

    def __init__(self, platform_manager: Optional[GitPlatformManager] = None):
        """
        初始化 Git 仓库管理器

        Args:
            platform_manager: Git 平台配置管理器（可选）
                如果未提供，将尝试加载默认配置
        """
        self.platform_manager = platform_manager or self._load_platform_manager()
        logger.info("GitRepoManager 初始化成功")

    def _load_platform_manager(self) -> GitPlatformManager:
        """
        加载默认的 Git 平台配置管理器

        Returns:
            GitPlatformManager 实例
        """
        # 尝试从默认位置加载配置
        config_file = Path.home() / ".auto-coder" / "plugins" / "git_helper_config.json"
        manager = GitPlatformManager(config_file=str(config_file) if config_file.exists() else None)
        return manager

    def clone_or_update_repo(
        self,
        repo_url: str,
        target_dir: str,
        branch: Optional[str] = None,
        tag: Optional[str] = None,
        commit: Optional[str] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        克隆或更新远程仓库

        逻辑：
        1. 检查 target_dir 是否已存在该仓库
        2. 如果已存在：执行 git fetch 更新，然后 checkout 指定版本
        3. 如果不存在：执行 git clone，然后 checkout 指定版本

        Args:
            repo_url: 仓库 URL
            target_dir: 目标目录
            branch: 分支名（可选）
            tag: 标签名（可选）
            commit: 提交哈希（可选）

        Returns:
            (repo_path, repo_info) 元组
            - repo_path: 仓库路径
            - repo_info: 仓库信息字典

        Raises:
            RuntimeError: 克隆或更新失败
            ValueError: 参数错误
        """
        # 参数验证
        version_count = sum([branch is not None, tag is not None, commit is not None])
        if version_count > 1:
            raise ValueError("只能指定 branch、tag 或 commit 中的一个")

        # 获取认证配置
        config = self._match_git_config(repo_url)

        # 友好提示：如果是 HTTP(S) URL 但没有配置 token
        parsed = urlparse(repo_url)
        is_http = parsed.scheme in ['http', 'https']
        has_token = config and config.token

        if is_http and not has_token:
            logger.warning(
                f"⚠️  未找到匹配的 Git 平台配置或 token\n"
                f"   仓库 URL: {repo_url}\n"
                f"   将尝试使用 Git 凭证助手进行认证（可能需要输入账号密码）\n"
                f"   提示：可使用 '/git /config' 命令配置 GitLab/GitHub token 以避免重复输入"
            )

        auth_url = self._build_auth_url(repo_url, config) if config else repo_url
        use_credential_helper = is_http and not has_token

        # 确保目标目录存在
        target_path = Path(target_dir).resolve()
        target_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"目标目录: {target_path}")

        # 检查是否已存在仓库
        repo_path = str(target_path)

        if (target_path / ".git").exists():
            logger.info(f"仓库已存在，执行更新: {repo_path}")
            repo = self._update_repo(repo_path, auth_url, use_credential_helper)
        else:
            logger.info(f"仓库不存在，执行克隆: {repo_url} -> {repo_path}")
            repo = self._clone_repo(auth_url, repo_path, use_credential_helper)

        # 切换到指定版本
        self._checkout_version(repo, branch, tag, commit)

        # 获取仓库信息
        repo_info = self.get_repo_info(repo_path)

        logger.info(f"仓库准备完成: {repo_info['current_commit']['short_hash']}")
        return repo_path, repo_info

    def _clone_repo(self, repo_url: str, target_dir: str, use_credential_helper: bool = False) -> Repo:
        """
        克隆远程仓库

        Args:
            repo_url: 仓库 URL（可能包含认证信息）
            target_dir: 目标目录
            use_credential_helper: 是否使用 Git 凭证助手（支持交互式认证）

        Returns:
            Repo 对象

        Raises:
            RuntimeError: 克隆失败
        """
        try:
            logger.info(f"开始克隆仓库...")

            # 准备环境变量和 Git 配置
            env = os.environ.copy()
            git_config = {}

            if use_credential_helper:
                # 启用交互式认证
                # GIT_TERMINAL_PROMPT=1 允许 Git 提示输入凭证
                env['GIT_TERMINAL_PROMPT'] = '1'

                # 配置凭证助手（使用系统默认）
                # Windows: manager-core, Linux/Mac: cache 或 store
                if os.name == 'nt':  # Windows
                    git_config['credential.helper'] = 'manager-core'
                else:  # Linux/Mac
                    # 优先使用 cache（临时缓存），如果不可用则使用 store（永久保存）
                    git_config['credential.helper'] = 'cache --timeout=3600'

                logger.info("已启用 Git 凭证助手，支持交互式认证")
            else:
                # 禁用交互式提示（已有 token）
                env['GIT_TERMINAL_PROMPT'] = '0'
                logger.debug("已禁用交互式提示（使用 token 认证）")

            # 使用 GitPython 克隆仓库
            # 注意：GitPython 会继承当前进程的环境变量
            # 由于 GitPython 的安全限制，我们不能直接使用 -c 选项
            # 改用环境变量方式传递 Git 配置
            if git_config:
                for key, value in git_config.items():
                    # 将 Git 配置转换为环境变量
                    # 例如: credential.helper -> GIT_CONFIG_KEY_0=credential.helper, GIT_CONFIG_VALUE_0=cache
                    # 但更简单的方法是使用 subprocess 直接调用 git clone
                    pass

            # 方案：如果需要凭证助手，使用 subprocess 调用 git clone
            # 否则使用 GitPython
            if use_credential_helper:
                logger.info("使用 subprocess 调用 git clone（支持交互式认证）")

                # 构建 git clone 命令
                cmd = ['git', 'clone', repo_url, target_dir]

                # 添加 Git 配置
                for key, value in git_config.items():
                    cmd.insert(1, '-c')
                    cmd.insert(2, f'{key}={value}')

                # 执行 git clone
                result = subprocess.run(
                    cmd,
                    env=env,
                    capture_output=True,
                    text=True
                )

                if result.returncode != 0:
                    # 克隆失败，解析错误信息
                    error_msg = result.stderr or result.stdout or "Unknown error"

                    if "Authentication failed" in error_msg or "could not read Username" in error_msg:
                        raise RuntimeError(
                            f"克隆失败：认证错误\n"
                            f"请检查：\n"
                            f"1. 仓库 URL 是否正确\n"
                            f"2. 输入的账号密码是否正确\n"
                            f"3. 是否有权限访问该仓库\n"
                            f"提示：可使用 '/git /config' 命令配置 token 以避免每次输入"
                        )
                    elif "Repository not found" in error_msg:
                        raise RuntimeError(
                            f"克隆失败：仓库不存在\n"
                            f"请检查仓库 URL 是否正确"
                        )
                    elif "Could not resolve host" in error_msg:
                        raise RuntimeError(
                            f"克隆失败：网络错误\n"
                            f"请检查网络连接和仓库 URL"
                        )
                    else:
                        raise RuntimeError(f"克隆仓库失败: {error_msg}")

                # 加载克隆好的仓库
                repo = Repo(target_dir)
            else:
                # 使用 GitPython 克隆（已有 token，不需要交互）
                repo = Repo.clone_from(
                    repo_url,
                    target_dir,
                    env=env
                )

            logger.info(f"克隆完成: {target_dir}")
            return repo

        except GitCommandError as e:
            error_msg = str(e)

            # 解析常见错误
            if "Authentication failed" in error_msg or "could not read Username" in error_msg:
                hint = (
                    f"克隆失败：认证错误\n"
                    f"请检查：\n"
                    f"1. 仓库 URL 是否正确\n"
                )

                if use_credential_helper:
                    hint += (
                        f"2. 输入的账号密码是否正确\n"
                        f"3. 是否有权限访问该仓库\n"
                        f"提示：可使用 '/git /config' 命令配置 token 以避免每次输入"
                    )
                else:
                    hint += (
                        f"2. 是否已配置 Git 平台认证（使用 /git /config 命令）\n"
                        f"3. Token 是否有效且有权限访问该仓库"
                    )

                raise RuntimeError(hint)

            elif "Repository not found" in error_msg:
                raise RuntimeError(
                    f"克隆失败：仓库不存在\n"
                    f"请检查仓库 URL 是否正确"
                )
            elif "Could not resolve host" in error_msg:
                raise RuntimeError(
                    f"克隆失败：网络错误\n"
                    f"请检查网络连接和仓库 URL"
                )
            else:
                raise RuntimeError(f"克隆仓库失败: {error_msg}")

        except Exception as e:
            raise RuntimeError(f"克隆仓库失败: {e}")

    def _update_repo(self, repo_path: str, repo_url: str, use_credential_helper: bool = False) -> Repo:
        """
        更新已存在的仓库

        Args:
            repo_path: 仓库路径
            repo_url: 仓库 URL（可能包含认证信息）
            use_credential_helper: 是否使用 Git 凭证助手（支持交互式认证）

        Returns:
            Repo 对象

        Raises:
            RuntimeError: 更新失败
        """
        try:
            repo = Repo(repo_path)

            # 确保工作目录干净
            if repo.is_dirty():
                logger.warning("工作目录有未提交的修改，将被重置")
                repo.git.reset('--hard', 'HEAD')

            # 更新远程 URL（可能包含新的认证信息）
            origin = repo.remote('origin')
            if origin.url != repo_url:
                logger.info(f"更新远程 URL: {origin.url} -> {repo_url}")
                origin.set_url(repo_url)

            # 准备环境变量（与 _clone_repo 一致）
            env = os.environ.copy()

            if use_credential_helper:
                # 启用交互式认证
                env['GIT_TERMINAL_PROMPT'] = '1'
                logger.info("已启用 Git 凭证助手（fetch 操作）")
            else:
                # 禁用交互式提示（已有 token）
                env['GIT_TERMINAL_PROMPT'] = '0'
                logger.debug("已禁用交互式提示（fetch 操作）")

            # 执行 fetch
            logger.info("开始 fetch...")

            # 注意：GitPython 的 fetch() 方法会继承环境变量
            # 但为了确保环境变量生效，我们使用底层的 git 命令
            with repo.git.custom_environment(**env):
                origin.fetch()

            logger.info("Fetch 完成")

            return repo

        except GitCommandError as e:
            error_msg = str(e)

            # 解析常见错误（与 _clone_repo 类似）
            if "Authentication failed" in error_msg or "could not read Username" in error_msg:
                hint = (
                    f"更新仓库失败：认证错误\n"
                    f"请检查：\n"
                )

                if use_credential_helper:
                    hint += (
                        f"1. 输入的账号密码是否正确\n"
                        f"2. 是否有权限访问该仓库\n"
                        f"提示：可使用 '/git /config' 命令配置 token 以避免每次输入"
                    )
                else:
                    hint += (
                        f"1. 是否已配置 Git 平台认证（使用 /git /config 命令）\n"
                        f"2. Token 是否有效且有权限访问该仓库"
                    )

                raise RuntimeError(hint)

            else:
                raise RuntimeError(f"更新仓库失败: {error_msg}")

        except Exception as e:
            raise RuntimeError(f"更新仓库失败: {e}")

    def _checkout_version(
        self,
        repo: Repo,
        branch: Optional[str] = None,
        tag: Optional[str] = None,
        commit: Optional[str] = None
    ):
        """
        切换到指定版本

        Args:
            repo: Repo 对象
            branch: 分支名
            tag: 标签名
            commit: 提交哈希

        Raises:
            RuntimeError: 切换失败
            ValueError: 指定的版本不存在
        """
        try:
            if commit:
                logger.info(f"切换到 commit: {commit}")
                repo.git.checkout(commit)
            elif tag:
                logger.info(f"切换到 tag: {tag}")
                repo.git.checkout(tag)
            elif branch:
                logger.info(f"切换到 branch: {branch}")
                # 尝试切换到远程分支
                try:
                    repo.git.checkout(f"origin/{branch}")
                except GitCommandError:
                    # 如果远程分支不存在，尝试本地分支
                    repo.git.checkout(branch)
            else:
                # 默认切换到默认分支（通常是 main 或 master）
                default_branch = repo.git.symbolic_ref('refs/remotes/origin/HEAD').split('/')[-1]
                logger.info(f"切换到默认分支: {default_branch}")
                repo.git.checkout(default_branch)

        except GitCommandError as e:
            error_msg = str(e)

            if "pathspec" in error_msg and "did not match" in error_msg:
                version = commit or tag or branch
                raise ValueError(
                    f"指定的版本不存在: {version}\n"
                    f"请检查分支、标签或提交哈希是否正确"
                )
            else:
                raise RuntimeError(f"切换版本失败: {error_msg}")
        except Exception as e:
            raise RuntimeError(f"切换版本失败: {e}")

    def get_repo_info(self, repo_path: str) -> Dict[str, Any]:
        """
        获取仓库信息

        Args:
            repo_path: 仓库路径

        Returns:
            仓库信息字典:
            {
                "repo_url": "http://...",
                "repo_path": "/path/to/repo",
                "current_branch": "main" or None (detached HEAD),
                "current_commit": {
                    "hash": "abc1234...",
                    "short_hash": "abc1234",
                    "message": "feat: ...",
                    "author": "John Doe <john@example.com>",
                    "date": "2025-10-17T14:30:00+08:00"
                }
            }
        """
        try:
            repo = Repo(repo_path)
            commit = repo.head.commit

            # 获取当前分支（可能是 detached HEAD）
            current_branch = None
            try:
                current_branch = repo.active_branch.name
            except TypeError:
                # detached HEAD 状态
                logger.debug("当前处于 detached HEAD 状态")

            # 获取远程 URL（移除认证信息）
            origin_url = repo.remote('origin').url
            repo_url = self._remove_auth_from_url(origin_url)

            return {
                "repo_url": repo_url,
                "repo_path": repo_path,
                "current_branch": current_branch,
                "current_commit": {
                    "hash": commit.hexsha,
                    "short_hash": commit.hexsha[:7],
                    "message": commit.message.strip(),
                    "author": f"{commit.author.name} <{commit.author.email}>",
                    "date": commit.committed_datetime.isoformat()
                }
            }

        except Exception as e:
            logger.error(f"获取仓库信息失败: {e}")
            return {}

    def get_diff_files(
        self,
        repo_path: str,
        version1: str,
        version2: str = "HEAD"
    ) -> Tuple[List[str], Dict[str, FileDiffInfo]]:
        """
        获取两个版本间的差异文件

        Args:
            repo_path: 仓库路径
            version1: 起始版本（branch/tag/commit）
            version2: 结束版本（默认 HEAD）

        Returns:
            (file_list, diff_info_dict) 元组
            - file_list: 差异文件路径列表（绝对路径）
            - diff_info_dict: 文件路径到 FileDiffInfo 的映射
        """
        try:
            helper = GitFileHelper(repo_path)

            # 获取差异文件列表（相对路径）
            rel_files = helper.get_diff_files(version1, version2)

            # 转换为绝对路径
            abs_files = [os.path.join(repo_path, f) for f in rel_files]

            # 获取 diff 信息
            diff_info_dict_rel = helper.get_diff_between_commits(version1, version2)

            # 转换为绝对路径的映射
            diff_info_dict_abs = {
                os.path.join(repo_path, rel_path): diff_info
                for rel_path, diff_info in diff_info_dict_rel.items()
            }

            logger.info(f"获取差异文件: {len(abs_files)} 个文件")
            return abs_files, diff_info_dict_abs

        except Exception as e:
            logger.error(f"获取差异文件失败: {e}", exc_info=True)
            raise RuntimeError(f"获取差异文件失败: {e}")

    def _match_git_config(self, repo_url: str) -> Optional[GitPlatformConfig]:
        """
        根据仓库 URL 匹配 Git 平台配置

        匹配策略：
        1. 提取 URL 的 host（如 10.56.215.182 或 github.com）
        2. 在 GitPlatformManager 中查找匹配的配置
        3. 返回当前激活的配置

        Args:
            repo_url: 仓库 URL

        Returns:
            匹配的配置对象，未找到返回 None
        """
        if not self.platform_manager:
            return None

        try:
            # 解析 URL
            parsed = urlparse(repo_url)

            # 提取 host（可能是 user@host 格式的 SSH URL）
            if '@' in parsed.netloc:
                host = parsed.netloc.split('@')[-1]
            else:
                host = parsed.netloc

            # 移除端口号
            if ':' in host:
                host = host.split(':')[0]

            logger.debug(f"从 URL 提取 host: {host}")

            # 遍历所有平台的配置
            for platform in ['gitlab', 'github']:
                configs = self.platform_manager.list_configs(platform)

                for config in configs:
                    # 提取配置的 host
                    config_parsed = urlparse(config.base_url)
                    config_host = config_parsed.netloc

                    if ':' in config_host:
                        config_host = config_host.split(':')[0]

                    # 匹配 host
                    if host == config_host:
                        logger.info(f"匹配到 Git 配置: {config.name} ({config.platform})")
                        return config

            logger.warning(f"未找到匹配的 Git 配置: {host}")
            return None

        except Exception as e:
            logger.error(f"匹配 Git 配置失败: {e}")
            return None

    def _build_auth_url(
        self,
        repo_url: str,
        config: Optional[GitPlatformConfig]
    ) -> str:
        """
        构建带认证的 Git URL

        支持：
        - HTTP(S): https://oauth2:token@host/path.git (GitLab)
        - HTTP(S): https://token@host/path.git (GitHub)
        - SSH: 使用本地 SSH key（不修改 URL）

        Args:
            repo_url: 原始仓库 URL
            config: Git 平台配置（可选）

        Returns:
            带认证的 URL
        """
        if not config or not config.token:
            logger.debug("未提供配置或 token，使用原始 URL")
            return repo_url

        # SSH URL 不处理
        if repo_url.startswith('git@') or repo_url.startswith('ssh://'):
            logger.debug("SSH URL，使用本地 SSH key")
            return repo_url

        try:
            parsed = urlparse(repo_url)

            # 只处理 HTTP(S) URL
            if parsed.scheme not in ['http', 'https']:
                return repo_url

            # 构建带认证的 netloc
            if config.platform == 'gitlab':
                # GitLab 使用 oauth2:token 格式
                auth_netloc = f"oauth2:{config.token}@{parsed.netloc}"
            else:
                # GitHub 等使用 token 格式
                auth_netloc = f"{config.token}@{parsed.netloc}"

            # 重建 URL
            auth_url = urlunparse((
                parsed.scheme,
                auth_netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))

            logger.debug("已构建认证 URL")
            return auth_url

        except Exception as e:
            logger.error(f"构建认证 URL 失败: {e}")
            return repo_url

    def _remove_auth_from_url(self, url: str) -> str:
        """
        从 URL 中移除认证信息

        Args:
            url: 可能包含认证信息的 URL

        Returns:
            移除认证信息后的 URL
        """
        try:
            parsed = urlparse(url)

            # 如果 netloc 包含认证信息（user:pass@host），移除之
            if '@' in parsed.netloc:
                host = parsed.netloc.split('@')[-1]
            else:
                host = parsed.netloc

            # 重建 URL
            clean_url = urlunparse((
                parsed.scheme,
                host,
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))

            return clean_url

        except Exception:
            return url
