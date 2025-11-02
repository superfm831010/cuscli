# 黄埔海关 AI 代码新技术应用服务项目
## API接口文档

**文档编号**: GZSW25156FC3066-DOC-031
**文档版本**: v1.0
**编制单位**: 联奕科技股份有限公司
**编制日期**: 2025年11月
**密级**: 内部

---

## 文档修订记录

| 版本号 | 修订日期 | 修订人 | 修订内容 | 审核人 |
|--------|----------|--------|----------|--------|
| v1.0 | 2025-11-02 | 项目组 | 初始版本 | 技术负责人 |

---

## 目录

[TOC]

---

## 1. 概述

### 1.1 编写目的

本文档详细说明 **Cuscli AI 编程助手平台 v1.1.0** 提供的编程接口(API)和软件开发工具包(SDK),帮助用户通过编程方式集成和扩展系统功能。

### 1.2 适用对象

- 系统集成开发人员
- 二次开发人员
- 自动化运维人员
- 工具开发人员

### 1.3 API概述

| API类型 | 语言 | 用途 | 成熟度 |
|---------|------|------|--------|
| **Python SDK** | Python 3.10+ | 编程调用核心功能 | 稳定 |
| **命令行接口** | Shell | 脚本自动化 | 稳定 |
| **插件API** | Python | 扩展系统功能 | 稳定 |

**说明**: 本系统不提供REST API或HTTP API,所有功能均通过Python SDK或命令行调用。

---

## 2. Python SDK

### 2.1 SDK概述

Python SDK 提供了对系统核心功能的编程访问,支持以下场景:

- ✅ 代码自动生成
- ✅ 代码检查与分析
- ✅ 项目索引与检索
- ✅ 自定义工作流
- ✅ 批处理任务

### 2.2 SDK安装

SDK已随主程序包安装,无需单独安装:

```python
# 验证SDK可用
import autocoder.sdk
print(autocoder.sdk.__version__)
```

### 2.3 核心API

#### 2.3.1 auto_code - 同步代码生成

**函数签名**:
```python
def auto_code(
    prompt: str,
    options: Optional[AutoCodeOptions] = None,
    show_terminal: Optional[bool] = None,
    cancel_token: Optional[str] = None
) -> str
```

**参数说明**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| prompt | str | 是 | 代码生成提示 |
| options | AutoCodeOptions | 否 | 配置选项 |
| show_terminal | bool | 否 | 是否显示终端输出 |
| cancel_token | str | 否 | 取消令牌 |

**返回值**: `str` - 生成的代码内容

**示例代码**:
```python
from autocoder.sdk import auto_code, AutoCodeOptions

# 基本使用
response = auto_code("Write a function to calculate factorial")
print(response)

# 使用配置选项
options = AutoCodeOptions(
    model="gpt-4",
    max_turns=1,
    temperature=0.7
)
response = auto_code("Create a REST API endpoint", options)
```

#### 2.3.2 auto_code_stream - 异步流式生成

**函数签名**:
```python
async def auto_code_stream(
    prompt: str,
    options: Optional[AutoCodeOptions] = None,
    show_terminal: Optional[bool] = None,
    cancel_token: Optional[str] = None
) -> AsyncIterator[StreamEvent]
```

**参数说明**: 与 `auto_code` 相同

**返回值**: `AsyncIterator[StreamEvent]` - 事件流

**StreamEvent 结构**:
```python
class StreamEvent:
    event_type: str    # "thinking", "code", "done", "error"
    data: Any         # 事件数据
    timestamp: float  # 时间戳
```

**示例代码**:
```python
import asyncio
from autocoder.sdk import auto_code_stream, AutoCodeOptions

async def main():
    options = AutoCodeOptions(max_turns=3)
    async for event in auto_code_stream("Write a hello world function", options):
        print(f"[{event.event_type}] {event.data}")

asyncio.run(main())
```

#### 2.3.3 AutoCodeOptions 配置类

**类定义**:
```python
class AutoCodeOptions:
    # LLM配置
    model: Optional[str] = None           # 模型名称
    temperature: float = 0.7              # 温度
    max_tokens: int = 4000                # 最大token数

    # 执行配置
    max_turns: int = 5                    # 最大轮次
    timeout: int = 300                    # 超时时间(秒)

    # 项目配置
    project_path: Optional[str] = None    # 项目路径
    target_files: Optional[List[str]] = None  # 目标文件

    # 输出配置
    verbose: bool = False                 # 详细输出
    output_file: Optional[str] = None     # 输出文件路径

    # 取消机制
    cancel_token: Optional[str] = None    # 取消令牌
```

