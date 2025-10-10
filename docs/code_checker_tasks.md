# 代码检查功能开发任务清单

> 本文档将开发工作拆分为 10 个阶段，每个阶段包含多个可独立执行和测试的小任务。
> 每完成一个任务提交一次 git，确保进度可追踪、可回滚。

---

## Phase 1: 规则文件准备 ⏱️ 预计30分钟

### 📋 Task 1.1: 转换 backend.txt 为 backend_rules.md

**目标**: 将 `rules/backend.txt` 转换为结构化的 Markdown 格式

**步骤**:
1. 创建 `rules/backend_rules.md` 文件
2. 解析原 txt 文件中的规则
3. 按类别分组（应用开发架构、代码结构、异常处理、安全性等）
4. 为每条规则添加：
   - 规则ID（backend_001, backend_002...）
   - 标题和描述
   - 严重程度（error/warning/info）
   - 错误示例和正确示例（如适用）

**验收标准**:
- ✅ 文件结构清晰，按类别分组
- ✅ 每条规则有唯一 ID
- ✅ 所有原始规则都已转换
- ✅ 格式统一，便于程序解析

**测试方式**:
```bash
# 手动检查文件格式
cat rules/backend_rules.md

# 确认规则数量（应该有 77+ 条）
grep "^### 规则ID:" rules/backend_rules.md | wc -l
```

**提交信息**:
```bash
git add rules/backend_rules.md
git commit -m "feat(checker): 转换后端检查规则为 Markdown 格式

- 按类别组织规则
- 添加规则 ID 和严重程度
- 添加示例代码
"
```

---

### 📋 Task 1.2: 转换 frontend.txt 为 frontend_rules.md

**目标**: 将 `rules/frontend.txt` 转换为结构化的 Markdown 格式

**步骤**:
1. 创建 `rules/frontend_rules.md` 文件
2. 解析原 txt 文件中的规则
3. 按类别分组（应用开发架构、代码结构、布局规范、颜色规范等）
4. 为每条规则添加规则ID（frontend_001, frontend_002...）

**验收标准**:
- ✅ 文件结构清晰，按类别分组
- ✅ 每条规则有唯一 ID
- ✅ 所有原始规则都已转换
- ✅ 前端特定规则（如样式、布局）格式正确

**测试方式**:
```bash
# 确认规则数量（应该有 105+ 条）
grep "^### 规则ID:" rules/frontend_rules.md | wc -l
```

**提交信息**:
```bash
git add rules/frontend_rules.md
git commit -m "feat(checker): 转换前端检查规则为 Markdown 格式"
```

---

### 📋 Task 1.3: 创建规则配置文件

**目标**: 创建 `rules/rules_config.json` 用于规则管理

**步骤**:
1. 创建配置文件
2. 定义规则元数据结构
3. 配置默认启用的规则
4. 配置严重程度阈值

**配置文件示例**:
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
      "file_patterns": ["**/*.js", "**/*.jsx", "**/*.ts", "**/*.tsx", "**/*.vue"],
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

**验收标准**:
- ✅ JSON 格式正确
- ✅ 包含前后端规则集配置
- ✅ 包含全局设置

**测试方式**:
```bash
# 验证 JSON 格式
python -c "import json; json.load(open('rules/rules_config.json'))"
```

**提交信息**:
```bash
git add rules/rules_config.json
git commit -m "feat(checker): 添加规则配置文件"
```

---

## Phase 2: 类型定义和基础工具 ⏱️ 预计45分钟

### 📋 Task 2.1: 创建类型定义模块

**目标**: 创建 `autocoder/checker/types.py` 定义所有数据模型

**步骤**:
1. 创建 `autocoder/checker/` 目录
2. 创建 `__init__.py`
3. 创建 `types.py` 并定义：
   - `Severity` 枚举
   - `Rule` 类
   - `Issue` 类
   - `FileCheckResult` 类
   - `BatchCheckResult` 类
   - `CheckState` 类
   - `CodeChunk` 类
   - `FileFilters` 类

**代码框架**:
```python
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel
from datetime import datetime

class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class Rule(BaseModel):
    id: str
    category: str
    title: str
    description: str
    severity: Severity
    enabled: bool = True
    examples: Optional[str] = None

# ... 其他类定义
```

**验收标准**:
- ✅ 所有类型定义完整
- ✅ 使用 pydantic 进行数据验证
- ✅ 类型注解完整
- ✅ 有文档字符串

**测试方式**:
```python
# tests/checker/test_types.py
from autocoder.checker.types import Rule, Severity, Issue

def test_rule_creation():
    rule = Rule(
        id="test_001",
        category="测试",
        title="测试规则",
        description="这是一个测试",
        severity=Severity.WARNING
    )
    assert rule.id == "test_001"
    assert rule.enabled == True

def test_issue_creation():
    issue = Issue(
        rule_id="test_001",
        severity=Severity.ERROR,
        line_start=10,
        line_end=15,
        description="测试问题",
        suggestion="修复建议",
        code_snippet="code here"
    )
    assert issue.line_start == 10
```

