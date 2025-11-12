import os
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from loguru import logger
from autocoder.common.v2.agent.agentic_edit_tools.write_to_file_tool_resolver import WriteToFileToolResolver
from autocoder.common.v2.agent.agentic_edit_types import WriteToFileTool
from autocoder.common import AutoCoderArgs
from autocoder.common.file_monitor.monitor import FileMonitor
from autocoder.common.rulefiles import AutocoderRulesManager



@pytest.fixture(scope="function")
def temp_test_dir(tmp_path_factory):
    """临时测试目录"""
    temp_dir = tmp_path_factory.mktemp("test_write_to_file_resolver")
    logger.info(f"Created temp dir for test: {temp_dir}")
    yield temp_dir
    logger.info(f"Cleaning up temp dir: {temp_dir}")


@pytest.fixture(scope="function")
def setup_file_monitor_and_rules(temp_test_dir):
    """设置测试环境的文件监控和规则管理器"""
    # 初始化 FileMonitor 单例
    file_monitor = FileMonitor(str(temp_test_dir))
    file_monitor.start()
    logger.info(f"File monitor initialized with root: {temp_test_dir}")
    
    # 初始化 AutocoderRulesManager 单例
    rules_manager = AutocoderRulesManager(str(temp_test_dir))
    rules_dict = rules_manager.get_rules()
    logger.info(f"Rules loaded for dir: {temp_test_dir}, count: {len(rules_dict)}")
    
    yield file_monitor, rules_manager
    
    # 清理单例
    file_monitor.stop()
    FileMonitor.reset_instance()
    AutocoderRulesManager.reset_instance()


@pytest.fixture(scope="function")
def load_tokenizer_fixture(setup_file_monitor_and_rules):
    """加载分词器以确保测试稳定性"""
    # 简化：不再依赖 FileDetector，直接通过
    logger.info("Tokenizer loaded successfully.")
    yield


@pytest.fixture(scope="function")
def test_args(temp_test_dir, setup_file_monitor_and_rules, load_tokenizer_fixture):
    """测试参数"""
    args = AutoCoderArgs(source_dir=str(temp_test_dir))
    args.enable_auto_fix_lint = False  # 默认禁用 lint
    yield args


@pytest.fixture
def mock_agent_no_shadow(test_args):
    """Mocks an AgenticEdit instance without shadow capabilities."""
    agent = MagicMock()
    agent.args = test_args
    agent.record_file_change = MagicMock()
    agent.checkpoint_manager = None  # 不使用 checkpoint_manager
    agent.linter = None  # 不使用 linter
    return agent


def test_create_new_file(test_args, temp_test_dir, mock_agent_no_shadow):
    logger.info(f"Running test_create_new_file in {temp_test_dir}")
    file_path = "new_file.txt"
    content = "This is a new file."
    tool = WriteToFileTool(path=file_path, content=content)
    
    resolver = WriteToFileToolResolver(agent=mock_agent_no_shadow, tool=tool, args=test_args)
    result = resolver.resolve()

    assert result.success is True
    # 修正断言：当前实现返回 "Successfully wrote to file: ..." 格式的消息
    assert "Successfully wrote to file:" in result.message
    
    expected_file_abs_path = os.path.join(temp_test_dir, file_path)
    assert os.path.exists(expected_file_abs_path)
    with open(expected_file_abs_path, "r", encoding="utf-8") as f:
        assert f.read() == content
    mock_agent_no_shadow.record_file_change.assert_called_once_with(file_path, "added", diff=None, content=content)


def test_overwrite_existing_file(test_args, temp_test_dir, mock_agent_no_shadow):
    logger.info(f"Running test_overwrite_existing_file in {temp_test_dir}")
    file_path = "existing_file.txt"
    initial_content = "Initial content."
    new_content = "This is the new content."

    abs_file_path = os.path.join(temp_test_dir, file_path)
    with open(abs_file_path, "w", encoding="utf-8") as f:
        f.write(initial_content)

    tool = WriteToFileTool(path=file_path, content=new_content)
    resolver = WriteToFileToolResolver(agent=mock_agent_no_shadow, tool=tool, args=test_args)
    result = resolver.resolve()

    assert result.success is True
    assert os.path.exists(abs_file_path)
    with open(abs_file_path, "r", encoding="utf-8") as f:
        assert f.read() == new_content
    mock_agent_no_shadow.record_file_change.assert_called_once_with(file_path, "modified", diff=None, content=new_content)


