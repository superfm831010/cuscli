# Phase 2: 插件命令扩展设计

## 目标

修改 `autocoder/plugins/code_checker_plugin.py`，新增 `/check /git` 命令及其子命令处理。

## 命令结构设计

```
/check /git <subcommand> [options]

子命令:
  /staged                      - 检查暂存区文件
  /unstaged                    - 检查工作区修改文件
  /commit <hash>               - 检查指定 commit
  /diff <commit1> [commit2]    - 检查两个 commit 间差异

通用选项:
  /repeat <次数>               - LLM 调用次数
  /consensus <0-1>             - 共识阈值
  /workers <数量>              - 并发数
```

## 修改点

### 1. 导入新模块

在文件顶部添加：

```python
from autocoder.checker.git_helper import GitFileHelper
```

### 2. 更新命令补全

修改 `get_completions()` 方法：

```python
def get_completions(self) -> Dict[str, List[str]]:
    """
    提供静态补全
    """
    return {
        "/check": [
            "/file",
            "/folder",
            "/resume",
            "/report",
            "/config",
            "/git"  # 新增
        ],
        "/check /folder": [
            "/path", "/ext", "/ignore",
            "/workers", "/repeat", "/consensus"
        ],
        "/check /config": ["/repeat", "/consensus"],
        "/check /git": [  # 新增
            "/staged",
            "/unstaged",
            "/commit",
            "/diff"
        ],
        "/check /git /staged": [  # 新增
            "/repeat", "/consensus", "/workers"
        ],
        "/check /git /unstaged": [  # 新增
            "/repeat", "/consensus", "/workers"
        ],
        "/check /git /commit": [  # 新增
            "/repeat", "/consensus", "/workers"
        ],
        "/check /git /diff": [  # 新增
            "/repeat", "/consensus", "/workers"
        ],
    }
```

### 3. 更新命令路由

修改 `handle_check()` 方法，添加 `/git` 分支：

```python
def handle_check(self, args: str) -> None:
    """
    处理 /check 命令
    """
    args = args.strip()

    if not args:
        self._show_help()
        return

    # 解析子命令
    parts = args.split(maxsplit=1)
    subcommand = parts[0]
    sub_args = parts[1] if len(parts) > 1 else ""

    # 路由到对应的处理函数
    if subcommand == "/file":
        self._check_file(sub_args)
    elif subcommand == "/config":
        self._config_checker(sub_args)
    elif subcommand == "/folder":
        self._check_folder(sub_args)
    elif subcommand == "/resume":
        self._resume_check(sub_args)
    elif subcommand == "/report":
        self._show_report(sub_args)
    elif subcommand == "/git":  # 新增
        self._check_git(sub_args)
    else:
        print(f"❌ 未知的子命令: {subcommand}")
        self._show_help()
```

### 4. 实现 Git 命令路由

新增 `_check_git()` 方法：

```python
def _check_git(self, args: str) -> None:
    """
    处理 /check /git 命令

    Args:
        args: 子命令和参数
    """
    args = args.strip()

    if not args:
        print("❌ 请指定 git 子命令")
        print()
        print("可用子命令:")
        print("  /check /git /staged              - 检查暂存区文件")
        print("  /check /git /unstaged            - 检查工作区修改文件")
        print("  /check /git /commit <hash>       - 检查指定 commit")
        print("  /check /git /diff <c1> [c2]      - 检查两个 commit 间差异")
        return

    # 解析子命令
    parts = shlex.split(args)
    subcommand = parts[0]
    sub_args = parts[1:]

    # 路由到具体处理函数
    if subcommand == "/staged":
        self._check_git_staged(sub_args)
    elif subcommand == "/unstaged":
        self._check_git_unstaged(sub_args)
    elif subcommand == "/commit":
        self._check_git_commit(sub_args)
    elif subcommand == "/diff":
        self._check_git_diff(sub_args)
    else:
        print(f"❌ 未知的 git 子命令: {subcommand}")
```

