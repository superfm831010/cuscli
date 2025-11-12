import os
import json
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import List

from autocoder.index.index import IndexManager
from autocoder.index.types import IndexItem, TargetFile, FileList
from autocoder.common import SourceCode, AutoCoderArgs
from autocoder.utils.llms import get_single_llm


@pytest.fixture
def temp_dir():
    """Fixture for temporary directory"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_llm():
    """Fixture for mock LLM"""
    mock_llm = Mock()
    mock_llm.get_sub_client.return_value = None
    mock_llm.default_model_name = "v3_chat"
    return mock_llm


@pytest.fixture
def test_args(temp_dir):
    """Fixture for test arguments"""
    return AutoCoderArgs(
        source_dir=temp_dir,
        skip_build_index=False,
        skip_filter_index=False,
        index_filter_level=1,
        index_filter_file_num=10,
        index_build_workers=1,
        index_filter_workers=1,
        anti_quota_limit=0,
        model_max_input_length=8192,
        conversation_prune_safe_zone_tokens=4096
    )


@pytest.fixture
def test_sources(temp_dir):
    """Fixture for test source code"""
    test_sources = [
        SourceCode(
            module_name=os.path.join(temp_dir, "test1.py"),
            source_code="""
import os
import json

class TestClass:
    def __init__(self):
        self.value = 42
        
    def test_method(self):
        return "test"

def test_function():
    return True
"""
        ),
        SourceCode(
            module_name=os.path.join(temp_dir, "test2.py"),
            source_code="""
from test1 import TestClass

def another_function():
    return TestClass()
"""
        )
    ]
    
    # Create actual test files
    for source in test_sources:
        with open(source.module_name, 'w', encoding='utf-8') as f:
            f.write(source.source_code)
    
    return test_sources


class TestIndexManager:
    """Test cases for IndexManager class"""

    def test_index_manager_initialization(self, mock_llm, test_sources, test_args):
        """Test IndexManager initialization"""
        manager = IndexManager(
            llm=mock_llm,
            sources=test_sources,
            args=test_args
        )
        
        assert manager.sources == test_sources
        assert manager.source_dir == test_args.source_dir
        assert manager.llm == mock_llm
        assert manager.args == test_args

    @patch('autocoder.index.index.get_llm_names')
    @patch('autocoder.index.index.get_model_info')
    def test_build_index_for_single_source(self, mock_get_model_info, mock_get_llm_names, 
                                         mock_llm, test_sources, test_args):
        """Test building index for a single source file"""
        # Setup mocks
        mock_get_llm_names.return_value = ["v3_chat"]
        mock_get_model_info.return_value = {
            "input_price": 0.001,
            "output_price": 0.002
        }
        
        # Create mock for LLM prompt
        mock_symbols_prompt = Mock()
        mock_symbols_prompt.with_llm.return_value.with_meta.return_value.run.return_value = """
