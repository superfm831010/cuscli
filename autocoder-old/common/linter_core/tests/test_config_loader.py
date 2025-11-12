"""
Tests for the centralized configuration loader.
"""

import os
import json
import tempfile
import pytest
from unittest.mock import patch, Mock
from pathlib import Path

from autocoder.common.linter_core.config_loader import LinterConfigLoader, load_linter_config


class TestLinterConfigLoader:
    """Test cases for LinterConfigLoader."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def config_loader(self, temp_dir):
        """Create a config loader instance."""
        return LinterConfigLoader(source_dir=str(temp_dir))
    
    def test_default_config(self, config_loader):
        """Test that default configuration is returned when no config files exist."""
        config = config_loader.load_config()
        
        assert config == LinterConfigLoader.DEFAULT_CONFIG
        assert config['enabled'] is False
        assert config['mode'] == 'warning'
        assert config['check_after_modification'] is True
        assert config['report']['format'] == 'simple'
        assert config['report']['include_in_result'] is True
    
    def test_load_from_explicit_path_json(self, config_loader, temp_dir):
        """Test loading configuration from explicit JSON file path."""
        config_data = {
            'enabled': True,
            'mode': 'blocking',
            'report': {'format': 'detailed'}
        }
        
        config_file = temp_dir / 'custom_config.json'
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        config = config_loader.load_config(config_path=str(config_file))
        
        assert config == config_data
    
    def test_load_from_explicit_path_yaml(self, config_loader, temp_dir):
        """Test loading configuration from explicit YAML file path."""
        config_data = {
            'enabled': True,
            'mode': 'silent',
            'report': {'format': 'json'}
        }
        
        config_file = temp_dir / 'custom_config.yaml'
        
        # Create YAML content manually (to avoid yaml dependency in test)
        yaml_content = """
enabled: true
mode: silent
report:
  format: json
