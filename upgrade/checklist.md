# Auto-Coder 2.0.2 升级检查清单

**项目**: cuscli
**目标版本**: 2.0.2
**当前版本**: 1.0.39-custom
**新版本号**: 1.1.5

---

## 使用说明

- 每完成一项，标记为 `[x]`
- 遇到问题，在备注栏记录
- 每个阶段完成后，记录实际耗时

---

## 第一阶段：准备和备份 ⏱️ 30分钟

### Git 备份
- [ ] 当前工作区干净（`git status`）
- [ ] 所有修改已提交
- [ ] 创建备份标签 `v1.0.39-custom-backup-$(date +%Y%m%d)`
- [ ] 备份标签推送到远程
- [ ] 创建升级分支 `upgrade/terminal-2.0.2`
- [ ] 切换到升级分支

**备注**: _______________
**实际耗时**: _____ 分钟

### 2.0.2 源码提取
- [ ] 创建临时目录 `/tmp/autocoder-2.0.2-extracted`
- [ ] 解压 wheel 文件
- [ ] 验证 `autocoder/` 目录存在
- [ ] 验证 `autocoder/terminal/` 目录存在
- [ ] 验证 `autocoder/terminal_v3/` 目录存在
- [ ] 验证元数据目录存在

**备注**: _______________
**实际耗时**: _____ 分钟

---

## 第二阶段：保留自定义内容 ⏱️ 1小时

### 创建备份目录
- [ ] 创建 `.upgrade-backup/` 目录
- [ ] 创建子目录结构（plugins/, common/, 等）

### 备份 Checker 系统
- [ ] 备份 `autocoder/checker/` 完整目录
- [ ] 验证 12 个核心文件都已备份
- [ ] 验证文件内容完整（spot check）

**文件清单**:
- [ ] `__init__.py`
- [ ] `types.py`
- [ ] `core.py`
- [ ] `rules_loader.py`
- [ ] `file_processor.py`
- [ ] `progress_tracker.py`
- [ ] `progress_display.py`
- [ ] `report_generator.py`
- [ ] `git_helper.py`
- [ ] `git_repo_manager.py`
- [ ] `simple_scan_tracker.py`
- [ ] `task_logger.py`

### 备份自定义插件
- [ ] 备份 `code_checker_plugin.py`
- [ ] 备份 `customs_rules_plugin.py`
- [ ] 备份 `git_helper_plugin.py`
- [ ] 备份 `utils.py`
- [ ] 备份 `plugins/__init__.py` (重要！)

### 备份通用模块
- [ ] 备份 `common/git_platform_config.py`
- [ ] 备份 `common/terminal_compat.py`（如存在）
- [ ] 备份 `common/llm_error_handler.py`（如存在）

### 备份海关规范数据
- [ ] 备份 `data/customs_rules/` 完整目录
- [ ] 验证 12 个 .md 文件都已备份
- [ ] 验证 `index.md` 存在

### 备份配置文件
- [ ] 备份 `setup.py`
- [ ] 备份 `README.md`
- [ ] 备份 `requirements.txt`（可选）

### 创建保留清单
- [ ] 创建 `PRESERVED_FILES.txt` 清单文件
- [ ] 清单包含所有自定义文件路径

**备注**: _______________
**实际耗时**: _____ 分钟

---

## 第三阶段：覆盖官方代码 ⏱️ 2小时

### 清理当前代码
- [ ] 移走 `autocoder/` 目录为 `autocoder-old/`
- [ ] 验证 `autocoder/` 不存在

### 复制 2.0.2 代码
- [ ] 复制完整的 `autocoder/` 目录
- [ ] 验证 `autocoder/terminal/` 存在
- [ ] 验证 `autocoder/terminal_v3/` 存在
- [ ] 验证 `autocoder/plugins/` 存在
- [ ] 验证 `autocoder/data/` 存在
- [ ] 复制元数据到 `.metadata-2.0.2/`

### 恢复 Checker 系统
- [ ] 复制 `.upgrade-backup/checker/` 到 `autocoder/checker/`
- [ ] 验证 12 个文件都已恢复
- [ ] 快速检查文件内容（spot check）

