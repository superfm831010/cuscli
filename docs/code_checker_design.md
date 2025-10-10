# 代码检查功能设计文档

## 1. 功能概述

实现一个基于大模型的代码规范检查工具，用于检查 Python 后端代码和前端代码是否符合海关定制的开发规范。

### 1.1 核心功能

- ✅ 单文件检查：`/check /file <filename>`
- ✅ 目录检查：`/check /folder [options]`
- ✅ 规则管理：支持前后端不同规则集
- ✅ 大文件处理：使用 chunk 机制分段检查
- ✅ 并发检查：多文件并行处理
- ✅ 进度跟踪：实时显示检查进度
- ✅ 中断恢复：支持检查过程中断后恢复
- ✅ 结果保存：生成详细的检查报告
- ✅ 行号定位：准确返回问题代码的行号范围

### 1.2 设计目标

1. **可扩展性**：插件化设计，易于添加新规则
2. **高性能**：并发处理，支持大型项目
3. **用户友好**：清晰的进度提示和报告
4. **可靠性**：支持中断恢复，避免重复检查
5. **准确性**：精确定位问题代码位置

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    Chat Auto Coder                      │
│                     (主应用)                             │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ 插件加载
                     ▼
┌─────────────────────────────────────────────────────────┐
│              CodeCheckerPlugin                          │
│            (命令注册和调度)                              │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│  /check  │  │  /check  │  │  /check  │
│  /file   │  │ /folder  │  │ /resume  │
└─────┬────┘  └─────┬────┘  └─────┬────┘
      │             │              │
      └─────────────┼──────────────┘
                    ▼
        ┌───────────────────────┐
        │    CodeChecker        │
        │   (核心检查逻辑)       │
        └───────────┬───────────┘
                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│  Rules   │ │  File    │ │Progress  │
│  Loader  │ │Processor │ │ Tracker  │
└──────────┘ └──────────┘ └──────────┘
        │           │           │
        └───────────┼───────────┘
                    ▼
        ┌───────────────────────┐
        │   Report Generator    │
        │   (生成检查报告)       │
        └───────────────────────┘
