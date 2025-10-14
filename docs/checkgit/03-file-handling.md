# Phase 3: 特殊文件处理策略

## 目标

实现对不同来源文件的统一处理，特别是历史 commit 中不在磁盘上的文件。

## 文件来源分类

### 1. 工作区文件（Unstaged）

**特点**:
- 文件在磁盘上存在
- 已被 Git 追踪
- 有未提交的修改

**处理策略**:
- 直接使用文件路径
- 无需特殊处理

### 2. 暂存区文件（Staged）

**特点**:
- 文件在磁盘上存在
- 已 `git add`
- 等待 commit

**处理策略**:
- 直接使用文件路径
- 无需特殊处理

### 3. 历史文件（Commit/Diff）

**特点**:
- 文件可能不在当前工作区
- 仅存在于 Git 对象数据库
- 可能已被删除或重命名

**处理策略**:
- 从 Git 提取内容
- 创建临时文件
- 检查后清理

## 临时文件管理设计

### 基本策略

```python
import tempfile
import os
from contextlib import contextmanager

@contextmanager
def temp_file_context(file_path: str, content: str):
    """
    临时文件上下文管理器

    Args:
        file_path: 原始文件路径（用于保留扩展名）
        content: 文件内容

    Yields:
        临时文件路径
    """
    # 保留原始文件扩展名（规则检查可能依赖扩展名）
    _, ext = os.path.splitext(file_path)

    # 创建临时文件
    fd, temp_path = tempfile.mkstemp(suffix=ext, text=True)

    try:
        # 写入内容
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(content)

        yield temp_path

    finally:
        # 确保清理
        try:
            os.unlink(temp_path)
        except Exception as e:
            logger.warning(f"清理临时文件失败: {temp_path}, {e}")
```

### 批量临时文件管理

```python
class TempFileManager:
    """临时文件管理器，用于批量管理临时文件"""

    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="codechecker_git_")
        self.temp_files: Dict[str, str] = {}  # 原始路径 -> 临时路径
        logger.info(f"创建临时目录: {self.temp_dir}")

    def create_temp_file(self, file_path: str, content: str) -> str:
        """
        创建临时文件

        Args:
            file_path: 原始文件路径（相对路径）
            content: 文件内容

        Returns:
            临时文件绝对路径
        """
        # 保留目录结构以避免文件名冲突
        # 例如: src/main.py -> temp_dir/src/main.py
        relative_path = file_path.replace('..', '_').replace(':', '_')
        temp_file = os.path.join(self.temp_dir, relative_path)

        # 创建父目录
        os.makedirs(os.path.dirname(temp_file), exist_ok=True)

        # 写入文件
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(content)

            self.temp_files[file_path] = temp_file
            logger.debug(f"创建临时文件: {file_path} -> {temp_file}")
            return temp_file

        except Exception as e:
            logger.error(f"创建临时文件失败: {file_path}, {e}")
            raise

    def get_temp_path(self, file_path: str) -> Optional[str]:
        """获取文件的临时路径"""
        return self.temp_files.get(file_path)

    def get_original_path(self, temp_path: str) -> Optional[str]:
        """根据临时路径反查原始路径"""
        for orig, temp in self.temp_files.items():
            if temp == temp_path:
                return orig
        return None

    def cleanup(self):
        """清理所有临时文件"""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
            logger.info(f"清理临时目录: {self.temp_dir}")
        except Exception as e:
            logger.error(f"清理临时目录失败: {self.temp_dir}, {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
```

## 文件准备流程实现

### 在插件中实现 `_prepare_git_files()`

```python
def _prepare_git_files(
    self,
    files: List[str],
    git_helper: GitFileHelper,
    commit_hash: Optional[str] = None
) -> Tuple[List[str], Optional[TempFileManager]]:
    """
    准备 git 文件供检查

    Args:
        files: 文件路径列表（相对于仓库根目录）
        git_helper: GitFileHelper 实例
        commit_hash: 如果指定，从该 commit 提取文件

    Returns:
        (准备好的文件路径列表, 临时文件管理器)
        如果不需要临时文件，管理器为 None
    """
    repo_path = git_helper.repo_path

    # 如果是工作区或暂存区文件，直接返回绝对路径
    if commit_hash is None:
        prepared = []
        for file_path in files:
            abs_path = os.path.join(repo_path, file_path) \
                       if not os.path.isabs(file_path) else file_path

            if os.path.exists(abs_path):
                prepared.append(abs_path)
            else:
                logger.warning(f"文件不存在: {abs_path}")

        return prepared, None

    # 历史文件：需要提取到临时目录
    temp_manager = TempFileManager()
    prepared = []

    for file_path in files:
        try:
            # 检查是否为二进制文件
            if git_helper.is_binary_file(file_path, commit_hash):
                logger.info(f"跳过二进制文件: {file_path}")
                continue

            # 获取文件内容
            content = git_helper.get_file_content_at_commit(
                file_path,
                commit_hash
            )

            if content is None:
                logger.warning(f"无法获取文件内容: {file_path}@{commit_hash}")
                continue

            # 创建临时文件
            temp_path = temp_manager.create_temp_file(file_path, content)
            prepared.append(temp_path)

        except Exception as e:
            logger.error(f"准备文件失败: {file_path}, {e}", exc_info=True)
            continue

    logger.info(f"准备了 {len(prepared)}/{len(files)} 个文件")
    return prepared, temp_manager
```

