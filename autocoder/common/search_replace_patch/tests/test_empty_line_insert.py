"""
Test module for empty line insertion functionality
"""

import unittest
from unittest.mock import patch

from ..manager import SearchReplaceManager
from ..base import ReplaceStrategy


class TestEmptyLineInsert(unittest.TestCase):
    """Test empty line insertion (file head insertion) functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = SearchReplaceManager()
    
    def test_insert_at_file_head_regex(self):
        """Test inserting content at file head using regex strategy"""
        content = "line1\nline2\nline3\n"
        search_blocks = [("", "# Header comment")]
        
        result = self.manager.replace(content, search_blocks, ReplaceStrategy.STRING)
        
        self.assertTrue(result.success)
        self.assertEqual(result.applied_count, 1)
        self.assertEqual(result.total_count, 1)
        self.assertIsNotNone(result.new_content)
        if result.new_content:
            self.assertTrue(result.new_content.startswith("# Header comment\n"))
            self.assertIn("line1", result.new_content)
    
    def test_insert_at_file_head_similarity(self):
        """Test inserting content at file head using similarity strategy"""
        content = "line1\nline2\nline3\n"
        search_blocks = [("", "#!/usr/bin/env python3")]
        
        result = self.manager.replace(content, search_blocks, ReplaceStrategy.SIMILARITY)
        
        self.assertTrue(result.success)
        self.assertEqual(result.applied_count, 1)
        self.assertEqual(result.total_count, 1)
        self.assertIsNotNone(result.new_content)
        if result.new_content:
            self.assertTrue(result.new_content.startswith("#!/usr/bin/env python3\n"))
    
    def test_insert_multiple_blocks(self):
        """Test inserting multiple blocks at file head"""
        content = "original content\n"
        search_blocks = [
            ("", "# First comment"),
            ("", "# Second comment")
        ]
        
        result = self.manager.replace(content, search_blocks, ReplaceStrategy.STRING)
        
        self.assertTrue(result.success)
        self.assertEqual(result.applied_count, 2)
        self.assertEqual(result.total_count, 2)
        self.assertIsNotNone(result.new_content)
        if result.new_content:
            # 后插入的内容会出现在前面（插入顺序是反向的）
            self.assertTrue(result.new_content.startswith("# Second comment\n"))
            self.assertIn("# First comment", result.new_content)
            self.assertIn("original content", result.new_content)
            
            # 验证完整顺序
            expected_content = "# Second comment\n# First comment\noriginal content\n"
            self.assertEqual(result.new_content, expected_content)
    
    def test_insert_with_mixed_operations(self):
        """Test mixing insertion and replacement operations"""
        content = "Hello world\nGoodbye world\n"
        search_blocks = [
            ("", "# File header"),
            ("Hello world", "Hi world")
        ]
        
        result = self.manager.replace(content, search_blocks, ReplaceStrategy.STRING)
        
        self.assertTrue(result.success)
        self.assertEqual(result.applied_count, 2)
        self.assertEqual(result.total_count, 2)
        self.assertIsNotNone(result.new_content)
        if result.new_content:
            self.assertTrue(result.new_content.startswith("# File header\n"))
            self.assertIn("Hi world", result.new_content)
            self.assertIn("Goodbye world", result.new_content)
    
    def test_insert_empty_file(self):
        """Test inserting content into an empty file"""
        content = ""
        search_blocks = [("", "New file content")]
        
        result = self.manager.replace(content, search_blocks, ReplaceStrategy.STRING)
        
        self.assertTrue(result.success)
        self.assertEqual(result.applied_count, 1)
        self.assertEqual(result.total_count, 1)
        self.assertEqual(result.new_content, "New file content\n")
    
    def test_insert_with_newline_preservation(self):
        """Test that newlines are properly handled in insertions"""
        content = "existing line\n"
        search_blocks = [("", "inserted line")]
        
        result = self.manager.replace(content, search_blocks, ReplaceStrategy.STRING)
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.new_content)
        if result.new_content:
            # Should have newline after inserted content
            self.assertTrue(result.new_content.startswith("inserted line\n"))
            self.assertIn("existing line", result.new_content)
    
    def test_insert_multiline_content(self):
        """Test inserting multiline content"""
        content = "original\n"
        search_blocks = [("", "line1\nline2\nline3")]
        
        result = self.manager.replace(content, search_blocks, ReplaceStrategy.STRING)
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.new_content)
        if result.new_content:
            self.assertTrue(result.new_content.startswith("line1\nline2\nline3\n"))
            self.assertIn("original", result.new_content)
    
    def test_insert_with_fallback_strategy(self):
        """Test insertion with fallback strategy"""
        content = "test content\n"
        search_blocks = [("", "header")]
        
        result = self.manager.replace_with_fallback(content, search_blocks)
        
        self.assertTrue(result.success)
        self.assertEqual(result.applied_count, 1)
        self.assertIsNotNone(result.new_content)
        if result.new_content:
            self.assertTrue(result.new_content.startswith("header\n"))
        self.assertIn('used_strategy', result.metadata)
    
    def test_insert_validation(self):
        """Test that insertion operations pass validation"""
        content = "test"
        search_blocks = [("", "insert")]
        
        # Should pass validation
        regex_replacer = self.manager.get_replacer(ReplaceStrategy.STRING)
        if regex_replacer:
            self.assertTrue(regex_replacer.validate_search_blocks(search_blocks))
        
        similarity_replacer = self.manager.get_replacer(ReplaceStrategy.SIMILARITY)
        if similarity_replacer:
            self.assertTrue(similarity_replacer.validate_search_blocks(search_blocks))
    
    def test_insert_only_blocks(self):
        """Test when all blocks are insert operations"""
        content = "original\n"
        search_blocks = [
            ("", "header1"),
            ("", "header2"),
            ("", "header3")
        ]
        
        result = self.manager.replace(content, search_blocks, ReplaceStrategy.STRING)
        
        self.assertTrue(result.success)
        self.assertEqual(result.applied_count, 3)
        self.assertEqual(result.total_count, 3)
        self.assertIsNotNone(result.new_content)
        if result.new_content:
            # 后插入的内容会出现在前面（插入顺序是反向的）
            self.assertTrue(result.new_content.startswith("header3\n"))
            self.assertIn("header2", result.new_content)
            self.assertIn("header1", result.new_content)
            self.assertIn("original", result.new_content)
            
            # 验证完整顺序：header3, header2, header1, original
            expected_content = "header3\nheader2\nheader1\noriginal\n"
            self.assertEqual(result.new_content, expected_content)
    
    def test_real_world_shebang_insertion(self):
        """Test a real-world scenario: adding shebang to Python file"""
        python_content = """import os