**提交信息**:
```bash
git add autocoder/checker/
git commit -m "feat(checker): 添加核心数据模型定义

- 定义 Rule、Issue、FileCheckResult 等模型
- 使用 pydantic 进行数据验证
- 添加完整的类型注解
"
```

---

### 📋 Task 2.2: 创建进度跟踪器

**目标**: 创建 `autocoder/checker/progress_tracker.py` 管理检查进度

**步骤**:
1. 实现 `ProgressTracker` 类
2. 实现进度状态保存和加载
3. 实现中断恢复逻辑
4. 生成唯一的 check_id

**核心方法**:
```python
class ProgressTracker:
    def __init__(self, state_dir: str = ".auto-coder/codecheck/progress"):
        self.state_dir = state_dir
        os.makedirs(state_dir, exist_ok=True)

    def start_check(self, files: List[str], config: Dict) -> str:
        """开始新的检查，返回 check_id"""
        pass

    def mark_completed(self, check_id: str, file_path: str) -> None:
        """标记文件已完成检查"""
        pass

    def get_remaining_files(self, check_id: str) -> List[str]:
        """获取待检查的文件列表"""
        pass

    def save_state(self, check_id: str, state: CheckState) -> None:
        """保存检查状态"""
        pass

    def load_state(self, check_id: str) -> Optional[CheckState]:
        """加载检查状态"""
        pass

    def list_checks(self) -> List[Dict[str, Any]]:
        """列出所有检查记录"""
        pass
```

**验收标准**:
- ✅ 能正确保存和加载状态
- ✅ check_id 格式：`{project}_{timestamp}`
- ✅ 支持并发访问（使用文件锁）
- ✅ 能列出历史检查记录

**测试方式**:
```python
# tests/checker/test_progress_tracker.py
def test_progress_tracker():
    tracker = ProgressTracker()
    files = ["file1.py", "file2.py", "file3.py"]

    # 开始检查
    check_id = tracker.start_check(files, {})
    assert check_id.startswith("test_")

    # 标记完成
    tracker.mark_completed(check_id, "file1.py")

    # 获取剩余文件
    remaining = tracker.get_remaining_files(check_id)
    assert len(remaining) == 2
    assert "file1.py" not in remaining

    # 重新加载状态
    state = tracker.load_state(check_id)
    assert len(state.completed_files) == 1
```

**提交信息**:
```bash
git add autocoder/checker/progress_tracker.py tests/checker/test_progress_tracker.py
git commit -m "feat(checker): 实现进度跟踪器

- 支持检查状态保存和恢复
- 生成唯一 check_id
- 支持中断恢复
"
```

---

### 📋 Task 2.3: 运行单元测试

**目标**: 确保 Phase 2 的代码质量

**步骤**:
```bash
# 安装测试依赖（如需要）
pip install pytest pytest-cov

# 运行测试
pytest tests/checker/ -v --cov=autocoder/checker

# 查看覆盖率报告
```

**验收标准**:
- ✅ 所有测试通过
- ✅ 代码覆盖率 > 80%

---

## Phase 3: 规则加载器 ⏱️ 预计45分钟

### 📋 Task 3.1: 创建规则加载器骨架

**目标**: 创建 `autocoder/checker/rules_loader.py`

**步骤**:
1. 创建 `RulesLoader` 类
2. 实现初始化方法
3. 定义公共接口

**代码框架**:
```python
class RulesLoader:
    def __init__(self, rules_dir: str = "rules"):
        self.rules_dir = rules_dir
        self._rule_cache: Dict[str, List[Rule]] = {}

    def load_rules(self, rule_type: str) -> List[Rule]:
        """加载指定类型的规则（backend/frontend）"""
        pass

    def get_applicable_rules(self, file_path: str) -> List[Rule]:
        """根据文件路径获取适用的规则"""
        pass

    def reload_rules(self) -> None:
        """重新加载所有规则"""
        pass

    def _parse_markdown_rules(self, file_path: str) -> List[Rule]:
        """解析 Markdown 格式的规则文件"""
        pass
```

**提交信息**:
```bash
git add autocoder/checker/rules_loader.py
git commit -m "feat(checker): 创建规则加载器骨架"
```

---

### 📋 Task 3.2: 实现规则文件解析

**目标**: 实现 Markdown 规则文件的解析

**步骤**:
1. 实现 `_parse_markdown_rules` 方法
2. 解析规则 ID、标题、描述、严重程度
3. 提取示例代码

**解析逻辑**:
```python
def _parse_markdown_rules(self, file_path: str) -> List[Rule]:
    """解析 Markdown 格式的规则文件"""
    rules = []
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 按 "### 规则ID:" 分割
    sections = re.split(r'### 规则ID:\s*(\w+)', content)

    current_category = ""
    for i in range(1, len(sections), 2):
        rule_id = sections[i].strip()
        rule_content = sections[i+1]

        # 提取标题、描述、严重程度等
        # ...

        rules.append(Rule(...))

    return rules
```