**示例**:
```python
from autocoder.sdk import AutoCodeOptions

options = AutoCodeOptions(
    model="gpt-4",
    temperature=0.5,
    max_turns=3,
    project_path="/path/to/project",
    verbose=True
)
```

### 2.4 代码检查API

#### 2.4.1 check_file - 检查单个文件

**函数签名**:
```python
def check_file(
    file_path: str,
    rules_file: str = "rules/backend_rules.md",
    output_format: str = "markdown"
) -> CheckResult
```

**参数说明**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file_path | str | 是 | 文件路径 |
| rules_file | str | 否 | 规则文件路径 |
| output_format | str | 否 | 输出格式(markdown/json) |

**返回值**: `CheckResult` - 检查结果对象

**示例代码**:
```python
from autocoder.checker import check_file

result = check_file(
    file_path="src/services/user_service.py",
    rules_file="rules/backend_rules.md"
)

print(f"检查完成: {result.total_issues} 个问题")
print(f"错误: {result.error_count}")
print(f"警告: {result.warning_count}")
```

#### 2.4.2 check_folder - 检查整个目录

**函数签名**:
```python
def check_folder(
    folder_path: str,
    rules_file: str = "rules/backend_rules.md",
    recursive: bool = True,
    output_dir: str = "codecheck"
) -> FolderCheckResult
```

**参数说明**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| folder_path | str | 是 | 目录路径 |
| rules_file | str | 否 | 规则文件路径 |
| recursive | bool | 否 | 是否递归检查 |
| output_dir | str | 否 | 报告输出目录 |

**示例代码**:
```python
from autocoder.checker import check_folder

result = check_folder(
    folder_path="src/",
    rules_file="rules/backend_rules.md",
    recursive=True,
    output_dir="reports"
)

print(f"检查了 {result.total_files} 个文件")
print(f"发现 {result.total_issues} 个问题")
```

### 2.5 项目初始化API

#### 2.5.1 init_project - 初始化项目

**函数签名**:
```python
def init_project(
    project_path: str,
    config: Optional[Dict[str, Any]] = None
) -> bool
```

**参数说明**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| project_path | str | 是 | 项目根目录 |
| config | dict | 否 | 初始化配置 |

**示例代码**:
```python
from autocoder.sdk import init_project

config = {
    "model": "gpt-4",
    "language": "python",
    "framework": "ecim"
}

success = init_project("/path/to/project", config)
if success:
    print("项目初始化成功")
```

### 2.6 工具函数API

#### 2.6.1 load_config - 加载配置

```python
from autocoder.sdk import load_config

config = load_config("/path/to/project/.auto-coder/project.yml")
print(config)
```

#### 2.6.2 get_llm - 获取LLM实例

```python
from autocoder.utils.llms import get_single_llm

llm = get_single_llm("gpt-4")
response = llm.chat("Hello")
print(response)
```

---

## 3. 命令行接口(CLI)

### 3.1 CLI概述

命令行接口提供了所有主要功能的Shell访问,适合脚本自动化。

### 3.2 主要命令

#### 3.2.1 auto-coder 命令

**语法**:
```bash
auto-coder [选项] [动作文件]
```

**常用选项**:
| 选项 | 说明 | 示例 |
|------|------|------|
| `--model` | 指定模型 | `--model gpt-4` |
| `--project` | 项目路径 | `--project /path/to/proj` |
| `--query` | 直接提问 | `--query "生成代码"` |
| `--file` | 动作文件 | `--file actions/task.yml` |

**示例**:
```bash
# 使用动作文件
auto-coder --file actions/generate_service.yml

# 直接提问
auto-coder --query "生成一个用户服务类" --model gpt-4

# 指定项目
auto-coder --project /opt/my-project --query "重构代码"
```

#### 3.2.2 chat-auto-coder 命令

**语法**:
```bash
chat-auto-coder [选项]
```

**常用选项**:
| 选项 | 说明 |
|------|------|
| `--quick` | 快速模式(跳过插件加载) |
| `--mode` | 交互模式 |
| `--project` | 项目路径 |

**示例**:
```bash
# 标准模式
chat-auto-coder

# 快速模式
chat-auto-coder --quick

# 指定项目
chat-auto-coder --project /opt/my-project
```