### 5. 实现暂存区检查

新增 `_check_git_staged()` 方法：

```python
def _check_git_staged(self, args: List[str]) -> None:
    """
    检查暂存区文件（已 add 但未 commit）

    Args:
        args: 选项参数列表
    """
    print("🔍 检查暂存区文件...")
    print()

    try:
        # 初始化 GitFileHelper
        git_helper = GitFileHelper()

        # 获取暂存区文件
        files = git_helper.get_staged_files()

        if not files:
            print("📭 暂存区没有文件")
            print()
            print("💡 提示: 使用 git add <文件> 将文件添加到暂存区")
            return

        print(f"✅ 找到 {len(files)} 个暂存区文件")
        print()

        # 解析选项
        options = self._parse_git_check_options(args)

        # 执行检查（复用现有逻辑）
        self._execute_batch_check(
            files=files,
            check_type="git_staged",
            options=options
        )

    except RuntimeError as e:
        print(f"❌ {e}")
        logger.error(f"Git 暂存区检查失败: {e}", exc_info=True)
    except Exception as e:
        print(f"❌ 检查过程出错: {e}")
        logger.error(f"Git 暂存区检查失败: {e}", exc_info=True)
```

### 6. 实现工作区检查

新增 `_check_git_unstaged()` 方法：

```python
def _check_git_unstaged(self, args: List[str]) -> None:
    """
    检查工作区修改文件（已修改但未 add）

    Args:
        args: 选项参数列表
    """
    print("🔍 检查工作区修改文件...")
    print()

    try:
        git_helper = GitFileHelper()
        files = git_helper.get_unstaged_files()

        if not files:
            print("📭 工作区没有修改文件")
            print()
            print("💡 提示: 修改文件后即可检查，使用 git status 查看状态")
            return

        print(f"✅ 找到 {len(files)} 个修改文件")
        print()

        options = self._parse_git_check_options(args)

        self._execute_batch_check(
            files=files,
            check_type="git_unstaged",
            options=options
        )

    except RuntimeError as e:
        print(f"❌ {e}")
        logger.error(f"Git 工作区检查失败: {e}", exc_info=True)
    except Exception as e:
        print(f"❌ 检查过程出错: {e}")
        logger.error(f"Git 工作区检查失败: {e}", exc_info=True)
```

### 7. 实现 Commit 检查

新增 `_check_git_commit()` 方法：

```python
def _check_git_commit(self, args: List[str]) -> None:
    """
    检查指定 commit 的变更文件

    Args:
        args: [commit_hash, ...options]
    """
    if not args:
        print("❌ 请指定 commit 哈希值")
        print("用法: /check /git /commit <commit_hash> [/repeat N] [/consensus 0.8]")
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
        print(f"   日期: {commit_info['date']}")
        print(f"   信息: {commit_info['message'].splitlines()[0]}")
        print()

        # 获取变更文件
        files = git_helper.get_commit_files(commit_hash)

        if not files:
            print("📭 该 commit 没有文件变更")
            return

        print(f"✅ 找到 {len(files)} 个变更文件")
        print()

        # 准备临时文件（如果需要）
        prepared_files = self._prepare_git_files(
            files,
            git_helper,
            commit_hash
        )

        options = self._parse_git_check_options(option_args)
        options['commit_info'] = commit_info  # 传递 commit 信息用于报告

        self._execute_batch_check(
            files=prepared_files,
            check_type=f"git_commit_{commit_info['short_hash']}",
            options=options
        )

    except ValueError as e:
        print(f"❌ {e}")
    except RuntimeError as e:
        print(f"❌ {e}")
        logger.error(f"Git commit 检查失败: {e}", exc_info=True)
    except Exception as e:
        print(f"❌ 检查过程出错: {e}")
        logger.error(f"Git commit 检查失败: {e}", exc_info=True)
```

### 8. 实现 Diff 检查

新增 `_check_git_diff()` 方法：

