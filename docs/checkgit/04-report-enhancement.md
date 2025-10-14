# Phase 4: 报告增强设计

## 目标

在检查报告中添加 Git 相关信息，让用户了解检查的上下文。

## 报告类型扩展

### 1. Git 暂存区报告

**元数据**:
```json
{
  "check_type": "git_staged",
  "git_info": {
    "type": "staged",
    "branch": "main",
    "files_count": 5
  }
}
```

**Markdown 报告头部**:
```markdown
# 代码检查报告 - Git 暂存区

**检查类型**: Git 暂存区文件
**当前分支**: main
**文件数量**: 5 个
**检查时间**: 2025-01-10 14:30:22

---
```

### 2. Git 工作区报告

**元数据**:
```json
{
  "check_type": "git_unstaged",
  "git_info": {
    "type": "unstaged",
    "branch": "main",
    "files_count": 3
  }
}
```

**Markdown 报告头部**:
```markdown
# 代码检查报告 - Git 工作区

**检查类型**: Git 工作区修改文件
**当前分支**: main
**文件数量**: 3 个
**检查时间**: 2025-01-10 14:30:22

---
```

### 3. Git Commit 报告

**元数据**:
```json
{
  "check_type": "git_commit",
  "git_info": {
    "type": "commit",
    "commit_hash": "abc1234567890def",
    "short_hash": "abc1234",
    "message": "feat: add new feature",
    "author": "John Doe <john@example.com>",
    "date": "2025-01-10T10:30:00+08:00",
    "files_changed": 5
  }
}
```

**Markdown 报告头部**:
```markdown
# 代码检查报告 - Git Commit

**检查类型**: Git Commit 检查
**Commit**: `abc1234` - feat: add new feature
**作者**: John Doe <john@example.com>
**日期**: 2025-01-10 10:30:00
**变更文件**: 5 个
**检查时间**: 2025-01-10 14:30:22

---
```

### 4. Git Diff 报告

**元数据**:
```json
{
  "check_type": "git_diff",
  "git_info": {
    "type": "diff",
    "commit1": "abc1234",
    "commit2": "def5678",
    "files_changed": 8
  }
}
```

**Markdown 报告头部**:
```markdown
# 代码检查报告 - Git Diff

**检查类型**: Git Diff 检查
**对比范围**: `abc1234`...`def5678`
**差异文件**: 8 个
**检查时间**: 2025-01-10 14:30:22

---
```

## 实现方案

### 方案一：扩展 ReportGenerator（推荐）

修改 `autocoder/checker/report_generator.py`，添加 Git 信息支持。

#### 1. 添加 Git 信息数据类

```python
# 在 types.py 中添加
from typing import Optional
from pydantic import BaseModel

class GitInfo(BaseModel):
    """Git 检查信息"""
    type: str  # staged, unstaged, commit, diff
    branch: Optional[str] = None
    commit_hash: Optional[str] = None
    short_hash: Optional[str] = None
    message: Optional[str] = None
    author: Optional[str] = None
    date: Optional[str] = None
    commit1: Optional[str] = None
    commit2: Optional[str] = None
    files_changed: int = 0
```

#### 2. 修改 BatchCheckResult

```python
class BatchCheckResult(BaseModel):
    """批量检查结果"""
    check_id: str
    start_time: str
    end_time: str
    total_files: int
    checked_files: int
    total_issues: int
    total_errors: int
    total_warnings: int
    total_infos: int
    file_results: List[FileCheckResult]
    git_info: Optional[GitInfo] = None  # 新增
```

#### 3. 修改报告生成方法

