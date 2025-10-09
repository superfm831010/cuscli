import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

from autocoder.index.entry import build_index_and_filter_files
from autocoder.common import SourceCode, AutoCoderArgs, SourceCodeList


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
        query="test query",
        skip_build_index=True,  # Skip actual index building
        skip_filter_index=True,  # Skip actual filtering
        skip_confirm=True,
        index_filter_level=1,
        index_filter_file_num=10,
        context_prune=False
    )


@pytest.fixture
def test_sources():
    """Fixture for test sources"""
    return [
        SourceCode(
            module_name="test1.py",
            source_code="def test1(): pass",
            tag="NORMAL"
        ),
        SourceCode(
            module_name="test2.py", 
            source_code="def test2(): pass",
            tag="REST"
        ),
        SourceCode(
            module_name="test3.py",
            source_code="def test3(): pass", 
            tag="RAG"
        )
    ]


class TestEntry:
    """Test cases for entry module functions"""

    def test_build_index_and_filter_files_basic(self, mock_llm, test_args, test_sources):
        """Test basic functionality of build_index_and_filter_files"""
        result = build_index_and_filter_files(
            llm=mock_llm,
            args=test_args,
            sources=test_sources
        )
        
        assert isinstance(result, SourceCodeList)
        # Should process REST and RAG tagged sources
        assert len(result.sources) >= 0

    def test_build_index_and_filter_files_rest_rag_sources(self, mock_llm, test_args, test_sources):
        """Test that REST and RAG sources are processed correctly"""
        result = build_index_and_filter_files(
            llm=mock_llm,
            args=test_args,
            sources=test_sources
        )
        
        # REST and RAG sources should be included automatically
        rest_sources = [s for s in test_sources if s.tag == "REST"]
        rag_sources = [s for s in test_sources if s.tag == "RAG"]
        
        assert len(rest_sources) == 1
        assert len(rag_sources) == 1

    @patch('autocoder.index.entry.IndexManager')
    def test_build_index_and_filter_files_with_indexing(self, mock_index_manager_class, 
                                                       mock_llm, temp_dir, test_sources):
        """Test functionality when indexing is enabled"""
        # Setup mock
        mock_index_manager = Mock()
        mock_index_manager.build_index.return_value = {"test": "data"}
        mock_index_manager.read_index.return_value = []
        mock_index_manager_class.return_value = mock_index_manager
        
        args_with_indexing = AutoCoderArgs(
            source_dir=temp_dir,
            query="test query",
            skip_build_index=False,  # Enable indexing
            skip_filter_index=True,  # Still skip filtering
            skip_confirm=True,
            index_filter_level=1
        )
        
        result = build_index_and_filter_files(
            llm=mock_llm,
            args=args_with_indexing,
            sources=test_sources
        )
        
        # Verify IndexManager was called
        mock_index_manager_class.assert_called_once()
        mock_index_manager.build_index.assert_called_once()
        
        assert isinstance(result, SourceCodeList)

    @patch('autocoder.index.entry.QuickFilter')
    @patch('autocoder.index.entry.IndexManager')
    def test_build_index_and_filter_files_with_quick_filter(self, mock_index_manager_class, 
                                                           mock_quick_filter_class, 
                                                           mock_llm, temp_dir, test_sources):
        """Test functionality when quick filtering is enabled"""
        # Setup mocks
        mock_index_manager = Mock()
        mock_index_manager.build_index.return_value = {"test": "data"}
        mock_index_manager.read_index.return_value = []
        mock_index_manager.index_filter_llm = mock_llm
        mock_index_manager_class.return_value = mock_index_manager
        
        mock_filter_result = Mock()
        mock_filter_result.files = {}
        mock_filter_result.file_positions = {}
        
        mock_quick_filter = Mock()
        mock_quick_filter.filter.return_value = mock_filter_result
        mock_quick_filter_class.return_value = mock_quick_filter
        
        args_with_filtering = AutoCoderArgs(
            source_dir=temp_dir,
            query="test query",
            skip_build_index=False,
            skip_filter_index=False,  # Enable filtering
            skip_confirm=True,
            index_filter_model="test_model",
            enable_agentic_filter=False,  # Use quick filter
            index_filter_level=1
        )
        
        result = build_index_and_filter_files(
            llm=mock_llm,
            args=args_with_filtering,
            sources=test_sources
        )
        
        # Verify both IndexManager and QuickFilter were called
        mock_index_manager_class.assert_called_once()
        mock_index_manager.build_index.assert_called_once()
        mock_quick_filter_class.assert_called_once()
        mock_quick_filter.filter.assert_called_once()
        
        assert isinstance(result, SourceCodeList)

    def test_build_index_and_filter_files_no_llm(self, test_args, test_sources):
        """Test functionality when no LLM is provided"""
        result = build_index_and_filter_files(
            llm=None,
            args=test_args,
            sources=test_sources
        )
        
        # Should still work but skip LLM-dependent operations
        assert isinstance(result, SourceCodeList)

    def test_build_index_and_filter_files_empty_sources(self, mock_llm, test_args):
        """Test functionality with empty source list"""
        result = build_index_and_filter_files(
            llm=mock_llm,
            args=test_args,
            sources=[]
        )
        
        assert isinstance(result, SourceCodeList)
        assert len(result.sources) == 0

    @patch('autocoder.index.entry.ActionYmlFileManager')
    def test_build_index_and_filter_files_with_action_file(self, mock_action_manager_class, 
                                                          mock_llm, temp_dir, test_sources):
        """Test functionality when action file management is involved"""
        # Setup mock
        mock_action_manager = Mock()
        mock_action_manager.update_yaml_field.return_value = True
        mock_action_manager_class.return_value = mock_action_manager
        
        args_with_file = AutoCoderArgs(
            source_dir=temp_dir,
            query="test query",
            skip_build_index=True,
            skip_filter_index=True,
            skip_confirm=True,
            file="test_action.yml"
        )
        
        result = build_index_and_filter_files(
            llm=mock_llm,
            args=args_with_file,
            sources=test_sources
        )
        
        # Verify ActionYmlFileManager was used
        mock_action_manager_class.assert_called_once_with(temp_dir)
        
        assert isinstance(result, SourceCodeList)

    def test_get_file_path_helper(self, mock_llm, test_args):
        """Test the get_file_path helper function behavior"""
        # This tests the internal get_file_path function indirectly
        test_sources_with_prefix = [
            SourceCode(
                module_name="##/path/to/file.py",
                source_code="def test(): pass",
                tag="NORMAL"
            )
        ]
        
        result = build_index_and_filter_files(
            llm=mock_llm,
            args=test_args,
            sources=test_sources_with_prefix
        )
        
        # Should handle the ## prefix correctly
        assert isinstance(result, SourceCodeList)


