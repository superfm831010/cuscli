# 代码检查功能使用指南

> 基于大模型的智能代码规范检查工具

## 📋 功能概述

代码检查功能是 Auto-Coder 的一个强大插件，它使用大语言模型（LLM）对代码进行智能检查，确保代码符合预定义的开发规范。

### 主要特性

- ✅ **智能检查**：基于 LLM 的语义理解，不仅检查语法，还能理解代码逻辑
- ✅ **规则定制**：支持前后端不同规则集，可自定义规则
- ✅ **准确定位**：精确返回问题代码的行号范围
- ✅ **大文件支持**：自动分块处理大文件，避免 token 限制
- ✅ **并发处理**：支持多文件并行检查，提高效率
- ✅ **进度跟踪**：实时显示检查进度，支持中断恢复
- ✅ **详细报告**：生成 JSON 和 Markdown 格式的检查报告
- ✅ **修复建议**：针对每个问题提供具体的修复建议

### 支持的检查类型

| 检查类型 | 规则文件 | 适用文件 |
|---------|---------|---------|
| 后端代码 | `rules/backend_rules.md` | `*.py` |
| 前端代码 | `rules/frontend_rules.md` | `*.js`, `*.jsx`, `*.ts`, `*.tsx`, `*.vue` |

---

## 🚀 快速开始

### 前置条件

1. 已安装并配置 Auto-Coder
2. 已配置 LLM API（OpenAI、Anthropic 等）
3. 已准备规则文件（`rules/backend_rules.md` 或 `rules/frontend_rules.md`）

### 基本使用流程

1. **启动 chat_auto_coder**
   ```bash
   python -m autocoder.chat_auto_coder
   ```

2. **检查单个文件**
   ```bash
   /check /file src/main.py
   ```

3. **检查整个项目**
   ```bash
   /check /folder
   ```

4. **查看检查报告**
   - 报告保存在 `codecheck/{project}_{timestamp}/` 目录
   - 包含 JSON 和 Markdown 两种格式

---

## 📖 命令参考

### 1. `/check /file` - 单文件检查

检查指定的单个文件。

**语法**：
```bash
/check /file <filename>
```

**示例**：
```bash
# 检查 Python 文件
/check /file autocoder/auto_coder.py

# 检查 JavaScript 文件
/check /file src/App.jsx

# 使用相对路径
/check /file ./utils/helper.py
```

**执行流程**：
1. 加载适用的规则（根据文件扩展名自动选择）
2. 读取文件内容并添加行号
3. 如果文件过大，自动分块处理
4. 调用 LLM 进行检查
5. 生成检查报告

**输出示例**：
```
正在检查文件: autocoder/auto_coder.py

✅ 检查完成！
   发现问题: 5
   错误: 2
   警告: 3
   提示: 0

📄 报告已保存到: codecheck/cuscli_20251010_143022/
   - files/autocoder_auto_coder_py.json
   - files/autocoder_auto_coder_py.md
```

---

### 2. `/check /folder` - 目录检查

批量检查目录下的文件。

**语法**：
```bash
/check /folder [/path <path>] [/ext <extensions>] [/ignore <patterns>] [/workers <count>]
```

**参数说明**：

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `/path` | 检查路径 | 当前目录 | `/path src` |
| `/ext` | 文件扩展名（逗号分隔） | 所有支持的类型 | `/ext .py,.js` |
| `/ignore` | 忽略的目录/文件（逗号分隔） | 无 | `/ignore tests,__pycache__` |
| `/workers` | 并发数 | 5 | `/workers 10` |

**示例**：

```bash
# 检查当前目录
/check /folder

# 检查指定目录
/check /folder /path src

# 只检查 Python 文件
/check /folder /ext .py

# 检查 Python 和 JavaScript 文件
/check /folder /ext .py,.js,.jsx

# 忽略测试文件和缓存目录
/check /folder /ignore tests,__pycache__,*.pyc

# 使用 10 个并发
/check /folder /workers 10

# 组合使用
/check /folder /path src /ext .py /ignore tests /workers 5
```

**执行流程**：
1. 扫描指定目录，根据参数过滤文件
2. 生成唯一的 check_id（格式：`{project}_{timestamp}`）
3. 使用并发检查所有文件
4. 实时显示进度（文件名、百分比、剩余时间）
5. 生成汇总报告

