"""
优先级目录查找器测试套件

测试所有主要功能，包括查找策略、验证规则、文件过滤等。
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

from .models import (
    SearchStrategy, ValidationMode, FileTypeFilter, DirectoryConfig,
    SearchResult, FinderConfig
)
from .finder import PriorityDirectoryFinder, QuickFinder
from . import find_command_directories, create_file_filter


class TestFileTypeFilter(unittest.TestCase):
    """测试文件类型过滤器"""
    
    def setUp(self):
        self.filter = FileTypeFilter(
            extensions={'.md', '.txt'},
            patterns={'config.*', '*.yml'},
            min_count=1,
            recursive=True,
            include_hidden=False
        )
    
    def test_matches_file_by_extension(self):
        """测试按扩展名匹配文件"""
        self.assertTrue(self.filter.matches_file("test.md"))
        self.assertTrue(self.filter.matches_file("test.txt"))
        self.assertFalse(self.filter.matches_file("test.py"))
        self.assertFalse(self.filter.matches_file("test"))
    
    def test_matches_file_by_pattern(self):
        """测试按模式匹配文件"""
        filter_patterns = FileTypeFilter(patterns={'*.yml', 'config.*'})
        self.assertTrue(filter_patterns.matches_file("test.yml"))
        self.assertTrue(filter_patterns.matches_file("config.json"))
        self.assertTrue(filter_patterns.matches_file("config.py"))
        self.assertFalse(filter_patterns.matches_file("test.py"))
    
    def test_hidden_files(self):
        """测试隐藏文件处理"""
        filter_no_hidden = FileTypeFilter(include_hidden=False)
        self.assertFalse(filter_no_hidden.matches_file(".hidden.txt"))
        
        filter_with_hidden = FileTypeFilter(include_hidden=True)
        self.assertTrue(filter_with_hidden.matches_file(".hidden.txt"))


class TestDirectoryConfig(unittest.TestCase):
    """测试目录配置"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.md")
        with open(self.test_file, 'w') as f:
            f.write("# Test")
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_get_expanded_path(self):
        """测试路径展开"""
        config = DirectoryConfig("~/test")
        expanded = config.get_expanded_path()
        self.assertTrue(expanded.startswith(os.path.expanduser("~")))
        self.assertTrue(os.path.isabs(expanded))
    
    def test_validate_directory_exists(self):
        """测试目录存在验证"""
        config = DirectoryConfig(self.temp_dir, validation_mode=ValidationMode.EXISTS)
        self.assertTrue(config.validate_directory())
        
        config_nonexistent = DirectoryConfig("/nonexistent", validation_mode=ValidationMode.EXISTS)
        self.assertFalse(config_nonexistent.validate_directory())
    
    def test_validate_directory_has_files(self):
        """测试目录包含文件验证"""
        config = DirectoryConfig(self.temp_dir, validation_mode=ValidationMode.HAS_FILES)
        self.assertTrue(config.validate_directory())
        
        empty_dir = tempfile.mkdtemp()
        try:
            config_empty = DirectoryConfig(empty_dir, validation_mode=ValidationMode.HAS_FILES)
            self.assertFalse(config_empty.validate_directory())
        finally:
            os.rmdir(empty_dir)
    
    def test_validate_directory_specific_files(self):
        """测试特定文件类型验证"""
        file_filter = FileTypeFilter(extensions={'.md'})
        config = DirectoryConfig(
            self.temp_dir,
            validation_mode=ValidationMode.HAS_SPECIFIC_FILES,
            file_filter=file_filter
        )
        self.assertTrue(config.validate_directory())
        
        filter_py = FileTypeFilter(extensions={'.py'})
        config_py = DirectoryConfig(
            self.temp_dir,
            validation_mode=ValidationMode.HAS_SPECIFIC_FILES,
            file_filter=filter_py
        )
        self.assertFalse(config_py.validate_directory())
    
    def test_validate_directory_custom(self):
        """测试自定义验证"""
        def always_true(path):
            return True
        
        def always_false(path):
            return False
        
        config_true = DirectoryConfig(
            self.temp_dir,
            validation_mode=ValidationMode.CUSTOM,
            custom_validator=always_true
        )
        self.assertTrue(config_true.validate_directory())
        
        config_false = DirectoryConfig(
            self.temp_dir,
            validation_mode=ValidationMode.CUSTOM,
            custom_validator=always_false
        )
        self.assertFalse(config_false.validate_directory())