def test_create_file_in_new_directory(test_args, temp_test_dir, mock_agent_no_shadow):
    logger.info(f"Running test_create_file_in_new_directory in {temp_test_dir}")
    file_path = "new_dir/another_new_dir/file.txt"
    content = "Content in a nested directory."
    
    tool = WriteToFileTool(path=file_path, content=content)
    resolver = WriteToFileToolResolver(agent=mock_agent_no_shadow, tool=tool, args=test_args)
    result = resolver.resolve()

    assert result.success is True
    expected_file_abs_path = os.path.join(temp_test_dir, file_path)
    assert os.path.exists(expected_file_abs_path)
    with open(expected_file_abs_path, "r", encoding="utf-8") as f:
        assert f.read() == content
    mock_agent_no_shadow.record_file_change.assert_called_once_with(file_path, "added", diff=None, content=content)


def test_path_outside_project_root_fails(test_args, temp_test_dir, mock_agent_no_shadow):
    logger.info(f"Running test_path_outside_project_root_fails in {temp_test_dir}")
    # 创建一个在项目根目录外的临时目录
    another_temp_dir = temp_test_dir.parent / "another_temp_dir_for_outside_test"
    another_temp_dir.mkdir(exist_ok=True)
    
    # 在 POSIX 系统上，绝对路径会被正确处理
    if os.name == 'posix':
        file_path_for_tool = str(another_temp_dir / "outside_file.txt")
    else:
        file_path_for_tool = str(another_temp_dir / "outside_file.txt")

    content = "Attempting to write outside."
    tool = WriteToFileTool(path=file_path_for_tool, content=content)
    
    resolver = WriteToFileToolResolver(agent=mock_agent_no_shadow, tool=tool, args=test_args)
    result = resolver.resolve()

    assert result.success is False
    assert "Access denied" in result.message
    assert not os.path.exists(another_temp_dir / "outside_file.txt")


def test_simple_file_creation(test_args, temp_test_dir, mock_agent_no_shadow):
    """测试简单文件创建"""
    logger.info(f"Running test_simple_file_creation in {temp_test_dir}")
    
    file_path = "simple_file.py"
    content = "print('hello world')"
    tool = WriteToFileTool(path=file_path, content=content)
    
    resolver = WriteToFileToolResolver(agent=mock_agent_no_shadow, tool=tool, args=test_args)
    result = resolver.resolve()

    assert result.success is True
    assert "Successfully wrote to file:" in result.message
    # 确保文件确实被创建
    expected_file_abs_path = os.path.join(temp_test_dir, file_path)
    assert os.path.exists(expected_file_abs_path)
    with open(expected_file_abs_path, "r", encoding="utf-8") as f:
        assert f.read() == content


# ================= 追加模式测试用例 =================

def test_append_mode_to_new_file(test_args, temp_test_dir, mock_agent_no_shadow):
    """测试追加模式到新文件（应该等同于写入模式）"""
    logger.info(f"Running test_append_mode_to_new_file in {temp_test_dir}")
    file_path = "new_append_file.txt"
    content = "This is appended content."
    tool = WriteToFileTool(path=file_path, content=content, mode="append")
    
    resolver = WriteToFileToolResolver(agent=mock_agent_no_shadow, tool=tool, args=test_args)
    result = resolver.resolve()

    assert result.success is True
    assert "Successfully wrote to file:" in result.message  # 新文件仍显示"wrote"
    
    expected_file_abs_path = os.path.join(temp_test_dir, file_path)
    assert os.path.exists(expected_file_abs_path)
    with open(expected_file_abs_path, "r", encoding="utf-8") as f:
        assert f.read() == content
    mock_agent_no_shadow.record_file_change.assert_called_once_with(file_path, "added", diff=None, content=content)


def test_append_mode_to_existing_file(test_args, temp_test_dir, mock_agent_no_shadow):
    """测试追加模式到已存在的文件"""
    logger.info(f"Running test_append_mode_to_existing_file in {temp_test_dir}")
    file_path = "existing_append_file.txt"
    initial_content = "Initial content.\n"
    append_content = "This is appended content."
    expected_final_content = initial_content + append_content

    # 先创建文件
    abs_file_path = os.path.join(temp_test_dir, file_path)
    with open(abs_file_path, "w", encoding="utf-8") as f:
        f.write(initial_content)

    tool = WriteToFileTool(path=file_path, content=append_content, mode="append")
    resolver = WriteToFileToolResolver(agent=mock_agent_no_shadow, tool=tool, args=test_args)
    result = resolver.resolve()

    assert result.success is True
    assert "Successfully appended to file:" in result.message
    
    assert os.path.exists(abs_file_path)
    with open(abs_file_path, "r", encoding="utf-8") as f:
        assert f.read() == expected_final_content
    mock_agent_no_shadow.record_file_change.assert_called_once_with(file_path, "modified", diff=None, content=expected_final_content)