**输出示例**：
```
扫描目录: src
找到 156 个文件（Python: 156）

检查 ID: cuscli_20251010_143022

正在检查文件... (并发: 5)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:00
检查 utils.py (并发: 5)

✅ 检查完成！
   总文件数: 156
   发现问题: 342 (错误: 45, 警告: 267, 提示: 30)

📄 报告已保存到: codecheck/cuscli_20251010_143022/
   - summary.json
   - summary.md
   - files/（各文件详细报告）
```

---

### 3. `/check /resume` - 恢复检查

恢复中断的检查任务。

**语法**：
```bash
/check /resume [<check_id>]
```

**使用场景**：
- 检查过程中按 `Ctrl+C` 中断
- 网络异常导致中断
- 系统崩溃需要恢复

**示例**：

```bash
# 不指定 check_id，列出可恢复的检查
/check /resume

# 输出：
# 可恢复的检查:
#
#   ID: cuscli_20251010_143022
#   时间: 2025-10-10 14:30:22
#   进度: 89/156

# 恢复指定的检查
/check /resume cuscli_20251010_143022
```

**执行流程**：
1. 加载检查状态（已完成和待完成的文件列表）
2. 继续检查剩余文件
3. 合并之前的结果
4. 更新汇总报告

**输出示例**：
```
恢复检查: cuscli_20251010_143022
剩余文件: 67/156

正在检查文件... (并发: 5)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:01:23

✅ 检查完成！
   总文件数: 156
   发现问题: 342
```

---

### 4. `/check /report` - 查看报告

查看历史检查报告（功能开发中）。

**语法**：
```bash
/check /report <check_id>
```

---

### 5. `/check /git` - Git 检查（新功能）

检查 Git 相关的文件变更，包括暂存区、工作区、历史 commit 和 diff。

**语法**：
```bash
/check /git <subcommand> [options]
```

**子命令**：

| 子命令 | 说明 | 示例 |
|--------|------|------|
| `/staged` | 检查暂存区文件（已 add 但未 commit） | `/check /git /staged` |
| `/unstaged` | 检查工作区修改文件（已修改但未 add） | `/check /git /unstaged` |
| `/commit <hash>` | 检查指定 commit 的变更文件 | `/check /git /commit abc1234` |
| `/diff <commit1> [commit2]` | 检查两个 commit 间的差异文件 | `/check /git /diff main dev` |

**通用选项**：

| 选项 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `/repeat` | LLM 调用重复次数 | 1 | `/repeat 3` |
| `/consensus` | 共识阈值（0-1） | 1.0 | `/consensus 0.8` |
| `/workers` | 并发检查数 | 5 | `/workers 10` |

**示例**：

```bash
# 检查暂存区文件
/check /git /staged

# 检查工作区修改
/check /git /unstaged

# 检查某个 commit（支持短 hash）
/check /git /commit abc1234

# 检查两个 commit 间差异
/check /git /diff main dev

# 检查暂存区，使用多次 LLM 调用提高准确性
/check /git /staged /repeat 3 /consensus 0.8

# 检查 commit，使用更多并发
/check /git /commit abc1234 /workers 10
```

**执行流程**：
1. 从 Git 获取相应的文件列表
2. 对于历史文件（commit/diff），创建临时文件
3. 调用代码检查器检查所有文件
4. 生成包含 Git 信息的检查报告
5. 自动清理临时文件

**输出示例**：
```
检查暂存区文件...
找到 3 个文件

正在检查文件... (并发: 5)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:15

✅ 检查完成！
   总文件数: 3
   发现问题: 8 (错误: 2, 警告: 5, 提示: 1)

📄 报告已保存到: codecheck/git_staged_20251010_143022/
   - summary.json
   - summary.md
   - files/（各文件详细报告）
```

**报告增强**：

Git 检查生成的报告会包含额外的 Git 上下文信息：

```markdown
# 代码检查报告 - Git Staged

**检查类型**: Git 暂存区检查
**分支**: main
**变更文件**: 3 个

## 检查概况
...
```