```

### 2.2 模块说明

#### 2.2.1 CodeCheckerPlugin (`autocoder/plugins/code_checker_plugin.py`)

**职责：**
- 注册 `/check` 命令及子命令
- 提供命令补全功能
- 参数解析和验证
- 调用核心检查逻辑

**命令接口：**
```python
/check /file <filename>                    # 检查单个文件
/check /folder                             # 检查当前目录
/check /folder /path <path>                # 检查指定目录
/check /folder /ext .py,.js                # 按扩展名过滤
/check /folder /ignore node_modules,dist   # 忽略目录/文件
/check /resume <check_id>                  # 恢复检查
/check /report <check_id>                  # 查看报告
```

#### 2.2.2 CodeChecker (`autocoder/checker/core.py`)

**职责：**
- 协调各模块完成检查任务
- 调用 LLM 进行代码检查
- 处理检查结果
- 管理并发执行

**核心方法：**
```python
class CodeChecker:
    def check_file(self, file_path: str) -> FileCheckResult
    def check_files(self, files: List[str]) -> BatchCheckResult
    def check_code_chunk(self, code: str, rules: List[Rule]) -> List[Issue>
    def merge_chunk_results(self, results: List[ChunkResult]) -> FileCheckResult
```

#### 2.2.3 RulesLoader (`autocoder/checker/rules_loader.py`)

**职责：**
- 加载规则文件（Markdown 格式）
- 解析规则配置
- 根据文件类型选择适用规则

**核心方法：**
```python
class RulesLoader:
    def load_rules(self, rule_type: str) -> List[Rule]
    def get_applicable_rules(self, file_path: str) -> List[Rule]
    def reload_rules(self) -> None
```

#### 2.2.4 FileProcessor (`autocoder/checker/file_processor.py`)

**职责：**
- 文件遍历和过滤
- 大文件分块（复用 TokenLimiter）
- 文件类型检测

**核心方法：**
```python
class FileProcessor:
    def scan_files(self, path: str, filters: FileFilters) -> List[str]
    def chunk_file(self, file_path: str, chunk_size: int) -> List[CodeChunk]
    def is_checkable(self, file_path: str) -> bool
```

#### 2.2.5 ProgressTracker (`autocoder/checker/progress_tracker.py`)

**职责：**
- 跟踪检查进度
- 持久化检查状态
- 支持中断恢复

**核心方法：**
```python
class ProgressTracker:
    def start_check(self, files: List[str]) -> str  # 返回 check_id
    def mark_completed(self, file_path: str) -> None
    def get_remaining_files(self, check_id: str) -> List[str]
    def save_state(self) -> None
    def load_state(self, check_id: str) -> CheckState
```

#### 2.2.6 ReportGenerator (`autocoder/checker/report_generator.py`)

**职责：**
- 生成 JSON 格式报告
- 生成 Markdown 格式报告
- 汇总统计信息

**核心方法：**
```python
class ReportGenerator:
    def generate_file_report(self, result: FileCheckResult) -> None
    def generate_summary_report(self, results: List[FileCheckResult]) -> None
    def save_report(self, report_path: str) -> None
```

## 3. 数据模型

### 3.1 核心类型定义

```python
# types.py

from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel

class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class Rule(BaseModel):
    """规则定义"""
    id: str                    # 规则ID，如 "backend_001"
    category: str              # 规则类别
    title: str                 # 规则标题
    description: str           # 规则描述
    severity: Severity         # 严重程度
    enabled: bool = True       # 是否启用
    examples: Optional[str]    # 示例代码

class Issue(BaseModel):
    """检查发现的问题"""
    rule_id: str              # 违反的规则ID
    severity: Severity        # 严重程度
    line_start: int           # 问题起始行号
    line_end: int             # 问题结束行号
    description: str          # 问题描述
    suggestion: str           # 修复建议
    code_snippet: str         # 问题代码片段

class FileCheckResult(BaseModel):
    """单个文件的检查结果"""
    file_path: str
    check_time: str
    issues: List[Issue]
    error_count: int
    warning_count: int
    info_count: int
    status: str               # "success" | "failed" | "skipped"
    error_message: Optional[str]

class BatchCheckResult(BaseModel):
    """批量检查结果"""
    check_id: str
    start_time: str
    end_time: str
    total_files: int
    checked_files: int
    total_issues: int
    file_results: List[FileCheckResult]

class CheckState(BaseModel):
    """检查状态（用于持久化）"""
    check_id: str
    start_time: str
    config: Dict[str, Any]
    total_files: List[str]
    completed_files: List[str]
    remaining_files: List[str]
```

## 4. 技术要点

### 4.1 复用 auto-coder 能力

#### 4.1.1 TokenLimiter 的 chunk 机制

**位置：** `autocoder/rag/token_limiter.py`

**复用方式：**
```python
# 处理大文件时的分块策略
from autocoder.rag.token_limiter import TokenLimiter

class FileProcessor:
    def chunk_large_file(self, file_content: str, max_tokens: int):
        """使用 TokenLimiter 的思路分块大文件"""
        # 1. 按行号添加行标记
        lines = file_content.split('\n')
        numbered_content = '\n'.join(f"{i+1} {line}" for i, line in enumerate(lines))

        # 2. 计算 token 数量
        token_count = count_tokens(numbered_content)

        # 3. 如果超过限制，分块处理
        if token_count > max_tokens:
            chunks = self._split_into_chunks(lines, max_tokens)
            return chunks
        else:
            return [numbered_content]
```

#### 4.1.2 并发处理

**参考：** `autocoder/rag/token_limiter.py:223-290`

**复用方式：**
```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def check_files_concurrently(self, files: List[str], max_workers: int = 5):
    """并发检查多个文件"""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(self.check_file, file): file
            for file in files
        }

        for future in as_completed(future_to_file):
            file = future_to_file[future]
            try:
                result = future.result()
                yield result
            except Exception as exc:
                logger.error(f"File {file} check failed: {exc}")
```

#### 4.1.3 LLM Prompt 设计

**参考：** `autocoder/common/code_auto_generate_editblock.py`

**Prompt 模板：**
```python
@byzerllm.prompt()
def check_code_prompt(self, code_with_lines: str, rules: str) -> str:
    """
    你是一个代码审查专家，请根据以下规则检查代码。

    ## 检查规则
    {{ rules }}

    ## 待检查代码（带行号）
    ```
    {{ code_with_lines }}
    ```

    ## 任务要求
    1. 仔细检查代码是否违反上述规则
    2. 对于每个问题，准确定位起始和结束行号
    3. 提供问题描述和修复建议

    ## 输出格式
    请以 JSON 数组格式返回检查结果，每个问题包含：
    - rule_id: 违反的规则ID
    - severity: 严重程度 (error/warning/info)
    - line_start: 问题起始行号
    - line_end: 问题结束行号
    - description: 问题描述
    - suggestion: 修复建议

    示例：
    ```json
    [
        {
            "rule_id": "backend_006",
            "severity": "warning",
            "line_start": 15,
            "line_end": 32,
            "description": "发现复杂的 if-else 嵌套，嵌套层数为 4，超过规定的 3 层",
            "suggestion": "建议将内层逻辑抽取为独立方法，或使用策略模式简化"
        }
    ]
    ```

    如果没有发现问题，返回空数组 []
    """
```

### 4.2 进度显示

使用 `rich` 库实现友好的进度显示：

```python
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
) as progress:
    task = progress.add_task("正在检查文件...", total=len(files))

    for file in files:
        # 检查文件
        progress.update(task, advance=1, description=f"检查 {file}")
```

### 4.3 状态持久化

```python
# 状态保存位置
STATE_DIR = ".auto-coder/codecheck/progress"