### 恢复自定义插件
- [ ] 恢复 `code_checker_plugin.py`
- [ ] 恢复 `customs_rules_plugin.py`
- [ ] 恢复 `utils.py`
- [ ] 复制并重命名 `git_helper_plugin.py` → `git_platform_plugin.py`
- [ ] 验证所有插件文件存在

### 恢复通用模块
- [ ] 恢复 `common/git_platform_config.py`
- [ ] 恢复 `common/terminal_compat.py`（如适用）
- [ ] 恢复 `common/llm_error_handler.py`（如适用）

### 恢复海关规范数据
- [ ] 创建 `autocoder/data/customs_rules/` 目录
- [ ] 恢复所有 .md 文件
- [ ] 恢复 `index.md`
- [ ] 验证文件数量正确（12个）

**备注**: _______________
**实际耗时**: _____ 分钟

---

## 第四阶段：插件系统适配 ⏱️ 3小时

### git_platform_plugin 适配
- [ ] 打开 `autocoder/plugins/git_platform_plugin.py`
- [ ] 修改类名: `GitHelperPlugin` → `GitPlatformPlugin`
- [ ] 修改插件名: `"git_helper"` → `"git_platform"`
- [ ] 保存文件
- [ ] 语法检查（`python -m py_compile`）

### plugins/__init__.py 合并
- [ ] 打开 `.upgrade-backup/plugins/__init__.py.custom`（当前版本）
- [ ] 打开 `autocoder/plugins/__init__.py`（2.0.2 版本）
- [ ] 使用 diff 工具对比差异
- [ ] 识别需要保留的自定义部分
- [ ] 识别需要采纳的官方改进
- [ ] 手动合并两个版本

**需要保留的部分**:
- [ ] 自定义插件导入（CodeCheckerPlugin, CustomsRulesPlugin, GitPlatformPlugin）
- [ ] 自定义插件注册逻辑
- [ ] dynamic_cmds 相关代码（如有自定义）

**需要采纳的部分**:
- [ ] 官方新增的方法
- [ ] 官方 bug 修复
- [ ] 官方性能优化

- [ ] 合并完成后保存
- [ ] 语法检查

### 插件加载测试
- [ ] 创建测试脚本验证插件导入
- [ ] 运行测试脚本
- [ ] 确认所有自定义插件能成功导入
- [ ] 确认插件名称正确

**测试脚本**:
```python
from autocoder.plugins import PluginManager
from autocoder.plugins.code_checker_plugin import CodeCheckerPlugin
from autocoder.plugins.customs_rules_plugin import CustomsRulesPlugin
from autocoder.plugins.git_platform_plugin import GitPlatformPlugin

print("✅ 所有插件导入成功")
```

**备注**: _______________
**实际耗时**: _____ 分钟

---

## 第五阶段：入口点配置 ⏱️ 1小时

### 更新 setup.py
- [ ] 打开 `setup.py`
- [ ] 更新 `version` 为 `"1.1.5"`
- [ ] 更新 `entry_points` 配置

**entry_points 配置**:
- [ ] 主入口: `cuscli=autocoder.terminal.bootstrap:run_cli`
- [ ] V3 入口: `cuscli-v3=autocoder.auto_coder_terminal_v3:main`
- [ ] Legacy 入口: `cuscli-legacy=autocoder.chat_auto_coder:main`（可选）

- [ ] 更新 `package_data` 包含 `customs_rules`
- [ ] 更新 `install_requires`（见第六阶段）
- [ ] 保存文件
- [ ] 语法检查

### 更新版本文件
- [ ] 创建/更新 `autocoder/version.py`
- [ ] 设置 `__version__ = "1.1.5"`
- [ ] 设置 `__base_version__ = "2.0.2"`（可选）

**备注**: _______________
**实际耗时**: _____ 分钟

---

## 第六阶段：依赖管理 ⏱️ 1小时

### 提取 2.0.2 依赖
- [ ] 提取 METADATA 中的依赖列表
- [ ] 保存为 `upgrade/requirements-2.0.2-raw.txt`
- [ ] 格式化为标准 requirements 格式
- [ ] 保存为 `upgrade/requirements-2.0.2.txt`