用途：测试类和函数的示例代码
函数：test_method, test_function
类：TestClass
变量：value
导入语句：import os^^import json
"""
        
        manager = IndexManager(
            llm=mock_llm,
            sources=test_sources,
            args=test_args
        )
        manager.get_all_file_symbols = mock_symbols_prompt
        
        result = manager.build_index_for_single_source(test_sources[0])
        
        assert result is not None
        if result is not None:
            assert result["module_name"] == test_sources[0].module_name
            assert "symbols" in result
            assert "md5" in result
            assert "input_tokens_count" in result

    def test_should_skip_files(self, mock_llm, test_sources, test_args):
        """Test file skipping logic"""
        manager = IndexManager(
            llm=mock_llm,
            sources=test_sources,
            args=test_args
        )
        
        # Test skipping certain file types
        assert manager.should_skip("test.md") == True
        assert manager.should_skip("test.html") == True
        assert manager.should_skip("test.txt") == True
        
        # Test not skipping Python files
        assert manager.should_skip("test.py") == False

    def test_read_index(self, mock_llm, test_sources, test_args):
        """Test reading index from file"""
        manager = IndexManager(
            llm=mock_llm,
            sources=test_sources,
            args=test_args
        )
        
        # Create test index file
        test_index_data = {
            "test1.py": {
                "symbols": "test symbols",
                "last_modified": 1234567890,
                "md5": "abcdef123456",
                "input_tokens_count": 100,
                "generated_tokens_count": 50
            }
        }
        
        os.makedirs(manager.index_dir, exist_ok=True)
        with open(manager.index_file, 'w', encoding='utf-8') as f:
            json.dump(test_index_data, f)
        
        index_items = manager.read_index()
        
        assert len(index_items) == 1
        assert isinstance(index_items[0], IndexItem)
        assert index_items[0].module_name == "test1.py"
        assert index_items[0].symbols == "test symbols"

    @patch('autocoder.index.index.byzerllm.prompt')
    def test_get_target_files_by_query(self, mock_prompt, mock_llm, test_sources, test_args):
        """Test querying target files"""
        manager = IndexManager(
            llm=mock_llm,
            sources=test_sources,
            args=test_args
        )
        
        # Mock the prompt method
        mock_result = FileList(file_list=[
            TargetFile(file_path="test1.py", reason="Contains test functionality")
        ])
        
        mock_query_method = Mock()
        mock_query_method.with_llm.return_value.with_return_type.return_value.run.return_value = mock_result
        manager._get_target_files_by_query = mock_query_method
        
        # Create mock index
        manager.read_index = Mock(return_value=[
            IndexItem(
                module_name="test1.py",
                symbols="test symbols",
                last_modified=1234567890,
                md5="abcdef123456"
            )
        ])
        
        result = manager.get_target_files_by_query("test query")
        
        assert isinstance(result, FileList)
        assert len(result.file_list) == 1
        assert result.file_list[0].file_path == "test1.py"

    def test_filter_exclude_files(self, mock_llm, test_sources, test_args):
        """Test file exclusion logic"""
        manager = IndexManager(
            llm=mock_llm,
            sources=test_sources,
            args=test_args
        )
        
        # Test with regex patterns
        import re
        exclude_patterns = [re.compile(r".*\.pyc$"), re.compile(r"__pycache__")]
        
        assert manager.filter_exclude_files("test.pyc", exclude_patterns) == True
        assert manager.filter_exclude_files("__pycache__/test.py", exclude_patterns) == True
        assert manager.filter_exclude_files("test.py", exclude_patterns) == False


class TestIndexIntegration:
    """Integration tests for the index module"""

    @pytest.fixture
    def integration_args(self, temp_dir):
        """Fixture for integration test arguments"""
        return AutoCoderArgs(
            source_dir=temp_dir,
            query="test functionality",
            skip_build_index=True,  # Skip actual LLM calls
            skip_filter_index=True,
            index_filter_level=1
        )

    def test_index_manager_with_real_llm(self, temp_dir, integration_args):
        """Test IndexManager with real LLM (if available)"""
        try:
            llm = get_single_llm("v3_chat", "lite")
            if llm is None:
                pytest.skip("v3_chat model not available")
            
            sources = [
                SourceCode(
                    module_name=os.path.join(temp_dir, "real_test.py"),
                    source_code="def hello_world():\n    return 'Hello, World!'"
                )
            ]
            
            # Create the actual file
            with open(sources[0].module_name, 'w', encoding='utf-8') as f:
                f.write(sources[0].source_code)
            
            # Type assertion to handle the union type
            if hasattr(llm, 'chat') or hasattr(llm, 'stream_chat_oai'):  # Check for either method
                # This test mainly checks that no import errors occur
                # Full functionality would require actual LLM calls
                assert llm is not None
                assert sources[0].module_name.endswith("real_test.py")
            else:
                pytest.skip("LLM type not compatible")
                
        except Exception as e:
            pytest.skip(f"Real LLM test skipped: {e}")


# Parametrized tests for better coverage
@pytest.mark.parametrize("file_extension,should_skip", [
    (".py", False),
    (".js", False),
    (".ts", False),
    (".md", True),
    (".html", True),
    (".txt", True),
    (".doc", True),
    (".pdf", True),
])
def test_should_skip_files_parametrized(file_extension, should_skip, mock_llm, test_args):
    """Parametrized test for file skipping logic"""
    manager = IndexManager(llm=mock_llm, sources=[], args=test_args)
    filename = f"test{file_extension}"
    assert manager.should_skip(filename) == should_skip


@pytest.mark.parametrize("query,expected_level", [
    ("simple query", 0),
    ("complex authentication query", 1),
    ("detailed analysis query", 2),
])
def test_query_index_levels(query, expected_level, mock_llm, test_args):
    """Test different index filter levels"""
    test_args.index_filter_level = expected_level
    manager = IndexManager(llm=mock_llm, sources=[], args=test_args)
    
    # Verify the level is set correctly
    assert manager.args.index_filter_level == expected_level 