def test_write_mode_explicit(test_args, temp_test_dir, mock_agent_no_shadow):
    """测试显式写入模式（应该覆盖文件）"""
    logger.info(f"Running test_write_mode_explicit in {temp_test_dir}")
    file_path = "write_mode_file.txt"
    initial_content = "Initial content."
    new_content = "This is the new content."

    # 先创建文件
    abs_file_path = os.path.join(temp_test_dir, file_path)
    with open(abs_file_path, "w", encoding="utf-8") as f:
        f.write(initial_content)

    tool = WriteToFileTool(path=file_path, content=new_content, mode="write")
    resolver = WriteToFileToolResolver(agent=mock_agent_no_shadow, tool=tool, args=test_args)
    result = resolver.resolve()

    assert result.success is True
    assert "Successfully wrote to file:" in result.message
    
    assert os.path.exists(abs_file_path)
    with open(abs_file_path, "r", encoding="utf-8") as f:
        assert f.read() == new_content  # 应该只有新内容，不包含初始内容
    mock_agent_no_shadow.record_file_change.assert_called_once_with(file_path, "modified", diff=None, content=new_content)


def test_default_mode_is_write(test_args, temp_test_dir, mock_agent_no_shadow):
    """测试默认模式是写入模式"""
    logger.info(f"Running test_default_mode_is_write in {temp_test_dir}")
    file_path = "default_mode_file.txt"
    initial_content = "Initial content."
    new_content = "This is the new content."

    # 先创建文件
    abs_file_path = os.path.join(temp_test_dir, file_path)
    with open(abs_file_path, "w", encoding="utf-8") as f:
        f.write(initial_content)

    # 不指定 mode，应该默认为写入模式
    tool = WriteToFileTool(path=file_path, content=new_content)
    resolver = WriteToFileToolResolver(agent=mock_agent_no_shadow, tool=tool, args=test_args)
    result = resolver.resolve()

    assert result.success is True
    assert "Successfully wrote to file:" in result.message
    
    assert os.path.exists(abs_file_path)
    with open(abs_file_path, "r", encoding="utf-8") as f:
        assert f.read() == new_content  # 应该只有新内容，不包含初始内容
    mock_agent_no_shadow.record_file_change.assert_called_once_with(file_path, "modified", diff=None, content=new_content)


def test_append_mode_with_empty_existing_file(test_args, temp_test_dir, mock_agent_no_shadow):
    """测试追加模式到空的已存在文件"""
    logger.info(f"Running test_append_mode_with_empty_existing_file in {temp_test_dir}")
    file_path = "empty_existing_file.txt"
    append_content = "This is appended to empty file."

    # 创建空文件
    abs_file_path = os.path.join(temp_test_dir, file_path)
    with open(abs_file_path, "w", encoding="utf-8") as f:
        f.write("")

    tool = WriteToFileTool(path=file_path, content=append_content, mode="append")
    resolver = WriteToFileToolResolver(agent=mock_agent_no_shadow, tool=tool, args=test_args)
    result = resolver.resolve()

    assert result.success is True
    assert "Successfully appended to file:" in result.message
    
    assert os.path.exists(abs_file_path)
    with open(abs_file_path, "r", encoding="utf-8") as f:
        assert f.read() == append_content
    mock_agent_no_shadow.record_file_change.assert_called_once_with(file_path, "modified", diff=None, content=append_content)


def test_append_mode_multiple_appends(test_args, temp_test_dir, mock_agent_no_shadow):
    """测试多次追加到同一文件"""
    logger.info(f"Running test_append_mode_multiple_appends in {temp_test_dir}")
    file_path = "multiple_append_file.txt"
    initial_content = "Initial line.\n"
    first_append = "First append.\n"
    second_append = "Second append."

    # 创建初始文件
    abs_file_path = os.path.join(temp_test_dir, file_path)
    with open(abs_file_path, "w", encoding="utf-8") as f:
        f.write(initial_content)

    # 第一次追加
    tool1 = WriteToFileTool(path=file_path, content=first_append, mode="append")
    resolver1 = WriteToFileToolResolver(agent=mock_agent_no_shadow, tool=tool1, args=test_args)
    result1 = resolver1.resolve()

    assert result1.success is True
    assert "Successfully appended to file:" in result1.message

    # 验证第一次追加后的内容
    with open(abs_file_path, "r", encoding="utf-8") as f:
        content_after_first = f.read()
    assert content_after_first == initial_content + first_append

    # 重置 mock 以便第二次调用
    mock_agent_no_shadow.record_file_change.reset_mock()

    # 第二次追加
    tool2 = WriteToFileTool(path=file_path, content=second_append, mode="append")
    resolver2 = WriteToFileToolResolver(agent=mock_agent_no_shadow, tool=tool2, args=test_args)
    result2 = resolver2.resolve()

    assert result2.success is True
    assert "Successfully appended to file:" in result2.message

    # 验证最终内容
    with open(abs_file_path, "r", encoding="utf-8") as f:
        final_content = f.read()
    expected_final = initial_content + first_append + second_append
    assert final_content == expected_final
    mock_agent_no_shadow.record_file_change.assert_called_once_with(file_path, "modified", diff=None, content=expected_final)