### 对比依赖差异
- [ ] 使用 diff 对比当前和 2.0.2 的依赖
- [ ] 记录新增的依赖
- [ ] 记录版本变更的依赖
- [ ] 记录可能的冲突

### 合并依赖
- [ ] 更新 `requirements.txt`
- [ ] 核心依赖使用 2.0.2 的版本
- [ ] 保留自定义额外依赖（如有）
- [ ] 解决版本冲突

### 测试依赖安装
- [ ] 创建测试虚拟环境
- [ ] 安装 requirements.txt
- [ ] 运行 `pip check` 检查冲突
- [ ] 验证关键包版本正确
- [ ] 清理测试环境

### 更新 setup.py
- [ ] 将依赖添加到 `install_requires`
- [ ] 或配置从 requirements.txt 读取

**备注**: _______________
**实际耗时**: _____ 分钟

---

## 第七阶段：全面测试 ⏱️ 4小时

### 单元测试 - Checker 模块
- [ ] 安装测试依赖（pytest, pytest-cov）
- [ ] 运行 `pytest tests/checker/ -v`
- [ ] 所有测试通过

**具体测试**:
- [ ] `test_core.py` - 核心逻辑
- [ ] `test_file_processor.py` - 文件处理
- [ ] `test_rules_loader.py` - 规则加载
- [ ] `test_progress_tracker.py` - 进度跟踪
- [ ] `test_report_generator.py` - 报告生成
- [ ] `test_git_helper.py` - Git 辅助
- [ ] `test_git_repo_manager.py` - Git 仓库管理
- [ ] `test_plugin.py` - 插件集成

**通过率**: _____% (____/____个测试)

### 单元测试 - 其他模块
- [ ] `test_git_platform_config.py`
- [ ] `test_completion_longest_match.py`
- [ ] `test_third_level_completion.py`
- [ ] 其他相关测试

**通过率**: _____% (____/____个测试)

### 集成测试 - CLI 启动
- [ ] 构建开发安装: `python setup.py develop`
- [ ] 测试 `cuscli --help`
- [ ] 能看到帮助信息
- [ ] 测试 `cuscli --version`
- [ ] 能看到版本信息

### 集成测试 - 插件加载
- [ ] 启动 `cuscli`
- [ ] 执行 `/plugins`
- [ ] 验证显示所有插件

**插件检查**:
- [ ] code_checker 插件显示
- [ ] customs_rules 插件显示
- [ ] git_platform 插件显示
- [ ] 其他官方插件显示

### 集成测试 - Checker 命令
- [ ] 执行 `/check /file <测试文件>`
- [ ] 文件路径补全正常（Tab 键）
- [ ] 检查执行成功
- [ ] 报告生成正确

- [ ] 执行 `/check /folder <测试目录>`
- [ ] 文件夹扫描正常
- [ ] 进度显示正常
- [ ] 汇总报告正确

- [ ] 执行 `/check /resume`
- [ ] 显示可恢复任务（或提示无任务）
- [ ] ID 补全正常（如有任务）

### 集成测试 - Customs Rules
- [ ] 执行 `/apply-customs`
- [ ] 显示规范列表
- [ ] 提示是否应用
- [ ] 成功应用规范

### 集成测试 - Git Platform
- [ ] 执行 `/git /status`
- [ ] Git 状态显示正常

- [ ] 执行 `/git /github setup`（或 `/git /gitlab setup`）
- [ ] 配置交互正常
- [ ] 异步输入正常
- [ ] 配置保存成功

### 动态补全测试
- [ ] `/check /file` + Tab - 文件列表补全
- [ ] `/check /resume` + Tab - 任务 ID 补全
- [ ] `/git /checkout` + Tab - 分支列表补全
- [ ] 其他动态补全命令

### 跨平台测试 - Linux
- [ ] Linux 环境安装成功
- [ ] CLI 启动正常
- [ ] 所有命令执行正常
- [ ] 动态补全正常

### 跨平台测试 - Windows（如适用）
- [ ] Windows 环境安装成功
- [ ] CLI 启动正常
- [ ] 所有命令执行正常
- [ ] 动态补全正常
- [ ] 路径分隔符处理正确