```python
# report_generator.py

def generate_summary_report(
    self,
    results: List[FileCheckResult],
    report_dir: str,
    git_info: Optional[GitInfo] = None  # 新增参数
) -> None:
    """
    生成汇总报告

    Args:
        results: 检查结果列表
        report_dir: 报告目录
        git_info: Git 检查信息（可选）
    """
    # 生成 Markdown
    md_content = self._generate_markdown_summary(results, git_info)
    md_path = os.path.join(report_dir, "summary.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)

    # 生成 JSON
    json_data = self._generate_json_summary(results, git_info)
    json_path = os.path.join(report_dir, "summary.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)

def _generate_markdown_summary(
    self,
    results: List[FileCheckResult],
    git_info: Optional[GitInfo] = None
) -> str:
    """生成 Markdown 汇总报告"""
    lines = []

    # 标题
    if git_info:
        title = self._get_git_report_title(git_info)
        lines.append(f"# {title}")
    else:
        lines.append("# 代码检查报告")

    lines.append("")

    # Git 信息部分
    if git_info:
        lines.extend(self._format_git_info_markdown(git_info))
        lines.append("")
        lines.append("---")
        lines.append("")

    # 统计信息
    total_files = len(results)
    total_issues = sum(len(r.issues) for r in results)
    total_errors = sum(r.error_count for r in results)
    total_warnings = sum(r.warning_count for r in results)
    total_infos = sum(r.info_count for r in results)

    lines.append("## 检查统计")
    lines.append("")
    lines.append(f"- **检查文件**: {total_files} 个")
    lines.append(f"- **总问题数**: {total_issues} 个")
    lines.append(f"  - ❌ **错误**: {total_errors} 个")
    lines.append(f"  - ⚠️ **警告**: {total_warnings} 个")
    lines.append(f"  - ℹ️ **提示**: {total_infos} 个")
    lines.append("")

    # 问题详情
    # ... 其余内容不变 ...

    return "\n".join(lines)

def _get_git_report_title(self, git_info: GitInfo) -> str:
    """根据 Git 类型生成报告标题"""
    if git_info.type == "staged":
        return "代码检查报告 - Git 暂存区"
    elif git_info.type == "unstaged":
        return "代码检查报告 - Git 工作区"
    elif git_info.type == "commit":
        return "代码检查报告 - Git Commit"
    elif git_info.type == "diff":
        return "代码检查报告 - Git Diff"
    else:
        return "代码检查报告"

def _format_git_info_markdown(self, git_info: GitInfo) -> List[str]:
    """格式化 Git 信息为 Markdown"""
    lines = []

    if git_info.type == "staged":
        lines.append("**检查类型**: Git 暂存区文件")
        if git_info.branch:
            lines.append(f"**当前分支**: {git_info.branch}")
        lines.append(f"**文件数量**: {git_info.files_changed} 个")

    elif git_info.type == "unstaged":
        lines.append("**检查类型**: Git 工作区修改文件")
        if git_info.branch:
            lines.append(f"**当前分支**: {git_info.branch}")
        lines.append(f"**文件数量**: {git_info.files_changed} 个")

    elif git_info.type == "commit":
        lines.append("**检查类型**: Git Commit 检查")
        lines.append(f"**Commit**: `{git_info.short_hash}` - {git_info.message}")
        if git_info.author:
            lines.append(f"**作者**: {git_info.author}")
        if git_info.date:
            lines.append(f"**日期**: {git_info.date}")
        lines.append(f"**变更文件**: {git_info.files_changed} 个")

    elif git_info.type == "diff":
        lines.append("**检查类型**: Git Diff 检查")
        lines.append(f"**对比范围**: `{git_info.commit1}`...`{git_info.commit2}`")
        lines.append(f"**差异文件**: {git_info.files_changed} 个")

    return lines
```

### 方案二：在插件中生成 Git 元数据文件（备选）

如果不想修改 `report_generator.py`，可以在报告目录生成单独的 Git 信息文件。

```python
# 在 code_checker_plugin.py 中
def _save_git_metadata(
    self,
    report_dir: str,
    git_info: Dict[str, Any]
) -> None:
    """保存 Git 元数据到报告目录"""
    metadata_path = os.path.join(report_dir, "git_metadata.json")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(git_info, f, indent=2, ensure_ascii=False)

    # 同时生成 Markdown 文件
    md_path = os.path.join(report_dir, "git_info.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(self._format_git_info_markdown(git_info))
```

## 插件中的调用

### 在 `_execute_batch_check()` 中传递 Git 信息