```python
def _check_git_diff(self, args: List[str]) -> None:
    """
    检查两个 commit 之间的差异文件

    Args:
        args: [commit1, [commit2], ...options]
    """
    if not args:
        print("❌ 请指定 commit")
        print("用法: /check /git /diff <commit1> [commit2] [options]")
        print("     commit2 默认为 HEAD")
        return

    commit1 = args[0]

    # 判断第二个参数是选项还是 commit
    if len(args) > 1 and not args[1].startswith('/'):
        commit2 = args[1]
        option_args = args[2:]
    else:
        commit2 = "HEAD"
        option_args = args[1:]

    print(f"🔍 检查 diff: {commit1}...{commit2}")
    print()

    try:
        git_helper = GitFileHelper()

        # 获取差异文件
        files = git_helper.get_diff_files(commit1, commit2)

        if not files:
            print(f"📭 {commit1} 和 {commit2} 之间没有差异")
            return

        print(f"✅ 找到 {len(files)} 个差异文件")
        print()

        # 准备文件（使用 commit2 的版本）
        prepared_files = self._prepare_git_files(
            files,
            git_helper,
            commit2
        )

        options = self._parse_git_check_options(option_args)
        options['diff_info'] = f"{commit1}...{commit2}"

        self._execute_batch_check(
            files=prepared_files,
            check_type=f"git_diff_{commit1[:7]}_{commit2[:7]}",
            options=options
        )

    except ValueError as e:
        print(f"❌ {e}")
    except RuntimeError as e:
        print(f"❌ {e}")
        logger.error(f"Git diff 检查失败: {e}", exc_info=True)
    except Exception as e:
        print(f"❌ 检查过程出错: {e}")
        logger.error(f"Git diff 检查失败: {e}", exc_info=True)
```

### 9. 辅助方法：选项解析

新增 `_parse_git_check_options()` 方法：

```python
def _parse_git_check_options(self, args: List[str]) -> Dict[str, Any]:
    """
    解析 git 检查的选项参数

    Args:
        args: 参数列表

    Returns:
        选项字典 {repeat, consensus, workers}
    """
    options = {
        "repeat": None,
        "consensus": None,
        "workers": 5  # 默认并发数
    }

    i = 0
    while i < len(args):
        arg = args[i]

        if arg == "/repeat" and i + 1 < len(args):
            try:
                options["repeat"] = int(args[i + 1])
            except ValueError:
                print(f"⚠️  无效的重复次数: {args[i + 1]}")
            i += 2
        elif arg == "/consensus" and i + 1 < len(args):
            try:
                options["consensus"] = float(args[i + 1])
            except ValueError:
                print(f"⚠️  无效的共识阈值: {args[i + 1]}")
            i += 2
        elif arg == "/workers" and i + 1 < len(args):
            try:
                options["workers"] = int(args[i + 1])
            except ValueError:
                print(f"⚠️  无效的并发数: {args[i + 1]}")
            i += 2
        else:
            i += 1

    return options
```

### 10. 辅助方法：文件准备

新增 `_prepare_git_files()` 方法（详见 Phase 3）：

```python
def _prepare_git_files(
    self,
    files: List[str],
    git_helper: GitFileHelper,
    commit_hash: Optional[str] = None
) -> List[str]:
    """
    准备 git 文件供检查

    对于历史文件（commit），提取到临时目录
    对于工作区文件（staged/unstaged），直接返回路径

    Args:
        files: 文件路径列表（相对路径）
        git_helper: GitFileHelper 实例
        commit_hash: 如果指定，表示从该 commit 提取文件

    Returns:
        准备好的文件路径列表（绝对路径）
    """
    # 详细实现见 Phase 3
    pass
```

### 11. 辅助方法：批量检查执行

新增 `_execute_batch_check()` 方法：

