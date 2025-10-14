# Phase 1: Git 文件获取模块设计

## 目标

创建 `autocoder/checker/git_helper.py` 模块，提供 Git 文件信息获取的统一接口。

## 模块结构

```python
# autocoder/checker/git_helper.py

from typing import List, Optional, Dict, Tuple
from pathlib import Path
import os
import tempfile
from git import Repo, GitCommandError
from loguru import logger

class GitFileHelper:
    """Git 文件操作辅助类"""

    def __init__(self, repo_path: str = "."):
        """初始化，检测 Git 仓库"""
        pass

    def get_staged_files(self) -> List[str]:
        """获取暂存区文件列表"""
        pass

    def get_unstaged_files(self) -> List[str]:
        """获取工作区修改文件列表"""
        pass

    def get_commit_files(self, commit_hash: str) -> List[str]:
        """获取指定 commit 的变更文件"""
        pass

    def get_diff_files(self, commit1: str, commit2: str = "HEAD") -> List[str]:
        """获取两个 commit 间的差异文件"""
        pass

    def get_file_content_at_commit(self, file_path: str, commit_hash: str) -> Optional[str]:
        """获取文件在指定 commit 时的内容"""
        pass

    def is_binary_file(self, file_path: str, commit_hash: Optional[str] = None) -> bool:
        """判断是否为二进制文件"""
        pass
```

## 详细设计

### 1. 初始化和仓库检测

```python
def __init__(self, repo_path: str = "."):
    """
    初始化 GitFileHelper

    Args:
        repo_path: Git 仓库路径，默认当前目录

    Raises:
        RuntimeError: 如果不是 Git 仓库
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
```

### 2. 暂存区文件获取

```python
def get_staged_files(self) -> List[str]:
    """
    获取暂存区文件列表（已 add 但未 commit）

    Returns:
        文件路径列表（相对于仓库根目录）

    Example:
        >>> helper = GitFileHelper()
        >>> files = helper.get_staged_files()
        >>> print(files)
        ['src/main.py', 'src/utils.py']
    """
    try:
        # 获取暂存区与 HEAD 的差异
        diff_index = self.repo.index.diff("HEAD")

        files = []
        for diff_item in diff_index:
            # 跳过删除的文件
            if diff_item.deleted_file:
                logger.debug(f"跳过删除的文件: {diff_item.a_path}")
                continue

            # 使用 b_path（变更后的路径）
            file_path = diff_item.b_path or diff_item.a_path

            # 转换为绝对路径
            abs_path = os.path.join(self.repo_path, file_path)

            # 确保文件存在
            if os.path.exists(abs_path):
                files.append(abs_path)
            else:
                logger.warning(f"文件不存在: {abs_path}")

        logger.info(f"暂存区文件: {len(files)} 个")
        return files

    except GitCommandError as e:
        logger.error(f"获取暂存区文件失败: {e}")
        raise RuntimeError(f"获取暂存区文件失败: {e}")
```

### 3. 工作区文件获取

```python
def get_unstaged_files(self) -> List[str]:
    """
    获取工作区修改文件列表（已修改但未 add）

    Returns:
        文件路径列表（绝对路径）
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
```

### 4. Commit 文件获取

```python
def get_commit_files(self, commit_hash: str) -> List[str]:
    """
    获取指定 commit 的变更文件

    Args:
        commit_hash: commit 哈希值（完整或短哈希）

    Returns:
        文件路径列表（相对路径）

    Raises:
        ValueError: commit 不存在
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

    except ValueError:
        raise ValueError(f"Commit 不存在: {commit_hash}")
    except GitCommandError as e:
        logger.error(f"获取 commit 文件失败: {e}")
        raise RuntimeError(f"获取 commit 文件失败: {e}")
```

### 5. Diff 文件获取

```python
def get_diff_files(self, commit1: str, commit2: str = "HEAD") -> List[str]:
    """
    获取两个 commit 之间的差异文件

    Args:
        commit1: 起始 commit
        commit2: 结束 commit（默认 HEAD）

    Returns:
        文件路径列表（相对路径）
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
                continue

            file_path = diff_item.b_path or diff_item.a_path
            files.append(file_path)

        logger.info(f"Diff 文件: {len(files)} 个")
        return files

    except ValueError as e:
        raise ValueError(f"Commit 不存在: {e}")
    except GitCommandError as e:
        raise RuntimeError(f"获取 diff 文件失败: {e}")
```

### 6. 历史文件内容提取