**注意事项**：
- 必须在 Git 仓库中执行该命令
- 二进制文件和删除的文件会自动跳过
- 大文件（>10MB）会自动跳过
- commit hash 支持完整 hash 和短 hash（最少 4 位）
- 历史文件检查使用临时文件，检查完成后自动清理

**常见场景**：

1. **Pre-commit 检查**：提交前检查暂存区文件
   ```bash
   /check /git /staged
   ```

2. **代码审查**：检查某个 PR 的 commit
   ```bash
   /check /git /commit abc1234
   ```

3. **对比检查**：检查两个分支间的差异
   ```bash
   /check /git /diff main feature-branch
   ```

4. **快速修改检查**：检查工作区修改（未暂存）
   ```bash
   /check /git /unstaged
   ```

---

## 💡 使用示例

### 场景 1：快速检查单个文件

适用于修改单个文件后的快速验证。

```bash
# 1. 修改文件
vim src/main.py

# 2. 启动 chat_auto_coder
python -m autocoder.chat_auto_coder

# 3. 检查文件
/check /file src/main.py

# 4. 查看报告
cat codecheck/*/files/src_main_py.md
```

---

### 场景 2：检查整个项目

适用于项目规范检查、代码审查。

```bash
# 1. 启动 chat_auto_coder
python -m autocoder.chat_auto_coder

# 2. 检查所有 Python 文件，忽略测试
/check /folder /ext .py /ignore tests,__pycache__

# 3. 查看汇总报告
cat codecheck/*/summary.md
```

---

### 场景 3：前端代码检查

检查 React/Vue 项目。

```bash
# 检查 JavaScript/TypeScript/Vue 文件
/check /folder /path frontend/src /ext .js,.jsx,.ts,.tsx,.vue

# 忽略 node_modules 和 dist
/check /folder /path frontend /ext .js,.jsx,.ts,.tsx /ignore node_modules,dist
```

---

### 场景 4：大型项目并发检查

提高大型项目的检查速度。

```bash
# 使用 10 个并发
/check /folder /workers 10

# 如果遇到 API 限流，降低并发数
/check /folder /workers 3
```

---

### 场景 5：中断恢复

处理检查过程中的意外中断。

```bash
# 1. 开始检查
/check /folder

# 2. 检查过程中按 Ctrl+C 中断
# 输出：
# ⚠️  检查已中断
#    检查 ID: cuscli_20251010_143022
#    使用 /check /resume cuscli_20251010_143022 继续

# 3. 稍后恢复
/check /resume cuscli_20251010_143022
```

---

### 场景 6：Git 提交前检查

确保提交的代码符合规范。

```bash
# 1. 修改代码并暂存
git add src/main.py src/utils.py

# 2. 启动 chat_auto_coder
python -m autocoder.chat_auto_coder

# 3. 检查暂存区文件
/check /git /staged

# 4. 查看报告并修复问题
cat codecheck/git_staged_*/summary.md

# 5. 修复后再次检查
/check /git /staged

# 6. 确认无问题后提交
git commit -m "fix: update functions"
```

---

### 场景 7：代码审查 PR

检查 PR 中的commit。

```bash
# 1. 获取 PR 的 commit hash
git log -1 --format="%H"

# 2. 启动 chat_auto_coder
python -m autocoder.chat_auto_coder

# 3. 检查该 commit
/check /git /commit abc1234

# 4. 或检查两个分支的差异
/check /git /diff main feature-branch

# 5. 查看报告
cat codecheck/git_commit_*/summary.md
```

---

## ⚙️ 配置选项

### 规则配置文件

**位置**：`rules/rules_config.json`

**配置示例**：
```json
{
  "version": "1.0.0",
  "rule_sets": {
    "backend": {
      "enabled": true,
      "file_patterns": ["**/*.py"],
      "severity_threshold": "warning",
      "disabled_rules": []
    },
    "frontend": {
      "enabled": true,
      "file_patterns": [
        "**/*.js",
        "**/*.jsx",
        "**/*.ts",
        "**/*.tsx",
        "**/*.vue"
      ],
      "severity_threshold": "warning",
      "disabled_rules": []
    }
  },
  "global_settings": {
    "max_workers": 5,
    "chunk_size": 4000,
    "chunk_overlap": 200
  }
}
```

