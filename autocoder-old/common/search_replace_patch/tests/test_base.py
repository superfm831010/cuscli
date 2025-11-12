"""
Test module for base classes and enums
"""

import unittest
from typing import List, Tuple

from ..base import BaseReplacer, ReplaceResult, ReplaceStrategy


class MockReplacer(BaseReplacer):
    """Mock replacer for testing BaseReplacer"""
    
    def __init__(self, strategy: ReplaceStrategy = ReplaceStrategy.STRING):
        super().__init__(strategy)
        self.should_succeed = True
        self.should_handle = True
    
    def replace(self, content: str, search_blocks: List[Tuple[str, str]]) -> ReplaceResult:
        if self.should_succeed:
            return ReplaceResult(
                success=True,
                message="Mock replacement successful",
                new_content=content + "_modified",
                applied_count=len(search_blocks),
                total_count=len(search_blocks)
            )
        else:
            return ReplaceResult(
                success=False,
                message="Mock replacement failed",
                total_count=len(search_blocks)
            )
    
    def can_handle(self, content: str, search_blocks: List[Tuple[str, str]]) -> bool:
        return self.should_handle


class TestReplaceStrategy(unittest.TestCase):
    """Test ReplaceStrategy enum"""
    
    def test_strategy_enum_values(self):
        """Test that strategy enum has correct values"""
        self.assertEqual(ReplaceStrategy.STRING.value, "string")
        self.assertEqual(ReplaceStrategy.PATCH.value, "patch")
        self.assertEqual(ReplaceStrategy.SIMILARITY.value, "similarity")
    
    def test_enum_uniqueness(self):
        """Test that all enum values are unique"""
        values = [strategy.value for strategy in ReplaceStrategy]
        self.assertEqual(len(values), len(set(values)))


class TestReplaceResult(unittest.TestCase):
    """Test ReplaceResult dataclass"""
    
    def test_default_values(self):
        """Test default values of ReplaceResult"""
        result = ReplaceResult(success=True, message="test")
        
        self.assertTrue(result.success)
        self.assertEqual(result.message, "test")
        self.assertIsNone(result.new_content)
        self.assertEqual(result.applied_count, 0)
        self.assertEqual(result.total_count, 0)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.metadata, {})
    
    def test_full_initialization(self):
        """Test full initialization of ReplaceResult"""
        result = ReplaceResult(
            success=True,
            message="test message",
            new_content="new content",
            applied_count=5,
            total_count=10,
            errors=["error1", "error2"],
            metadata={"key": "value"}
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.message, "test message")
        self.assertEqual(result.new_content, "new content")
        self.assertEqual(result.applied_count, 5)
        self.assertEqual(result.total_count, 10)
        self.assertEqual(result.errors, ["error1", "error2"])
        self.assertEqual(result.metadata, {"key": "value"})


class TestBaseReplacer(unittest.TestCase):
    """Test BaseReplacer abstract base class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.replacer = MockReplacer()
    
    def test_initialization(self):
        """Test proper initialization"""
        replacer = MockReplacer(ReplaceStrategy.SIMILARITY)
        self.assertEqual(replacer.strategy, ReplaceStrategy.SIMILARITY)
    
    def test_get_strategy_name(self):
        """Test get_strategy_name method"""
        self.assertEqual(self.replacer.get_strategy_name(), "string")
        
        similarity_replacer = MockReplacer(ReplaceStrategy.SIMILARITY)
        self.assertEqual(similarity_replacer.get_strategy_name(), "similarity")
    
    def test_validate_search_blocks_empty(self):
        """Test validation with empty search blocks"""
        self.assertFalse(self.replacer.validate_search_blocks([]))
    
    def test_validate_search_blocks_valid(self):
        """Test validation with valid search blocks"""
        valid_blocks = [
            ("old_text", "new_text"),
            ("another_old", "another_new"),
        ]
        self.assertTrue(self.replacer.validate_search_blocks(valid_blocks))
    
    def test_validate_search_blocks_empty_search(self):
        """Test validation with empty search text"""
        # Empty search text is now valid for insertion
        valid_blocks = [
            ("", "new_text"),  # This is now valid for insertion
            ("old_text", "new_text"),
        ]
        self.assertTrue(self.replacer.validate_search_blocks(valid_blocks))
        
        # Only whitespace search text is still invalid
        invalid_blocks = [
            ("   ", "new_text"),
        ]
        self.assertFalse(self.replacer.validate_search_blocks(invalid_blocks))
    
    def test_validate_search_blocks_wrong_type(self):
        """Test validation with wrong types"""
        invalid_blocks = [
            (123, "new_text"),
            ("old_text", 456),
        ]
        self.assertFalse(self.replacer.validate_search_blocks(invalid_blocks))
    
    def test_replace_abstract_method_implemented(self):
        """Test that replace method is implemented in mock"""
        result = self.replacer.replace("content", [("old", "new")])
        self.assertIsInstance(result, ReplaceResult)
        self.assertTrue(result.success)
    
    def test_can_handle_abstract_method_implemented(self):
        """Test that can_handle method is implemented in mock"""
        can_handle = self.replacer.can_handle("content", [("old", "new")])
        self.assertIsInstance(can_handle, bool)
        self.assertTrue(can_handle)
    
    def test_mock_replacer_success(self):
        """Test mock replacer success case"""
        self.replacer.should_succeed = True
        result = self.replacer.replace("test_content", [("old", "new")])
        
        self.assertTrue(result.success)
        self.assertEqual(result.message, "Mock replacement successful")
        self.assertEqual(result.new_content, "test_content_modified")
        self.assertEqual(result.applied_count, 1)
        self.assertEqual(result.total_count, 1)
    
    def test_mock_replacer_failure(self):
        """Test mock replacer failure case"""
        self.replacer.should_succeed = False
        result = self.replacer.replace("test_content", [("old", "new")])
        
        self.assertFalse(result.success)
        self.assertEqual(result.message, "Mock replacement failed")
        self.assertIsNone(result.new_content)
        self.assertEqual(result.applied_count, 0)
        self.assertEqual(result.total_count, 1)
    
    def test_mock_replacer_can_handle(self):
        """Test mock replacer can_handle method"""
        self.replacer.should_handle = True
        self.assertTrue(self.replacer.can_handle("content", [("old", "new")]))
        
        self.replacer.should_handle = False
        self.assertFalse(self.replacer.can_handle("content", [("old", "new")]))


if __name__ == '__main__':
    unittest.main() 