# 保存状态
def save_state(self, check_id: str, state: CheckState):
    state_file = os.path.join(STATE_DIR, f"{check_id}.json")
    with open(state_file, 'w') as f:
        json.dump(state.dict(), f, indent=2, ensure_ascii=False)

# 加载状态
def load_state(self, check_id: str) -> CheckState:
    state_file = os.path.join(STATE_DIR, f"{check_id}.json")
    with open(state_file, 'r') as f:
        data = json.load(f)
    return CheckState(**data)
```

## 5. 报告格式

### 5.1 目录结构

```
codecheck/
├── {project_name}_{timestamp}/
│   ├── summary.json              # 总体摘要（JSON）
│   ├── summary.md                # 总体摘要（Markdown）
│   ├── files/                    # 各文件详细报告
│   │   ├── src_main_py.json
│   │   ├── src_main_py.md
│   │   ├── src_utils_py.json
│   │   └── src_utils_py.md
│   └── progress.json             # 检查进度快照
```

### 5.2 summary.json 格式

```json
{
  "check_id": "cuscli_20250110_143022",
  "project_name": "cuscli",
  "start_time": "2025-01-10T14:30:22",
  "end_time": "2025-01-10T14:35:18",
  "duration_seconds": 296,
  "config": {
    "path": "/projects/cuscli",
    "extensions": [".py"],
    "ignored": ["__pycache__", "*.pyc"]
  },
  "statistics": {
    "total_files": 156,
    "checked_files": 156,
    "skipped_files": 0,
    "total_issues": 342,
    "error_count": 45,
    "warning_count": 267,
    "info_count": 30
  },
  "top_issues": [
    {
      "rule_id": "backend_006",
      "count": 23,
      "title": "复杂的 if-else 嵌套"
    }
  ],
  "files_with_most_issues": [
    {
      "file": "autocoder/auto_coder.py",
      "issue_count": 18
    }
  ]
}
```

### 5.3 summary.md 格式

```markdown
# 代码检查报告

**检查ID**: cuscli_20250110_143022
**项目名称**: cuscli
**检查时间**: 2025-01-10 14:30:22 ~ 14:35:18 (耗时: 4分56秒)

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
| ... | ... | ... |

### 问题最多的文件

1. `autocoder/auto_coder.py` - 18 个问题
2. `autocoder/chat_auto_coder.py` - 15 个问题
3. ...

## 详细报告

详见 `files/` 目录下各文件的检查报告。
```

### 5.4 文件报告格式（files/xxx.md）

```markdown
# 文件检查报告: src/main.py

**检查时间**: 2025-01-10 14:31:05
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

---
```

## 6. 开发流程

### 6.1 Git 提交规范

每完成一个独立任务，提交一次 git：

```bash
# Phase 1
git add rules/backend_rules.md
git commit -m "feat(checker): 转换后端检查规则为 Markdown 格式"

# Phase 2
git add autocoder/checker/types.py
git commit -m "feat(checker): 添加数据模型定义"

# ...
```

### 6.2 测试策略

每个模块开发完成后进行单元测试：

```python
# tests/checker/test_rules_loader.py
def test_load_backend_rules():
    loader = RulesLoader()
    rules = loader.load_rules("backend")
    assert len(rules) > 0
    assert rules[0].id.startswith("backend_")
```

## 7. 扩展性设计

### 7.1 添加新规则

只需在规则文件中添加新规则：

```markdown
## 新规则类别

### 规则ID: backend_xxx
**标题**: 规则标题
**严重程度**: warning
**描述**: 规则详细描述

**错误示例**:
```python
# 错误代码
```

**正确示例**:
```python
# 正确代码
```
```

### 7.2 支持新语言

1. 添加新的规则文件：`rules/{language}_rules.md`
2. 在 `RulesLoader` 中添加文件类型映射
3. 无需修改核心逻辑

## 8. 性能考虑

### 8.1 并发处理

- 默认并发数：5
- 可通过参数调整：`/check /folder /workers 10`

### 8.2 缓存机制

- 规则文件缓存：避免重复加载
- 文件内容缓存：避免重复读取（对于小文件）

### 8.3 大文件优化

- 使用 chunk 机制，每个 chunk 不超过 4000 tokens
- chunk 之间有 200 行重叠，避免边界问题

## 9. 配置选项

支持通过配置文件自定义行为：

```json
// .auto-coder/checker_config.json
{
  "max_workers": 5,
  "chunk_size": 4000,
  "chunk_overlap": 200,
  "ignored_patterns": [
    "__pycache__",
    "*.pyc",
    "node_modules",
    "dist"
  ],
  "rules": {
    "backend": {
      "enabled": true,
      "severity_threshold": "warning"
    },
    "frontend": {
      "enabled": true
    }
  }
}
```

## 10. 参考资料

- auto-coder 插件系统：`autocoder/plugins/__init__.py`
- TokenLimiter 实现：`autocoder/rag/token_limiter.py`
- Code Generate 实现：`autocoder/common/code_auto_generate_editblock.py`
- 文件检测：`autocoder/common/tokens/file_detector.py`
