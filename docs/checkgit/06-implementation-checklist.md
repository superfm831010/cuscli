# Phase 6: 实施清单

## 总体进度跟踪

- [ ] Phase 1: Git 文件获取模块
- [ ] Phase 2: 插件命令扩展
- [ ] Phase 3: 特殊文件处理
- [ ] Phase 4: 报告增强
- [ ] Phase 5: 测试和文档

## Phase 1: Git 文件获取模块 (预计 1 天)

### 1.1 创建基础文件
- [ ] 创建 `autocoder/checker/git_helper.py`
- [ ] 导入必要的依赖（GitPython, loguru, typing 等）
- [ ] 定义 `GitFileHelper` 类骨架

### 1.2 实现核心方法
- [ ] `__init__()` - 初始化和仓库检测
- [ ] `get_staged_files()` - 获取暂存区文件
- [ ] `get_unstaged_files()` - 获取工作区修改文件
- [ ] `get_commit_files()` - 获取 commit 文件
- [ ] `get_diff_files()` - 获取 diff 文件

### 1.3 实现辅助方法
- [ ] `get_file_content_at_commit()` - 获取历史文件内容
- [ ] `is_binary_file()` - 判断二进制文件
- [ ] `get_commit_info()` - 获取 commit 详细信息

### 1.4 边界情况处理
- [ ] 处理初始 commit（无父节点）
- [ ] 处理删除的文件
- [ ] 处理二进制文件
- [ ] 处理编码错误
- [ ] 处理大文件（>10MB）

### 1.5 测试
- [ ] 创建 `tests/checker/test_git_helper.py`
- [ ] 测试暂存区文件获取
- [ ] 测试工作区文件获取
- [ ] 测试 commit 文件获取
- [ ] 测试 diff 文件获取
- [ ] 测试错误处理
- [ ] 测试短 hash 支持
- [ ] 所有测试通过

### 1.6 文档
- [ ] 添加函数文档字符串
- [ ] 添加使用示例

---

## Phase 2: 插件命令扩展 (预计 1 天)

### 2.1 导入和初始化
- [ ] 在 `code_checker_plugin.py` 导入 `GitFileHelper`
- [ ] 在 `code_checker_plugin.py` 导入 `TempFileManager`（Phase 3）

### 2.2 更新命令补全
- [ ] 在 `get_completions()` 添加 `/git` 补全
- [ ] 添加 `/git` 子命令补全（/staged, /unstaged, /commit, /diff）
- [ ] 添加 git 子命令的选项补全

### 2.3 命令路由
- [ ] 在 `handle_check()` 添加 `/git` 分支
- [ ] 实现 `_check_git()` 方法（git 子命令路由）

### 2.4 实现子命令处理
- [ ] 实现 `_check_git_staged()` - 暂存区检查
- [ ] 实现 `_check_git_unstaged()` - 工作区检查
- [ ] 实现 `_check_git_commit()` - commit 检查
- [ ] 实现 `_check_git_diff()` - diff 检查

### 2.5 实现辅助方法
- [ ] 实现 `_parse_git_check_options()` - 选项解析
- [ ] 实现 `_prepare_git_files()` - 文件准备（Phase 3）
- [ ] 实现 `_execute_batch_check()` 或扩展现有方法
- [ ] 实现 `_create_check_id_with_prefix()` - 生成带前缀的 check_id

### 2.6 更新帮助信息
- [ ] 更新 `_show_help()` 添加 git 命令说明
- [ ] 更新 `get_help_text()` 添加 git 命令

### 2.7 错误处理
- [ ] 不在 Git 仓库时的友好提示
- [ ] 无文件变更时的提示
- [ ] 无效 commit hash 的提示
- [ ] 参数缺失的提示

### 2.8 测试
- [ ] 测试命令解析
- [ ] 测试各子命令执行
- [ ] 测试参数传递
- [ ] 测试错误提示

---

## Phase 3: 特殊文件处理 (预计 0.5 天)

### 3.1 临时文件管理器
- [ ] 实现 `TempFileManager` 类
- [ ] `__init__()` - 创建临时目录
- [ ] `create_temp_file()` - 创建临时文件
- [ ] `get_temp_path()` - 获取临时路径
- [ ] `get_original_path()` - 反查原始路径
- [ ] `cleanup()` - 清理临时文件
- [ ] 实现 context manager (`__enter__`, `__exit__`)

### 3.2 文件准备流程
- [ ] 实现 `_prepare_git_files()` 方法
- [ ] 处理工作区文件（直接返回路径）
- [ ] 处理历史文件（创建临时文件）
- [ ] 跳过二进制文件
- [ ] 跳过删除的文件
- [ ] 处理编码错误

### 3.3 批量检查集成
- [ ] 更新 `_execute_batch_check()` 支持 `TempFileManager`
- [ ] 检查后恢复原始文件路径（用于报告）
- [ ] 确保临时文件清理

### 3.4 路径处理
- [ ] Windows 路径兼容（反斜杠）
- [ ] Linux 路径兼容
- [ ] 长路径支持
- [ ] 特殊字符处理

### 3.5 测试
- [ ] 创建 `tests/checker/test_temp_file_manager.py`
- [ ] 测试临时文件创建
- [ ] 测试路径映射
- [ ] 测试自动清理
- [ ] 测试多文件管理
- [ ] Windows 和 Linux 测试

---

## Phase 4: 报告增强 (预计 0.5 天)

### 4.1 数据模型扩展
- [ ] 在 `types.py` 添加 `GitInfo` 类
- [ ] 在 `BatchCheckResult` 添加 `git_info` 字段