```python
def get_file_content_at_commit(
    self,
    file_path: str,
    commit_hash: str
) -> Optional[str]:
    """
    获取文件在指定 commit 时的内容

    Args:
        file_path: 文件路径（相对于仓库根目录）
        commit_hash: commit 哈希值

    Returns:
        文件内容字符串，如果失败返回 None
    """
    try:
        # 使用 git show 命令获取文件内容
        content = self.repo.git.show(f"{commit_hash}:{file_path}")
        return content

    except GitCommandError as e:
        logger.warning(f"无法获取文件内容: {file_path}@{commit_hash}, {e}")
        return None
```

### 7. 二进制文件判断

```python
def is_binary_file(
    self,
    file_path: str,
    commit_hash: Optional[str] = None
) -> bool:
    """
    判断是否为二进制文件

    Args:
        file_path: 文件路径
        commit_hash: 如果指定，检查该 commit 时的文件

    Returns:
        True 表示二进制文件
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
```

## 辅助函数

### 获取 Commit 信息

```python
def get_commit_info(self, commit_hash: str) -> Dict[str, str]:
    """
    获取 commit 详细信息

    Returns:
        {
            'hash': '完整哈希',
            'short_hash': '短哈希',
            'message': '提交信息',
            'author': '作者',
            'date': '提交日期',
            'files_changed': 变更文件数
        }
    """
    try:
        commit = self.repo.commit(commit_hash)

        files_changed = 0
        if commit.parents:
            diff = commit.parents[0].diff(commit)
            files_changed = len(list(diff))

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
```

## 测试用例设计

创建 `tests/checker/test_git_helper.py`:

```python
import pytest
import os
import tempfile
from git import Repo
from autocoder.checker.git_helper import GitFileHelper

@pytest.fixture
def temp_git_repo():
    """创建临时 Git 仓库用于测试"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 初始化仓库
        repo = Repo.init(tmpdir)

        # 配置用户信息
        repo.config_writer().set_value("user", "name", "Test User").release()
        repo.config_writer().set_value("user", "email", "test@example.com").release()

        # 创建初始文件
        test_file = os.path.join(tmpdir, "test.py")
        with open(test_file, 'w') as f:
            f.write("print('hello')\n")

        repo.index.add(['test.py'])
        repo.index.commit("Initial commit")

        yield tmpdir

def test_get_staged_files(temp_git_repo):
    """测试获取暂存区文件"""
    # 创建新文件并 add
    new_file = os.path.join(temp_git_repo, "new.py")
    with open(new_file, 'w') as f:
        f.write("print('new')\n")

    repo = Repo(temp_git_repo)
    repo.index.add(['new.py'])

    # 测试
    helper = GitFileHelper(temp_git_repo)
    files = helper.get_staged_files()

    assert len(files) == 1
    assert files[0].endswith('new.py')

def test_get_unstaged_files(temp_git_repo):
    """测试获取工作区修改文件"""
    # 修改现有文件但不 add
    test_file = os.path.join(temp_git_repo, "test.py")
    with open(test_file, 'a') as f:
        f.write("print('modified')\n")

    helper = GitFileHelper(temp_git_repo)
    files = helper.get_unstaged_files()

    assert len(files) == 1
    assert files[0].endswith('test.py')

def test_get_commit_files(temp_git_repo):
    """测试获取 commit 文件"""
    helper = GitFileHelper(temp_git_repo)
    repo = Repo(temp_git_repo)

    # 获取最后一次 commit
    last_commit = repo.head.commit.hexsha

    files = helper.get_commit_files(last_commit)
    assert len(files) == 1
    assert 'test.py' in files[0]

def test_not_git_repo():
    """测试非 Git 仓库"""
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(RuntimeError, match="不是有效的 Git 仓库"):
            GitFileHelper(tmpdir)
```

## 实施步骤

1. ✅ **创建文件**: `autocoder/checker/git_helper.py`
2. ✅ **实现类结构**: 定义 `GitFileHelper` 类
3. ✅ **实现核心方法**:
   - `get_staged_files()`
   - `get_unstaged_files()`
   - `get_commit_files()`
   - `get_diff_files()`
4. ✅ **实现辅助方法**:
   - `get_file_content_at_commit()`
   - `is_binary_file()`
   - `get_commit_info()`
5. ✅ **编写单元测试**: `tests/checker/test_git_helper.py`
6. ✅ **运行测试**: 确保所有测试通过
7. ✅ **Windows 测试**: 在 Windows 上验证路径处理

## 注意事项

1. **路径处理**: 统一使用 `os.path.join()` 和 `os.path.abspath()`
2. **编码问题**: 统一使用 UTF-8，失败时捕获异常
3. **Git 命令错误**: 捕获 `GitCommandError`，转换为友好错误信息
4. **日志记录**: 关键步骤记录 info 日志，异常记录 error 日志
5. **边界情况**: 处理空仓库、初始 commit、删除文件等特殊情况