```python
def _execute_batch_check(
    self,
    files: List[str],
    check_type: str,
    options: Dict[str, Any],
    temp_manager: Optional[TempFileManager] = None
) -> None:
    """执行批量检查"""
    # ... 前面代码不变 ...

    # 提取 Git 信息
    git_info = None
    if 'commit_info' in options:
        # Commit 检查
        commit_info = options['commit_info']
        git_info = GitInfo(
            type="commit",
            commit_hash=commit_info['hash'],
            short_hash=commit_info['short_hash'],
            message=commit_info['message'],
            author=commit_info['author'],
            date=commit_info['date'],
            files_changed=len(files)
        )
    elif 'diff_info' in options:
        # Diff 检查
        diff_parts = options['diff_info'].split('...')
        git_info = GitInfo(
            type="diff",
            commit1=diff_parts[0],
            commit2=diff_parts[1] if len(diff_parts) > 1 else "HEAD",
            files_changed=len(files)
        )
    elif check_type == "git_staged":
        # 暂存区检查
        git_helper = GitFileHelper()
        branch = git_helper.repo.active_branch.name
        git_info = GitInfo(
            type="staged",
            branch=branch,
            files_changed=len(files)
        )
    elif check_type == "git_unstaged":
        # 工作区检查
        git_helper = GitFileHelper()
        branch = git_helper.repo.active_branch.name
        git_info = GitInfo(
            type="unstaged",
            branch=branch,
            files_changed=len(files)
        )

    # ... 执行检查 ...

    # 生成报告时传入 git_info
    self.report_generator.generate_summary_report(
        results,
        report_dir,
        git_info=git_info  # 传递 Git 信息
    )

    # ... 后续代码 ...
```

## 控制台输出增强

### 在检查开始时显示 Git 信息

```python
def _check_git_commit(self, args: List[str]) -> None:
    """检查指定 commit"""
    # ... 前面代码 ...

    # 显示 commit 信息（更丰富）
    commit_info = git_helper.get_commit_info(commit_hash)

    print("=" * 60)
    print(f"📝 Commit 信息")
    print("=" * 60)
    print(f"  哈希: {commit_info['short_hash']} ({commit_info['hash'][:16]}...)")
    print(f"  作者: {commit_info['author']}")
    print(f"  日期: {commit_info['date']}")
    print(f"  信息: {commit_info['message'].splitlines()[0]}")
    print(f"  变更: {commit_info['files_changed']} 个文件")
    print("=" * 60)
    print()

    # ... 后续代码 ...
```

## 实施步骤

1. ✅ 在 `types.py` 添加 `GitInfo` 数据类
2. ✅ 修改 `BatchCheckResult` 添加 `git_info` 字段
3. ✅ 修改 `report_generator.py`:
   - 更新 `generate_summary_report()` 签名
   - 实现 `_format_git_info_markdown()`
   - 实现 `_get_git_report_title()`
4. ✅ 修改 `code_checker_plugin.py`:
   - 在 `_execute_batch_check()` 中构造 `GitInfo`
   - 传递给 `generate_summary_report()`
5. ✅ 增强控制台输出
6. ✅ 测试各种 Git 检查类型的报告

## 报告示例

### Git Commit 报告示例

```markdown
# 代码检查报告 - Git Commit

**检查类型**: Git Commit 检查
**Commit**: `abc1234` - feat: add new feature
**作者**: John Doe <john@example.com>
**日期**: 2025-01-10 10:30:00
**变更文件**: 5 个
**检查时间**: 2025-01-10 14:30:22

---

## 检查统计

- **检查文件**: 5 个
- **总问题数**: 12 个
  - ❌ **错误**: 3 个
  - ⚠️ **警告**: 7 个
  - ℹ️ **提示**: 2 个

## 问题最多的文件

1. src/main.py - 5 个问题
2. src/utils.py - 4 个问题
3. src/api.py - 3 个问题

## 详细报告

详细的文件检查报告请查看 `files/` 目录：
- 有问题的文件: `files/with_issues/`
- 无问题的文件: `files/no_issues/`
```

## 注意事项

1. **兼容性**: 确保非 Git 检查（`/check /file`, `/check /folder`）不受影响
2. **可选性**: Git 信息应该是可选的，不影响核心功能
3. **格式化**: 日期时间格式统一，使用 ISO 8601
4. **长度限制**: Commit message 过长时截断显示
5. **特殊字符**: 处理 Git 信息中的特殊字符（如 Markdown 语法）