### 4.2 报告生成器修改
- [ ] 更新 `generate_summary_report()` 签名（添加 git_info 参数）
- [ ] 实现 `_get_git_report_title()` - 根据 Git 类型生成标题
- [ ] 实现 `_format_git_info_markdown()` - 格式化 Git 信息
- [ ] 更新 `_generate_json_summary()` 包含 Git 信息

### 4.3 插件集成
- [ ] 在 `_execute_batch_check()` 构造 `GitInfo`
- [ ] 传递 `GitInfo` 给报告生成器
- [ ] 在控制台输出显示 Git 信息

### 4.4 报告格式
- [ ] 暂存区报告格式
- [ ] 工作区报告格式
- [ ] Commit 报告格式
- [ ] Diff 报告格式

### 4.5 测试
- [ ] 验证报告包含 Git 信息
- [ ] 验证不同类型的报告格式
- [ ] 验证兼容性（非 Git 检查不受影响）

---

## Phase 5: 测试和文档 (预计 1 天)

### 5.1 单元测试补充
- [ ] 补充 `git_helper.py` 测试覆盖率
- [ ] 补充临时文件管理测试
- [ ] 补充插件方法测试

### 5.2 集成测试
- [ ] 端到端测试：暂存区检查
- [ ] 端到端测试：工作区检查
- [ ] 端到端测试：commit 检查
- [ ] 端到端测试：diff 检查
- [ ] 测试参数组合

### 5.3 边界情况测试
- [ ] 空暂存区
- [ ] 空工作区
- [ ] 初始 commit
- [ ] 大文件
- [ ] 二进制文件
- [ ] 删除的文件
- [ ] 编码错误
- [ ] 无效 commit hash

### 5.4 跨平台测试
- [ ] Windows 环境测试
- [ ] Linux 环境测试
- [ ] 路径兼容性测试
- [ ] 临时文件处理测试

### 5.5 性能测试
- [ ] 大型 commit 性能测试
- [ ] 并发性能测试

### 5.6 用户文档
- [ ] 更新 `docs/code_checker_usage.md`
- [ ] 添加 Git 检查使用说明
- [ ] 添加命令示例
- [ ] 添加常见问题

### 5.7 开发文档
- [ ] 更新 `docs/二次开发记录.md`
- [ ] 记录实施过程
- [ ] 记录遇到的问题和解决方案
- [ ] 记录性能优化

### 5.8 代码审查
- [ ] 代码风格检查
- [ ] 注释完整性检查
- [ ] 错误处理检查
- [ ] 日志记录检查

---

## 验收标准

### 功能完整性
- [ ] 所有子命令都能正常工作
- [ ] 支持所有选项参数
- [ ] 错误提示清晰友好
- [ ] 进度显示正常

### 代码质量
- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] 代码覆盖率 > 80%
- [ ] 无 pylint/flake8 警告

### 跨平台兼容
- [ ] Windows 测试通过
- [ ] Linux 测试通过
- [ ] 路径处理正确

### 文档完整
- [ ] 用户文档完整
- [ ] 开发文档完整
- [ ] 代码注释完整
- [ ] 示例清晰

### 性能
- [ ] 检查性能与现有功能相当
- [ ] 临时文件及时清理
- [ ] 无内存泄漏

---

## 风险和缓解

### 风险 1: GitPython 兼容性问题
- **风险等级**: 中
- **缓解措施**:
  - 使用 GitPython 稳定版本
  - 充分测试不同 Git 版本
  - 提供降级方案

### 风险 2: Windows 路径问题
- **风险等级**: 中
- **缓解措施**:
  - 统一使用 `os.path` 和 `pathlib`
  - 在 Windows 上充分测试
  - 处理长路径和特殊字符

### 风险 3: 临时文件清理失败
- **风险等级**: 低
- **缓解措施**:
  - 使用 context manager 确保清理
  - 添加异常处理
  - 记录清理失败日志

### 风险 4: 性能问题
- **风险等级**: 低
- **缓解措施**:
  - 复用现有并发机制
  - 对大文件设置限制
  - 性能测试和优化

---

## 发布计划

### Pre-release 测试
1. 开发分支测试
2. 邀请内部用户测试
3. 收集反馈
4. 修复问题

### 正式发布
1. 合并到主分支
2. 更新版本号
3. 创建 Release Tag
4. 更新 CHANGELOG
5. 通知用户

### 发布后
1. 监控问题报告
2. 及时修复 Bug
3. 收集功能建议

---

## 时间估算

| Phase | 任务 | 预计时间 |
|-------|------|----------|
| Phase 1 | Git 文件获取模块 | 1 天 |
| Phase 2 | 插件命令扩展 | 1 天 |
| Phase 3 | 特殊文件处理 | 0.5 天 |
| Phase 4 | 报告增强 | 0.5 天 |
| Phase 5 | 测试和文档 | 1 天 |
| **总计** | | **4 天** |

---

## 快速开始

### 第一天
1. [ ] 完成 Phase 1 (Git 文件获取模块)
2. [ ] 编写和运行单元测试

### 第二天
1. [ ] 完成 Phase 2 (插件命令扩展)
2. [ ] 完成 Phase 3 (特殊文件处理)
3. [ ] 初步集成测试

### 第三天
1. [ ] 完成 Phase 4 (报告增强)
2. [ ] 完成 Phase 5 (测试)

### 第四天
1. [ ] 跨平台测试
2. [ ] 完成文档
3. [ ] 代码审查和优化

---

## 参考资料

- [GitPython 文档](https://gitpython.readthedocs.io/)
- [Git 内部原理](https://git-scm.com/book/zh/v2/Git-内部原理-Git-对象)
- 现有 Checker 系统文档: `docs/code_checker_usage.md`
- Git 工具模块: `autocoder/common/git_utils.py`