#### 3.2.3 auto-coder.run 命令

SDK命令行接口:

```bash
# 查看帮助
auto-coder.run --help

# 执行任务
auto-coder.run --task generate_code --prompt "Write function"
```

### 3.3 Shell脚本集成

#### 3.3.1 批量代码检查脚本

```bash
#!/bin/bash
# batch_check.sh - 批量代码检查脚本

PROJECT_ROOT="/opt/my-project"
REPORT_DIR="$PROJECT_ROOT/reports"

# 创建报告目录
mkdir -p "$REPORT_DIR"

# 检查后端代码
echo "检查后端代码..."
auto-coder check /folder "$PROJECT_ROOT/src/backend" \
    --rules rules/backend_rules.md \
    --output "$REPORT_DIR/backend_$(date +%Y%m%d).md"

# 检查前端代码
echo "检查前端代码..."
auto-coder check /folder "$PROJECT_ROOT/src/frontend" \
    --rules rules/frontend_rules.md \
    --output "$REPORT_DIR/frontend_$(date +%Y%m%d).md"

echo "检查完成,报告保存在: $REPORT_DIR"
```

#### 3.3.2 Git钩子集成脚本

```bash
#!/bin/bash
# .git/hooks/pre-commit

# 获取暂存的Python文件
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$')

if [ -z "$STAGED_FILES" ]; then
    exit 0
fi

echo "执行代码检查..."

# 检查暂存的文件
for file in $STAGED_FILES; do
    echo "检查: $file"
    auto-coder check /file "$file" --rules rules/backend_rules.md
    if [ $? -ne 0 ]; then
        echo "错误: $file 检查失败"
        exit 1
    fi
done

echo "代码检查通过"
exit 0
```

---

## 4. 插件API

### 4.1 插件系统概述

插件系统允许用户扩展系统功能,添加自定义命令和工具。

### 4.2 插件基类

**BasePlugin 类**:
```python
from autocoder.plugins.base_plugin import BasePlugin

class MyCustomPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.name = "my_plugin"
        self.description = "我的自定义插件"

    def register_commands(self) -> List[str]:
        """注册命令"""
        return ["/mycmd"]

    async def handle_command(self, command: str, args: List[str]) -> str:
        """处理命令"""
        if command == "/mycmd":
            return await self.do_something(args)
        return ""

    async def do_something(self, args: List[str]) -> str:
        """实际功能"""
        return f"执行了自定义命令: {' '.join(args)}"
```

### 4.3 插件注册

**方式1: 配置文件注册**

在 `.auto-coder/project.yml` 中:
```yaml
plugins:
  - name: "my_plugin"
    module: "plugins.my_plugin"
    enabled: true
```

**方式2: 代码注册**

```python
from autocoder.plugins.plugin_manager import PluginManager
from plugins.my_plugin import MyCustomPlugin

pm = PluginManager()
pm.register_plugin(MyCustomPlugin())
```

### 4.4 插件示例

#### 4.4.1 自定义代码格式化插件

```python
from autocoder.plugins.base_plugin import BasePlugin
import subprocess

class CodeFormatterPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.name = "code_formatter"

    def register_commands(self):
        return ["/format"]

    async def handle_command(self, command, args):
        if command == "/format":
            file_path = args[0] if args else "."
            return await self.format_code(file_path)
        return ""

    async def format_code(self, file_path: str) -> str:
        """使用black格式化Python代码"""
        try:
            result = subprocess.run(
                ["black", file_path],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return f"✅ 代码格式化完成: {file_path}"
            else:
                return f"❌ 格式化失败: {result.stderr}"
        except Exception as e:
            return f"❌ 错误: {str(e)}"
```

---

## 5. 错误处理

### 5.1 异常类型

| 异常类 | 说明 | 处理建议 |
|-------|------|---------|
| `AutoCoderError` | 基础异常 | 捕获所有异常 |
| `ConfigError` | 配置错误 | 检查配置文件 |
| `ModelError` | 模型错误 | 检查API密钥 |
| `TimeoutError` | 超时错误 | 增加timeout参数 |
| `CancelledError` | 取消错误 | 正常情况,用户主动取消 |

### 5.2 错误处理示例

