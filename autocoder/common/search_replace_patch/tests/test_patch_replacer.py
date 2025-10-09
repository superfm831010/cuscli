"""
Test module for PatchReplacer
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import os

from ..patch_replacer import PatchReplacer
from ..base import ReplaceStrategy

# Type ignore for MagicMock assignments in tests
# pyright: reportAttributeAccessIssue=false


class TestPatchReplacer(unittest.TestCase):
    """Test PatchReplacer functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.replacer = PatchReplacer(use_patch_ng=True)
        self.unidiff_replacer = PatchReplacer(use_patch_ng=False)
    
    def test_initialization(self):
        """Test proper initialization"""
        self.assertEqual(self.replacer.strategy, ReplaceStrategy.PATCH)
        self.assertTrue(self.replacer.use_patch_ng)
        self.assertFalse(self.unidiff_replacer.use_patch_ng)
    
    def test_search_blocks_to_unified_diff(self):
        """Test converting search blocks to unified diff format"""
        search_blocks = [
            ("old_line1\nold_line2", "new_line1\nnew_line2"),
            ("old_line3", "new_line3")
        ]
        
        diff = self.replacer._search_blocks_to_unified_diff(search_blocks, "test.txt")
        
        self.assertIn("--- a/test.txt", diff)
        self.assertIn("+++ b/test.txt", diff)
        self.assertIn("@@", diff)
        self.assertIn("-old_line1", diff)
        self.assertIn("+new_line1", diff)
        self.assertIn("-old_line3", diff)
        self.assertIn("+new_line3", diff)
    
    def test_replace_no_patch_module(self):
        """Test replace when no patch module is available"""
        replacer = PatchReplacer()
        replacer._patch_module = None
        
        content = "Hello world"
        search_blocks = [("Hello", "Hi")]
        
        result = replacer.replace(content, search_blocks)
        
        self.assertFalse(result.success)
        self.assertIn("No patch module available", result.message)
    
    def test_replace_invalid_search_blocks(self):
        """Test replace with invalid search blocks"""
        content = "Hello world"
        
        # Empty search blocks
        result = self.replacer.replace(content, [])
        self.assertFalse(result.success)
        self.assertIn("Invalid search blocks", result.message)
        
        # Empty search text is now valid for insertion
        result = self.replacer.replace(content, [("", "replacement")])
        self.assertTrue(result.success)  # Should succeed as insertion
    
    def test_can_handle(self):
        """Test can_handle method"""
        # Should handle valid blocks when module is available
        self.replacer._patch_module = MagicMock()  # type: ignore
        self.assertTrue(self.replacer.can_handle("content", [("old", "new")]))
        
        # Should not handle when no module available
        self.replacer._patch_module = None
        self.assertFalse(self.replacer.can_handle("content", [("old", "new")]))
        
        # Should not handle invalid blocks
        self.replacer._patch_module = MagicMock()  # type: ignore
        self.assertFalse(self.replacer.can_handle("content", []))
    
    @patch('tempfile.NamedTemporaryFile')
    @patch('builtins.open', new_callable=mock_open, read_data="Hello AutoCoder")
    @patch('os.path.exists', return_value=True)
    @patch('os.unlink')
    def test_apply_patch_ng_success(self, mock_unlink, mock_exists, mock_file, mock_temp):
        """Test successful patch application with patch-ng"""
        # Mock temp file
        mock_temp_file = MagicMock()
        mock_temp_file.name = "/tmp/test.txt"
        mock_temp.return_value.__enter__.return_value = mock_temp_file
        
        # Mock patch-ng
        mock_patch_module = MagicMock()
        mock_patchset = MagicMock()
        mock_patchset.apply.return_value = True
        mock_patch_module.PatchSet.from_string.return_value = mock_patchset
        
        self.replacer._patch_module = mock_patch_module
        
        content = "Hello world"
        diff_content = "some diff content"
        
        result = self.replacer._apply_patch_ng(content, diff_content, "test.txt")
        
        self.assertEqual(result, "Hello AutoCoder")
        mock_patchset.apply.assert_called_once()
    
    @patch('tempfile.NamedTemporaryFile')
    def test_apply_patch_ng_failure(self, mock_temp):
        """Test failed patch application with patch-ng"""
        # Mock temp file
        mock_temp_file = MagicMock()
        mock_temp_file.name = "/tmp/test.txt"
        mock_temp.return_value.__enter__.return_value = mock_temp_file
        
        # Mock patch-ng failure
        mock_patch_module = MagicMock()
        mock_patchset = MagicMock()
        mock_patchset.apply.return_value = False
        mock_patch_module.PatchSet.from_string.return_value = mock_patchset
        
        self.replacer._patch_module = mock_patch_module
        
        content = "Hello world"
        diff_content = "some diff content"
        
        result = self.replacer._apply_patch_ng(content, diff_content, "test.txt")
        
        self.assertIsNone(result)
    
    @patch('tempfile.NamedTemporaryFile')
    def test_apply_patch_ng_exception(self, mock_temp):
        """Test exception handling in patch-ng application"""
        # Mock temp file
        mock_temp_file = MagicMock()
        mock_temp_file.name = "/tmp/test.txt"
        mock_temp.return_value.__enter__.return_value = mock_temp_file
        
        # Mock patch-ng exception
        mock_patch_module = MagicMock()
        mock_patch_module.PatchSet.from_string.side_effect = Exception("Patch error")
        
        self.replacer._patch_module = mock_patch_module
        
        content = "Hello world"
        diff_content = "some diff content"
        
        result = self.replacer._apply_patch_ng(content, diff_content, "test.txt")
        
        self.assertIsNone(result)
    
    def test_apply_unidiff_no_patches(self):
        """Test unidiff application when no patches are found"""
        mock_patch_module = MagicMock()
        mock_patchset = MagicMock()
        mock_patchset.__bool__.return_value = False
        mock_patch_module.PatchSet.return_value = mock_patchset
        
        self.replacer._patch_module = mock_patch_module
        
        content = "Hello world"
        diff_content = "some diff content"
        
        result = self.replacer._apply_unidiff(content, diff_content, "test.txt")
        
        self.assertIsNone(result)
    
    def test_apply_unidiff_success(self):
        """Test successful unidiff application"""
        mock_patch_module = MagicMock()
        mock_patchset = MagicMock()
        mock_patchset.__bool__.return_value = True
        mock_patch_file = MagicMock()
        mock_patchset.__getitem__.return_value = mock_patch_file
        mock_patch_module.PatchSet.return_value = mock_patchset
        
        self.replacer._patch_module = mock_patch_module
        
        content = "Hello world"
        diff_content = "some diff content"
        
        with patch.object(self.replacer, '_apply_patch_to_lines', return_value=["Hello AutoCoder"]):
            result = self.replacer._apply_unidiff(content, diff_content, "test.txt")
            
            self.assertEqual(result, "Hello AutoCoder")
    
    def test_apply_unidiff_exception(self):
        """Test exception handling in unidiff application"""
        mock_patch_module = MagicMock()
        mock_patch_module.PatchSet.side_effect = Exception("Unidiff error")
        
        self.replacer._patch_module = mock_patch_module
        
        content = "Hello world"
        diff_content = "some diff content"
        
        result = self.replacer._apply_unidiff(content, diff_content, "test.txt")
        
        self.assertIsNone(result)
    
    def test_replace_with_patch_ng_success(self):
        """Test successful replace using patch-ng"""
        mock_patch_module = MagicMock()
        self.replacer._patch_module = mock_patch_module
        self.replacer.use_patch_ng = True
        
        content = "Hello world"
        search_blocks = [("Hello", "Hi")]
        
        with patch.object(self.replacer, '_apply_patch_ng', return_value="Hi world"):
            result = self.replacer.replace(content, search_blocks)
            
            self.assertTrue(result.success)
            self.assertEqual(result.new_content, "Hi world")
            self.assertEqual(result.applied_count, 1)
            self.assertEqual(result.total_count, 1)
            self.assertEqual(result.metadata['strategy'], 'patch')
            self.assertEqual(result.metadata['patch_module'], 'patch-ng')
    
    def test_replace_with_unidiff_success(self):
        """Test successful replace using unidiff"""
        mock_patch_module = MagicMock()
        self.replacer._patch_module = mock_patch_module
        self.replacer.use_patch_ng = False
        
        content = "Hello world"
        search_blocks = [("Hello", "Hi")]
        
        with patch.object(self.replacer, '_apply_unidiff', return_value="Hi world"):
            result = self.replacer.replace(content, search_blocks)
            
            self.assertTrue(result.success)
            self.assertEqual(result.new_content, "Hi world")
            self.assertEqual(result.applied_count, 1)
            self.assertEqual(result.total_count, 1)
            self.assertEqual(result.metadata['strategy'], 'patch')
            self.assertEqual(result.metadata['patch_module'], 'unidiff')
    
    def test_replace_patch_failure(self):
        """Test replace when patch application fails"""
        mock_patch_module = MagicMock()
        self.replacer._patch_module = mock_patch_module
        
        content = "Hello world"
        search_blocks = [("Hello", "Hi")]
        
        with patch.object(self.replacer, '_apply_patch_ng', return_value=None):
            result = self.replacer.replace(content, search_blocks)
            
            self.assertFalse(result.success)
            self.assertIn("Failed to apply patch", result.message)
            self.assertEqual(result.applied_count, 0)
            self.assertEqual(result.total_count, 1)
            self.assertEqual(len(result.errors), 1)
    
    def test_replace_exception_handling(self):
        """Test exception handling in replace method"""
        mock_patch_module = MagicMock()
        self.replacer._patch_module = mock_patch_module
        
        content = "Hello world"
        search_blocks = [("Hello", "Hi")]
        
        with patch.object(self.replacer, '_search_blocks_to_unified_diff', side_effect=Exception("Diff error")):
            result = self.replacer.replace(content, search_blocks)
            
            self.assertFalse(result.success)
            self.assertIn("Error in patch replacement", result.message)
            self.assertEqual(result.applied_count, 0)
            self.assertEqual(result.total_count, 1)
            self.assertEqual(len(result.errors), 1)
    
    def test_multiple_search_blocks(self):
        """Test with multiple search blocks"""
        mock_patch_module = MagicMock()
        self.replacer._patch_module = mock_patch_module
        
        content = "Hello world, goodbye world"
        search_blocks = [
            ("Hello", "Hi"),
            ("goodbye", "farewell")
        ]
        
        with patch.object(self.replacer, '_apply_patch_ng', return_value="Hi world, farewell world"):
            result = self.replacer.replace(content, search_blocks)
            
            self.assertTrue(result.success)
            self.assertEqual(result.new_content, "Hi world, farewell world")
            self.assertEqual(result.applied_count, 2)
            self.assertEqual(result.total_count, 2)
    
    def test_diff_content_generation(self):
        """Test that diff content is generated correctly"""
        search_blocks = [("line1", "modified_line1")]
        
        with patch.object(self.replacer, '_search_blocks_to_unified_diff') as mock_diff:
            mock_diff.return_value = "mocked_diff"
            
            mock_patch_module = MagicMock()
            self.replacer._patch_module = mock_patch_module
            
            with patch.object(self.replacer, '_apply_patch_ng', return_value="result"):
                self.replacer.replace("content", search_blocks)
                
                mock_diff.assert_called_once_with(search_blocks)


if __name__ == '__main__':
    unittest.main() 