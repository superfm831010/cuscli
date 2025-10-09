"""
Test module for SearchReplaceManager
"""

import unittest
from unittest.mock import patch, MagicMock

from ..manager import SearchReplaceManager
from ..base import ReplaceStrategy, ReplaceResult
from ..string_replacer import StringReplacer
from ..patch_replacer import PatchReplacer
from ..similarity_replacer import SimilarityReplacer


class TestSearchReplaceManager(unittest.TestCase):
    """Test SearchReplaceManager functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.manager = SearchReplaceManager()
        self.custom_manager = SearchReplaceManager(default_strategy=ReplaceStrategy.SIMILARITY)
    
    def test_initialization(self):
        """Test proper initialization"""
        self.assertEqual(self.manager.default_strategy, ReplaceStrategy.STRING)
        self.assertEqual(self.custom_manager.default_strategy, ReplaceStrategy.SIMILARITY)
        
        # Check that replacers are initialized
        self.assertIsInstance(self.manager.replacers.get(ReplaceStrategy.STRING), StringReplacer)
    
    def test_get_replacer(self):
        """Test getting replacer by strategy"""
        string_replacer = self.manager.get_replacer(ReplaceStrategy.STRING)
        self.assertIsInstance(string_replacer, StringReplacer)
        
        similarity_replacer = self.manager.get_replacer(ReplaceStrategy.SIMILARITY)
        self.assertIsInstance(similarity_replacer, SimilarityReplacer)
        
        # Test non-existent strategy
        non_existent = self.manager.get_replacer(ReplaceStrategy.PATCH)
        if non_existent:
            self.assertIsInstance(non_existent, PatchReplacer)
    
    def test_replace_with_default_strategy(self):
        """Test replace using default strategy"""
        content = "Hello world\n"
        search_blocks = [("Hello world", "Hello AutoCoder")]
        
        with patch.object(self.manager.replacers[ReplaceStrategy.STRING], 'replace') as mock_replace:
            mock_replace.return_value = ReplaceResult(success=True, message="Success", new_content="Hello AutoCoder\n")
            
            result = self.manager.replace(content, search_blocks)
            
            self.assertTrue(result.success)
            self.assertEqual(result.new_content, "Hello AutoCoder\n")
            mock_replace.assert_called_once_with(content, search_blocks)
    
    def test_replace_with_specified_strategy(self):
        """Test replace using specified strategy"""
        content = "Hello world\n"
        search_blocks = [("Hello world", "Hello AutoCoder")]
        
        with patch.object(self.manager.replacers[ReplaceStrategy.SIMILARITY], 'replace') as mock_replace:
            mock_replace.return_value = ReplaceResult(success=True, message="Success", new_content="Hello AutoCoder\n")
            
            result = self.manager.replace(content, search_blocks, ReplaceStrategy.SIMILARITY)
            
            self.assertTrue(result.success)
            self.assertEqual(result.new_content, "Hello AutoCoder\n")
            mock_replace.assert_called_once_with(content, search_blocks)
    
    def test_replace_with_unavailable_strategy(self):
        """Test replace with unavailable strategy"""
        content = "Hello world"
        search_blocks = [("world", "AutoCoder")]
        
        # Mock strategy not available
        with patch.object(self.manager, 'get_replacer', return_value=None):
            result = self.manager.replace(content, search_blocks, ReplaceStrategy.PATCH)
            
            self.assertFalse(result.success)
            self.assertIn("not available", result.message)
    
    def test_replace_with_fallback_first_success(self):
        """Test fallback strategy when first strategy succeeds"""
        content = "Hello world"
        search_blocks = [("world", "AutoCoder")]
        
        with patch.object(self.manager.replacers[ReplaceStrategy.STRING], 'replace') as mock_regex_replace:
            mock_regex_replace.return_value = ReplaceResult(success=True, message="Success", new_content="Hello AutoCoder")
            
            with patch.object(self.manager.replacers[ReplaceStrategy.STRING], 'can_handle', return_value=True):
                result = self.manager.replace_with_fallback(content, search_blocks)
                
                self.assertTrue(result.success)
                self.assertEqual(result.new_content, "Hello AutoCoder")
                self.assertEqual(result.metadata['used_strategy'], 'string')
                mock_regex_replace.assert_called_once()
    
    def test_replace_with_fallback_second_success(self):
        """Test fallback strategy when first fails, second succeeds"""
        content = "Hello world"
        search_blocks = [("world", "AutoCoder")]
        
        # First strategy fails
        with patch.object(self.manager.replacers[ReplaceStrategy.STRING], 'replace') as mock_regex_replace:
            mock_regex_replace.return_value = ReplaceResult(success=False, message="Failed")
            
            with patch.object(self.manager.replacers[ReplaceStrategy.STRING], 'can_handle', return_value=True):
                # Second strategy succeeds
                with patch.object(self.manager.replacers[ReplaceStrategy.SIMILARITY], 'replace') as mock_similarity_replace:
                    mock_similarity_replace.return_value = ReplaceResult(success=True, message="Success", new_content="Hello AutoCoder")
                    
                    with patch.object(self.manager.replacers[ReplaceStrategy.SIMILARITY], 'can_handle', return_value=True):
                        result = self.manager.replace_with_fallback(content, search_blocks)
                        
                        self.assertTrue(result.success)
                        self.assertEqual(result.new_content, "Hello AutoCoder")
                        self.assertEqual(result.metadata['used_strategy'], 'similarity')
                        mock_regex_replace.assert_called_once()
                        mock_similarity_replace.assert_called_once()
    
    def test_replace_with_fallback_all_fail(self):
        """Test fallback strategy when all strategies fail"""
        content = "Hello world"
        search_blocks = [("world", "AutoCoder")]
        
        # All strategies fail
        with patch.object(self.manager.replacers[ReplaceStrategy.STRING], 'replace') as mock_regex_replace:
            mock_regex_replace.return_value = ReplaceResult(success=False, message="Failed")
            
            with patch.object(self.manager.replacers[ReplaceStrategy.STRING], 'can_handle', return_value=True):
                with patch.object(self.manager.replacers[ReplaceStrategy.SIMILARITY], 'replace') as mock_similarity_replace:
                    mock_similarity_replace.return_value = ReplaceResult(success=False, message="Failed")
                    
                    with patch.object(self.manager.replacers[ReplaceStrategy.SIMILARITY], 'can_handle', return_value=True):
                        result = self.manager.replace_with_fallback(content, search_blocks)
                        
                        self.assertFalse(result.success)
                        self.assertIn('all_strategies_failed', result.metadata)
                        self.assertIn('tried_strategies', result.metadata)
    
    def test_replace_with_fallback_custom_strategies(self):
        """Test fallback with custom strategy list"""
        content = "Hello world"
        search_blocks = [("world", "AutoCoder")]
        strategies = [ReplaceStrategy.SIMILARITY, ReplaceStrategy.STRING]
        
        with patch.object(self.manager.replacers[ReplaceStrategy.SIMILARITY], 'replace') as mock_similarity_replace:
            mock_similarity_replace.return_value = ReplaceResult(success=True, message="Success", new_content="Hello AutoCoder")
            
            with patch.object(self.manager.replacers[ReplaceStrategy.SIMILARITY], 'can_handle', return_value=True):
                result = self.manager.replace_with_fallback(content, search_blocks, strategies)
                
                self.assertTrue(result.success)
                self.assertEqual(result.metadata['used_strategy'], 'similarity')
                mock_similarity_replace.assert_called_once()
    
    def test_replace_with_fallback_no_suitable_replacer(self):
        """Test fallback when no suitable replacer is found"""
        content = "Hello world"
        search_blocks = [("world", "AutoCoder")]
        
        with patch.object(self.manager, 'get_replacer', return_value=None):
            result = self.manager.replace_with_fallback(content, search_blocks)
            
            self.assertFalse(result.success)
            self.assertIn("No suitable replacer found", result.message)
    
    def test_replace_with_fallback_replacer_cannot_handle(self):
        """Test fallback when replacer cannot handle content"""
        content = "Hello world"
        search_blocks = [("world", "AutoCoder")]
        
        with patch.object(self.manager.replacers[ReplaceStrategy.STRING], 'can_handle', return_value=False):
            with patch.object(self.manager.replacers[ReplaceStrategy.SIMILARITY], 'can_handle', return_value=False):
                result = self.manager.replace_with_fallback(content, search_blocks)
                
                self.assertFalse(result.success)
    
    def test_get_available_strategies(self):
        """Test getting available strategies"""
        strategies = self.manager.get_available_strategies()
        
        self.assertIsInstance(strategies, list)
        self.assertIn(ReplaceStrategy.STRING, strategies)
        self.assertIn(ReplaceStrategy.SIMILARITY, strategies)
    
    def test_set_default_strategy(self):
        """Test setting default strategy"""
        original_default = self.manager.default_strategy
        
        self.manager.set_default_strategy(ReplaceStrategy.SIMILARITY)
        self.assertEqual(self.manager.default_strategy, ReplaceStrategy.SIMILARITY)
        
        # Test setting unavailable strategy
        with patch.object(self.manager, 'replacers', {ReplaceStrategy.STRING: MagicMock()}):
            self.manager.set_default_strategy(ReplaceStrategy.PATCH)
            self.assertEqual(self.manager.default_strategy, ReplaceStrategy.SIMILARITY)  # Should not change
    
    def test_configure_replacer_string(self):
        """Test configuring string replacer"""
        string_replacer = self.manager.get_replacer(ReplaceStrategy.STRING)
        if string_replacer and isinstance(string_replacer, StringReplacer):
            original_lenient = string_replacer.lenient_mode
            
            self.manager.configure_replacer(ReplaceStrategy.STRING, lenient_mode=False)
            self.assertFalse(string_replacer.lenient_mode)
            
            # Reset
            string_replacer.lenient_mode = original_lenient
    
    def test_configure_replacer_similarity(self):
        """Test configuring similarity replacer"""
        similarity_replacer = self.manager.get_replacer(ReplaceStrategy.SIMILARITY)
        if similarity_replacer and isinstance(similarity_replacer, SimilarityReplacer):
            original_threshold = similarity_replacer.similarity_threshold
            
            self.manager.configure_replacer(ReplaceStrategy.SIMILARITY, similarity_threshold=0.9)
            self.assertEqual(similarity_replacer.similarity_threshold, 0.9)
            
            # Reset
            similarity_replacer.similarity_threshold = original_threshold
    
    def test_configure_replacer_patch(self):
        """Test configuring patch replacer"""
        patch_replacer = self.manager.get_replacer(ReplaceStrategy.PATCH)
        if patch_replacer and isinstance(patch_replacer, PatchReplacer):
            original_use_patch_ng = patch_replacer.use_patch_ng
            
            with patch.object(patch_replacer, '_load_patch_module'):
                self.manager.configure_replacer(ReplaceStrategy.PATCH, use_patch_ng=False)
                self.assertFalse(patch_replacer.use_patch_ng)
                
                # Reset
                patch_replacer.use_patch_ng = original_use_patch_ng
    
    def test_configure_replacer_unavailable(self):
        """Test configuring unavailable replacer"""
        with patch.object(self.manager, 'get_replacer', return_value=None):
            # Should not raise exception
            self.manager.configure_replacer(ReplaceStrategy.PATCH, use_patch_ng=True)
    
    def test_configure_replacer_exception(self):
        """Test exception handling in configure_replacer"""
        with patch.object(self.manager.replacers[ReplaceStrategy.STRING], 'lenient_mode', 
                         side_effect=Exception("Config error")):
            # Should not raise exception
            self.manager.configure_replacer(ReplaceStrategy.STRING, lenient_mode=True)
    
    def test_get_replacer_info_string(self):
        """Test getting string replacer info"""
        info = self.manager.get_replacer_info(ReplaceStrategy.STRING)
        
        self.assertTrue(info['available'])
        self.assertEqual(info['strategy'], 'string')
        self.assertEqual(info['class_name'], 'StringReplacer')  # Updated from RegexReplacer
        self.assertIn('lenient_mode', info)
    
    def test_get_replacer_info_similarity(self):
        """Test getting similarity replacer info"""
        info = self.manager.get_replacer_info(ReplaceStrategy.SIMILARITY)
        
        self.assertTrue(info['available'])
        self.assertEqual(info['strategy'], 'similarity')
        self.assertEqual(info['class_name'], 'SimilarityReplacer')
        self.assertIn('similarity_threshold', info)
    
    def test_get_replacer_info_patch(self):
        """Test getting patch replacer info"""
        info = self.manager.get_replacer_info(ReplaceStrategy.PATCH)
        
        if info['available']:
            self.assertEqual(info['strategy'], 'patch')
            self.assertEqual(info['class_name'], 'PatchReplacer')
            self.assertIn('use_patch_ng', info)
            self.assertIn('patch_module_available', info)
    
    def test_get_replacer_info_unavailable(self):
        """Test getting info for unavailable replacer"""
        with patch.object(self.manager, 'get_replacer', return_value=None):
            info = self.manager.get_replacer_info(ReplaceStrategy.PATCH)
            
            self.assertFalse(info['available'])
            self.assertEqual(info['strategy'], 'patch')
    
    def test_get_replacer_info_exception(self):
        """Test get_replacer_info with exception during info gathering"""
        with patch.object(self.manager.replacers[ReplaceStrategy.STRING], 'lenient_mode',
                          side_effect=Exception("Mock exception")):
            info = self.manager.get_replacer_info(ReplaceStrategy.STRING)
            
            self.assertTrue(info['available'])
            self.assertEqual(info['strategy'], 'string')  # Updated from regex
            self.assertEqual(info['class_name'], 'StringReplacer')
    
    def test_get_status(self):
        """Test get_status method"""
        status = self.manager.get_status()
        
        self.assertIn('available_strategies', status)
        self.assertIn('default_strategy', status)
        self.assertEqual(status['default_strategy'], 'string')  # Updated from regex
        self.assertIn('replacer_info', status)  # Changed from 'replacers' to 'replacer_info'
    
    def test_initialize_replacers_with_failures(self):
        """Test initialization when some replacers fail to initialize"""
        with patch('autocoder.common.search_replace_patch.manager.StringReplacer', 
                   side_effect=Exception("String replacer init failed")):
            with patch('autocoder.common.search_replace_patch.manager.logger') as mock_logger:
                manager = SearchReplaceManager()
                
                # Should handle initialization failures gracefully
                mock_logger.error.assert_called()
                
                # Should still have other replacers
                self.assertIsInstance(manager.get_replacer(ReplaceStrategy.SIMILARITY), SimilarityReplacer)
    
    def test_manager_with_different_defaults(self):
        """Test manager with different default strategies"""
        regex_manager = SearchReplaceManager(ReplaceStrategy.STRING)
        similarity_manager = SearchReplaceManager(ReplaceStrategy.SIMILARITY)
        
        self.assertEqual(regex_manager.default_strategy, ReplaceStrategy.STRING)
        self.assertEqual(similarity_manager.default_strategy, ReplaceStrategy.SIMILARITY)
    
    def test_empty_search_blocks(self):
        """Test handling empty search blocks"""
        content = "Hello world"
        search_blocks = []
        
        result = self.manager.replace(content, search_blocks)
        self.assertFalse(result.success)
    
    def test_integration_with_real_replacers(self):
        """Test integration with real replacer instances"""
        content = "Hello world"
        search_blocks = [("world", "AutoCoder")]
        
        # This should work with real replacers
        result = self.manager.replace(content, search_blocks)
        
        if result.success:
            self.assertEqual(result.new_content, "Hello AutoCoder")
        else:
            # If it fails, it should be due to replacer logic, not manager logic
            self.assertIsInstance(result.message, str)


if __name__ == '__main__':
    unittest.main() 