**验收标准**:
- ✅ 能正确解析所有规则
- ✅ 规则数量与原始文件一致
- ✅ 所有字段都被正确提取

**测试方式**:
```python
def test_parse_backend_rules():
    loader = RulesLoader()
    rules = loader.load_rules("backend")
    assert len(rules) > 70
    assert all(r.id.startswith("backend_") for r in rules)
```

**提交信息**:
```bash
git add autocoder/checker/rules_loader.py
git commit -m "feat(checker): 实现 Markdown 规则文件解析"
```

---

### 📋 Task 3.3: 实现规则配置加载

**目标**: 支持从 `rules_config.json` 加载配置

**步骤**:
1. 加载配置文件
2. 应用 enabled/disabled 规则
3. 应用严重程度过滤

**验收标准**:
- ✅ 配置正确应用到规则
- ✅ 被禁用的规则不会被加载

**提交信息**:
```bash
git add autocoder/checker/rules_loader.py
git commit -m "feat(checker): 支持规则配置文件"
```

---

### 📋 Task 3.4: 规则加载器单元测试

**测试用例**:
```python
def test_load_backend_rules():
    """测试加载后端规则"""
    pass

def test_load_frontend_rules():
    """测试加载前端规则"""
    pass

def test_get_applicable_rules_for_python():
    """测试 Python 文件规则选择"""
    pass

def test_get_applicable_rules_for_javascript():
    """测试 JavaScript 文件规则选择"""
    pass

def test_rule_caching():
    """测试规则缓存"""
    pass
```

**提交信息**:
```bash
git add tests/checker/test_rules_loader.py
git commit -m "test(checker): 添加规则加载器单元测试"
```

---

## Phase 4: 文件处理器 ⏱️ 预计1小时

### 📋 Task 4.1: 创建文件处理器

**目标**: 创建 `autocoder/checker/file_processor.py`

**核心功能**:
- 文件扫描和过滤
- 大文件分块
- 文件类型检测

**代码框架**:
```python
class FileProcessor:
    def __init__(self, chunk_size: int = 4000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def scan_files(self, path: str, filters: FileFilters) -> List[str]:
        """扫描目录，返回符合条件的文件列表"""
        pass

    def chunk_file(self, file_path: str) -> List[CodeChunk]:
        """将大文件分块"""
        pass

    def is_checkable(self, file_path: str) -> bool:
        """判断文件是否可检查"""
        pass

    def add_line_numbers(self, content: str) -> str:
        """为代码添加行号"""
        pass
```

**提交信息**:
```bash
git add autocoder/checker/file_processor.py
git commit -m "feat(checker): 创建文件处理器骨架"
```

---

### 📋 Task 4.2: 实现文件扫描和过滤

**步骤**:
1. 使用 `pathlib` 遍历目录
2. 应用扩展名过滤
3. 应用忽略模式（类似 .gitignore）
4. 集成 `FileTypeDetector`

**验收标准**:
- ✅ 正确过滤文件
- ✅ 支持 glob 模式
- ✅ 排除二进制文件

**测试方式**:
```python
def test_scan_python_files():
    processor = FileProcessor()
    filters = FileFilters(extensions=[".py"], ignored=["__pycache__"])
    files = processor.scan_files("autocoder", filters)
    assert all(f.endswith(".py") for f in files)
```

**提交信息**:
```bash
git add autocoder/checker/file_processor.py
git commit -m "feat(checker): 实现文件扫描和过滤"
```

---

### 📋 Task 4.3: 实现大文件分块

**目标**: 复用 TokenLimiter 的思路实现文件分块

**步骤**:
1. 为代码添加行号
2. 计算 token 数量
3. 如果超过限制，分块处理
4. 保证 chunk 之间有重叠

**关键代码**:
```python
def chunk_file(self, file_path: str) -> List[CodeChunk]:
    """将文件分块，确保每块不超过 token 限制"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 添加行号
    numbered_lines = [f"{i+1} {line}" for i, line in enumerate(lines)]

    # 计算 tokens
    total_tokens = count_tokens('\n'.join(numbered_lines))

    if total_tokens <= self.chunk_size:
        # 不需要分块
        return [CodeChunk(
            content='\n'.join(numbered_lines),
            start_line=1,
            end_line=len(lines),
            chunk_index=0
        )]

    # 需要分块
    chunks = []
    current_line = 0
    chunk_index = 0

    while current_line < len(lines):
        # 计算当前 chunk 的结束行
        end_line = self._calculate_chunk_end(
            numbered_lines, current_line, self.chunk_size
        )

        # 创建 chunk
        chunk_content = '\n'.join(numbered_lines[current_line:end_line])
        chunks.append(CodeChunk(
            content=chunk_content,
            start_line=current_line + 1,
            end_line=end_line,
            chunk_index=chunk_index
        ))

        # 移动到下一个 chunk（考虑重叠）
        current_line = end_line - self.overlap
        chunk_index += 1

    return chunks
```