### 性能测试
- [ ] 测试启动时间（`time cuscli --version`）
- [ ] 启动时间: _____ 秒
- [ ] 测试命令响应时间
- [ ] 响应时间: _____ 秒
- [ ] 测试内存占用
- [ ] 内存占用: _____ MB

### 稳定性测试
- [ ] 运行 `pytest tests/stability/` -v
- [ ] 所有稳定性测试通过

**测试总结**:
- 单元测试通过率: _____%
- 集成测试通过率: _____%
- 发现问题: _____个
- 已解决: _____个
- 待解决: _____个

**备注**: _______________
**实际耗时**: _____ 小时

---

## 第八阶段：文档更新 ⏱️ 2小时

### 更新开发记录
- [ ] 打开 `docs/二次开发记录.md`
- [ ] 跳转到文件末尾
- [ ] 追加升级记录章节（见模板）
- [ ] 记录升级背景
- [ ] 记录架构变化
- [ ] 记录插件适配
- [ ] 记录保留功能
- [ ] 记录采纳的新功能
- [ ] 记录迁移过程
- [ ] 记录测试结果
- [ ] 记录遗留问题（如有）
- [ ] 记录后续优化建议
- [ ] 保存文件

### 更新 README.md
- [ ] 打开 `README.md`
- [ ] 更新版本信息（1.1.5）
- [ ] 更新基于版本（2.0.2）
- [ ] 更新架构说明（Terminal）
- [ ] 更新安装说明
- [ ] 更新入口点说明
- [ ] 添加/更新迁移说明
- [ ] 保存文件

### 创建迁移指南（可选）
- [ ] 创建 `docs/migration-guide-2.0.2.md`
- [ ] 记录用户视角的变化
- [ ] 记录开发者视角的变化
- [ ] 记录常见问题
- [ ] 保存文件

### 文档验证
- [ ] 所有文档 Markdown 语法正确
- [ ] 所有链接有效
- [ ] 代码块格式正确

**备注**: _______________
**实际耗时**: _____ 小时

---

## 第九阶段：打包和部署 ⏱️ 1小时

### 清理临时文件
- [ ] 删除/保留 `.upgrade-backup/`（建议先保留）
- [ ] 删除/保留 `autocoder-old/`（建议先保留）
- [ ] 删除 `/tmp/autocoder-2.0.2-extracted/`
- [ ] 清理 Python 缓存（__pycache__, *.pyc）

### 构建 wheel 包
- [ ] 安装构建工具（build, wheel, setuptools）
- [ ] 运行 `python setup.py sdist bdist_wheel`
- [ ] 检查 `dist/` 目录
- [ ] 验证 wheel 文件名: `cuscli-1.1.5-py3-none-any.whl`
- [ ] 验证 tar.gz 文件名: `cuscli-1.1.5.tar.gz`

### 验证打包内容
- [ ] 使用 `unzip -l` 查看 wheel 内容
- [ ] 确认包含 `autocoder/checker/`
- [ ] 确认包含 `autocoder/data/customs_rules/`
- [ ] 确认包含所有自定义插件
- [ ] 确认入口点配置正确

### 本地安装测试
- [ ] 创建测试虚拟环境
- [ ] 安装 wheel: `pip install dist/cuscli-1.1.5-py3-none-any.whl`
- [ ] 验证 `which cuscli` 正确
- [ ] 运行 `cuscli --version`
- [ ] 运行 `cuscli --help`
- [ ] 启动 CLI 并测试基本功能
- [ ] 清理测试环境

**备注**: _______________
**实际耗时**: _____ 分钟

---

## 第十阶段：Git 提交 ⏱️ 30分钟

### 检查修改
- [ ] 运行 `git status`
- [ ] 查看修改的文件列表
- [ ] 运行 `git diff --name-only`
- [ ] 确认所有修改符合预期

### 更新 .gitignore
- [ ] 检查 `.gitignore` 是否排除临时文件
- [ ] 添加 `.upgrade-backup/`（如需）
- [ ] 添加 `autocoder-old/`（如需）
- [ ] 添加 `upgrade/`（按要求文档不提交）
- [ ] 添加 `dist/`, `build/`, `*.egg-info/`

