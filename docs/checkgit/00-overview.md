# Git提交代码检查功能 - 总体设计概述

## 功能目标

为 CodeChecker 插件新增 Git 集成功能，支持对 Git 提交相关的文件进行代码规范检查，提升开发流程中的代码质量把控。

## 核心价值

1. **Pre-commit 检查**：在提交前检查暂存区文件，及早发现问题
2. **工作区检查**：检查当前修改但未暂存的文件
3. **历史审查**：检查历史 commit 中的代码，用于代码审查或技术债务排查
4. **差异对比**：检查两个版本间的差异文件

## 设计原则

1. **复用现有架构**：最大化复用现有 checker 模块（core、file_processor、report_generator 等）
2. **无侵入式**：不修改核心检查逻辑，仅扩展文件来源
3. **跨平台兼容**：确保 Windows 和 Linux 都能正常运行
4. **用户友好**：清晰的命令结构、进度提示、错误处理

## 命令设计

### 命令结构

```
/check /git <subcommand> [options]
```

### 子命令

| 子命令 | 说明 | 示例 |
|--------|------|------|
| `/staged` | 检查暂存区文件（已 add 未 commit） | `/check /git /staged` |
| `/unstaged` | 检查工作区修改文件（未 add） | `/check /git /unstaged` |
| `/commit <hash>` | 检查指定 commit 的变更文件 | `/check /git /commit abc1234` |
| `/diff <commit1> [commit2]` | 检查两个 commit 间的差异文件 | `/check /git /diff main dev` |

### 通用选项

- `/repeat <次数>` - LLM 调用重复次数（默认：1）
- `/consensus <0-1>` - 共识阈值（默认：1.0）
- `/workers <数量>` - 并发检查数（默认：5）

## 架构设计

### 模块划分

```
autocoder/checker/
├── git_helper.py          # 新增：Git 文件获取辅助模块
├── core.py                # 现有：检查核心逻辑（无需修改）
├── file_processor.py      # 现有：文件处理（无需修改）
└── ...

autocoder/plugins/
└── code_checker_plugin.py # 修改：新增 git 命令处理
```

### 数据流

```
用户命令
    ↓
code_checker_plugin.py (命令解析)
    ↓
git_helper.py (获取文件列表)
    ↓
临时文件处理（如需要）
    ↓
core.CodeChecker (执行检查)
    ↓
report_generator.py (生成报告)
    ↓
用户反馈
```

## 技术方案

### 文件来源分类

1. **工作区文件**（/unstaged）
   - 文件在磁盘上存在
   - 直接使用文件路径检查

2. **暂存区文件**（/staged）
   - 已 add 的文件在磁盘上存在
   - 直接使用文件路径检查

3. **历史文件**（/commit, /diff）
   - 文件可能只存在于 Git 对象中
   - 需要提取到临时文件

### Git API 使用（基于 GitPython）

```python
from git import Repo

repo = Repo(repo_path)

# 暂存区
diff_index = repo.index.diff("HEAD")
staged_files = [item.a_path for item in diff_index]

# 工作区
diff_working = repo.index.diff(None)
unstaged_files = [item.a_path for item in diff_working]

# Commit
commit = repo.commit(commit_hash)
if commit.parents:
    diff = commit.parents[0].diff(commit)
    changed_files = [item.a_path or item.b_path for item in diff]
```

## 实施路线图

### Phase 1: Git 文件获取模块（1天）
- 创建 `git_helper.py`
- 实现文件列表获取函数
- 编写单元测试
- **文档**: `01-git-helper.md`

### Phase 2: 插件命令扩展（1天）
- 修改 `code_checker_plugin.py`
- 添加命令解析和路由
- 实现 git 子命令处理函数
- **文档**: `02-plugin-extension.md`

### Phase 3: 特殊文件处理（0.5天）
- 实现临时文件创建和清理
- 处理边界情况（删除文件、二进制文件等）
- **文档**: `03-file-handling.md`

### Phase 4: 报告增强（0.5天）
- 在报告中添加 Git 信息
- 显示 commit 详情
- **文档**: `04-report-enhancement.md`

### Phase 5: 测试和文档（1天）
- 集成测试
- 用户文档更新
- 开发记录更新
- **文档**: `05-testing-plan.md`

**总计**: 约 4 天完成

## 关键风险和缓解措施

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 不在 Git 仓库中执行 | 功能不可用 | 检测仓库状态，友好提示 |
| 历史文件编码问题 | 检查失败 | 尝试多种编码，失败时跳过 |
| 临时文件清理失败 | 磁盘空间占用 | 使用 context manager 确保清理 |
| Windows 路径兼容 | 跨平台问题 | 统一使用 `os.path` 和 `pathlib` |
| 大型 commit 处理 | 性能问题 | 复用现有的并发和分块机制 |

## 成功标准

- ✅ 所有子命令都能正常工作
- ✅ 在 Windows 和 Linux 上测试通过
- ✅ 能正确处理边界情况（空 commit、删除文件等）
- ✅ 错误提示清晰友好
- ✅ 性能与现有 `/check /folder` 相当
- ✅ 文档完整（使用说明 + 开发记录）

## 后续扩展可能

1. **Pre-commit Hook 集成**：自动化在 commit 前检查
2. **CI/CD 集成**：支持在 PR 中自动检查
3. **增量检查**：只检查相对于 base branch 的变更
4. **检查结果缓存**：避免重复检查相同文件
5. **自动修复建议**：基于检查结果生成 patch

## 参考文档

- 现有 Checker 系统：`docs/code_checker_usage.md`
- Git 工具模块：`autocoder/common/git_utils.py`
- GitPython 文档：https://gitpython.readthedocs.io/