**验收标准**:
- ✅ 小文件不分块
- ✅ 大文件正确分块
- ✅ chunk 之间有重叠
- ✅ 行号连续且正确

**测试方式**:
```python
def test_chunk_small_file():
    """小文件不应该分块"""
    processor = FileProcessor(chunk_size=10000)
    chunks = processor.chunk_file("small_file.py")
    assert len(chunks) == 1

def test_chunk_large_file():
    """大文件应该被正确分块"""
    processor = FileProcessor(chunk_size=1000, overlap=100)
    chunks = processor.chunk_file("large_file.py")
    assert len(chunks) > 1
    # 验证重叠
    assert chunks[0].end_line - chunks[1].start_line == 100
```

**提交信息**:
```bash
git add autocoder/checker/file_processor.py
git commit -m "feat(checker): 实现大文件分块机制

- 支持按 token 数量分块
- chunk 之间有重叠避免边界问题
- 保持行号连续性
"
```

---

### 📋 Task 4.4: 文件处理器单元测试

**提交信息**:
```bash
git add tests/checker/test_file_processor.py
git commit -m "test(checker): 添加文件处理器单元测试"
```

---

## Phase 5: 核心检查逻辑 ⏱️ 预计1.5小时

### 📋 Task 5.1: 创建核心检查器

**目标**: 创建 `autocoder/checker/core.py`

**代码框架**:
```python
class CodeChecker:
    def __init__(self, llm: byzerllm.ByzerLLM, args: AutoCoderArgs):
        self.llm = llm
        self.args = args
        self.rules_loader = RulesLoader()
        self.file_processor = FileProcessor()
        self.progress_tracker = ProgressTracker()

    def check_file(self, file_path: str) -> FileCheckResult:
        """检查单个文件"""
        pass

    def check_files(self, files: List[str]) -> BatchCheckResult:
        """批量检查文件"""
        pass

    def check_code_chunk(
        self, code: str, rules: List[Rule]
    ) -> List[Issue]:
        """检查代码块"""
        pass
```

**提交信息**:
```bash
git add autocoder/checker/core.py
git commit -m "feat(checker): 创建核心检查器骨架"
```

---

### 📋 Task 5.2: 设计检查 Prompt

**目标**: 设计并实现 LLM Prompt

**Prompt 模板**:
```python
@byzerllm.prompt()
def check_code_prompt(self, code_with_lines: str, rules: str) -> str:
    """
    你是一个代码审查专家。请根据提供的规则检查代码，找出不符合规范的地方。

    ## 检查规则

    {{ rules }}

    ## 待检查代码（带行号）

    ```
    {{ code_with_lines }}
    ```

    ## 输出要求

    请仔细检查代码，对于每个发现的问题：
    1. 准确定位问题的起始和结束行号
    2. 引用违反的规则ID
    3. 描述问题
    4. 提供修复建议

    以 JSON 数组格式输出，每个问题包含：
    - rule_id: 违反的规则ID
    - severity: 严重程度 (error/warning/info)
    - line_start: 问题起始行号（整数）
    - line_end: 问题结束行号（整数）
    - description: 问题描述
    - suggestion: 修复建议

    如果没有发现问题，返回空数组 []

    示例输出：
    ```json
    [
        {
            "rule_id": "backend_006",
            "severity": "warning",
            "line_start": 15,
            "line_end": 32,
            "description": "发现复杂的 if-else 嵌套",
            "suggestion": "建议将内层逻辑抽取为独立方法"
        }
    ]
    ```
    """
```

**提交信息**:
```bash
git add autocoder/checker/core.py
git commit -m "feat(checker): 设计代码检查 Prompt"
```

---

### 📋 Task 5.3: 实现单文件检查

**步骤**:
1. 加载适用规则
2. 读取文件并添加行号
3. 判断是否需要分块
4. 调用 LLM 检查
5. 解析结果
6. 返回 `FileCheckResult`

**关键代码**:
```python
def check_file(self, file_path: str) -> FileCheckResult:
    """检查单个文件"""
    try:
        start_time = datetime.now()

        # 1. 获取适用规则
        rules = self.rules_loader.get_applicable_rules(file_path)
        if not rules:
            return FileCheckResult(
                file_path=file_path,
                check_time=start_time.isoformat(),
                issues=[],
                error_count=0,
                warning_count=0,
                info_count=0,
                status="skipped"
            )

        # 2. 分块处理
        chunks = self.file_processor.chunk_file(file_path)

        # 3. 检查每个 chunk
        all_issues = []
        for chunk in chunks:
            issues = self.check_code_chunk(chunk.content, rules)
            all_issues.extend(issues)

        # 4. 合并重复问题
        merged_issues = self._merge_duplicate_issues(all_issues)

        # 5. 统计
        error_count = sum(1 for i in merged_issues if i.severity == Severity.ERROR)
        warning_count = sum(1 for i in merged_issues if i.severity == Severity.WARNING)
        info_count = sum(1 for i in merged_issues if i.severity == Severity.INFO)

        return FileCheckResult(
            file_path=file_path,
            check_time=datetime.now().isoformat(),
            issues=merged_issues,
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count,
            status="success"
        )

    except Exception as e:
        return FileCheckResult(
            file_path=file_path,
            check_time=datetime.now().isoformat(),
            issues=[],
            error_count=0,
            warning_count=0,
            info_count=0,
            status="failed",
            error_message=str(e)
        )
```