class TestFinderConfig(unittest.TestCase):
    """测试查找器配置"""
    
    def test_add_directory(self):
        """测试添加目录"""
        config = FinderConfig()
        config.add_directory("/test", priority=1, description="Test dir")
        
        self.assertEqual(len(config.directories), 1)
        self.assertEqual(config.directories[0].path, "/test")
        self.assertEqual(config.directories[0].priority, 1)
        self.assertEqual(config.directories[0].description, "Test dir")
    
    def test_add_standard_paths(self):
        """测试添加标准路径"""
        config = FinderConfig()
        config.add_standard_paths(".test", "/tmp")
        
        self.assertEqual(len(config.directories), 3)
        
        # 检查路径
        paths = [d.path for d in config.directories]
        self.assertIn("/tmp/.test", paths)
        self.assertIn("/tmp/.auto-coder/.test", paths)
        self.assertIn("~/.auto-coder/.test", paths)
    
    def test_get_sorted_directories(self):
        """测试目录排序"""
        config = FinderConfig()
        config.add_directory("/test3", priority=3)
        config.add_directory("/test1", priority=1)
        config.add_directory("/test2", priority=2)
        
        sorted_dirs = config.get_sorted_directories()
        priorities = [d.priority for d in sorted_dirs]
        self.assertEqual(priorities, [1, 2, 3])


class TestPriorityDirectoryFinder(unittest.TestCase):
    """测试优先级目录查找器"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建测试目录结构
        self.test_dirs = []
        for i in range(3):
            dir_path = os.path.join(self.temp_dir, f"test_{i}")
            os.makedirs(dir_path)
            
            # 在前两个目录创建文件
            if i < 2:
                with open(os.path.join(dir_path, f"file_{i}.md"), 'w') as f:
                    f.write(f"Test {i}")
            
            self.test_dirs.append(dir_path)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_find_directories_first_match(self):
        """测试顺序查找策略"""
        config = FinderConfig(strategy=SearchStrategy.FIRST_MATCH)
        for i, dir_path in enumerate(self.test_dirs):
            config.add_directory(dir_path, priority=i)
        
        finder = PriorityDirectoryFinder(config)
        result = finder.find_directories()
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.selected_directories), 1)
        self.assertEqual(result.selected_directories[0], self.test_dirs[0])
        self.assertEqual(len(result.all_valid_directories), 2)  # 只有前两个有文件
    
    def test_find_directories_list_all(self):
        """测试全部查找策略"""
        config = FinderConfig(strategy=SearchStrategy.LIST_ALL)
        for i, dir_path in enumerate(self.test_dirs):
            config.add_directory(dir_path, priority=i)
        
        finder = PriorityDirectoryFinder(config)
        result = finder.find_directories()
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.selected_directories), 2)  # 只有前两个有文件
        self.assertEqual(set(result.selected_directories), set(self.test_dirs[:2]))
    
    def test_find_directories_merge_all(self):
        """测试合并查找策略"""
        config = FinderConfig(strategy=SearchStrategy.MERGE_ALL)
        for i, dir_path in enumerate(self.test_dirs):
            config.add_directory(dir_path, priority=i)
        
        finder = PriorityDirectoryFinder(config)
        result = finder.find_directories()
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.selected_directories), 2)  # 只有前两个有文件
    
    def test_find_directories_with_fallback(self):
        """测试回退目录"""
        empty_dir = tempfile.mkdtemp()
        try:
            config = FinderConfig(default_fallback=empty_dir)
            config.add_directory("/nonexistent", priority=1)
            
            finder = PriorityDirectoryFinder(config)
            result = finder.find_directories()
            
            self.assertTrue(result.success)
            self.assertEqual(result.primary_directory, empty_dir)
        finally:
            os.rmdir(empty_dir)
    
    def test_find_first_directory(self):
        """测试查找第一个目录的便捷方法"""
        config = FinderConfig()
        config.add_directory(self.test_dirs[0], priority=1)
        
        finder = PriorityDirectoryFinder(config)
        first_dir = finder.find_first_directory()
        
        self.assertEqual(first_dir, self.test_dirs[0])
    
    def test_find_all_directories(self):
        """测试查找所有目录的便捷方法"""
        config = FinderConfig()
        for i, dir_path in enumerate(self.test_dirs[:2]):  # 只添加有文件的目录
            config.add_directory(dir_path, priority=i)
        
        finder = PriorityDirectoryFinder(config)
        all_dirs = finder.find_all_directories()
        
        self.assertEqual(len(all_dirs), 2)
        self.assertEqual(set(all_dirs), set(self.test_dirs[:2]))
    
    def test_collect_files_from_directories(self):
        """测试从目录收集文件"""
        finder = PriorityDirectoryFinder()
        
        md_filter = FileTypeFilter(extensions={'.md'})
        files = finder.collect_files_from_directories(self.test_dirs[:2], md_filter)
        
        self.assertEqual(len(files), 2)
        for file_path in files:
            self.assertTrue(file_path.endswith('.md'))
    
    def test_metadata_inclusion(self):
        """测试元数据包含"""
        config = FinderConfig(include_metadata=True)
        config.add_directory(self.test_dirs[0], priority=1, description="Test directory")
        
        finder = PriorityDirectoryFinder(config)
        result = finder.find_directories()
        
        self.assertIn('total_configured', result.metadata)
        self.assertIn('total_valid', result.metadata)
        self.assertIn('strategy_used', result.metadata)
        self.assertIn('directory_configs', result.metadata)
        
        self.assertEqual(result.metadata['total_configured'], 1)
        self.assertEqual(result.metadata['total_valid'], 1)


class TestQuickFinder(unittest.TestCase):
    """测试快速查找器"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建标准目录结构
        self.cmd_dir = os.path.join(self.temp_dir, ".autocodercommands")
        os.makedirs(self.cmd_dir)
        with open(os.path.join(self.cmd_dir, "test.md"), 'w') as f:
            f.write("# Test command")
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_find_standard_directories(self):
        """测试查找标准目录"""
        result = QuickFinder.find_standard_directories(
            base_name=".autocodercommands",
            current_dir=self.temp_dir,
            file_extensions=["md"]
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.primary_directory, self.cmd_dir)
    
    def test_find_command_directories(self):
        """测试查找命令目录"""
        with patch('os.getcwd', return_value=self.temp_dir):
            result = QuickFinder.find_command_directories()
            self.assertTrue(result.success)
            self.assertEqual(result.primary_directory, self.cmd_dir)