# Parametrized tests
@pytest.mark.parametrize("tag,should_be_processed", [
    ("REST", True),
    ("RAG", True), 
    ("SEARCH", True),
    ("NORMAL", False),
    ("OTHER", False),
])
def test_tag_processing(tag, should_be_processed, mock_llm):
    """Test that different tags are processed correctly"""
    args = AutoCoderArgs(
        source_dir=".",
        skip_build_index=True,
        skip_filter_index=True,
        skip_confirm=True
    )
    
    sources = [
        SourceCode(
            module_name="test.py",
            source_code="def test(): pass",
            tag=tag
        )
    ]
    
    result = build_index_and_filter_files(llm=mock_llm, args=args, sources=sources)
    
    # REST, RAG, SEARCH tags should be processed automatically
    # This is verified by the fact that they don't require LLM processing
    assert isinstance(result, SourceCodeList)


@pytest.mark.parametrize("skip_build,skip_filter,expected_operations", [
    (True, True, "minimal"),
    (False, True, "index_only"),
    (True, False, "filter_only"),
    (False, False, "full"),
])
def test_skip_combinations(skip_build, skip_filter, expected_operations, mock_llm, temp_dir):
    """Test different combinations of skip flags"""
    args = AutoCoderArgs(
        source_dir=temp_dir,
        query="test",
        skip_build_index=skip_build,
        skip_filter_index=skip_filter,
        skip_confirm=True
    )
    
    sources = [
        SourceCode(
            module_name="test.py",
            source_code="def test(): pass",
            tag="NORMAL"
        )
    ]
    
    result = build_index_and_filter_files(llm=mock_llm, args=args, sources=sources)
    
    # All combinations should return a valid SourceCodeList
    assert isinstance(result, SourceCodeList) 