**提交信息**:
```bash
git add autocoder/checker/core.py
git commit -m "feat(checker): 实现单文件检查逻辑"
```

---

### 📋 Task 5.4: 实现 chunk 结果合并

**目标**: 合并多个 chunk 的检查结果，去重

**算法**:
```python
def _merge_duplicate_issues(self, issues: List[Issue]) -> List[Issue]:
    """合并重复的问题"""
    # 按 rule_id 和行号范围合并
    merged = {}
    for issue in issues:
        key = (issue.rule_id, issue.line_start, issue.line_end)
        if key not in merged:
            merged[key] = issue
        # 如果重复，保留描述更详细的
        elif len(issue.description) > len(merged[key].description):
            merged[key] = issue

    return list(merged.values())
```

**提交信息**:
```bash
git add autocoder/checker/core.py
git commit -m "feat(checker): 实现检查结果合并逻辑"
```

---

### 📋 Task 5.5: 核心检查器单元测试（使用 mock）

**测试策略**: 使用 mock LLM 避免实际调用

```python
from unittest.mock import Mock, patch

def test_check_file_with_mock_llm():
    # Mock LLM 返回
    mock_llm = Mock()
    mock_response = """
    ```json
    [
        {
            "rule_id": "backend_001",
            "severity": "error",
            "line_start": 10,
            "line_end": 15,
            "description": "测试问题",
            "suggestion": "测试建议"
        }
    ]
    ```
    """

    with patch.object(CodeChecker, 'check_code_chunk', return_value=[...]):
        checker = CodeChecker(mock_llm, args)
        result = checker.check_file("test.py")

        assert result.status == "success"
        assert len(result.issues) == 1
```

**提交信息**:
```bash
git add tests/checker/test_core.py
git commit -m "test(checker): 添加核心检查器单元测试"
```

---

## Phase 6: 报告生成器 ⏱️ 预计1小时

### 📋 Task 6.1: 创建报告生成器

**目标**: 创建 `autocoder/checker/report_generator.py`

**代码框架**:
```python
class ReportGenerator:
    def __init__(self, output_dir: str = "codecheck"):
        self.output_dir = output_dir

    def generate_file_report(
        self, result: FileCheckResult, report_dir: str
    ) -> None:
        """生成单个文件的检查报告"""
        pass

    def generate_summary_report(
        self, results: List[FileCheckResult], report_dir: str
    ) -> None:
        """生成汇总报告"""
        pass

    def _generate_json_report(self, data: Dict, output_path: str) -> None:
        """生成 JSON 格式报告"""
        pass

    def _generate_markdown_report(self, data: Dict, output_path: str) -> None:
        """生成 Markdown 格式报告"""
        pass
```

**提交信息**:
```bash
git add autocoder/checker/report_generator.py
git commit -m "feat(checker): 创建报告生成器骨架"
```

---

### 📋 Task 6.2: 实现 JSON 报告生成

**步骤**:
1. 实现文件报告 JSON 生成
2. 实现汇总报告 JSON 生成
3. 确保目录结构正确

**验收标准**:
- ✅ JSON 格式正确
- ✅ 包含所有必要信息
- ✅ 文件路径转换正确（斜杠替换）

**提交信息**:
```bash
git add autocoder/checker/report_generator.py
git commit -m "feat(checker): 实现 JSON 报告生成"
```

---

### 📋 Task 6.3: 实现 Markdown 报告生成

**步骤**:
1. 设计 Markdown 模板
2. 实现文件报告 Markdown 生成
3. 实现汇总报告 Markdown 生成
4. 添加代码高亮

**Markdown 模板示例**:
```python
def _generate_file_markdown(self, result: FileCheckResult) -> str:
    md = f"""# 文件检查报告: {result.file_path}

**检查时间**: {result.check_time}
**问题数量**: {len(result.issues)} (错误: {result.error_count}, 警告: {result.warning_count}, 提示: {result.info_count})

---

"""

    # 按严重程度分组
    errors = [i for i in result.issues if i.severity == Severity.ERROR]
    warnings = [i for i in result.issues if i.severity == Severity.WARNING]
    infos = [i for i in result.issues if i.severity == Severity.INFO]

    if errors:
        md += "## ❌ 错误\n\n"
        for idx, issue in enumerate(errors, 1):
            md += self._format_issue_markdown(idx, issue)

    # ... 类似处理 warnings 和 infos

    return md
```