```python
from autocoder.sdk import auto_code, AutoCodeOptions
from autocoder.sdk.exceptions import AutoCoderError, ModelError, TimeoutError

try:
    options = AutoCodeOptions(timeout=60)
    response = auto_code("Generate code", options)
    print(response)

except ModelError as e:
    print(f"模型错误: {e}")
    print("请检查API密钥和网络连接")

except TimeoutError as e:
    print(f"请求超时: {e}")
    print("请增加timeout参数或简化提示")

except AutoCoderError as e:
    print(f"系统错误: {e}")

except Exception as e:
    print(f"未知错误: {e}")
```

---

## 6. 使用示例

### 6.1 完整示例:自动化代码生成流程

```python
#!/usr/bin/env python3
"""
自动化代码生成流程示例
"""

from autocoder.sdk import auto_code, AutoCodeOptions, init_project
from autocoder.checker import check_file
import os

def automated_workflow(project_path: str, service_name: str):
    """
    自动化工作流:
    1. 初始化项目
    2. 生成服务类
    3. 生成单元测试
    4. 代码检查
    5. 格式化代码
    """

    # 1. 初始化项目(如未初始化)
    if not os.path.exists(f"{project_path}/.auto-coder"):
        print("初始化项目...")
        init_project(project_path)

    # 2. 生成服务类
    print(f"生成 {service_name} 服务类...")

    options = AutoCodeOptions(
        model="gpt-4",
        project_path=project_path,
        temperature=0.7
    )

    prompt = f"""
    生成一个名为 {service_name} 的业务服务类:
    - 继承 BaseService
    - 包含 create, read, update, delete 方法
    - 添加日志记录
    - 添加异常处理
    - 符合海关开发规范

    输出文件: src/services/{service_name.lower()}.py
    """

    service_code = auto_code(prompt, options)
    print("✅ 服务类生成完成")

    # 3. 生成单元测试
    print(f"生成 {service_name} 单元测试...")

    test_prompt = f"""
    为 src/services/{service_name.lower()}.py 生成单元测试:
    - 使用 pytest
    - 覆盖所有CRUD方法
    - 包含正常和异常场景

    输出文件: tests/services/test_{service_name.lower()}.py
    """

    test_code = auto_code(test_prompt, options)
    print("✅ 单元测试生成完成")

    # 4. 代码检查
    print("执行代码检查...")

    service_file = f"{project_path}/src/services/{service_name.lower()}.py"
    check_result = check_file(
        file_path=service_file,
        rules_file="rules/backend_rules.md"
    )

    if check_result.error_count > 0:
        print(f"❌ 发现 {check_result.error_count} 个错误")
        for issue in check_result.errors:
            print(f"  - {issue.description}")
        return False
    else:
        print(f"✅ 代码检查通过 ({check_result.warning_count} 个警告)")

    # 5. 格式化代码(可选)
    import subprocess
    print("格式化代码...")
    subprocess.run(["black", service_file])
    print("✅ 代码格式化完成")

    print(f"\n🎉 {service_name} 生成流程完成!")
    return True

# 使用示例
if __name__ == "__main__":
    automated_workflow(
        project_path="/opt/customs-project",
        service_name="DeclarationService"
    )
```

### 6.2 示例:并发代码检查

```python
#!/usr/bin/env python3
"""
并发代码检查示例
"""

from autocoder.checker import check_file
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from pathlib import Path

def check_project_concurrent(project_path: str, max_workers: int = 5):
    """
    并发检查项目中的所有Python文件
    """

    # 查找所有Python文件
    py_files = list(Path(project_path).rglob("*.py"))
    print(f"找到 {len(py_files)} 个Python文件")

    results = []

    # 并发检查
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {
            executor.submit(check_file, str(f), "rules/backend_rules.md"): f
            for f in py_files
        }

        for future in as_completed(future_to_file):
            file_path = future_to_file[future]
            try:
                result = future.result()
                results.append((file_path, result))
                print(f"✅ {file_path.name}: {result.total_issues} 个问题")
            except Exception as e:
                print(f"❌ {file_path.name}: 检查失败 - {e}")

    # 汇总结果
    total_issues = sum(r[1].total_issues for r in results)
    total_errors = sum(r[1].error_count for r in results)
    total_warnings = sum(r[1].warning_count for r in results)

    print(f"\n检查完成:")
    print(f"  文件数: {len(results)}")
    print(f"  总问题: {total_issues}")
    print(f"  错误: {total_errors}")
    print(f"  警告: {total_warnings}")

    return results

# 使用示例
if __name__ == "__main__":
    check_project_concurrent("/opt/customs-project/src", max_workers=8)
```