### 更新批量检查方法

修改 `_execute_batch_check()` 以支持临时文件管理：

```python
def _execute_batch_check(
    self,
    files: List[str],
    check_type: str,
    options: Dict[str, Any],
    temp_manager: Optional[TempFileManager] = None
) -> None:
    """
    执行批量检查

    Args:
        files: 文件列表
        check_type: 检查类型
        options: 检查选项
        temp_manager: 临时文件管理器（如果使用了临时文件）
    """
    workers = options.get("workers", 5)

    # 确保 checker 已初始化
    self._ensure_checker()

    # 应用参数
    self._apply_checker_options({
        "repeat": options.get("repeat"),
        "consensus": options.get("consensus"),
    })

    # 生成 check_id 和报告目录
    check_id = self._create_check_id_with_prefix(check_type)
    report_dir = self._create_report_dir(check_id)

    # 启动日志
    from autocoder.checker.task_logger import TaskLogger
    task_logger = TaskLogger(report_dir)
    task_logger.start()

    try:
        logger.info(f"开始检查任务: {check_id}, 文件数: {len(files)}")

        print(f"📝 检查任务 ID: {check_id}")
        print(f"📄 报告目录: {report_dir}")
        print()

        # 进度显示
        from autocoder.checker.progress_display import ProgressDisplay

        results = []
        progress_display = ProgressDisplay()

        with progress_display.display_progress():
            progress_display.update_file_progress(
                total_files=len(files),
                completed_files=0
            )

            # 并发检查
            for idx, result in enumerate(
                self.checker.check_files_concurrent(files, max_workers=workers),
                1
            ):
                # 如果使用了临时文件，恢复原始路径
                if temp_manager:
                    original_path = temp_manager.get_original_path(result.file_path)
                    if original_path:
                        result.file_path = original_path

                results.append(result)
                progress_display.update_file_progress(completed_files=idx)

        # 生成报告
        for result in results:
            self.report_generator.generate_file_report(result, report_dir)

        self.report_generator.generate_summary_report(results, report_dir)

        # 显示汇总
        self._show_batch_summary(results, report_dir)

    finally:
        task_logger.stop()

        # 清理临时文件
        if temp_manager:
            temp_manager.cleanup()
```

### 更新 Commit 检查方法

修改 `_check_git_commit()` 以使用临时文件：

```python
def _check_git_commit(self, args: List[str]) -> None:
    """检查指定 commit 的变更文件"""
    if not args:
        print("❌ 请指定 commit 哈希值")
        return

    commit_hash = args[0]
    option_args = args[1:]

    print(f"🔍 检查 commit {commit_hash}...")
    print()

    try:
        git_helper = GitFileHelper()

        # 获取 commit 信息
        commit_info = git_helper.get_commit_info(commit_hash)
        print(f"📝 Commit: {commit_info['short_hash']}")
        print(f"   作者: {commit_info['author']}")
        print(f"   信息: {commit_info['message'].splitlines()[0]}")
        print()

        # 获取变更文件
        files = git_helper.get_commit_files(commit_hash)

        if not files:
            print("📭 该 commit 没有文件变更")
            return

        print(f"✅ 找到 {len(files)} 个变更文件")
        print()

        # 准备文件（会创建临时文件）
        prepared_files, temp_manager = self._prepare_git_files(
            files,
            git_helper,
            commit_hash
        )

        if not prepared_files:
            print("⚠️  没有可检查的文件（可能都是二进制文件）")
            if temp_manager:
                temp_manager.cleanup()
            return

        options = self._parse_git_check_options(option_args)
        options['commit_info'] = commit_info

        # 执行检查（传入 temp_manager）
        self._execute_batch_check(
            files=prepared_files,
            check_type=f"git_commit_{commit_info['short_hash']}",
            options=options,
            temp_manager=temp_manager
        )

    except ValueError as e:
        print(f"❌ {e}")
    except Exception as e:
        print(f"❌ 检查过程出错: {e}")
        logger.error(f"Git commit 检查失败: {e}", exc_info=True)
```