**提交信息**:
```bash
git add autocoder/checker/report_generator.py
git commit -m "feat(checker): 实现 Markdown 报告生成"
```

---

### 📋 Task 6.4: 报告生成器单元测试

**提交信息**:
```bash
git add tests/checker/test_report_generator.py
git commit -m "test(checker): 添加报告生成器单元测试"
```

---

## Phase 7: 插件开发 ⏱️ 预计1.5小时

### 📋 Task 7.1: 创建插件文件

**目标**: 创建 `autocoder/plugins/code_checker_plugin.py`

**代码框架**:
```python
from autocoder.plugins import Plugin
from autocoder.checker.core import CodeChecker
from autocoder.checker.types import FileFilters

class CodeCheckerPlugin(Plugin):
    name = "code_checker"
    description = "代码规范检查插件"
    version = "1.0.0"

    def initialize(self) -> bool:
        """初始化插件"""
        self.checker = CodeChecker(...)
        return True

    def get_commands(self):
        """注册命令"""
        return {
            "check": (self.handle_check, "代码检查命令"),
        }

    def handle_check(self, args: str):
        """处理 /check 命令"""
        pass
```

**提交信息**:
```bash
git add autocoder/plugins/code_checker_plugin.py
git commit -m "feat(checker): 创建代码检查插件骨架"
```

---

### 📋 Task 7.2: 实现 /check /file 命令

**步骤**:
1. 解析命令参数
2. 调用 `checker.check_file()`
3. 生成报告
4. 显示结果摘要

**命令处理**:
```python
def handle_check(self, args: str):
    """处理 /check 命令"""
    parts = args.strip().split(maxsplit=1)

    if not parts:
        print(self._show_help())
        return

    subcommand = parts[0]

    if subcommand == "/file":
        if len(parts) < 2:
            print("用法: /check /file <filename>")
            return

        file_path = parts[1].strip()
        self._check_single_file(file_path)

    # ... 其他子命令

def _check_single_file(self, file_path: str):
    """检查单个文件"""
    print(f"正在检查文件: {file_path}")

    result = self.checker.check_file(file_path)

    if result.status == "success":
        print(f"\n✅ 检查完成！")
        print(f"   发现问题: {len(result.issues)}")
        print(f"   错误: {result.error_count}")
        print(f"   警告: {result.warning_count}")
        print(f"   提示: {result.info_count}")

        # 生成报告
        report_dir = self._create_report_dir()
        self.report_generator.generate_file_report(result, report_dir)
        print(f"\n📄 报告已保存到: {report_dir}")
    else:
        print(f"❌ 检查失败: {result.error_message}")
```

**验收标准**:
- ✅ 命令参数解析正确
- ✅ 能成功检查文件
- ✅ 显示友好的输出

**测试方式**:
```bash
# 在 chat_auto_coder 中测试
/check /file autocoder/auto_coder.py
```

**提交信息**:
```bash
git add autocoder/plugins/code_checker_plugin.py
git commit -m "feat(checker): 实现 /check /file 命令"
```

---

### 📋 Task 7.3: 实现 /check /folder 命令

**步骤**:
1. 解析目录路径和过滤选项
2. 扫描文件
3. 调用 `checker.check_files()`
4. 显示进度
5. 生成汇总报告

**命令示例**:
```bash
/check /folder                              # 检查当前目录
/check /folder /path src                    # 检查 src 目录
/check /folder /ext .py,.js                 # 只检查 .py 和 .js
/check /folder /ignore tests,__pycache__    # 忽略目录
```

**实现**:
```python
def _check_folder(self, args: str):
    """检查目录"""
    # 解析参数
    options = self._parse_folder_options(args)

    # 扫描文件
    files = self.file_processor.scan_files(
        options["path"],
        FileFilters(
            extensions=options.get("extensions"),
            ignored=options.get("ignored")
        )
    )

    if not files:
        print("没有找到可检查的文件")
        return

    print(f"找到 {len(files)} 个文件")

    # 创建检查任务
    check_id = self.progress_tracker.start_check(files, options)

    # 批量检查（带进度显示）
    results = []
    with Progress(...) as progress:
        task = progress.add_task("检查文件...", total=len(files))

        for file in files:
            result = self.checker.check_file(file)
            results.append(result)
            self.progress_tracker.mark_completed(check_id, file)
            progress.update(task, advance=1)

    # 生成汇总报告
    report_dir = self._create_report_dir()
    self.report_generator.generate_summary_report(results, report_dir)

    # 显示汇总
    self._show_summary(results, report_dir)
```

**提交信息**:
```bash
git add autocoder/plugins/code_checker_plugin.py
git commit -m "feat(checker): 实现 /check /folder 命令"
```

---

### 📋 Task 7.4: 实现命令补全

**步骤**:
1. 实现 `get_completions()` 方法
2. 为子命令提供补全选项
3. 为文件路径提供补全

