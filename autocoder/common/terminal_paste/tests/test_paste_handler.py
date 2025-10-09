"""Tests for paste_handler functionality."""

import unittest
from unittest.mock import Mock, patch, MagicMock
from autocoder.common.terminal_paste.paste_handler import (
    register_paste_handler,
    resolve_paste_placeholders,
    get_paste_manager,
    PLACEHOLDER_PATTERN
)
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.clipboard import ClipboardData


class TestPasteHandler(unittest.TestCase):
    """Test cases for paste handler functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Reset global paste manager
        import autocoder.common.terminal_paste.paste_handler
        autocoder.common.terminal_paste.paste_handler._paste_manager = None
    
    def test_register_paste_handler_no_error(self):
        """Test that register_paste_handler runs without error."""
        kb = KeyBindings()
        # This should not raise any exception
        register_paste_handler(kb)
        
        # Verify that a key binding was registered
        self.assertTrue(len(kb.bindings) > 0)
        
        # Check that the binding is for 'c-p'
        binding_found = False
        for binding in kb.bindings:
            if binding.keys == ('c-p',):
                binding_found = True
                break
        self.assertTrue(binding_found, "Ctrl+P binding not found")
    
    def test_paste_handler_single_line(self):
        """Test paste handler with single-line content."""
        kb = KeyBindings()
        register_paste_handler(kb)
        
        # Create mock event
        mock_event = Mock()
        mock_app = Mock()
        mock_buffer = Mock()
        mock_clipboard_data = Mock()
        mock_clipboard_data.text = "single line text"
        
        mock_event.app = mock_app
        mock_event.current_buffer = mock_buffer
        mock_app.clipboard.get_data.return_value = mock_clipboard_data
        
        # Find and execute the paste handler
        paste_handler = None
        for binding in kb.bindings:
            if binding.keys == ('c-p',):
                paste_handler = binding.handler
                break
        
        self.assertIsNotNone(paste_handler)
        
        # Execute the handler (we know it's not None due to assertion above)
        if paste_handler:
            paste_handler(mock_event)
        
        # Verify single line was pasted normally
        mock_buffer.insert_text.assert_called_once_with("single line text")
    
    def test_paste_handler_multi_line(self):
        """Test paste handler with multi-line content."""
        kb = KeyBindings()
        register_paste_handler(kb)
        
        # Create mock event
        mock_event = Mock()
        mock_app = Mock()
        mock_buffer = Mock()
        mock_clipboard_data = Mock()
        mock_clipboard_data.text = "line 1\nline 2\nline 3"
        
        mock_event.app = mock_app
        mock_event.current_buffer = mock_buffer
        mock_app.clipboard.get_data.return_value = mock_clipboard_data
        
        # Mock the paste manager
        with patch('autocoder.common.terminal_paste.paste_handler.get_paste_manager') as mock_get_paste_manager:
            mock_paste_manager = Mock()
            mock_paste_manager.save_paste.return_value = "pasted-abc123def45678901234567890123456"
            mock_get_paste_manager.return_value = mock_paste_manager
            
            # Find and execute the paste handler
            paste_handler = None
            for binding in kb.bindings:
                if binding.keys == ('c-p',):
                    paste_handler = binding.handler
                    break
            
            self.assertIsNotNone(paste_handler)
            
            # Execute the handler (we know it's not None due to assertion above)
            if paste_handler:
                paste_handler(mock_event)
            
            # Verify multi-line content was saved and placeholder inserted
            mock_paste_manager.save_paste.assert_called_once_with("line 1\nline 2\nline 3")
            mock_buffer.insert_text.assert_called_once_with("[pasted-abc123def45678901234567890123456]")
    
    def test_get_paste_manager(self):
        """Test that get_paste_manager returns a PasteManager instance."""
        manager = get_paste_manager()
        self.assertIsNotNone(manager)
        
        # Test that it returns the same instance on subsequent calls
        manager2 = get_paste_manager()
        self.assertIs(manager, manager2)
    
    def test_resolve_paste_placeholders_no_placeholders(self):
        """Test resolving text without placeholders."""
        text = "This is normal text without placeholders"
        result = resolve_paste_placeholders(text)
        self.assertEqual(result, text)
    
    def test_resolve_paste_placeholders_with_placeholder(self):
        """Test resolving text with placeholders."""
        with patch('autocoder.common.terminal_paste.paste_handler.get_paste_manager') as mock_get_paste_manager:
            mock_paste_manager = Mock()
            mock_paste_manager.read_paste.return_value = "Hello World"
            mock_get_paste_manager.return_value = mock_paste_manager
            
            text_with_placeholder = "Say [pasted-abc123def45678901234567890123456]"
            result = resolve_paste_placeholders(text_with_placeholder)
            
            expected = "Say Hello World"
            self.assertEqual(result, expected)
            mock_paste_manager.read_paste.assert_called_once_with("pasted-abc123def45678901234567890123456")
    
    def test_resolve_multiple_placeholders(self):
        """Test resolving multiple placeholders in one text."""
        with patch('autocoder.common.terminal_paste.paste_handler.get_paste_manager') as mock_get_paste_manager:
            mock_paste_manager = Mock()
            # The resolve function calls read_paste with "pasted-" + file_id
            mock_paste_manager.read_paste.side_effect = lambda file_id: {
                "pasted-abc123def45678901234567890123456": "Hello",
                "pasted-def456abc78901234567890123456abc": "World"
            }.get(file_id, "Not found")
            mock_get_paste_manager.return_value = mock_paste_manager
            
            # Test with multiple placeholders (both 32 chars)
            text_with_placeholders = "Say [pasted-abc123def45678901234567890123456] [pasted-def456abc78901234567890123456abc]!"
            result = resolve_paste_placeholders(text_with_placeholders)
            
            expected = "Say Hello World!"
            self.assertEqual(result, expected)
    
    def test_placeholder_pattern_regex(self):
        """Test that the placeholder pattern matches correctly."""
        # Test valid placeholder
        valid_placeholder = "[pasted-abc123def45678901234567890123456]"
        match = PLACEHOLDER_PATTERN.search(valid_placeholder)
        self.assertIsNotNone(match)
        if match:  # Fix linter error by checking match is not None
            self.assertEqual(match.group(1), "abc123def45678901234567890123456")
        
        # Test invalid placeholders
        invalid_placeholders = [
            "[pasted-short]",  # Too short
            "[pasted-abc123def45678901234567890123456extra]",  # Too long
            "[pasted-abc123def45678901234567890123456X]",  # Contains invalid character
            "pasted-abc123def45678901234567890123456",  # Missing brackets
        ]
        
        for invalid in invalid_placeholders:
            match = PLACEHOLDER_PATTERN.search(invalid)
            self.assertIsNone(match, f"Pattern should not match: {invalid}")


if __name__ == '__main__':
    unittest.main() 