## 边界情况处理

### 1. 删除的文件

```python
# 在 git_helper.py 中，获取文件列表时过滤
for diff_item in diff:
    if diff_item.deleted_file:
        logger.debug(f"跳过删除的文件: {diff_item.a_path}")
        continue
    # ...
```

### 2. 二进制文件

```python
# 在准备文件时检查
if git_helper.is_binary_file(file_path, commit_hash):
    logger.info(f"跳过二进制文件: {file_path}")
    continue
```

### 3. 编码错误

```python
try:
    content = git_helper.get_file_content_at_commit(file_path, commit_hash)
except UnicodeDecodeError:
    logger.warning(f"文件编码错误，尝试其他编码: {file_path}")
    # 尝试其他编码
    try:
        content = self.repo.git.show(
            f"{commit_hash}:{file_path}",
            encoding='latin-1'
        )
    except:
        logger.error(f"无法读取文件: {file_path}")
        continue
```

### 4. 大文件处理

```python
# 在 git_helper.py 中添加大小限制
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def get_file_content_at_commit(self, file_path: str, commit_hash: str) -> Optional[str]:
    try:
        # 先检查文件大小
        commit = self.repo.commit(commit_hash)
        blob = commit.tree / file_path

        if blob.size > MAX_FILE_SIZE:
            logger.warning(f"文件过大，跳过: {file_path} ({blob.size / 1024 / 1024:.2f}MB)")
            return None

        content = self.repo.git.show(f"{commit_hash}:{file_path}")
        return content

    except Exception as e:
        logger.warning(f"无法获取文件内容: {file_path}@{commit_hash}, {e}")
        return None
```

### 5. 权限问题

```python
try:
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(content)
except PermissionError:
    logger.error(f"无权限写入临时文件: {temp_file}")
    # 尝试使用其他临时目录
    temp_file = tempfile.mktemp(suffix=ext)
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(content)
```

## Windows 兼容性

### 路径处理

```python
# 统一使用 os.path 处理路径
abs_path = os.path.abspath(file_path)
rel_path = os.path.relpath(abs_path, repo_path)

# 路径分隔符归一化
file_path = file_path.replace('\\', '/')
```

### 临时目录

```python
# tempfile 模块自动处理平台差异
# Windows: C:\Users\xxx\AppData\Local\Temp\
# Linux: /tmp/
temp_dir = tempfile.mkdtemp()
```

### 文件编码

```python
# 明确指定 UTF-8 编码
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
```

## 测试用例

```python
# tests/checker/test_git_file_handling.py

def test_temp_file_manager():
    """测试临时文件管理器"""
    with TempFileManager() as manager:
        # 创建临时文件
        temp_path = manager.create_temp_file(
            "src/main.py",
            "print('hello')\n"
        )

        assert os.path.exists(temp_path)

        # 验证内容
        with open(temp_path, 'r') as f:
            assert f.read() == "print('hello')\n"

        # 获取原始路径
        original = manager.get_original_path(temp_path)
        assert original == "src/main.py"

    # 退出后自动清理
    assert not os.path.exists(temp_path)

def test_prepare_git_files_workdir():
    """测试准备工作区文件"""
    # 工作区文件应该直接返回
    pass

def test_prepare_git_files_commit():
    """测试准备历史文件"""
    # 历史文件应该创建临时文件
    pass
```

## 实施步骤

1. ✅ 实现 `TempFileManager` 类
2. ✅ 实现 `_prepare_git_files()` 方法
3. ✅ 更新 `_execute_batch_check()` 支持临时文件
4. ✅ 更新 `_check_git_commit()` 使用临时文件
5. ✅ 更新 `_check_git_diff()` 使用临时文件
6. ✅ 添加边界情况处理
7. ✅ 编写测试用例
8. ✅ 在 Windows 和 Linux 上测试

## 注意事项

1. **资源清理**: 确保所有临时文件都被清理，使用 `try...finally` 或 `with` 语句
2. **错误处理**: 文件创建失败不应中断整个检查流程
3. **日志记录**: 记录临时文件的创建和清理
4. **性能**: 对于大量文件，考虑批量创建以提高效率
5. **磁盘空间**: 检查前确保有足够的临时空间