**实现**:
```python
def get_completions(self):
    """提供命令补全"""
    return {
        "/check": ["/file", "/folder", "/resume", "/report"],
        "/check /folder": ["/path", "/ext", "/ignore", "/workers"],
    }

def get_dynamic_completions(self, command: str, current_input: str):
    """动态补全（如文件路径）"""
    if command == "/check /file":
        # 补全文件路径
        return self._complete_file_path(current_input)

    return []
```

**提交信息**:
```bash
git add autocoder/plugins/code_checker_plugin.py
git commit -m "feat(checker): 实现命令补全功能"
```

---

### 📋 Task 7.5: 插件集成测试

**测试步骤**:
1. 启动 chat_auto_coder
2. 测试所有命令
3. 验证报告生成
4. 验证命令补全

**测试清单**:
```bash
# 1. 单文件检查
/check /file autocoder/auto_coder.py

# 2. 目录检查
/check /folder

# 3. 带过滤的目录检查
/check /folder /ext .py /ignore tests

# 4. 命令补全测试
/check <TAB>
/check /folder <TAB>
```

**提交信息**:
```bash
git commit -m "test(checker): 完成插件集成测试"
```

---

## Phase 8: 进度持久化和恢复 ⏱️ 预计1小时

### 📋 Task 8.1: 完善检查状态保存

**步骤**:
1. 在检查过程中定期保存状态
2. 保存检查配置
3. 保存已完成和待完成文件列表

**实现**:
```python
def check_files_with_resume(self, files: List[str], config: Dict) -> BatchCheckResult:
    """支持中断恢复的批量检查"""
    # 创建检查任务
    check_id = self.progress_tracker.start_check(files, config)

    results = []
    for file in files:
        try:
            result = self.check_file(file)
            results.append(result)

            # 标记完成并保存状态
            self.progress_tracker.mark_completed(check_id, file)
            self.progress_tracker.save_state(check_id, CheckState(...))

        except KeyboardInterrupt:
            print(f"\n⚠️  检查已中断")
            print(f"   检查 ID: {check_id}")
            print(f"   使用 /check /resume {check_id} 继续")
            break

    return BatchCheckResult(...)
```

**提交信息**:
```bash
git add autocoder/checker/core.py autocoder/checker/progress_tracker.py
git commit -m "feat(checker): 完善检查状态保存机制"
```

---

### 📋 Task 8.2: 实现中断恢复逻辑

**步骤**:
1. 加载检查状态
2. 获取剩余文件
3. 继续检查
4. 合并之前的结果

**实现**:
```python
def resume_check(self, check_id: str) -> BatchCheckResult:
    """恢复中断的检查"""
    # 加载状态
    state = self.progress_tracker.load_state(check_id)
    if not state:
        raise ValueError(f"检查记录不存在: {check_id}")

    # 获取剩余文件
    remaining_files = state.remaining_files

    print(f"恢复检查: {check_id}")
    print(f"剩余文件: {len(remaining_files)}/{len(state.total_files)}")

    # 继续检查
    return self.check_files_with_resume(remaining_files, state.config)
```

**提交信息**:
```bash
git add autocoder/checker/core.py
git commit -m "feat(checker): 实现检查中断恢复逻辑"
```

---

### 📋 Task 8.3: 实现 /check /resume 命令

**步骤**:
1. 在插件中添加 `/resume` 子命令
2. 解析 check_id
3. 调用恢复逻辑

**实现**:
```python
def handle_check(self, args: str):
    # ...
    elif subcommand == "/resume":
        if len(parts) < 2:
            # 显示可恢复的检查列表
            self._list_resumable_checks()
        else:
            check_id = parts[1].strip()
            self._resume_check(check_id)

def _list_resumable_checks(self):
    """列出可恢复的检查"""
    checks = self.progress_tracker.list_checks()
    incomplete = [c for c in checks if c["status"] == "incomplete"]

    if not incomplete:
        print("没有可恢复的检查")
        return

    print("可恢复的检查:\n")
    for check in incomplete:
        print(f"  ID: {check['check_id']}")
        print(f"  时间: {check['start_time']}")
        print(f"  进度: {check['completed']}/{check['total']}")
        print()

def _resume_check(self, check_id: str):
    """恢复检查"""
    result = self.checker.resume_check(check_id)
    # 生成报告
    # ...
```

**提交信息**:
```bash
git add autocoder/plugins/code_checker_plugin.py
git commit -m "feat(checker): 实现 /check /resume 命令"
```

---

### 📋 Task 8.4: 中断恢复集成测试

**测试步骤**:
1. 开始一个目录检查
2. 中途按 Ctrl+C 中断
3. 使用 `/check /resume` 恢复
4. 验证结果完整性

**提交信息**:
```bash
git commit -m "test(checker): 完成中断恢复集成测试"
```

---

## Phase 9: 并发优化和进度显示 ⏱️ 预计45分钟

### 📋 Task 9.1: 实现并发检查

**步骤**:
1. 使用 ThreadPoolExecutor
2. 支持可配置的并发数
3. 保证线程安全

