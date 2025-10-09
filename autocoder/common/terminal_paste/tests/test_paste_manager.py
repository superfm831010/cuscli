"""Tests for PasteManager."""

import os
import tempfile
import shutil
import unittest
from unittest.mock import patch
from autocoder.common.terminal_paste.paste_manager import PasteManager


class TestPasteManager(unittest.TestCase):
    """Test cases for PasteManager."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.paste_manager = PasteManager(self.temp_dir)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test PasteManager initialization."""
        # Test with custom directory
        manager = PasteManager(self.temp_dir)
        expected_paste_dir = os.path.join(self.temp_dir, ".auto-coder", "pastes")
        self.assertEqual(manager.paste_dir, expected_paste_dir)
        self.assertTrue(os.path.exists(expected_paste_dir))
        
        # Test with default directory (current working directory)
        with patch('os.getcwd', return_value=self.temp_dir):
            manager = PasteManager()
            self.assertEqual(manager.paste_dir, expected_paste_dir)
    
    def test_save_paste(self):
        """Test saving paste content."""
        content = "Hello, World!\nThis is a test paste."
        file_id = self.paste_manager.save_paste(content)
        
        # Check file ID format
        self.assertTrue(file_id.startswith("pasted-"))
        self.assertEqual(len(file_id), 39)  # "pasted-" + 32 hex chars
        
        # Check file exists and content is correct
        file_path = os.path.join(self.paste_manager.paste_dir, file_id)
        self.assertTrue(os.path.exists(file_path))
        
        with open(file_path, "r", encoding="utf-8") as f:
            saved_content = f.read()
        self.assertEqual(saved_content, content)
    
    def test_read_paste(self):
        """Test reading paste content."""
        content = "Test content for reading"
        file_id = self.paste_manager.save_paste(content)
        
        # Test reading with full file ID
        read_content = self.paste_manager.read_paste(file_id)
        self.assertEqual(read_content, content)
        
        # Test reading with UUID only (without "pasted-" prefix)
        uuid_only = file_id[7:]  # Remove "pasted-" prefix
        read_content = self.paste_manager.read_paste(uuid_only)
        self.assertEqual(read_content, content)
        
        # Test reading non-existent file
        non_existent = self.paste_manager.read_paste("pasted-nonexistent")
        self.assertIsNone(non_existent)
    
    def test_list_pastes(self):
        """Test listing paste files."""
        # Initially empty
        pastes = self.paste_manager.list_pastes()
        self.assertEqual(len(pastes), 0)
        
        # Add some pastes
        content1 = "First paste"
        content2 = "Second paste"
        file_id1 = self.paste_manager.save_paste(content1)
        file_id2 = self.paste_manager.save_paste(content2)
        
        pastes = self.paste_manager.list_pastes()
        self.assertEqual(len(pastes), 2)
        self.assertIn(file_id1, pastes)
        self.assertIn(file_id2, pastes)
        
        # Check sorting
        self.assertEqual(pastes, sorted(pastes))
    
    def test_cleanup_old_pastes(self):
        """Test cleaning up old paste files."""
        # Create some paste files
        content = "Test content"
        file_id1 = self.paste_manager.save_paste(content)
        file_id2 = self.paste_manager.save_paste(content)
        
        # Initially no cleanup (files are new)
        cleaned = self.paste_manager.cleanup_old_pastes(max_age_hours=24)
        self.assertEqual(cleaned, 0)
        
        # Mock old files by setting max_age_hours to 0
        cleaned = self.paste_manager.cleanup_old_pastes(max_age_hours=0)
        self.assertEqual(cleaned, 2)
        
        # Verify files are gone
        pastes = self.paste_manager.list_pastes()
        self.assertEqual(len(pastes), 0)
    
    def test_error_handling(self):
        """Test error handling in PasteManager."""
        # Test save_paste with invalid directory
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            with self.assertRaises(RuntimeError) as context:
                self.paste_manager.save_paste("test")
            self.assertIn("Failed to save paste content", str(context.exception))
        
        # Test read_paste with invalid file
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            with self.assertRaises(RuntimeError) as context:
                self.paste_manager.read_paste("pasted-test")
            self.assertIn("Failed to read paste file", str(context.exception))


if __name__ == "__main__":
    unittest.main() 