**配置项说明**：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `enabled` | 是否启用该规则集 | `true` |
| `file_patterns` | 适用的文件模式 | 根据类型 |
| `severity_threshold` | 最低严重程度 | `"warning"` |
| `disabled_rules` | 禁用的规则 ID | `[]` |
| `max_workers` | 最大并发数 | `5` |
| `chunk_size` | 文件分块大小（tokens） | `4000` |
| `chunk_overlap` | 分块重叠行数 | `200` |

### 禁用特定规则

如果某些规则不适用，可以禁用：

```json
{
  "rule_sets": {
    "backend": {
      "disabled_rules": ["backend_006", "backend_009"]
    }
  }
}
```

### 调整严重程度阈值

只检查特定严重程度以上的问题：

```json
{
  "rule_sets": {
    "backend": {
      "severity_threshold": "error"  // 只检查错误，忽略警告和提示
    }
  }
}
```

可选值：`"info"` < `"warning"` < `"error"`

---

## 📊 检查报告

### 报告目录结构

```
codecheck/
└── {project}_{timestamp}/
    ├── summary.json              # 总体摘要（JSON）
    ├── summary.md                # 总体摘要（Markdown）
    ├── files/                    # 各文件详细报告
    │   ├── src_main_py.json
    │   ├── src_main_py.md
    │   ├── src_utils_py.json
    │   └── src_utils_py.md
    └── progress.json             # 检查进度快照
```

### 汇总报告（summary.md）

```markdown
# 代码检查报告

**检查ID**: cuscli_20251010_143022
**项目名称**: cuscli
**检查时间**: 2025-10-10 14:30:22 ~ 14:35:18 (耗时: 4分56秒)

## 检查概况

- ✅ 总文件数: 156
- ✅ 已检查: 156
- ⚠️  发现问题: 342
  - 🔴 错误: 45
  - 🟡 警告: 267
  - 🔵 提示: 30

## 问题分布

### 按规则分类

| 规则 | 数量 | 严重程度 |
|------|------|----------|
| 复杂的 if-else 嵌套 | 23 | 警告 |
| 方法行数过长 | 18 | 警告 |
| 缺少异常处理 | 15 | 错误 |

### 问题最多的文件

1. `autocoder/auto_coder.py` - 18 个问题
2. `autocoder/chat_auto_coder.py` - 15 个问题
3. `autocoder/common/llms.py` - 12 个问题
```

### 文件报告（files/xxx.md）

```markdown
# 文件检查报告: src/main.py

**检查时间**: 2025-10-10 14:31:05
**问题数量**: 5 (错误: 2, 警告: 3)

---

## ❌ 错误

### 1. 空指针风险 (行 125-130)

**规则**: backend_027
**严重程度**: error

**问题描述**:
方法 `process_data` 在第 127 行直接使用了可能为 None 的变量 `data`，存在空指针风险。

**代码片段**:
```python
125 def process_data(data):
126     # 没有判空
127     result = data.strip()  # 风险点
128     return result
```

**修复建议**:
在使用前添加判空检查：
```python
def process_data(data):
    if data is None:
        return ""
    result = data.strip()
    return result
```

---

## ⚠️ 警告

### 2. 方法行数过长 (行 45-98)

**规则**: backend_009
**严重程度**: warning

**问题描述**:
方法 `calculate_metrics` 包含 54 行代码，超过推荐的 30 行限制。

**修复建议**:
建议将该方法拆分为多个更小的方法，每个方法负责单一职责。
```

### JSON 报告格式

JSON 报告包含结构化数据，方便程序处理：

```json
{
  "file_path": "src/main.py",
  "check_time": "2025-10-10T14:31:05",
  "issues": [
    {
      "rule_id": "backend_027",
      "severity": "error",
      "line_start": 125,
      "line_end": 130,
      "description": "方法 process_data 在第 127 行直接使用了可能为 None 的变量 data，存在空指针风险。",
      "suggestion": "在使用前添加判空检查",
      "code_snippet": "125 def process_data(data):\n126     # 没有判空\n127     result = data.strip()  # 风险点\n128     return result"
    }
  ],
  "error_count": 2,
  "warning_count": 3,
  "info_count": 0,
  "status": "success"
}
```

