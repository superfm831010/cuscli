"""
Pull Request 模块工具函数
"""
import re
import os
import subprocess
from typing import Optional, Tuple
from urllib.parse import urlparse
from pathlib import Path
from loguru import logger

from .models import PlatformType, RepoInfo
from .exceptions import ValidationError


def parse_git_url(url: str) -> Tuple[Optional[PlatformType], Optional[str], Optional[str]]:
    """
    解析Git URL，提取平台类型、所有者和仓库名
    
    Returns:
        Tuple[平台类型, 所有者, 仓库名]
    """
    if not url:
        return None, None, None
    
    platform_domains = {
        'github.com': PlatformType.GITHUB,
        'gitlab.com': PlatformType.GITLAB,
        'gitee.com': PlatformType.GITEE,
        'gitcode.net': PlatformType.GITCODE
    }
    
    # SSH URL 格式: git@domain:owner/repo.git
    ssh_pattern = r'^git@([^:]+):([^/]+)/([^/]+?)(?:\.git)?/?$'
    ssh_match = re.match(ssh_pattern, url)
    
    if ssh_match:
        domain, owner, repo = ssh_match.groups()
        platform = platform_domains.get(domain)
        return platform, owner, repo
    
    # HTTPS URL 格式: https://domain/owner/repo.git
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        platform = platform_domains.get(domain)
        
        if not platform:
            return None, None, None
        
        path_parts = [p for p in parsed.path.split('/') if p]
        if len(path_parts) >= 2:
            owner = path_parts[0]
            repo = path_parts[1]
            if repo.endswith('.git'):
                repo = repo[:-4]
            return platform, owner, repo
    
    except Exception as e:
        logger.error(f"解析Git URL失败: {e}")
    
    return None, None, None


