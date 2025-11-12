
"""
测试 LinterManager 的配置文件自动加载功能
"""

import os
import json
import yaml
import tempfile
import pytest
from unittest.mock import patch, Mock
from pathlib import Path

from autocoder.common.linter_core.linter_manager import LinterManager
from autocoder.common.priority_directory_finder import SearchResult


class TestConfigLoading:
    """测试配置文件加载功能"""
    
    def test_init_with_explicit_config(self):
        """测试：使用显式配置初始化"""
        config = {
            'max_workers': 8,
            'timeout': 600,
            'python_config': {'use_mypy': True}
        }
        
        manager = LinterManager(config)
        
        assert manager.global_config == config
        assert manager.max_workers == 8
        assert manager.timeout == 600
    
    def test_init_without_config_no_files_found(self):
        """测试：没有配置文件时的初始化"""
        # Mock QuickFinder 返回未找到配置文件
        mock_result = SearchResult(
            strategy=None,
            success=False,
            selected_directories=[],
            all_valid_directories=[]
        )
        
        with patch('autocoder.common.linter_core.linter_manager.QuickFinder.find_standard_directories', return_value=mock_result):
            manager = LinterManager()
            
            assert manager.global_config == {}
            assert manager.max_workers == 4  # 默认值
            assert manager.timeout == 300     # 默认值
    
    def test_load_json_config_file(self):
        """测试：加载 JSON 配置文件"""
        config_data = {
            'max_workers': 6,
            'timeout': 500,
            'python_config': {
                'use_mypy': True,
                'flake8_args': ['--max-line-length=120']
            }
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建配置文件
            config_file = os.path.join(temp_dir, 'config.json')
            with open(config_file, 'w') as f:
                json.dump(config_data, f)
            
            # Mock QuickFinder 返回找到的目录
            mock_result = SearchResult(
                strategy=None,
                success=True,
                selected_directories=[temp_dir],
                all_valid_directories=[temp_dir]
            )
            
            with patch('autocoder.common.linter_core.linter_manager.QuickFinder.find_standard_directories', return_value=mock_result):
                manager = LinterManager()
                
                assert manager.global_config == config_data
                assert manager.max_workers == 6
                assert manager.timeout == 500
    
    def test_load_yaml_config_file(self):
        """测试：加载 YAML 配置文件"""
        config_data = {
            'max_workers': 12,
            'timeout': 800,
            'typescript_config': {
                'use_eslint': True,
                'tsc_args': ['--strict']
            }
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建配置文件
            config_file = os.path.join(temp_dir, 'config.yaml')
            with open(config_file, 'w') as f:
                yaml.dump(config_data, f)
            
            # Mock QuickFinder 返回找到的目录
            mock_result = SearchResult(
                strategy=None,
                success=True,
                selected_directories=[temp_dir],
                all_valid_directories=[temp_dir]
            )
            
            with patch('autocoder.common.linter_core.linter_manager.QuickFinder.find_standard_directories', return_value=mock_result):
                manager = LinterManager()
                
                assert manager.global_config == config_data
                assert manager.max_workers == 12
                assert manager.timeout == 800
    
    def test_config_file_priority_order(self):
        """测试：配置文件优先级顺序"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建多个配置文件，config.json 应该优先
            config_json = {'max_workers': 10, 'source': 'json'}
            config_yaml = {'max_workers': 20, 'source': 'yaml'}
            
            with open(os.path.join(temp_dir, 'config.json'), 'w') as f:
                json.dump(config_json, f)
            
            with open(os.path.join(temp_dir, 'linter.yaml'), 'w') as f:
                yaml.dump(config_yaml, f)
            
            # Mock QuickFinder 返回找到的目录
            mock_result = SearchResult(
                strategy=None,
                success=True,
                selected_directories=[temp_dir],
                all_valid_directories=[temp_dir]
            )
            
            with patch('autocoder.common.linter_core.linter_manager.QuickFinder.find_standard_directories', return_value=mock_result):
                manager = LinterManager()
                
                # 应该加载 config.json（优先级更高）
                assert manager.global_config == config_json
                assert manager.global_config['source'] == 'json'
    
    def test_config_file_fallback_order(self):
        """测试：配置文件回退顺序"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 只创建 linter.yml 文件
            config_data = {'max_workers': 15, 'source': 'yml'}
            
            with open(os.path.join(temp_dir, 'linter.yml'), 'w') as f:
                yaml.dump(config_data, f)
            
            # Mock QuickFinder 返回找到的目录
            mock_result = SearchResult(
                strategy=None,
                success=True,
                selected_directories=[temp_dir],
                all_valid_directories=[temp_dir]
            )
            
            with patch('autocoder.common.linter_core.linter_manager.QuickFinder.find_standard_directories', return_value=mock_result):
                manager = LinterManager()
                
                # 应该加载 linter.yml（唯一可用的配置文件）
                assert manager.global_config == config_data
                assert manager.global_config['source'] == 'yml'
    
    def test_invalid_config_file_handling(self):
        """测试：处理无效的配置文件"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建无效的 JSON 文件
            invalid_json = os.path.join(temp_dir, 'config.json')
            with open(invalid_json, 'w') as f:
                f.write('{ invalid json content }')
            
            # 创建有效的 YAML 文件作为备选
            valid_yaml = os.path.join(temp_dir, 'config.yaml')
            config_data = {'max_workers': 8, 'source': 'yaml_backup'}
            with open(valid_yaml, 'w') as f:
                yaml.dump(config_data, f)
            
            # Mock QuickFinder 返回找到的目录
            mock_result = SearchResult(
                strategy=None,
                success=True,
                selected_directories=[temp_dir],
                all_valid_directories=[temp_dir]
            )
            
            with patch('autocoder.common.linter_core.linter_manager.QuickFinder.find_standard_directories', return_value=mock_result):
                # 应该捕获 JSON 解析错误，然后加载 YAML 文件
                manager = LinterManager()
                
                assert manager.global_config == config_data
                assert manager.global_config['source'] == 'yaml_backup'
    
    def test_priority_directory_finder_integration(self):
        """测试：与 priority_directory_finder 的集成"""
        # 这个测试验证 QuickFinder.find_standard_directories 被正确调用
        with patch('autocoder.common.linter_core.linter_manager.QuickFinder.find_standard_directories') as mock_finder:
            mock_result = SearchResult(
                strategy=None,
                success=False,
                selected_directories=[],
                all_valid_directories=[]
            )
            mock_finder.return_value = mock_result
            
            manager = LinterManager()
            
            # 验证 QuickFinder 被正确调用
            mock_finder.assert_called_once()
            call_args = mock_finder.call_args
            
            assert call_args[1]['base_name'] == '.autocoderlinters'
            assert call_args[1]['current_dir'] is None
            assert call_args[1]['file_extensions'] == ['json', 'yaml', 'yml']
    
    def test_load_config_file_unsupported_format(self):
        """测试：加载不支持的配置文件格式"""
        manager = LinterManager({})  # 创建一个实例来测试 _load_config_file 方法
        
        with tempfile.TemporaryDirectory() as temp_dir:
            unsupported_file = os.path.join(temp_dir, 'config.txt')
            with open(unsupported_file, 'w') as f:
                f.write('some content')
            
            with pytest.raises(ValueError, match="Unsupported configuration file format"):
                manager._load_config_file(unsupported_file)
    
    def test_empty_yaml_config_file(self):
        """测试：空的 YAML 配置文件"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建空的 YAML 文件
            config_file = os.path.join(temp_dir, 'config.yaml')
            with open(config_file, 'w') as f:
                f.write('')  # 空文件
            
            # Mock QuickFinder 返回找到的目录
            mock_result = SearchResult(
                strategy=None,
                success=True,
                selected_directories=[temp_dir],
                all_valid_directories=[temp_dir]
            )
            
            with patch('autocoder.common.linter_core.linter_manager.QuickFinder.find_standard_directories', return_value=mock_result):
                manager = LinterManager()
                
                # 空的 YAML 文件应该返回空字典
                assert manager.global_config == {}
    
    def test_config_file_with_complex_structure(self):
        """测试：复杂结构的配置文件"""
        complex_config = {
            'max_workers': 16,
            'timeout': 1200,
            'python_config': {
                'use_mypy': True,
                'flake8_args': ['--max-line-length=120', '--ignore=E501'],
                'mypy_args': ['--strict', '--no-implicit-optional'],
                'flake8_timeout': 60,
                'mypy_timeout': 90
            },
            'typescript_config': {
                'use_eslint': True,
                'tsc_args': ['--noEmit', '--strict'],
                'eslint_args': ['--ext', '.ts,.tsx'],
                'tsconfig_path': './tsconfig.json'
            },
            'java_config': {
                'javac_args': ['-Xlint:all', '-Werror'],
                'javac_timeout': 45
            }
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = os.path.join(temp_dir, 'config.json')
            with open(config_file, 'w') as f:
                json.dump(complex_config, f, indent=2)
            
            # Mock QuickFinder 返回找到的目录
            mock_result = SearchResult(
                strategy=None,
                success=True,
                selected_directories=[temp_dir],
                all_valid_directories=[temp_dir]
            )
            
            with patch('autocoder.common.linter_core.linter_manager.QuickFinder.find_standard_directories', return_value=mock_result):
                manager = LinterManager()
                
                assert manager.global_config == complex_config
                assert manager.max_workers == 16
                assert manager.timeout == 1200
                
                # 验证嵌套配置被正确加载
                python_config = manager.global_config.get('python_config', {})
                assert python_config.get('use_mypy') is True
                assert python_config.get('flake8_timeout') == 60
                
                typescript_config = manager.global_config.get('typescript_config', {})
                assert typescript_config.get('use_eslint') is True
                assert typescript_config.get('tsconfig_path') == './tsconfig.json'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
