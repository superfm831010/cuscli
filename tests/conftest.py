"""
共享的 pytest fixtures 和测试工具

提供跨测试文件的共享资源和工具类
"""

import os
import tempfile
import shutil
from typing import List, Dict, Any
from unittest.mock import Mock, MagicMock
from datetime import datetime
import pytest

from autocoder.checker.types import (
    Rule, Severity, Issue, FileCheckResult,
    BatchCheckResult, CheckState, CodeChunk, FileFilters
)


# ==================== Mock LLM Fixtures ====================

@pytest.fixture
def mock_llm():
    """
    创建 Mock LLM 实例

    返回一个配置好的 Mock LLM，模拟成功的代码检查响应
    """
    llm = Mock()

    # Mock chat_oai 方法，返回标准的检查结果
    mock_response = Mock()
    mock_response.output = """```json
[
    {
        "rule_id": "backend_001",
        "severity": "warning",
        "line_start": 10,
        "line_end": 15,
        "description": "发现代码质量问题",
        "suggestion": "建议进行优化",
        "code_snippet": "test code snippet"
    }
]
```"""
    llm.chat_oai.return_value = [mock_response]

    return llm


@pytest.fixture
def mock_llm_empty():
    """
    创建返回空结果的 Mock LLM

    用于测试没有发现问题的场景
    """
    llm = Mock()
    mock_response = Mock()
    mock_response.output = "```json\n[]\n```"
    llm.chat_oai.return_value = [mock_response]
    return llm


@pytest.fixture
def mock_llm_error():
    """
    创建会抛出异常的 Mock LLM

    用于测试 LLM 调用失败的场景
    """
    llm = Mock()
    llm.chat_oai.side_effect = Exception("LLM API error")
    return llm


# ==================== Args Fixtures ====================

@pytest.fixture
def mock_args():
    """创建 Mock AutoCoderArgs"""
    args = Mock()
    args.source_dir = "/test/project"
    return args


# ==================== 测试数据 Fixtures ====================

@pytest.fixture
def sample_rules() -> List[Rule]:
    """创建示例规则列表"""
    return [
        Rule(
            id="backend_001",
            category="代码结构",
            title="避免深层嵌套",
            description="if-else 嵌套不应超过 3 层",
            severity=Severity.WARNING,
            examples="示例代码"
        ),
        Rule(
            id="backend_002",
            category="安全性",
            title="防止空指针",
            description="使用变量前应检查 null",
            severity=Severity.ERROR,
            examples="示例代码"
        ),
        Rule(
            id="backend_003",
            category="命名规范",
            title="使用驼峰命名",
            description="变量名应使用驼峰命名法",
            severity=Severity.INFO
        )
    ]


@pytest.fixture
def sample_issues() -> List[Issue]:
    """创建示例问题列表"""
    return [
        Issue(
            rule_id="backend_001",
            severity=Severity.WARNING,
            line_start=10,
            line_end=15,
            description="发现深层嵌套",
            suggestion="建议抽取方法",
            code_snippet="if condition:\n    if nested:\n        pass"
        ),
        Issue(
            rule_id="backend_002",
            severity=Severity.ERROR,
            line_start=20,
            line_end=22,
            description="可能的空指针",
            suggestion="添加 null 检查"
        )
    ]


@pytest.fixture
def sample_file_result(sample_issues) -> FileCheckResult:
    """创建示例文件检查结果"""
    return FileCheckResult(
        file_path="test.py",
        check_time=datetime.now().isoformat(),
        issues=sample_issues,
        error_count=1,
        warning_count=1,
        info_count=0,
        status="success"
    )


# ==================== 临时目录 Fixtures ====================

@pytest.fixture
def temp_dir():
    """
    创建临时目录

    测试结束后自动清理
    """
    tmp = tempfile.mkdtemp()
    yield tmp
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def temp_project_dir(temp_dir):
    """
    创建临时项目目录结构

    包含示例代码文件和规则文件
    """
    # 创建项目结构
    src_dir = os.path.join(temp_dir, "src")
    tests_dir = os.path.join(temp_dir, "tests")
    rules_dir = os.path.join(temp_dir, "rules")

    os.makedirs(src_dir)
    os.makedirs(tests_dir)
    os.makedirs(rules_dir)

    # 创建示例代码文件
    with open(os.path.join(src_dir, "main.py"), "w") as f:
        f.write("""
def test_function():
    if True:
        if True:
            if True:
                if True:
                    pass  # 嵌套过深
""")

    with open(os.path.join(src_dir, "utils.py"), "w") as f:
        f.write("""
def helper():
    x = None
    print(x.value)  # 空指针问题
""")

    # 创建测试文件
    with open(os.path.join(tests_dir, "test_main.py"), "w") as f:
        f.write("def test_example():\n    assert True\n")

    # 创建规则文件
    with open(os.path.join(rules_dir, "backend_rules.md"), "w") as f:
        f.write("""
## 代码结构

### 规则ID: backend_001
**标题**: 避免深层嵌套
**严重程度**: warning
**描述**: if-else 嵌套不应超过 3 层
""")

    return temp_dir