---

## ❓ 常见问题

### Q1: 如何添加自定义规则？

**A**: 编辑 `rules/backend_rules.md` 或 `rules/frontend_rules.md`，按以下格式添加：

```markdown
### 规则ID: backend_xxx
**标题**: 规则标题
**严重程度**: warning
**描述**: 规则详细描述

**错误示例**:
```python
# 错误的代码
```

**正确示例**:
```python
# 正确的代码
```
```

### Q2: 检查速度太慢怎么办？

**A**: 有几种优化方式：

1. **增加并发数**：
   ```bash
   /check /folder /workers 10
   ```

2. **减少检查文件**：
   ```bash
   /check /folder /ext .py /ignore tests,docs
   ```

3. **使用更快的模型**：配置 API 时选择响应更快的模型

### Q3: 如何处理大文件？

**A**: 系统会自动处理大文件：

- 文件内容超过 4000 tokens 时自动分块
- 块之间有 200 行重叠，避免边界问题
- 结果自动合并，去除重复问题

可以在 `rules_config.json` 中调整：
```json
{
  "global_settings": {
    "chunk_size": 6000,      // 增加到 6000 tokens
    "chunk_overlap": 300     // 重叠增加到 300 行
  }
}
```

### Q4: 检查过程中遇到 API 限流怎么办？

**A**:

1. **降低并发数**：
   ```bash
   /check /folder /workers 3
   ```

2. **分批检查**：
   ```bash
   /check /folder /path src/module1
   /check /folder /path src/module2
   ```

3. **使用中断恢复**：遇到限流时按 Ctrl+C，等待后使用 `/check /resume` 继续

### Q5: 如何只检查修改过的文件？

**A**: 结合 git 使用：

```bash
# 获取修改的文件列表
git diff --name-only > changed_files.txt

# 逐个检查
/check /file src/main.py
/check /file src/utils.py
```

### Q6: 报告存储在哪里？如何清理？

**A**:

- **存储位置**：`codecheck/{project}_{timestamp}/`
- **清理旧报告**：
  ```bash
  # 删除 7 天前的报告
  find codecheck -type d -mtime +7 -exec rm -rf {} +
  ```

### Q7: 如何在 CI/CD 中使用？

**A**: 可以创建脚本调用检查功能：

```bash
#!/bin/bash
# ci-check.sh

# 启动检查（需要配置自动化参数）
python -m autocoder.checker_cli --folder src --ext .py --output ci-report.json

# 检查是否有错误
if grep -q '"error_count": [1-9]' ci-report.json; then
    echo "发现代码规范错误！"
    exit 1
fi
```

### Q8: 检查结果不准确怎么办？

**A**:

1. **优化规则描述**：在规则文件中添加更多示例
2. **调整 Prompt**：修改 `autocoder/checker/core.py` 中的 prompt 模板
3. **更换模型**：使用理解能力更强的模型（如 GPT-4、Claude）

### Q9: 如何禁用某个规则？

**A**: 在 `rules_config.json` 中配置：

```json
{
  "rule_sets": {
    "backend": {
      "disabled_rules": ["backend_006", "backend_009"]
    }
  }
}
```

### Q10: 支持哪些编程语言？

**A**: 当前版本支持：

- ✅ Python（`.py`）
- ✅ JavaScript（`.js`）
- ✅ TypeScript（`.ts`）
- ✅ React（`.jsx`, `.tsx`）
- ✅ Vue（`.vue`）

添加新语言支持：创建规则文件并配置 `rules_config.json`

---

## 🔗 相关文档

- **[代码检查设计文档](code_checker_design.md)** - 了解架构设计
- **[二次开发指南](code_checker_development.md)** - 扩展和定制功能
- **[任务清单](code_checker_tasks.md)** - 开发任务记录
- **[工作记录](checker_phase1_work_log.md)** - 各阶段工作记录

---

## 📞 支持

如有问题或建议，请：
- 查看项目文档：`docs/`
- 查看日志文件：`.auto-coder/logs/auto-coder.log`
- 联系开发团队

---

**最后更新**：2025-10-10
**文档版本**：1.0.0