### 添加修改
- [ ] `git add autocoder/`
- [ ] `git add setup.py`
- [ ] `git add README.md`
- [ ] `git add docs/二次开发记录.md`
- [ ] `git add requirements.txt`
- [ ] `git add .gitignore`
- [ ] 确认不添加 `upgrade/` 目录

### 提交变更
- [ ] 使用详细的提交信息
- [ ] 提交信息包含：主要变更、保留功能、新增功能、测试状态
- [ ] 运行 `git commit`
- [ ] 检查提交信息格式

### 打标签
- [ ] 创建版本标签: `git tag -a v1.1.5 -m "..."`
- [ ] 标签信息详细清晰
- [ ] 验证标签: `git tag -l -n5 v1.1.5`

### 合并到主分支
- [ ] 检查当前分支: `git branch --show-current`
- [ ] 切换到 main: `git checkout main`
- [ ] 合并升级分支: `git merge upgrade/terminal-2.0.2 --no-ff`
- [ ] 验证合并: `git log --oneline -5`

### 推送到远程
- [ ] 推送主分支: `git push origin main`
- [ ] 推送标签: `git push origin v1.1.5`
- [ ] 推送所有标签（可选）: `git push origin --tags`
- [ ] 推送升级分支（可选）: `git push origin upgrade/terminal-2.0.2`

### Git 验证
- [ ] GitHub/GitLab 上看到新提交
- [ ] 新标签显示正确
- [ ] 提交历史清晰

**备注**: _______________
**实际耗时**: _____ 分钟

---

## 最终验证

### 环境清理后测试
- [ ] 创建全新虚拟环境
- [ ] 从 GitHub/GitLab 克隆代码
- [ ] 安装: `pip install -e .`
- [ ] 运行 `cuscli --version`
- [ ] 运行 `cuscli`
- [ ] 测试核心功能
- [ ] 确认一切正常

### 文档检查
- [ ] `docs/二次开发记录.md` 包含升级记录
- [ ] `README.md` 版本信息正确
- [ ] `upgrade/` 目录包含所有计划文档（本地保留）

### 版本验证
- [ ] Git 标签 `v1.1.5` 存在
- [ ] `setup.py` 版本号为 `1.1.5`
- [ ] `autocoder/version.py` 版本号为 `1.1.5`

### 成功标准
- [ ] ✅ 所有单元测试通过
- [ ] ✅ 所有集成测试通过
- [ ] ✅ 动态补全功能正常
- [ ] ✅ Windows/Linux 验证通过
- [ ] ✅ 所有命令正常工作
- [ ] ✅ 文档更新完成
- [ ] ✅ Git 提交成功
- [ ] ✅ 版本号正确（1.1.5）
- [ ] ✅ 所有自定义功能保留
- [ ] ✅ 新功能采纳成功

---

## 总结

### 时间统计

| 阶段 | 预计 | 实际 | 差异 |
|------|------|------|------|
| 1. 准备和备份 | 30分钟 | ___ | ___ |
| 2. 保留自定义内容 | 1小时 | ___ | ___ |
| 3. 覆盖官方代码 | 2小时 | ___ | ___ |
| 4. 插件系统适配 | 3小时 | ___ | ___ |
| 5. 入口点配置 | 1小时 | ___ | ___ |
| 6. 依赖管理 | 1小时 | ___ | ___ |
| 7. 全面测试 | 4小时 | ___ | ___ |
| 8. 文档更新 | 2小时 | ___ | ___ |
| 9. 打包和部署 | 1小时 | ___ | ___ |
| 10. Git 提交 | 30分钟 | ___ | ___ |
| **总计** | **16小时** | ___ | ___ |

### 问题记录

#### 遇到的问题
1. _____________________
2. _____________________
3. _____________________

#### 解决方案
1. _____________________
2. _____________________
3. _____________________

### 经验教训
1. _____________________
2. _____________________
3. _____________________

### 后续优化
1. _____________________
2. _____________________
3. _____________________

---

**升级日期**: __________
**执行人**: __________
**复核人**: __________
**状态**: ⬜ 进行中 / ⬜ 已完成 / ⬜ 已回滚

**签名**: __________
