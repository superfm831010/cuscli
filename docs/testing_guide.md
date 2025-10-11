# 代码检查器测试指南

> 测试运行、开发和维护指南

## 📋 目录

- [快速开始](#快速开始)
- [测试结构](#测试结构)
- [运行测试](#运行测试)
- [编写测试](#编写测试)
- [覆盖率报告](#覆盖率报告)
- [CI/CD 集成](#cicd-集成)
- [常见问题](#常见问题)

---

## 快速开始

### 安装测试依赖

```bash
pip install pytest pytest-cov pytest-mock pytest-timeout
```

### 运行所有测试

```bash
# 使用测试脚本（推荐）
./scripts/run_tests.sh

# 或直接使用 pytest
pytest tests/checker/ -v
```

### 查看覆盖率

```bash
./scripts/run_tests.sh --html
# 然后打开 htmlcov/index.html
```

---

## 测试结构

### 测试目录组织

```
tests/
├── conftest.py                 # 共享 fixtures 和配置
└── checker/                    # 检查器测试
    ├── __init__.py
    ├── test_types.py          # 类型定义测试
    ├── test_rules_loader.py   # 规则加载器测试
    ├── test_file_processor.py # 文件处理器测试
    ├── test_core.py           # 核心检查器测试
    ├── test_progress_tracker.py # 进度跟踪器测试
    ├── test_report_generator.py # 报告生成器测试
    ├── test_plugin.py         # 插件测试
    └── test_integration.py    # 集成测试
```

### 测试分类

使用 pytest markers 进行分类：

- `@pytest.mark.unit` - 单元测试
- `@pytest.mark.integration` - 集成测试
- `@pytest.mark.e2e` - 端到端测试
- `@pytest.mark.performance` - 性能测试
- `@pytest.mark.slow` - 运行较慢的测试

---

## 运行测试

### 使用测试脚本

**基本用法：**

```bash
# 运行所有测试
./scripts/run_tests.sh

# 只运行单元测试
./scripts/run_tests.sh -u

# 只运行集成测试
./scripts/run_tests.sh -i

# 生成覆盖率报告
./scripts/run_tests.sh -c

# 生成 HTML 覆盖率报告
./scripts/run_tests.sh --html

# 详细输出
./scripts/run_tests.sh -v

# 清除缓存
./scripts/run_tests.sh --no-cache
```

**组合选项：**

```bash
# 单元测试 + 覆盖率
./scripts/run_tests.sh -u -c

# 集成测试 + 详细输出
./scripts/run_tests.sh -i -v

# 所有测试 + HTML 报告
./scripts/run_tests.sh -a --html
```

### 直接使用 pytest

**按标记运行：**

```bash
# 单元测试
pytest tests/checker/ -m unit

# 集成测试
pytest tests/checker/ -m integration

# 排除慢速测试
pytest tests/checker/ -m "not slow"
```

**按文件运行：**

```bash
# 单个测试文件
pytest tests/checker/test_core.py -v

# 单个测试类
pytest tests/checker/test_core.py::TestCodeChecker -v

# 单个测试方法
pytest tests/checker/test_core.py::TestCodeChecker::test_init -v
```

**覆盖率选项：**

```bash
# 基本覆盖率
pytest tests/checker/ --cov=autocoder/checker

# 详细覆盖率（显示缺失行）
pytest tests/checker/ --cov=autocoder/checker --cov-report=term-missing

# HTML 覆盖率报告
pytest tests/checker/ --cov=autocoder/checker --cov-report=html

# 设置覆盖率阈值
pytest tests/checker/ --cov=autocoder/checker --cov-fail-under=90
```

---

## 编写测试

### 使用共享 Fixtures

`tests/conftest.py` 提供了丰富的 fixtures：

**Mock LLM Fixtures：**

```python
def test_with_mock_llm(mock_llm):
    """使用 Mock LLM"""
    checker = CodeChecker(mock_llm, mock_args)
    # mock_llm 自动返回标准响应

def test_empty_result(mock_llm_empty):
    """测试无问题场景"""
    checker = CodeChecker(mock_llm_empty, mock_args)
    # mock_llm_empty 返回空结果

def test_llm_error(mock_llm_error):
    """测试 LLM 失败场景"""
    checker = CodeChecker(mock_llm_error, mock_args)
    # mock_llm_error 抛出异常
```

**数据 Fixtures：**

```python
def test_with_sample_data(sample_rules, sample_issues):
    """使用示例数据"""
    # sample_rules: 示例规则列表
    # sample_issues: 示例问题列表
    assert len(sample_rules) > 0
```

**临时目录 Fixtures：**

```python
def test_with_temp_dir(temp_dir):
    """使用临时目录"""
    test_file = os.path.join(temp_dir, "test.py")
    # 临时目录会自动清理

def test_with_project(temp_project_dir):
    """使用完整项目结构"""
    # temp_project_dir 包含完整的项目结构
    files = os.listdir(temp_project_dir)
```

### 编写单元测试

**基本结构：**

```python
import pytest
from autocoder.checker.core import CodeChecker

class TestMyFeature:
    """测试我的功能"""

    @pytest.fixture
    def my_fixture(self):
        """测试专用 fixture"""
        return "test data"

    def test_basic_functionality(self, my_fixture):
        """测试基本功能"""
        result = my_function(my_fixture)
        assert result == expected

    def test_edge_case(self):
        """测试边界情况"""
        with pytest.raises(ValueError):
            my_function(invalid_input)

    @pytest.mark.parametrize("input,expected", [
        (1, 2),
        (2, 4),
        (3, 6),
    ])
    def test_multiple_cases(self, input, expected):
        """测试多个案例"""
        assert my_function(input) == expected
```

### 编写集成测试

**标记为集成测试：**

```python
@pytest.mark.integration
class TestIntegrationWorkflow:
    """集成测试"""

    def test_full_workflow(self, mock_llm, temp_dir):
        """测试完整工作流"""
        # 1. 准备
        checker = CodeChecker(mock_llm, mock_args)

        # 2. 执行
        result = checker.check_file(test_file)

        # 3. 验证
        assert result.status == "success"
```

### 使用 Mock

**Mock 对象：**

```python
from unittest.mock import Mock, patch

def test_with_mock():
    """使用 Mock 对象"""
    mock_obj = Mock()
    mock_obj.method.return_value = "mocked result"

    result = mock_obj.method()
    assert result == "mocked result"
    assert mock_obj.method.called

def test_with_patch():
    """使用 patch 装饰器"""
    with patch('module.function') as mock_func:
        mock_func.return_value = "patched"
        result = call_function()
        assert mock_func.called
```

---

## 覆盖率报告

### 查看覆盖率

**命令行输出：**

```bash
pytest tests/checker/ --cov=autocoder/checker --cov-report=term-missing
```

**输出示例：**

```
Name                                    Stmts   Miss  Cover   Missing
---------------------------------------------------------------------
autocoder/checker/__init__.py               3      0   100%
autocoder/checker/core.py                 212     25    88%   335-339, 463-464
autocoder/checker/file_processor.py       140     12    91%   271-272, 374
autocoder/checker/types.py                104      4    96%   143-144
---------------------------------------------------------------------
TOTAL                                     927    125    86%
```

### HTML 报告

**生成报告：**

```bash
pytest tests/checker/ --cov=autocoder/checker --cov-report=html
```

**查看报告：**

```bash
# Linux/Mac
open htmlcov/index.html

# 或使用浏览器打开
file:///path/to/project/htmlcov/index.html
```

**HTML 报告特点：**
- 📊 可视化覆盖率统计
- 🔍 行级覆盖率显示
- 📂 文件树导航
- 🎯 快速定位未覆盖代码

### 提高覆盖率

**识别未覆盖代码：**

1. 查看 `Missing` 列找到未覆盖的行号
2. 添加测试覆盖这些代码路径
3. 重新运行测试验证

**覆盖率目标：**
- 核心模块：≥ 90%
- 工具模块：≥ 80%
- 总体目标：≥ 85%

---

## CI/CD 集成

### GitHub Actions

项目使用 GitHub Actions 进行自动化测试。

**工作流文件：** `.github/workflows/test.yml`

**触发条件：**
- Push 到 main/develop 分支
- Pull Request 到 main 分支
- 修改测试相关文件

**测试矩阵：**
- Python 3.8, 3.9, 3.10, 3.11
- Ubuntu Latest

**测试步骤：**
1. 运行单元测试
2. 运行集成测试
3. 生成覆盖率报告
4. 上传到 Codecov
5. 代码质量检查（flake8, mypy, black）

**查看结果：**

访问 GitHub Actions 页面查看测试结果：
```
https://github.com/your-org/your-repo/actions
```

### 本地 CI 模拟

**运行所有 CI 检查：**

```bash
# 1. 运行所有测试
./scripts/run_tests.sh -a -c

# 2. 代码格式检查
black --check autocoder/checker/ tests/checker/

# 3. 导入排序检查
isort --check-only autocoder/checker/ tests/checker/

# 4. Linting
flake8 autocoder/checker/ --max-line-length=127

# 5. 类型检查
mypy autocoder/checker/ --ignore-missing-imports
```

---

## 常见问题

### Q1: 如何只运行特定测试？

```bash
# 运行特定文件
pytest tests/checker/test_core.py

# 运行特定类
pytest tests/checker/test_core.py::TestCodeChecker

# 运行特定方法
pytest tests/checker/test_core.py::TestCodeChecker::test_init

# 按名称匹配
pytest tests/checker/ -k "test_parse"
```

### Q2: 如何跳过慢速测试？

```bash
# 排除标记为 slow 的测试
pytest tests/checker/ -m "not slow"

# 使用自定义标记
@pytest.mark.slow
def test_performance():
    # 慢速测试
    pass
```

### Q3: 如何调试失败的测试？

```bash
# 显示详细输出
pytest tests/checker/test_core.py -vv

# 显示 print 输出
pytest tests/checker/test_core.py -s

# 在失败时进入 pdb
pytest tests/checker/test_core.py --pdb

# 只运行失败的测试
pytest tests/checker/ --lf
```

### Q4: 如何并行运行测试？

```bash
# 安装 pytest-xdist
pip install pytest-xdist

# 并行运行（自动检测 CPU 数）
pytest tests/checker/ -n auto

# 指定进程数
pytest tests/checker/ -n 4
```

### Q5: 覆盖率不准确怎么办？

**检查配置：**

```ini
# pytest.ini
[coverage:run]
source = autocoder/checker
omit =
    */tests/*
    */test_*.py
```

**排除不需要覆盖的代码：**

```python
def debug_function():  # pragma: no cover
    """调试函数，不需要覆盖"""
    pass
```

### Q6: 如何测试异步代码？

```bash
# 安装 pytest-asyncio
pip install pytest-asyncio
```

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """测试异步函数"""
    result = await async_function()
    assert result == expected
```

### Q7: 测试运行很慢怎么办？

**优化策略：**

1. **只运行相关测试**
   ```bash
   pytest tests/checker/test_core.py -k "not slow"
   ```

2. **使用并行测试**
   ```bash
   pytest tests/checker/ -n auto
   ```

3. **禁用覆盖率**（开发时）
   ```bash
   pytest tests/checker/ --no-cov
   ```

4. **使用 fixtures 缓存**
   ```python
   @pytest.fixture(scope="session")
   def expensive_fixture():
       # 只执行一次
       return expensive_operation()
   ```

---

## 测试最佳实践

### 1. 测试命名

- 使用描述性名称
- 遵循 `test_<what>_<condition>_<expected>` 模式

```python
# 好的命名
def test_parse_json_with_valid_data_returns_issues():
    pass

def test_check_file_when_file_not_found_raises_error():
    pass

# 避免
def test_1():
    pass

def test_function():
    pass
```

### 2. 一个测试一个断言

```python
# 好的做法
def test_file_result_has_correct_path():
    assert result.file_path == expected_path

def test_file_result_has_correct_status():
    assert result.status == "success"

# 避免
def test_file_result():
    assert result.file_path == expected_path
    assert result.status == "success"
    assert len(result.issues) == 0
```

### 3. 使用 Arrange-Act-Assert 模式

```python
def test_feature():
    # Arrange: 准备测试数据
    checker = CodeChecker(mock_llm, mock_args)
    test_file = "test.py"

    # Act: 执行被测试的操作
    result = checker.check_file(test_file)

    # Assert: 验证结果
    assert result.status == "success"
```

### 4. 清理测试数据

```python
@pytest.fixture
def temp_file(tmp_path):
    """创建临时文件并自动清理"""
    file_path = tmp_path / "test.py"
    file_path.write_text("content")

    yield file_path

    # 自动清理（tmp_path 会自动清理）
```

---

## 参考资源

### 文档
- [Pytest 官方文档](https://docs.pytest.org/)
- [Pytest-cov 文档](https://pytest-cov.readthedocs.io/)
- [unittest.mock 文档](https://docs.python.org/3/library/unittest.mock.html)

### 工具
- **pytest**: 测试框架
- **pytest-cov**: 覆盖率插件
- **pytest-mock**: Mock 工具
- **pytest-xdist**: 并行测试
- **pytest-timeout**: 超时控制

### 相关文档
- [代码检查使用指南](code_checker_usage.md)
- [代码检查开发指南](code_checker_development.md)

---

**最后更新**：2025-10-11
**文档版本**：1.0.0