@pytest.fixture
def sample_code_files(temp_dir) -> List[str]:
    """
    创建一组测试代码文件

    Returns:
        文件路径列表
    """
    files = []

    for i in range(5):
        file_path = os.path.join(temp_dir, f"file_{i}.py")
        with open(file_path, "w") as f:
            f.write(f"""
def function_{i}():
    # Line {i*10}
    if True:
        if True:
            pass
""")
        files.append(file_path)

    return files


# ==================== 规则加载器 Fixtures ====================

@pytest.fixture
def mock_rules_loader(sample_rules):
    """创建 Mock RulesLoader"""
    from autocoder.checker.rules_loader import RulesLoader

    loader = Mock(spec=RulesLoader)
    loader.load_rules.return_value = sample_rules
    loader.get_applicable_rules.return_value = sample_rules
    loader.rules_dir = "rules"

    return loader


# ==================== 文件处理器 Fixtures ====================

@pytest.fixture
def mock_file_processor():
    """创建 Mock FileProcessor"""
    from autocoder.checker.file_processor import FileProcessor

    processor = Mock(spec=FileProcessor)
    processor.chunk_size = 4000
    processor.overlap = 200
    processor.is_checkable.return_value = True

    # Mock scan_files
    processor.scan_files.return_value = ["file1.py", "file2.py", "file3.py"]

    # Mock chunk_file
    processor.chunk_file.return_value = [
        CodeChunk(
            content="1 def test():\n2     pass",
            start_line=1,
            end_line=2,
            chunk_index=0,
            total_chunks=1
        )
    ]

    return processor


# ==================== 进度跟踪器 Fixtures ====================

@pytest.fixture
def mock_progress_tracker():
    """创建 Mock ProgressTracker"""
    from autocoder.checker.progress_tracker import ProgressTracker

    tracker = Mock(spec=ProgressTracker)
    tracker.state_dir = ".auto-coder/codecheck/progress"

    # Mock start_check
    tracker.start_check.return_value = "test_20251010_120000"

    # Mock load_state
    state = CheckState(
        check_id="test_20251010_120000",
        start_time=datetime.now().isoformat(),
        config={},
        total_files=["file1.py", "file2.py"],
        completed_files=["file1.py"],
        remaining_files=["file2.py"]
    )
    tracker.load_state.return_value = state

    return tracker


# ==================== 报告生成器 Fixtures ====================

@pytest.fixture
def mock_report_generator():
    """创建 Mock ReportGenerator"""
    from autocoder.checker.report_generator import ReportGenerator

    generator = Mock(spec=ReportGenerator)
    generator.output_dir = "codecheck"

    return generator


# ==================== 测试辅助函数 ====================

def create_test_file(path: str, content: str) -> str:
    """
    创建测试文件

    Args:
        path: 文件路径
        content: 文件内容

    Returns:
        文件绝对路径
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return os.path.abspath(path)


def assert_file_exists(path: str):
    """断言文件存在"""
    assert os.path.exists(path), f"文件不存在: {path}"
    assert os.path.isfile(path), f"不是文件: {path}"


def assert_dir_exists(path: str):
    """断言目录存在"""
    assert os.path.exists(path), f"目录不存在: {path}"
    assert os.path.isdir(path), f"不是目录: {path}"


# ==================== Pytest 配置 ====================

def pytest_configure(config):
    """Pytest 配置钩子"""
    # 添加自定义标记
    config.addinivalue_line(
        "markers", "unit: 单元测试"
    )
    config.addinivalue_line(
        "markers", "integration: 集成测试"
    )
    config.addinivalue_line(
        "markers", "e2e: 端到端测试"
    )
    config.addinivalue_line(
        "markers", "performance: 性能测试"
    )


def pytest_collection_modifyitems(config, items):
    """
    自动为测试添加标记

    根据测试文件路径自动添加相应的标记
    """
    for item in items:
        # 根据文件路径添加标记
        if "test_integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "test_e2e" in str(item.fspath) or "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        elif "test_performance" in str(item.fspath) or "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)
        else:
            item.add_marker(pytest.mark.unit)