```python
def _execute_batch_check(
    self,
    files: List[str],
    check_type: str,
    options: Dict[str, Any]
) -> None:
    """
    执行批量检查（复用现有逻辑）

    Args:
        files: 文件列表
        check_type: 检查类型（用于生成 check_id）
        options: 检查选项
    """
    workers = options.get("workers", 5)

    # 确保 checker 已初始化
    self._ensure_checker()

    # 应用 repeat/consensus 参数
    self._apply_checker_options({
        "repeat": options.get("repeat"),
        "consensus": options.get("consensus"),
    })

    # 生成 check_id
    check_id = self._create_check_id_with_prefix(check_type)
    report_dir = self._create_report_dir(check_id)

    # 启动任务日志
    from autocoder.checker.task_logger import TaskLogger
    task_logger = TaskLogger(report_dir)
    task_logger.start()

    try:
        logger.info(f"开始检查任务: {check_id}, 文件数: {len(files)}")

        print(f"📝 检查任务 ID: {check_id}")
        print(f"📄 报告目录: {report_dir}")
        print()

        # 导入进度显示
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
                results.append(result)

                # 更新进度
                progress_display.update_file_progress(completed_files=idx)

        # 生成报告
        for result in results:
            self.report_generator.generate_file_report(result, report_dir)

        self.report_generator.generate_summary_report(results, report_dir)

        # 显示汇总
        self._show_batch_summary(results, report_dir)

    finally:
        task_logger.stop()
```

### 12. 更新帮助信息

修改 `_show_help()` 方法：

```python
def _show_help(self) -> None:
    """显示帮助信息"""
    help_text = """
📋 代码检查命令帮助

使用方法:
  /check /file <filepath>              - 检查单个文件
  /check /config [options]             - 设置默认参数
  /check /folder [options]             - 检查目录
  /check /resume [check_id]            - 恢复中断的检查
  /check /report [check_id]            - 查看检查报告

  /check /git /staged [options]        - 检查暂存区文件 (NEW)
  /check /git /unstaged [options]      - 检查工作区修改 (NEW)
  /check /git /commit <hash> [options] - 检查指定 commit (NEW)
  /check /git /diff <c1> [c2] [opts]   - 检查 commit 差异 (NEW)

通用选项:
  /repeat <次数>                       - LLM 调用次数（默认: 1）
  /consensus <0-1>                     - 共识阈值（默认: 1.0）
  /workers <数量>                      - 并发数（默认: 5）

示例:
  /check /file autocoder/auto_coder.py
  /check /folder /path src /ext .py
  /check /git /staged
  /check /git /commit abc1234 /repeat 3
  /check /git /diff main dev
    """
    print(help_text)
```

## 实施步骤

1. ✅ 在插件文件顶部导入 `GitFileHelper`
2. ✅ 更新 `get_completions()` 添加 git 命令补全
3. ✅ 修改 `handle_check()` 添加 git 路由
4. ✅ 实现 `_check_git()` 方法（git 命令路由）
5. ✅ 实现 `_check_git_staged()` 方法
6. ✅ 实现 `_check_git_unstaged()` 方法
7. ✅ 实现 `_check_git_commit()` 方法
8. ✅ 实现 `_check_git_diff()` 方法
9. ✅ 实现辅助方法（选项解析、文件准备、批量检查）
10. ✅ 更新 `_show_help()` 方法
11. ✅ 测试所有子命令

## 测试要点

1. **命令解析**: 确保各种参数组合都能正确解析
2. **错误提示**: 参数缺失、commit 不存在等情况的友好提示
3. **进度显示**: 确保进度条正常工作
4. **报告生成**: 验证报告包含正确的 git 信息
5. **跨平台**: 在 Windows 和 Linux 上测试

## 注意事项

1. **复用现有代码**: 尽可能复用 `_check_folder()` 的逻辑
2. **错误处理**: 捕获所有可能的异常，提供友好提示
3. **日志记录**: 记录关键操作和错误
4. **性能**: 利用并发检查提高效率
5. **用户体验**: 清晰的进度显示和结果反馈