---

## 7. 性能优化

### 7.1 最佳实践

#### 7.1.1 使用流式API

对于长时间运行的任务,使用流式API获取实时进度:

```python
import asyncio
from autocoder.sdk import auto_code_stream

async def main():
    async for event in auto_code_stream("Complex task..."):
        if event.event_type == "thinking":
            print(f"思考中: {event.data}")
        elif event.event_type == "code":
            print(f"生成代码: {len(event.data)} 字符")

asyncio.run(main())
```

#### 7.1.2 并发处理

使用并发处理多个独立任务:

```python
from concurrent.futures import ThreadPoolExecutor
from autocoder.sdk import auto_code

tasks = [
    "Generate user service",
    "Generate order service",
    "Generate product service"
]

with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(auto_code, tasks))
```

#### 7.1.3 缓存结果

对于重复的任务,使用缓存:

```python
from functools import lru_cache
from autocoder.sdk import auto_code

@lru_cache(maxsize=100)
def cached_auto_code(prompt: str) -> str:
    return auto_code(prompt)

# 第一次调用会执行
result1 = cached_auto_code("Generate function")

# 第二次调用直接返回缓存结果
result2 = cached_auto_code("Generate function")  # 从缓存读取
```

---

## 8. 安全注意事项

### 8.1 API密钥管理

❌ **错误示例**:
```python
# 不要硬编码API密钥
options = AutoCodeOptions(api_key="sk-xxxxx")
```

✅ **正确示例**:
```python
import os

# 从环境变量读取
api_key = os.getenv("OPENAI_API_KEY")
options = AutoCodeOptions(api_key=api_key)
```

### 8.2 输入验证

对用户输入进行验证:

```python
def safe_auto_code(prompt: str) -> str:
    # 验证输入长度
    if len(prompt) > 10000:
        raise ValueError("提示过长")

    # 验证输入内容
    if any(word in prompt.lower() for word in ["rm -rf", "del /f"]):
        raise ValueError("检测到危险命令")

    return auto_code(prompt)
```

### 8.3 权限控制

在生产环境中限制API访问:

```python
def require_auth(func):
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user.has_permission("use_api"):
            raise PermissionError("无API使用权限")
        return func(*args, **kwargs)
    return wrapper

@require_auth
def protected_auto_code(prompt: str) -> str:
    return auto_code(prompt)
```

---

## 9. 参考文档

### 9.1 本项目相关文档

| 文档名称 | 文档编号 | 相关章节 |
|---------|---------|---------|
| 用户操作手册 | DOC-015 | 全文 |
| 命令参考手册 | DOC-016 | 全文 |
| 软件安装包及源代码说明 | DOC-029 | 第3节"源代码说明" |
| 示例和模板文件说明 | DOC-030 | 全文 |

### 9.2 Python参考

- Python asyncio文档: https://docs.python.org/3/library/asyncio.html
- Python typing文档: https://docs.python.org/3/library/typing.html

---

## 10. 附录

### 10.1 API速查表

| API | 类型 | 用途 |
|-----|------|------|
| `auto_code()` | 同步 | 代码生成 |
| `auto_code_stream()` | 异步 | 流式代码生成 |
| `check_file()` | 同步 | 文件检查 |
| `check_folder()` | 同步 | 目录检查 |
| `init_project()` | 同步 | 项目初始化 |
| `load_config()` | 同步 | 加载配置 |
| `get_single_llm()` | 同步 | 获取LLM实例 |

### 10.2 错误码表

| 错误码 | 说明 | 处理建议 |
|--------|------|---------|
| 1001 | 配置文件错误 | 检查配置文件格式 |
| 1002 | API密钥无效 | 检查环境变量 |
| 1003 | 模型不可用 | 更换模型或检查网络 |
| 1004 | 超时 | 增加timeout参数 |
| 1005 | 文件不存在 | 检查文件路径 |
| 1006 | 权限不足 | 检查文件权限 |

---

## 审核与批准

| 角色 | 姓名 | 签字 | 日期 |
|------|------|------|------|
| 编制人 | 项目组 |  | 2025-11-02 |
| 审核人 | 技术负责人 |  |  |
| 批准人 | 项目经理 |  |  |

---

**文档结束**

---

**联奕科技股份有限公司**
**技术API中心**
**2025年11月**
