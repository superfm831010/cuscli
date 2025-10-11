# 代码检查功能二次开发指南

> 面向开发者的代码检查系统架构、扩展和定制指南

## 📋 目录

- [架构概览](#架构概览)
- [核心模块详解](#核心模块详解)
- [插件系统](#插件系统)
- [添加新规则](#添加新规则)
- [扩展新功能](#扩展新功能)
- [API 参考](#api-参考)
- [测试指南](#测试指南)

---

## 架构概览

### 系统架构图

```
┌─────────────────────────────────────────────────────────┐
│                    Chat Auto Coder                      │
│                     (主应用)                             │
└────────────────────┬────────────────────────────────────┘
                     │
                     │ 加载插件
                     ▼
┌─────────────────────────────────────────────────────────┐
│              CodeCheckerPlugin                          │
│            (命令注册和调度)                              │
│  - 注册 /check 命令                                      │
│  - 解析参数                                              │
│  - 调用检查器                                            │
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
        │  - 协调各模块          │
        │  - 调用 LLM           │
        │  - 结果处理            │
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

### 模块关系

| 模块 | 文件 | 职责 | 依赖 |
|------|------|------|------|
| **插件** | `code_checker_plugin.py` | 命令注册、参数解析 | CodeChecker |
| **核心检查器** | `core.py` | 检查逻辑、LLM 调用 | 所有模块 |
| **规则加载器** | `rules_loader.py` | 规则文件解析 | types.py |
| **文件处理器** | `file_processor.py` | 文件扫描、分块 | types.py |
| **进度跟踪器** | `progress_tracker.py` | 进度持久化 | types.py |
| **报告生成器** | `report_generator.py` | 报告生成 | types.py |
| **类型定义** | `types.py` | 数据模型 | pydantic |

### 数据流

```
1. 用户输入命令
   ↓
2. Plugin 解析参数
   ↓
3. CodeChecker.check_file() 或 check_files()
   ↓
4. RulesLoader 加载规则
   ↓
5. FileProcessor 扫描/分块文件
   ↓
6. CodeChecker 调用 LLM 检查
   ↓
7. 解析 LLM 返回的 JSON
   ↓
8. ReportGenerator 生成报告
   ↓
9. ProgressTracker 保存进度
   ↓
10. 返回结果给用户
```

---

## 核心模块详解

### 1. types.py - 类型定义

**位置**：`autocoder/checker/types.py`

**核心类型**：

#### Severity - 严重程度枚举

```python
class Severity(str, Enum):
    ERROR = "error"      # 错误：必须修复
    WARNING = "warning"  # 警告：建议修复
    INFO = "info"        # 提示：可选修复
```

#### Rule - 规则定义

```python
class Rule(BaseModel):
    id: str                    # 规则ID，如 "backend_001"
    category: str              # 规则类别，如 "代码结构"
    title: str                 # 规则标题
    description: str           # 规则描述
    severity: Severity         # 严重程度
    enabled: bool = True       # 是否启用
    examples: Optional[str]    # 示例代码
```

#### Issue - 检查问题

```python
class Issue(BaseModel):
    rule_id: str              # 违反的规则ID
    severity: Severity        # 严重程度
    line_start: int           # 问题起始行号
    line_end: int             # 问题结束行号
    description: str          # 问题描述
    suggestion: str           # 修复建议
    code_snippet: str         # 问题代码片段
```

#### FileCheckResult - 文件检查结果

```python
class FileCheckResult(BaseModel):
    file_path: str                # 文件路径
    check_time: str              # 检查时间
    issues: List[Issue]          # 问题列表
    error_count: int             # 错误数量
    warning_count: int           # 警告数量
    info_count: int              # 提示数量
    status: str                  # "success" | "failed" | "skipped"
    error_message: Optional[str] # 错误信息（如果失败）
```

#### CheckState - 检查状态（用于持久化）

```python
class CheckState(BaseModel):
    check_id: str                  # 检查ID
    start_time: str               # 开始时间
    config: Dict[str, Any]        # 配置参数
    total_files: List[str]        # 总文件列表
    completed_files: List[str]    # 已完成文件
    remaining_files: List[str]    # 剩余文件
```

**扩展建议**：
- 添加新的严重程度级别（如 CRITICAL）
- 添加规则分组（RuleGroup）
- 添加检查统计信息（CheckStatistics）

---

### 2. rules_loader.py - 规则加载器

**位置**：`autocoder/checker/rules_loader.py`

**核心功能**：
- 加载 Markdown 格式的规则文件
- 解析规则配置
- 根据文件类型选择适用规则
- 规则缓存优化

**关键方法**：

#### load_rules() - 加载规则

```python
def load_rules(self, rule_type: str) -> List[Rule]:
    """
    加载指定类型的规则

    Args:
        rule_type: 规则类型（backend/frontend）

    Returns:
        规则列表
    """
    # 1. 检查缓存
    if rule_type in self._rule_cache:
        return self._rule_cache[rule_type]

    # 2. 加载规则文件
    rule_file = os.path.join(self.rules_dir, f"{rule_type}_rules.md")
    rules = self._parse_markdown_rules(rule_file)

    # 3. 应用配置
    rules = self._apply_config(rules, rule_type)

    # 4. 缓存结果
    self._rule_cache[rule_type] = rules

    return rules
```

#### _parse_markdown_rules() - 解析 Markdown 规则

```python
def _parse_markdown_rules(self, file_path: str) -> List[Rule]:
    """
    解析 Markdown 格式的规则文件

    规则格式：
    ### 规则ID: backend_001
    **标题**: 规则标题
    **严重程度**: warning
    **描述**: 规则描述
    """
    rules = []

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 按 "### 规则ID:" 分割
    sections = re.split(r'### 规则ID:\s*(\w+)', content)

    current_category = ""

    for i in range(1, len(sections), 2):
        rule_id = sections[i].strip()
        rule_content = sections[i+1]

        # 提取字段
        title = self._extract_field(rule_content, "标题")
        severity = self._extract_field(rule_content, "严重程度")
        description = self._extract_field(rule_content, "描述")

        # 提取示例
        examples = self._extract_examples(rule_content)

        rules.append(Rule(
            id=rule_id,
            category=current_category,
            title=title,
            description=description,
            severity=Severity(severity),
            examples=examples
        ))

    return rules
```

**扩展建议**：
- 支持 YAML/JSON 格式的规则文件
- 支持规则继承和覆盖
- 支持规则优先级
- 支持动态规则（从数据库加载）

---

### 3. file_processor.py - 文件处理器

**位置**：`autocoder/checker/file_processor.py`

**核心功能**：
- 文件扫描和过滤
- 大文件分块
- 文件类型检测

**关键方法**：

#### scan_files() - 扫描文件

```python
def scan_files(self, path: str, filters: FileFilters) -> List[str]:
    """
    扫描目录，返回符合条件的文件列表

    Args:
        path: 扫描路径
        filters: 文件过滤器（扩展名、忽略模式）

    Returns:
        文件路径列表
    """
    files = []

    for root, dirs, filenames in os.walk(path):
        # 过滤忽略的目录
        dirs[:] = [d for d in dirs if not self._should_ignore(d, filters.ignored)]

        for filename in filenames:
            file_path = os.path.join(root, filename)

            # 检查扩展名
            if filters.extensions:
                if not any(file_path.endswith(ext) for ext in filters.extensions):
                    continue

            # 检查忽略模式
            if self._should_ignore(file_path, filters.ignored):
                continue

            # 检查是否可检查
            if self.is_checkable(file_path):
                files.append(file_path)

    return files
```

#### chunk_file() - 文件分块

```python
def chunk_file(self, file_path: str) -> List[CodeChunk]:
    """
    将大文件分块，确保每块不超过 token 限制

    策略：
    1. 为每行添加行号
    2. 计算总 token 数
    3. 如果超过限制，按 token 分块
    4. 块之间有重叠，避免边界问题
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 添加行号
    numbered_lines = [f"{i+1} {line}" for i, line in enumerate(lines)]

    # 计算 tokens
    total_tokens = count_tokens('\n'.join(numbered_lines))

    # 不需要分块
    if total_tokens <= self.chunk_size:
        return [CodeChunk(
            content='\n'.join(numbered_lines),
            start_line=1,
            end_line=len(lines),
            chunk_index=0,
            total_chunks=1
        )]

    # 需要分块
    chunks = []
    current_line = 0
    chunk_index = 0

    while current_line < len(numbered_lines):
        # 计算当前 chunk 的结束行
        end_line = self._calculate_chunk_end(
            numbered_lines,
            current_line,
            self.chunk_size
        )

        # 创建 chunk
        chunk_content = '\n'.join(numbered_lines[current_line:end_line])
        chunks.append(CodeChunk(
            content=chunk_content,
            start_line=current_line + 1,
            end_line=end_line,
            chunk_index=chunk_index,
            total_chunks=0  # 稍后更新
        ))

        # 移动到下一个 chunk（考虑重叠）
        current_line = end_line - self.overlap
        chunk_index += 1

    # 更新总 chunk 数
    for chunk in chunks:
        chunk.total_chunks = len(chunks)

    return chunks
```

**扩展建议**：
- 支持智能分块（按函数/类边界）
- 支持增量检查（只检查修改的文件）
- 支持 Git diff 集成
- 支持文件内容缓存

---

### 4. core.py - 核心检查器

**位置**：`autocoder/checker/core.py`

**核心功能**：
- 协调各模块完成检查
- 调用 LLM 进行代码检查
- 处理检查结果
- 管理并发执行

**关键方法**：

#### check_file() - 单文件检查

```python
def check_file(self, file_path: str) -> FileCheckResult:
    """
    检查单个文件

    流程：
    1. 加载适用规则
    2. 读取文件并分块
    3. 检查每个 chunk
    4. 合并结果
    5. 返回检查结果
    """
    try:
        start_time = datetime.now()

        # 1. 获取适用规则
        rules = self.rules_loader.get_applicable_rules(file_path)
        if not rules:
            return FileCheckResult(
                file_path=file_path,
                check_time=start_time.isoformat(),
                issues=[],
                status="skipped"
            )

        # 2. 分块处理
        chunks = self.file_processor.chunk_file(file_path)
        logger.info(f"文件 {file_path} 被分为 {len(chunks)} 个 chunks")

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
        logger.error(f"检查文件 {file_path} 失败: {e}")
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

#### check_code_chunk() - 检查代码块

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

def check_code_chunk(self, code: str, rules: List[Rule]) -> List[Issue]:
    """调用 LLM 检查代码块"""
    # 格式化规则
    rules_text = self._format_rules(rules)

    # 调用 LLM
    response = self.llm.chat_oai(
        conversations=[{
            "role": "user",
            "content": self.check_code_prompt(code, rules_text)
        }]
    )[0].output

    # 解析 JSON
    issues = self._parse_llm_response(response)

    return issues
```

#### check_files_concurrent() - 并发检查

```python
def check_files_concurrent(
    self, files: List[str], max_workers: int = 5
) -> Generator[FileCheckResult, None, None]:
    """
    并发检查多个文件

    使用 ThreadPoolExecutor 实现并发检查，提高大型项目的检查速度。
    使用生成器模式按完成顺序实时返回结果，适合与进度条配合使用。

    Args:
        files: 文件列表
        max_workers: 最大并发数

    Yields:
        FileCheckResult: 按完成顺序返回检查结果
    """
    logger.info(f"开始并发检查 {len(files)} 个文件 (workers={max_workers})")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_file = {
            executor.submit(self.check_file, file_path): file_path
            for file_path in files
        }

        # 按完成顺序返回结果
        for future in as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                result = future.result()
                yield result
            except Exception as exc:
                logger.error(f"文件 {file_path} 检查失败: {exc}")
                yield FileCheckResult(
                    file_path=file_path,
                    check_time=datetime.now().isoformat(),
                    issues=[],
                    error_count=0,
                    warning_count=0,
                    info_count=0,
                    status="failed",
                    error_message=str(exc)
                )
```

**扩展建议**：
- 支持自定义 Prompt 模板
- 支持多模型对比检查
- 支持增量检查优化
- 支持检查结果缓存

---

### 5. progress_tracker.py - 进度跟踪器

**位置**：`autocoder/checker/progress_tracker.py`

**核心功能**：
- 跟踪检查进度
- 持久化检查状态
- 支持中断恢复

**关键方法**：

#### start_check() - 开始检查

```python
def start_check(self, files: List[str], config: Dict[str, Any]) -> str:
    """
    开始新的检查，返回 check_id

    Args:
        files: 文件列表
        config: 检查配置

    Returns:
        check_id: 格式为 {project}_{timestamp}
    """
    # 生成 check_id
    project_name = os.path.basename(os.getcwd())
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    check_id = f"{project_name}_{timestamp}"

    # 创建检查状态
    state = CheckState(
        check_id=check_id,
        start_time=datetime.now().isoformat(),
        config=config,
        total_files=files,
        completed_files=[],
        remaining_files=files
    )

    # 保存状态
    self.save_state(check_id, state)

    return check_id
```

#### mark_completed() - 标记完成

```python
def mark_completed(self, check_id: str, file_path: str) -> None:
    """标记文件已完成检查"""
    # 加载状态
    state = self.load_state(check_id)

    # 更新状态
    if file_path in state.remaining_files:
        state.remaining_files.remove(file_path)

    if file_path not in state.completed_files:
        state.completed_files.append(file_path)

    # 保存状态
    self.save_state(check_id, state)
```

#### resume_check() - 恢复检查

```python
def get_remaining_files(self, check_id: str) -> List[str]:
    """获取待检查的文件列表"""
    state = self.load_state(check_id)
    return state.remaining_files if state else []
```

**扩展建议**：
- 支持检查历史管理
- 支持检查统计分析
- 支持多用户检查隔离
- 支持分布式检查协调

---

### 6. report_generator.py - 报告生成器

**位置**：`autocoder/checker/report_generator.py`

**核心功能**：
- 生成 JSON 格式报告
- 生成 Markdown 格式报告
- 生成汇总统计

**关键方法**：

#### generate_file_report() - 生成文件报告

```python
def generate_file_report(self, result: FileCheckResult, report_dir: str) -> None:
    """生成单个文件的检查报告"""
    # 创建报告目录
    files_dir = os.path.join(report_dir, "files")
    os.makedirs(files_dir, exist_ok=True)

    # 生成文件名（替换路径分隔符）
    safe_filename = result.file_path.replace("/", "_").replace("\\", "_")

    # 生成 JSON 报告
    json_path = os.path.join(files_dir, f"{safe_filename}.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(result.dict(), f, indent=2, ensure_ascii=False)

    # 生成 Markdown 报告
    md_path = os.path.join(files_dir, f"{safe_filename}.md")
    md_content = self._generate_file_markdown(result)
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
```

#### generate_summary_report() - 生成汇总报告

```python
def generate_summary_report(
    self, results: List[FileCheckResult], report_dir: str
) -> None:
    """生成汇总报告"""
    # 统计信息
    total_files = len(results)
    total_issues = sum(len(r.issues) for r in results)
    total_errors = sum(r.error_count for r in results)
    total_warnings = sum(r.warning_count for r in results)
    total_infos = sum(r.info_count for r in results)

    # 问题最多的文件
    top_files = sorted(
        results,
        key=lambda r: len(r.issues),
        reverse=True
    )[:10]

    # 按规则分类
    rule_counts = {}
    for result in results:
        for issue in result.issues:
            rule_counts[issue.rule_id] = rule_counts.get(issue.rule_id, 0) + 1

    # 生成汇总数据
    summary = {
        "check_id": os.path.basename(report_dir),
        "total_files": total_files,
        "total_issues": total_issues,
        "error_count": total_errors,
        "warning_count": total_warnings,
        "info_count": total_infos,
        "top_files": [
            {"file": f.file_path, "issues": len(f.issues)}
            for f in top_files
        ],
        "rule_distribution": rule_counts
    }

    # 保存 JSON
    with open(os.path.join(report_dir, "summary.json"), 'w') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # 保存 Markdown
    md_content = self._generate_summary_markdown(summary, results)
    with open(os.path.join(report_dir, "summary.md"), 'w') as f:
        f.write(md_content)
```

**扩展建议**：
- 支持 HTML 报告
- 支持 PDF 导出
- 支持趋势分析（多次检查对比）
- 支持自定义报告模板

---

## 插件系统

### CodeCheckerPlugin

**位置**：`autocoder/plugins/code_checker_plugin.py`

**核心功能**：
- 注册 `/check` 命令及子命令
- 提供命令补全
- 参数解析和验证
- 调用核心检查逻辑

**插件结构**：

```python
class CodeCheckerPlugin(Plugin):
    name = "code_checker"
    description = "代码规范检查插件"
    version = "1.0.0"

    def initialize(self) -> bool:
        """初始化插件"""
        # 初始化核心组件
        self.checker = CodeChecker(self.llm, self.args)
        self.report_generator = ReportGenerator()
        self.progress_tracker = ProgressTracker()

        return True

    def get_commands(self):
        """注册命令"""
        return {
            "check": (self.handle_check, "代码检查命令"),
        }

    def get_completions(self):
        """提供命令补全"""
        return {
            "/check": ["/file", "/folder", "/resume", "/report"],
            "/check /folder": ["/path", "/ext", "/ignore", "/workers"],
        }
```

**命令处理**：

```python
def handle_check(self, args: str):
    """处理 /check 命令"""
    parts = args.strip().split(maxsplit=1)

    if not parts:
        print(self._show_help())
        return

    subcommand = parts[0]

    if subcommand == "/file":
        self._check_file(parts[1] if len(parts) > 1 else "")
    elif subcommand == "/folder":
        self._check_folder(parts[1] if len(parts) > 1 else "")
    elif subcommand == "/resume":
        self._resume_check(parts[1] if len(parts) > 1 else "")
    else:
        print(f"未知子命令: {subcommand}")
        print(self._show_help())
```

**扩展插件**：

1. **创建新插件**：
   ```python
   class MyCheckerPlugin(CodeCheckerPlugin):
       name = "my_checker"

       def initialize(self):
           super().initialize()
           # 自定义初始化
           return True

       def get_commands(self):
           commands = super().get_commands()
           # 添加新命令
           commands["mycheck"] = (self.handle_mycheck, "我的检查")
           return commands
   ```

2. **注册插件**：
   在 `autocoder/plugins/__init__.py` 中注册

---

## 添加新规则

### 规则文件格式

规则文件使用 Markdown 格式，便于阅读和维护。

**文件位置**：
- 后端规则：`rules/backend_rules.md`
- 前端规则：`rules/frontend_rules.md`

**规则格式**：

```markdown
## 规则类别名称

### 规则ID: backend_xxx
**标题**: 规则标题
**严重程度**: warning
**描述**: 规则的详细描述，说明为什么需要这个规则

**错误示例**:
```python
# 错误的代码示例
def bad_example():
    # 违反规则的代码
    pass
```

**正确示例**:
```python
# 正确的代码示例
def good_example():
    # 符合规则的代码
    pass
```
```

### 添加新规则步骤

1. **编辑规则文件**

   ```bash
   vim rules/backend_rules.md
   ```

2. **添加规则**

   ```markdown
   ## 性能优化

   ### 规则ID: backend_100
   **标题**: 避免在循环中进行数据库查询
   **严重程度**: error
   **描述**: 在循环中进行数据库查询会导致 N+1 问题，严重影响性能。应该使用批量查询或 JOIN 优化。

   **错误示例**:
   ```python
   def get_user_posts(user_ids):
       posts = []
       for user_id in user_ids:
           # 每次循环都查询数据库
           user_posts = db.query(Post).filter(Post.user_id == user_id).all()
           posts.extend(user_posts)
       return posts
   ```

   **正确示例**:
   ```python
   def get_user_posts(user_ids):
       # 批量查询
       posts = db.query(Post).filter(Post.user_id.in_(user_ids)).all()
       return posts
   ```
   ```

3. **更新规则配置**（可选）

   如果需要特殊配置，编辑 `rules/rules_config.json`：

   ```json
   {
     "rule_sets": {
       "backend": {
         "enabled": true,
         "disabled_rules": []  // 如需禁用某规则，添加到这里
       }
     }
   }
   ```

4. **测试规则**

   ```bash
   # 启动 chat_auto_coder
   python -m autocoder.chat_auto_coder

   # 测试新规则
   /check /file test_file.py
   ```

5. **验证结果**

   检查生成的报告，确认新规则正确生效

### 规则最佳实践

1. **规则ID规范**
   - 后端：`backend_001` - `backend_999`
   - 前端：`frontend_001` - `frontend_999`
   - 按类别分段（如 001-099 代码结构，100-199 性能优化）

2. **严重程度选择**
   - `error`：必须修复的问题（安全、致命bug）
   - `warning`：建议修复的问题（性能、规范）
   - `info`：提示性信息（优化建议）

3. **描述编写**
   - 说明"为什么"而不只是"是什么"
   - 提供具体的修复建议
   - 包含正反示例

4. **示例代码**
   - 使用实际场景的代码
   - 示例简洁明了
   - 突出关键问题

---

## 扩展新功能

### 1. 添加新的检查类型

假设要添加 SQL 检查：

**步骤 1：创建规则文件**

```bash
# 创建 SQL 规则文件
vim rules/sql_rules.md
```

**步骤 2：编写规则**

```markdown
## SQL 规范

### 规则ID: sql_001
**标题**: 避免使用 SELECT *
**严重程度**: warning
**描述**: SELECT * 会查询所有字段，影响性能，且在表结构变更时可能导致问题

**错误示例**:
```sql
SELECT * FROM users WHERE id = 1;
```

**正确示例**:
```sql
SELECT id, name, email FROM users WHERE id = 1;
```
```

**步骤 3：更新配置**

编辑 `rules/rules_config.json`：

```json
{
  "rule_sets": {
    "backend": { ... },
    "frontend": { ... },
    "sql": {
      "enabled": true,
      "file_patterns": ["**/*.sql"],
      "severity_threshold": "warning",
      "disabled_rules": []
    }
  }
}
```

**步骤 4：更新 RulesLoader**

在 `autocoder/checker/rules_loader.py` 中添加：

```python
def get_applicable_rules(self, file_path: str) -> List[Rule]:
    """根据文件路径获取适用的规则"""
    ext = os.path.splitext(file_path)[1].lower()

    # 现有映射
    if ext == ".py":
        return self.load_rules("backend")
    elif ext in [".js", ".jsx", ".ts", ".tsx", ".vue"]:
        return self.load_rules("frontend")
    elif ext == ".sql":  # 新增
        return self.load_rules("sql")

    return []
```

### 2. 添加自定义报告格式

假设要添加 HTML 报告：

**步骤 1：创建报告生成方法**

在 `autocoder/checker/report_generator.py` 中添加：

```python
def generate_html_report(
    self, results: List[FileCheckResult], report_dir: str
) -> None:
    """生成 HTML 格式报告"""
    # HTML 模板
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>代码检查报告</title>
        <style>
            /* CSS 样式 */
        </style>
    </head>
    <body>
        <h1>代码检查报告</h1>
        {content}
    </body>
    </html>
    """

    # 生成内容
    content = self._generate_html_content(results)

    # 保存文件
    html_path = os.path.join(report_dir, "report.html")
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_template.format(content=content))
```

**步骤 2：调用生成方法**

在插件中调用：

```python
def _check_folder(self, args: str):
    # ... 检查逻辑 ...

    # 生成报告
    self.report_generator.generate_summary_report(results, report_dir)
    self.report_generator.generate_html_report(results, report_dir)  # 新增
```

### 3. 集成外部检查工具

假设要集成 Pylint：

**步骤 1：创建工具包装器**

```python
# autocoder/checker/tools/pylint_wrapper.py

import subprocess
import json
from typing import List
from ..types import Issue, Severity

class PylintWrapper:
    def check(self, file_path: str) -> List[Issue]:
        """使用 Pylint 检查文件"""
        # 运行 Pylint
        result = subprocess.run(
            ["pylint", "--output-format=json", file_path],
            capture_output=True,
            text=True
        )

        # 解析结果
        pylint_issues = json.loads(result.stdout)

        # 转换为 Issue 对象
        issues = []
        for item in pylint_issues:
            issues.append(Issue(
                rule_id=f"pylint_{item['message-id']}",
                severity=self._map_severity(item['type']),
                line_start=item['line'],
                line_end=item['line'],
                description=item['message'],
                suggestion=item.get('hint', ''),
                code_snippet=''
            ))

        return issues

    def _map_severity(self, pylint_type: str) -> Severity:
        """映射 Pylint 严重程度"""
        mapping = {
            'error': Severity.ERROR,
            'warning': Severity.WARNING,
            'convention': Severity.INFO,
            'refactor': Severity.INFO,
        }
        return mapping.get(pylint_type, Severity.INFO)
```

**步骤 2：集成到检查流程**

在 `core.py` 中：

```python
def check_file(self, file_path: str) -> FileCheckResult:
    """检查单个文件"""
    # LLM 检查
    llm_issues = self._check_with_llm(file_path)

    # Pylint 检查（可选）
    if self.enable_pylint and file_path.endswith('.py'):
        pylint = PylintWrapper()
        pylint_issues = pylint.check(file_path)
        llm_issues.extend(pylint_issues)

    # 合并结果
    merged_issues = self._merge_duplicate_issues(llm_issues)

    # ... 返回结果
```

---

## API 参考

### CodeChecker

```python
class CodeChecker:
    def __init__(self, llm: byzerllm.ByzerLLM, args: AutoCoderArgs)

    def check_file(self, file_path: str) -> FileCheckResult
        """检查单个文件"""

    def check_files_concurrent(
        self, files: List[str], max_workers: int = 5
    ) -> Generator[FileCheckResult, None, None]
        """并发检查多个文件"""

    def check_code_chunk(
        self, code: str, rules: List[Rule]
    ) -> List[Issue]
        """检查代码块"""
```

### RulesLoader

```python
class RulesLoader:
    def __init__(self, rules_dir: str = "rules")

    def load_rules(self, rule_type: str) -> List[Rule]
        """加载指定类型的规则"""

    def get_applicable_rules(self, file_path: str) -> List[Rule]
        """根据文件路径获取适用的规则"""

    def reload_rules(self) -> None
        """重新加载所有规则"""
```

### FileProcessor

```python
class FileProcessor:
    def __init__(self, chunk_size: int = 4000, overlap: int = 200)

    def scan_files(self, path: str, filters: FileFilters) -> List[str]
        """扫描目录，返回符合条件的文件列表"""

    def chunk_file(self, file_path: str) -> List[CodeChunk]
        """将大文件分块"""

    def is_checkable(self, file_path: str) -> bool
        """判断文件是否可检查"""
```

### ProgressTracker

```python
class ProgressTracker:
    def __init__(self, state_dir: str = ".auto-coder/codecheck/progress")

    def start_check(self, files: List[str], config: Dict) -> str
        """开始新的检查，返回 check_id"""

    def mark_completed(self, check_id: str, file_path: str) -> None
        """标记文件已完成检查"""

    def get_remaining_files(self, check_id: str) -> List[str]
        """获取待检查的文件列表"""

    def save_state(self, check_id: str, state: CheckState) -> None
        """保存检查状态"""

    def load_state(self, check_id: str) -> Optional[CheckState]
        """加载检查状态"""
```

### ReportGenerator

```python
class ReportGenerator:
    def __init__(self, output_dir: str = "codecheck")

    def generate_file_report(
        self, result: FileCheckResult, report_dir: str
    ) -> None
        """生成单个文件的检查报告"""

    def generate_summary_report(
        self, results: List[FileCheckResult], report_dir: str
    ) -> None
        """生成汇总报告"""
```

---

## 测试指南

### 单元测试

**测试文件位置**：`tests/checker/`

**测试示例**：

```python
# tests/checker/test_rules_loader.py

import pytest
from autocoder.checker.rules_loader import RulesLoader
from autocoder.checker.types import Rule, Severity

def test_load_backend_rules():
    """测试加载后端规则"""
    loader = RulesLoader()
    rules = loader.load_rules("backend")

    assert len(rules) > 0
    assert all(isinstance(r, Rule) for r in rules)
    assert all(r.id.startswith("backend_") for r in rules)

def test_get_applicable_rules_for_python():
    """测试 Python 文件规则选择"""
    loader = RulesLoader()
    rules = loader.get_applicable_rules("test.py")

    assert len(rules) > 0
    assert all(r.id.startswith("backend_") for r in rules)

def test_rule_caching():
    """测试规则缓存"""
    loader = RulesLoader()

    rules1 = loader.load_rules("backend")
    rules2 = loader.load_rules("backend")

    # 应该返回同一个对象（缓存）
    assert rules1 is rules2
```

**运行测试**：

```bash
# 运行所有检查器测试
pytest tests/checker/ -v

# 运行特定测试文件
pytest tests/checker/test_rules_loader.py -v

# 查看覆盖率
pytest tests/checker/ --cov=autocoder/checker --cov-report=html
```

### 集成测试

```python
# tests/checker/test_integration.py

def test_full_check_workflow():
    """测试完整的检查流程"""
    # 1. 创建临时测试文件
    test_file = "test_code.py"
    with open(test_file, 'w') as f:
        f.write("""
def test_function():
    if True:
        if True:
            if True:
                if True:
                    pass  # 嵌套过深
        """)

    try:
        # 2. 初始化检查器
        checker = CodeChecker(mock_llm, mock_args)

        # 3. 执行检查
        result = checker.check_file(test_file)

        # 4. 验证结果
        assert result.status == "success"
        assert len(result.issues) > 0

        # 5. 验证报告生成
        report_gen = ReportGenerator()
        report_gen.generate_file_report(result, "test_reports")

        assert os.path.exists("test_reports/files/test_code_py.json")
        assert os.path.exists("test_reports/files/test_code_py.md")

    finally:
        # 清理
        os.remove(test_file)
        shutil.rmtree("test_reports")
```

### Mock 测试

```python
from unittest.mock import Mock, patch

def test_check_with_mock_llm():
    """使用 Mock LLM 测试"""
    # Mock LLM 返回
    mock_llm = Mock()
    mock_llm.chat_oai.return_value = [Mock(output="""
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
    """)]

    # 执行检查
    checker = CodeChecker(mock_llm, mock_args)
    result = checker.check_file("test.py")

    # 验证
    assert result.status == "success"
    assert len(result.issues) == 1
    assert result.issues[0].rule_id == "backend_001"
```

---

## 性能优化建议

### 1. 规则缓存

```python
# 使用 LRU 缓存
from functools import lru_cache

class RulesLoader:
    @lru_cache(maxsize=10)
    def load_rules(self, rule_type: str) -> List[Rule]:
        # 加载逻辑
        pass
```

### 2. 并发优化

```python
# 动态调整并发数
def get_optimal_workers(file_count: int) -> int:
    if file_count < 10:
        return 2
    elif file_count < 50:
        return 5
    else:
        return 10
```

### 3. 增量检查

```python
# 只检查修改的文件
def get_changed_files() -> List[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        capture_output=True,
        text=True
    )
    return result.stdout.strip().split('\n')
```

---

## 常见问题

### Q1: 如何调试 LLM Prompt？

**A**: 启用日志记录：

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("autocoder.checker")

# 查看 LLM 请求和响应
logger.debug(f"LLM Request: {prompt}")
logger.debug(f"LLM Response: {response}")
```

### Q2: 如何优化检查速度？

**A**:
1. 增加并发数
2. 减少规则数量
3. 使用更快的模型
4. 实现结果缓存

### Q3: 如何处理检查结果不准确？

**A**:
1. 优化 Prompt 模板
2. 添加更多示例到规则
3. 使用更强的模型
4. 结合静态分析工具

---

## 贡献指南

欢迎贡献代码和改进建议！

### 开发流程

1. Fork 项目
2. 创建特性分支
3. 编写代码和测试
4. 提交 Pull Request

### 代码规范

- 遵循 PEP 8
- 添加类型注解
- 编写文档字符串
- 添加单元测试

---

## 修复记录

### 2025-10-11: 修复模型获取逻辑

**问题描述**：
用户在使用 `/check /folder` 命令时遇到错误：
```
CodeChecker 初始化失败: Failed to create LLM instance for models: deepseek/deepseek-chat
- Model 'deepseek/deepseek-chat' not found
```

**问题原因**：
在 `code_checker_plugin.py` 的 `_ensure_checker()` 方法中（第103行），代码硬编码了一个默认模型：
```python
model_name = conf.get("model", "deepseek/deepseek-chat")
```

当配置中没有 "model" 字段时，会使用这个不存在的默认模型，导致初始化失败。

**修复方案**：
1. **智能模型选择**：按优先级选择模型
   - 优先使用 `chat_model`（chat 模式专用模型）
   - 其次使用 `model`（通用模型）
   - 最后从 LLMManager 中自动选择第一个有 API key 的可用模型

2. **友好的错误提示**：
   - 当完全没有可用模型时，提供清晰的配置指导
   - 当模型无法初始化时，提示可能的原因和解决方法

**修改文件**：
- `autocoder/plugins/code_checker_plugin.py` (第82-139行)

**修改内容**：
```python
def _ensure_checker(self):
    # ... 省略部分代码 ...

    # 智能获取模型配置
    # 1. 优先使用 chat_model（chat 模式专用）
    # 2. 其次使用 model（通用模型）
    # 3. 最后尝试获取第一个可用模型
    model_name = conf.get("chat_model") or conf.get("model")

    if not model_name:
        # 如果配置中没有模型，尝试从 LLMManager 获取第一个有 API key 的模型
        llm_manager = LLMManager()
        all_models = llm_manager.get_all_models()

        # 查找第一个有 API key 的模型
        for name, model in all_models.items():
            if llm_manager.has_key(name):
                model_name = name
                logger.info(f"[{self.name}] 配置中未指定模型，自动选择: {model_name}")
                break

        if not model_name:
            raise RuntimeError(
                "未配置模型，且未找到可用的模型\n"
                "请使用以下方式之一配置模型：\n"
                "1. /models /add <model_name> <api_key> - 添加并激活模型\n"
                "2. /config model <model_name> - 设置当前使用的模型"
            )

    # ... 省略后续代码 ...
```

**测试验证**：
- 场景1：配置中有 `chat_model` → 使用 `chat_model`
- 场景2：配置中只有 `model` → 使用 `model`
- 场景3：配置中都没有，但有已激活的模型 → 自动选择第一个有 API key 的模型
- 场景4：没有任何可用模型 → 显示友好的错误提示

**影响范围**：
- 仅影响 CodeChecker 的初始化逻辑
- 不影响现有功能
- 向后兼容

**相关文件**：
- `autocoder/plugins/code_checker_plugin.py`
- `autocoder/checker/core.py`

**提交信息**：
```
fix(checker): 智能获取当前激活的模型

- 优先使用 chat_model，其次 model，最后自动选择
- 移除硬编码的默认模型 "deepseek/deepseek-chat"
- 添加友好的错误提示和配置指导
- 修复用户使用 /check 命令时的模型初始化失败问题
```

---

### 2025-10-11: 添加规则文件自动初始化功能

**问题描述**：
用户在项目目录执行 `/check /folder` 命令时，遇到大量文件检查失败（102个失败，0个成功），原因是当前目录没有规则文件。

**解决方案**：
在 `RulesLoader` 中添加自动初始化功能，当规则文件不存在时自动从模板复制。

**主要改进**：

1. **智能模板查找**（按优先级）：
   - 构造函数参数 `template_rules_dir`
   - 环境变量 `CODE_CHECKER_TEMPLATE_DIR`
   - 默认位置：项目根目录 `rules/`

2. **自动初始化流程**：
   - 检测规则文件不存在
   - 查找模板目录
   - 验证模板文件完整性
   - 复制规则文件到当前目录
   - 显示友好提示

3. **用户友好的提示**：
```
✨ 检测到当前目录没有规则文件
📋 正在从模板自动创建规则文件...
   ✓ backend_rules.md (63条后端规则)
   ✓ frontend_rules.md (105条前端规则)
   ✓ rules_config.json (配置文件)

✅ 规则文件初始化成功！
   规则目录: /path/to/current/rules
```

**修改文件**：
- `autocoder/checker/rules_loader.py`
  - 修改 `__init__()` 添加 `template_rules_dir` 和 `auto_init` 参数
  - 修改 `load_rules()` 添加自动初始化逻辑
  - 新增 `_get_template_dir()` 方法
  - 新增 `_auto_initialize_rules()` 方法

**配置方式**：

方式1：使用默认行为（推荐）
```bash
/check /folder  # 自动从项目根目录的 rules/ 复制
```

方式2：通过环境变量指定
```bash
export CODE_CHECKER_TEMPLATE_DIR=/path/to/template/rules
/check /folder
```

方式3：禁用自动初始化
```python
loader = RulesLoader(auto_init=False)
```

**特性**：
- ✅ 默认启用，无需手动配置
- ✅ 向后兼容
- ✅ 友好的错误提示
- ✅ 支持多种模板路径配置
- ✅ 防止重复初始化

**提交信息**：
```
feat(checker): 添加规则文件自动初始化功能

- 当检测到没有规则文件时自动从模板复制
- 支持多种方式指定模板目录（参数/环境变量/默认位置）
- 提供友好的用户提示和错误指导
- 解决用户在项目目录执行检查时规则文件缺失的问题
- 默认启用，向后兼容

修复问题：用户执行 /check /folder 时 102 个文件失败
```

---

**最后更新**：2025-10-11
**文档版本**：1.0.2
**作者**：Claude AI