import sys

def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()
"""
        
        search_blocks = [("", "#!/usr/bin/env python3")]
        
        result = self.manager.replace(python_content, search_blocks, ReplaceStrategy.STRING)
        
        self.assertTrue(result.success)
        self.assertEqual(result.applied_count, 1)
        self.assertIsNotNone(result.new_content)
        if result.new_content:
            self.assertTrue(result.new_content.startswith("#!/usr/bin/env python3\n"))
            self.assertIn("import os", result.new_content)
            self.assertIn("def main():", result.new_content)
    
    def test_real_world_license_header_insertion(self):
        """Test a real-world scenario: adding license header to code file"""
        code_content = """function hello() {
    console.log("Hello, World!");
}
"""
        
        license_header = """/*
 * Copyright (c) 2024 Example Corp.
 * Licensed under the MIT License
 */"""
        
        search_blocks = [("", license_header)]
        
        result = self.manager.replace(code_content, search_blocks, ReplaceStrategy.STRING)
        
        self.assertTrue(result.success)
        self.assertEqual(result.applied_count, 1)
        self.assertIsNotNone(result.new_content)
        if result.new_content:
            self.assertTrue(result.new_content.startswith("/*\n * Copyright"))
            self.assertIn("function hello()", result.new_content)


if __name__ == '__main__':
    unittest.main() 