"""
        
        with open(config_file, 'w') as f:
            f.write(yaml_content)
        
        # Mock yaml.safe_load
        with patch('yaml.safe_load') as mock_yaml:
            mock_yaml.return_value = config_data
            
            config = config_loader.load_config(config_path=str(config_file))
            
            assert config == config_data
    
    def test_load_from_explicit_path_with_nested_key(self, config_loader, temp_dir):
        """Test loading configuration with nested key extraction."""
        full_config = {
            'linter': {
                'enabled': True,
                'mode': 'warning'
            },
            'other_section': {
                'key': 'value'
            }
        }
        
        config_file = temp_dir / 'nested_config.json'
        with open(config_file, 'w') as f:
            json.dump(full_config, f)
        
        config = config_loader.load_config(config_path=str(config_file), config_key='linter')
        
        assert config == full_config['linter']
    
    @patch.dict(os.environ, {'AUTOCODER_LINTER_CONFIG': '{"enabled": true, "mode": "blocking"}'})
    def test_load_from_environment(self, config_loader):
        """Test loading configuration from environment variable."""
        config = config_loader.load_config()
        
        assert config['enabled'] is True
        assert config['mode'] == 'blocking'
    
    @patch.dict(os.environ, {'AUTOCODER_LINTER_CONFIG': 'invalid json'})
    def test_load_from_environment_invalid_json(self, config_loader):
        """Test handling invalid JSON in environment variable."""
        config = config_loader.load_config()
        
        # Should fall back to default config
        assert config == LinterConfigLoader.DEFAULT_CONFIG
    
    def test_load_from_project_config_json(self, config_loader, temp_dir):
        """Test loading configuration from project .autocoderlinters directory."""
        config_data = {
            'enabled': True,
            'mode': 'warning',
            'custom_field': 'project_value'
        }
        
        # Create project config directory and file
        project_config_dir = temp_dir / '.autocoderlinters'
        project_config_dir.mkdir()
        
        config_file = project_config_dir / 'config.json'
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        config = config_loader.load_config()
        
        assert config == config_data
    
    def test_load_from_project_config_priority(self, config_loader, temp_dir):
        """Test that config.json has priority over linter.yaml in project config."""
        # Create project config directory
        project_config_dir = temp_dir / '.autocoderlinters'
        project_config_dir.mkdir()
        
        # Create both config.json and linter.yaml
        json_config = {'enabled': True, 'source': 'json'}
        yaml_config = {'enabled': False, 'source': 'yaml'}
        
        with open(project_config_dir / 'config.json', 'w') as f:
            json.dump(json_config, f)
        
        with open(project_config_dir / 'linter.yaml', 'w') as f:
            f.write('enabled: false\nsource: yaml\n')
        
        config = config_loader.load_config()
        
        # Should load JSON config (higher priority)
        assert config == json_config
        assert config['source'] == 'json'
    
    def test_load_from_global_config(self, config_loader, temp_dir):
        """Test loading configuration from global user config directory."""
        config_data = {
            'enabled': True,
            'mode': 'silent',
            'global_setting': True
        }
        
        # Mock the global config directory path to point to our temp dir
        fake_global_dir = temp_dir / '.auto-coder' / '.autocoderlinters'
        fake_global_dir.mkdir(parents=True)
        
        config_file = fake_global_dir / 'config.json'
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        # Mock os.path.expanduser to return our temp dir
        with patch('os.path.expanduser', return_value=str(temp_dir)):
            config = config_loader.load_config()
        
        assert config == config_data
    
    def test_config_priority_order(self, config_loader, temp_dir):
        """Test configuration priority order: explicit > env > project > global > default."""
        # Create project config
        project_config_dir = temp_dir / '.autocoderlinters'
        project_config_dir.mkdir()
        
        project_config = {'enabled': False, 'source': 'project'}
        with open(project_config_dir / 'config.json', 'w') as f:
            json.dump(project_config, f)
        
        # Create explicit config file
        explicit_config = {'enabled': True, 'source': 'explicit'}
        explicit_file = temp_dir / 'explicit.json'
        with open(explicit_file, 'w') as f:
            json.dump(explicit_config, f)
        
        # Test explicit config has highest priority
        config = config_loader.load_config(config_path=str(explicit_file))
        assert config['source'] == 'explicit'
        
        # Test project config is used when no explicit config
        config = config_loader.load_config()
        assert config['source'] == 'project'
    
    def test_validate_config(self, config_loader):
        """Test configuration validation and normalization."""
        # Test with valid config
        valid_config = {
            'enabled': True,
            'mode': 'blocking',
            'report': {
                'format': 'detailed',
                'include_in_result': False
            }
        }
        
        validated = config_loader.validate_config(valid_config)
        
        assert validated['enabled'] is True
        assert validated['mode'] == 'blocking'
        assert validated['report']['format'] == 'detailed'
        assert validated['report']['include_in_result'] is False
        # Should still have default values for missing keys
        assert 'check_after_modification' in validated
    
    def test_validate_config_invalid_mode(self, config_loader):
        """Test validation with invalid mode value."""
        invalid_config = {
            'enabled': True,
            'mode': 'invalid_mode'  # Invalid mode
        }
        
        validated = config_loader.validate_config(invalid_config)
        
        assert validated['mode'] == 'warning'  # Should fallback to default
    
    def test_validate_config_invalid_report_format(self, config_loader):
        """Test validation with invalid report format."""
        invalid_config = {
            'enabled': True,
            'report': {
                'format': 'invalid_format'  # Invalid format
            }
        }
        
        validated = config_loader.validate_config(invalid_config)
        
        assert validated['report']['format'] == 'simple'  # Should fallback to default
    
    def test_validate_config_non_dict(self, config_loader):
        """Test validation with non-dictionary input."""
        validated = config_loader.validate_config("not a dict")
        
        assert validated == LinterConfigLoader.DEFAULT_CONFIG
    
    def test_load_manager_config(self, temp_dir):
        """Test loading full configuration for LinterManager."""
        full_config = {
            'max_workers': 8,
            'timeout': 600,
            'linter': {
                'enabled': True,
                'mode': 'warning'
            },
            'python_config': {
                'use_mypy': True
            }
        }
        
        # Create project config
        project_config_dir = temp_dir / '.autocoderlinters'
        project_config_dir.mkdir()
        
        with open(project_config_dir / 'config.json', 'w') as f:
            json.dump(full_config, f)
        
        config = LinterConfigLoader.load_manager_config(source_dir=str(temp_dir))
        
        assert config == full_config
        assert config['max_workers'] == 8
        assert config['linter']['enabled'] is True
        assert config['python_config']['use_mypy'] is True
    
    def test_load_manager_config_empty(self):
        """Test loading manager config when no config files exist."""
        config = LinterConfigLoader.load_manager_config(source_dir='/nonexistent')
        
        assert config == {}


class TestConvenienceFunction:
    """Test the convenience function."""
    
    def test_load_linter_config_function(self):
        """Test the load_linter_config convenience function."""
        config = load_linter_config()
        
        # Should return default config when no files exist
        assert isinstance(config, dict)
        assert 'enabled' in config
        assert 'mode' in config
        assert 'report' in config
    
    def test_load_linter_config_with_params(self):
        """Test convenience function with parameters."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_data = {'enabled': True, 'mode': 'blocking'}
            config_file = Path(temp_dir) / 'test_config.json'
            
            with open(config_file, 'w') as f:
                json.dump(config_data, f)
            
            config = load_linter_config(
                config_path=str(config_file),
                source_dir=temp_dir
            )
            
            assert config['enabled'] is True
            assert config['mode'] == 'blocking'