def get_repo_remote_url(repo_path: str, remote_name: str = 'origin') -> Optional[str]:
    """获取仓库的远程URL"""
    try:
        result = subprocess.run(
            ['git', 'remote', 'get-url', remote_name],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def get_default_remote_branch(repo_path: str, remote_name: str = 'origin') -> Optional[str]:
    """
    获取默认远程分支
    
    Args:
        repo_path: 仓库路径
        remote_name: 远程名称，默认为 'origin'
        
    Returns:
        默认远程分支名，如果获取失败则返回 None
    """
    try:
        # 首先尝试获取远程的 HEAD 指向的分支
        result = subprocess.run(
            ['git', 'symbolic-ref', f'refs/remotes/{remote_name}/HEAD'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        # 输出格式通常是 "refs/remotes/origin/main"，我们需要提取分支名
        head_ref = result.stdout.strip()
        if head_ref.startswith(f'refs/remotes/{remote_name}/'):
            return head_ref[len(f'refs/remotes/{remote_name}/'):]
    except subprocess.CalledProcessError:
        # 如果上面的方法失败，尝试从远程获取 HEAD 信息
        try:
            result = subprocess.run(
                ['git', 'ls-remote', '--symref', remote_name, 'HEAD'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            # 解析输出，查找类似 "ref: refs/heads/main	HEAD"
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if line.startswith('ref: refs/heads/'):
                    return line.split('refs/heads/')[-1].split('\t')[0]
        except subprocess.CalledProcessError:
            pass
    
    # 如果都失败了，检查常见的默认分支是否存在
    common_branches = ['main', 'master', 'develop']
    for branch in common_branches:
        if branch_exists(repo_path, branch, remote=True):
            return branch
    
    return None


def detect_platform_from_repo(repo_path: str) -> Optional[PlatformType]:
    """从仓库路径自动检测平台类型"""
    remote_url = get_repo_remote_url(repo_path)
    if not remote_url:
        return None
    
    platform, _, _ = parse_git_url(remote_url)
    return platform


def get_repo_info_from_path(repo_path: str) -> Optional[RepoInfo]:
    """从仓库路径获取仓库信息"""
    remote_url = get_repo_remote_url(repo_path)
    if not remote_url:
        return None
    
    platform, owner, name = parse_git_url(remote_url)
    if not all([platform, owner, name]):
        return None
    
    return RepoInfo(
        platform=platform,  # type: ignore
        owner=owner,  # type: ignore
        name=name  # type: ignore
    )


def get_current_branch(repo_path: str) -> Optional[str]:
    """获取当前分支名"""
    try:
        result = subprocess.run(
            ['git', 'branch', '--show-current'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def branch_exists(repo_path: str, branch_name: str, remote: bool = False) -> bool:
    """检查分支是否存在"""
    try:
        if remote:
            result = subprocess.run(
                ['git', 'ls-remote', '--heads', 'origin', branch_name],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return bool(result.stdout.strip())
        else:
            result = subprocess.run(
                ['git', 'show-ref', '--verify', '--quiet', f'refs/heads/{branch_name}'],
                cwd=repo_path,
                capture_output=True
            )
            return result.returncode == 0
    except subprocess.CalledProcessError:
        return False


def is_git_repo(path: str) -> bool:
    """检查路径是否为Git仓库"""
    git_dir = Path(path) / '.git'
    return git_dir.exists() or git_dir.is_file()


def push_branch_to_remote(repo_path: str, branch_name: str, remote_name: str = 'origin') -> bool:
    """
    推送分支到远程仓库
    
    Args:
        repo_path: 仓库路径
        branch_name: 分支名称
        remote_name: 远程名称，默认为 'origin'
        
    Returns:
        推送是否成功
    """
    try:
        logger.info(f"正在推送分支 '{branch_name}' 到远程仓库...")
        result = subprocess.run(
            ['git', 'push', remote_name, branch_name],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"分支 '{branch_name}' 推送成功")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"推送分支 '{branch_name}' 失败: {e.stderr}")
        return False


def ensure_branch_exists_remotely(repo_path: str, branch_name: str, remote_name: str = 'origin') -> bool:
    """
    确保分支在远程仓库中存在，如果不存在则推送
    
    Args:
        repo_path: 仓库路径
        branch_name: 分支名称
        remote_name: 远程名称，默认为 'origin'
        
    Returns:
        分支是否存在于远程仓库（推送后）
    """
    # 首先检查分支是否已经存在于远程
    if branch_exists(repo_path, branch_name, remote=True):
        logger.debug(f"分支 '{branch_name}' 已存在于远程仓库")
        return True
    
    # 检查分支是否存在于本地
    if not branch_exists(repo_path, branch_name, remote=False):
        logger.error(f"分支 '{branch_name}' 在本地也不存在")
        return False
    
    # 推送分支到远程
    return push_branch_to_remote(repo_path, branch_name, remote_name)


def is_main_branch(branch_name: str) -> bool:
    """
    检查是否为主分支
    
    Args:
        branch_name: 分支名称
        
    Returns:
        是否为主分支
    """
    main_branches = ['main', 'master', 'develop', 'dev']
    return branch_name.lower() in main_branches


def create_and_checkout_branch(repo_path: str, branch_name: str) -> bool:
    """
    创建并切换到新分支
    
    Args:
        repo_path: 仓库路径
        branch_name: 新分支名称
        
    Returns:
        操作是否成功
    """
    try:
        logger.info(f"正在创建并切换到新分支: {branch_name}")
        result = subprocess.run(
            ['git', 'checkout', '-b', branch_name],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"成功创建并切换到分支: {branch_name}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"创建分支 '{branch_name}' 失败: {e.stderr}")
        return False


def generate_auto_branch_name() -> str:
    """
    生成自动分支名称，格式为 ac-<yyyyMMdd-HH-mm-ss>
    
    Returns:
        分支名称
    """
    import datetime
    now = datetime.datetime.now()
    return f"ac-{now.strftime('%Y%m%d-%H-%M-%S')}"


def validate_repo_path(repo_path: str) -> str:
    """验证并规范化仓库路径"""
    if not repo_path:
        raise ValidationError("仓库路径不能为空")
    
    path = Path(repo_path).resolve()
    
    if not path.exists():
        raise ValidationError(f"仓库路径不存在: {path}")
    
    if not path.is_dir():
        raise ValidationError(f"仓库路径不是目录: {path}")
    
    if not is_git_repo(str(path)):
        raise ValidationError(f"路径不是Git仓库: {path}")
    
    return str(path)


def has_uncommitted_changes(repo_path: str) -> bool:
    """检查是否有未提交的更改"""
    try:
        # 检查工作区是否有未暂存的更改
        result = subprocess.run(
            ['git', 'diff', '--quiet'],
            cwd=repo_path,
            capture_output=True
        )
        has_unstaged = result.returncode != 0
        
        # 检查暂存区是否有未提交的更改
        result = subprocess.run(
            ['git', 'diff', '--cached', '--quiet'],
            cwd=repo_path,
            capture_output=True
        )
        has_staged = result.returncode != 0
        
        return has_unstaged or has_staged
    except subprocess.CalledProcessError:
        return False


def get_uncommitted_files(repo_path: str) -> list:
    """获取未提交的文件列表"""
    try:
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        lines = result.stdout.strip().split('\n')
        return [line.strip() for line in lines if line.strip()]
    except subprocess.CalledProcessError:
        return []


def auto_commit_changes(repo_path: str, commit_message: str = None) -> bool:
    """自动提交所有更改"""
    try:
        # 检查是否有更改
        if not has_uncommitted_changes(repo_path):
            logger.info("没有需要提交的更改")
            return True
        
        # 获取未提交的文件列表用于日志
        uncommitted_files = get_uncommitted_files(repo_path)
        logger.info(f"发现 {len(uncommitted_files)} 个未提交的更改")
        
        # 添加所有更改到暂存区
        logger.info("正在添加所有更改到暂存区...")
        subprocess.run(
            ['git', 'add', '.'],
            cwd=repo_path,
            check=True
        )
        
        # 生成提交消息
        if not commit_message:
            current_branch = get_current_branch(repo_path)
            if current_branch and current_branch.startswith('ac-'):
                commit_message = f"Auto-commit changes for PR from {current_branch}"
            else:
                commit_message = "Auto-commit changes for PR creation"
        
        # 提交更改
        logger.info(f"正在提交更改: {commit_message}")
        subprocess.run(
            ['git', 'commit', '-m', commit_message],
            cwd=repo_path,
            check=True
        )
        
        logger.info("✓ 成功提交所有更改")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"自动提交失败: {e}")
        return False


def ensure_branch_has_commits(repo_path: str, branch_name: str, auto_commit: bool = True) -> bool:
    """确保分支有提交，如果没有则自动提交更改"""
    try:
        # 检查分支是否有提交（相对于目标分支的差异）
        result = subprocess.run(
            ['git', 'rev-list', '--count', f'origin/main..{branch_name}'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        commit_count = int(result.stdout.strip())
        
        if commit_count > 0:
            logger.info(f"分支 '{branch_name}' 已有 {commit_count} 个提交")
            return True
        
        # 如果没有提交，检查是否有未提交的更改
        if has_uncommitted_changes(repo_path):
            if auto_commit:
                logger.info(f"分支 '{branch_name}' 没有提交但有未提交的更改，正在自动提交...")
                return auto_commit_changes(repo_path)
            else:
                logger.warning(f"分支 '{branch_name}' 没有提交且有未提交的更改，但未启用自动提交")
                return False
        else:
            logger.warning(f"分支 '{branch_name}' 没有提交也没有更改")
            return False
            
    except subprocess.CalledProcessError as e:
        logger.error(f"检查分支提交状态失败: {e}")
        # 如果检查失败，尝试自动提交（如果有更改的话）
        if auto_commit and has_uncommitted_changes(repo_path):
            return auto_commit_changes(repo_path)
        return False


def build_pr_url(platform: PlatformType, repo_info: RepoInfo, pr_number: int) -> str:
    """构建PR的Web URL"""
    base_urls = {
        PlatformType.GITHUB: "https://github.com",
        PlatformType.GITLAB: "https://gitlab.com",
        PlatformType.GITEE: "https://gitee.com",
        PlatformType.GITCODE: "https://gitcode.net"
    }
    
    base_url = base_urls.get(platform)
    if not base_url:
        return ""
    
    if platform == PlatformType.GITLAB or platform == PlatformType.GITCODE:
        return f"{base_url}/{repo_info.full_name}/-/merge_requests/{pr_number}"
    else:
        return f"{base_url}/{repo_info.full_name}/pull/{pr_number}"