**实现**:
```python
def check_files_concurrent(
    self, files: List[str], max_workers: int = 5
) -> List[FileCheckResult]:
    """并发检查多个文件"""
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(self.check_file, file): file
            for file in files
        }

        for future in as_completed(future_to_file):
            file = future_to_file[future]
            try:
                result = future.result()
                results.append(result)
                # 更新进度
                yield result
            except Exception as exc:
                logger.error(f"检查文件 {file} 失败: {exc}")
                results.append(FileCheckResult(
                    file_path=file,
                    status="failed",
                    error_message=str(exc),
                    # ...
                ))

    return results
```

**提交信息**:
```bash
git add autocoder/checker/core.py
git commit -m "feat(checker): 实现并发检查逻辑"
```

---

### 📋 Task 9.2: 添加 rich 进度条

**步骤**:
1. 集成 `rich.progress`
2. 显示当前文件
3. 显示进度百分比
4. 显示预计剩余时间

**实现**:
```python
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
)

def check_with_progress(self, files: List[str], max_workers: int = 5):
    """带进度显示的检查"""
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
    ) as progress:
        task = progress.add_task(
            "正在检查文件...",
            total=len(files)
        )

        results = []
        for result in self.check_files_concurrent(files, max_workers):
            results.append(result)
            progress.update(
                task,
                advance=1,
                description=f"检查 {result.file_path}"
            )

        return results
```

**提交信息**:
```bash
git add autocoder/checker/core.py autocoder/plugins/code_checker_plugin.py
git commit -m "feat(checker): 添加 rich 进度条显示"
```

---

### 📋 Task 9.3: 性能测试和优化

**测试**:
1. 测试不同并发数的性能
2. 测试大型项目（100+ 文件）
3. 调整默认参数

**性能指标**:
- 单文件平均检查时间
- 并发提升比例
- 内存占用

**提交信息**:
```bash
git commit -m "perf(checker): 性能测试和优化"
```

---

## Phase 10: 文档和收尾 ⏱️ 预计30分钟

### 📋 Task 10.1: 创建用户文档

**目标**: 创建 `docs/code_checker_usage.md`

**内容**:
- 功能介绍
- 安装说明
- 使用示例
- 命令参考
- 配置选项
- 常见问题

**提交信息**:
```bash
git add docs/code_checker_usage.md
git commit -m "docs(checker): 添加用户使用文档"
```

---

### 📋 Task 10.2: 更新项目文档

**步骤**:
1. 更新 `CLAUDE.md`，添加代码检查功能说明
2. 更新 README（如有）

**提交信息**:
```bash
git add CLAUDE.md
git commit -m "docs: 更新项目文档，添加代码检查功能"
```

---

### 📋 Task 10.3: 创建二次开发文档

**目标**: 创建 `docs/code_checker_development.md`

**内容**:
- 架构说明
- 模块关系
- 添加新规则
- 扩展新功能
- API 参考

**提交信息**:
```bash
git add docs/code_checker_development.md
git commit -m "docs(checker): 添加二次开发指南"
```

---

## 🎯 总结

### 任务统计

| 阶段 | 任务数 | 预计时间 | 关键产出 |
|------|--------|----------|----------|
| Phase 1 | 3 | 30分钟 | 规则文件 + 配置 |
| Phase 2 | 3 | 45分钟 | 类型定义 + 进度跟踪 |
| Phase 3 | 4 | 45分钟 | 规则加载器 |
| Phase 4 | 4 | 1小时 | 文件处理器 |
| Phase 5 | 5 | 1.5小时 | 核心检查逻辑 |
| Phase 6 | 4 | 1小时 | 报告生成器 |
| Phase 7 | 5 | 1.5小时 | 插件开发 |
| Phase 8 | 4 | 1小时 | 中断恢复 |
| Phase 9 | 3 | 45分钟 | 并发优化 |
| Phase 10 | 3 | 30分钟 | 文档完善 |
| **总计** | **38** | **8.5小时** | - |

### 验收标准

每个阶段完成后，需确保：
- ✅ 所有单元测试通过
- ✅ 代码提交到 git
- ✅ 功能可独立演示
- ✅ 文档已更新

### 使用方式

完成后，用户可以这样使用：

```bash
# 启动 chat_auto_coder
python -m autocoder.chat_auto_coder

# 检查单个文件
/check /file src/main.py

# 检查整个项目
/check /folder

# 检查指定目录，过滤文件
/check /folder /path src /ext .py /ignore tests,__pycache__

# 查看检查报告
ls codecheck/

# 中断后恢复
/check /resume cuscli_20250110_143022
```

### 后续优化方向

1. **规则管理界面**：Web UI 管理规则
2. **自定义规则**：支持用户自定义规则
3. **修复建议应用**：一键应用修复建议
4. **CI/CD 集成**：支持在 CI 中运行
5. **性能优化**：缓存、增量检查

---

**准备好了吗？让我们从 Phase 1 Task 1.1 开始！** 🚀