class TestConvenienceFunctions(unittest.TestCase):
    """测试便捷函数"""
    
    def test_create_file_filter(self):
        """测试创建文件过滤器"""
        filter_obj = create_file_filter(
            extensions=[".md", ".txt"],
            patterns=["*.yml"],
            min_count=2
        )
        
        self.assertEqual(filter_obj.extensions, {".md", ".txt"})
        self.assertEqual(filter_obj.patterns, {"*.yml"})
        self.assertEqual(filter_obj.min_count, 2)
    
    def test_find_command_directories_function(self):
        """测试查找命令目录便捷函数"""
        with patch('autocoder.common.priority_directory_finder.finder.QuickFinder.find_command_directories') as mock_find:
            mock_result = MagicMock()
            mock_find.return_value = mock_result
            
            result = find_command_directories("/test")
            
            mock_find.assert_called_once_with("/test")
            self.assertEqual(result, mock_result)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建复杂的测试场景
        self.project_cmd = os.path.join(self.temp_dir, ".autocodercommands")
        self.auto_coder_cmd = os.path.join(self.temp_dir, ".auto-coder", ".autocodercommands")
        
        os.makedirs(self.project_cmd)
        os.makedirs(self.auto_coder_cmd)
        
        # 只在.auto-coder目录创建文件
        with open(os.path.join(self.auto_coder_cmd, "command.md"), 'w') as f:
            f.write("# Auto-coder command")
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_priority_selection(self):
        """测试优先级选择逻辑"""
        result = QuickFinder.find_standard_directories(
            base_name=".autocodercommands",
            current_dir=self.temp_dir,
            file_extensions=["md"],
            strategy=SearchStrategy.FIRST_MATCH
        )
        
        # 应该选择.auto-coder目录（因为项目级目录为空）
        self.assertTrue(result.success)
        self.assertEqual(result.primary_directory, self.auto_coder_cmd)
    
    def test_complete_workflow(self):
        """测试完整工作流程"""
        # 1. 配置查找器
        config = FinderConfig(strategy=SearchStrategy.LIST_ALL, include_metadata=True)
        config.add_standard_paths(".autocodercommands", self.temp_dir)
        
        # 设置文件过滤器
        md_filter = FileTypeFilter(extensions={'.md'})
        for dir_config in config.directories:
            dir_config.validation_mode = ValidationMode.HAS_SPECIFIC_FILES
            dir_config.file_filter = md_filter
        
        # 2. 执行查找
        finder = PriorityDirectoryFinder(config)
        result = finder.find_directories()
        
        # 3. 验证结果
        self.assertTrue(result.success)
        self.assertEqual(len(result.selected_directories), 1)
        self.assertEqual(result.selected_directories[0], self.auto_coder_cmd)
        
        # 4. 收集文件
        files = finder.collect_files_from_directories(result.selected_directories, md_filter)
        self.assertEqual(len(files), 1)
        self.assertTrue(files[0].endswith("command.md"))
        
        # 5. 检查元数据
        self.assertIn('total_configured', result.metadata)
        self.assertIn('directory_configs', result.metadata)


if __name__ == '__main__':
    unittest.main() 