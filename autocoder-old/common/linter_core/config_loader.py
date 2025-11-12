"""
Centralized configuration loader for the linter core module.

This module provides comprehensive configuration loading from multiple sources
with proper priority handling and format support.
"""

import os
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from loguru import logger


class LinterConfigLoader:
    """
    Centralized configuration loader for linter configurations.
    
    Loads configuration from multiple sources in priority order:
    1. Explicit config path (if provided)
    2. Environment variable AUTOCODER_LINTER_CONFIG
    3. Project config file (.autocoderlinters/)
    4. Global user config file (~/.auto-coder/.autocoderlinters/)
    5. Default configuration
    """
    
    DEFAULT_CONFIG = {
        'enabled': False,  # Disabled by default for safety
        'mode': 'warning',
        'check_after_modification': True,
        'report': {
            'format': 'simple',
            'include_in_result': True
        }
    }
    
    def __init__(self, source_dir: Optional[str] = None):
        """
        Initialize the config loader.
        
        Args:
            source_dir: Base directory for relative path resolution
        """
        self.source_dir = source_dir or "."
    
    def load_config(self, 
                   config_path: Optional[str] = None,
                   config_key: str = 'linter') -> Dict[str, Any]:
        """
        Load configuration from multiple sources in priority order.
        
        Args:
            config_path: Explicit path to configuration file
            config_key: Key to extract from configuration files (for nested configs)
            
        Returns:
            Dictionary containing the loaded configuration
        """
        # 1. Check explicit config path
        if config_path:
            config = self._load_from_file(config_path, config_key)
            if config is not None:
                logger.info(f"Loaded linter config from explicit path: {config_path}")
                return config
        
        # 2. Check environment variable
        config = self._load_from_environment()
        if config is not None:
            return config
        
        # 3. Check project config file
        config = self._load_from_project_config(config_key)
        if config is not None:
            return config
        
        # 4. Check global user config file
        config = self._load_from_global_config(config_key)
        if config is not None:
            return config
        
        # 5. Return default configuration
        logger.debug("Using default linter configuration")
        return self.DEFAULT_CONFIG.copy()
    
    def _load_from_file(self, file_path: str, config_key: str = 'linter') -> Optional[Dict[str, Any]]:
        """Load configuration from a specific file."""
        try:
            path = Path(file_path)
            if not path.exists():
                logger.debug(f"Config file not found: {file_path}")
                return None
            
            with open(path, 'r', encoding='utf-8') as f:
                if path.suffix.lower() == '.json':
                    data = json.load(f)
                else:
                    # Try YAML if available
                    try:
                        import yaml
                        data = yaml.safe_load(f)
                    except ImportError:
                        logger.warning(f"YAML support not available, treating {file_path} as JSON")
                        f.seek(0)  # Reset file pointer
                        data = json.load(f)
            
            # Extract the specified section if present, otherwise use the whole config
            config = data.get(config_key, data) if isinstance(data, dict) else data
            
            logger.info(f"Successfully loaded config from: {file_path}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load config from {file_path}: {e}")
            return None
    
    def _load_from_environment(self) -> Optional[Dict[str, Any]]:
        """Load configuration from environment variable."""
        env_config = os.environ.get('AUTOCODER_LINTER_CONFIG')
        if not env_config:
            return None
        
        try:
            config = json.loads(env_config)
            logger.info("Loaded linter config from environment variable")
            return config
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AUTOCODER_LINTER_CONFIG: {e}")
            return None
    
    def _load_from_project_config(self, config_key: str = 'linter') -> Optional[Dict[str, Any]]:
        """Load configuration from project config directory."""
        project_config_dir = Path(self.source_dir) / '.autocoderlinters'
        
        # Try different config file formats in order of preference
        config_files = [
            project_config_dir / 'config.json',
            project_config_dir / 'config.yaml',
            project_config_dir / 'config.yml',
            project_config_dir / 'linter.json',
            project_config_dir / 'linter.yaml',
            project_config_dir / 'linter.yml',
        ]
        
        for config_file in config_files:
            if config_file.exists():
                config = self._load_from_file(str(config_file), config_key)
                if config is not None:
                    logger.info(f"Loaded linter config from project: {config_file}")
                    return config
        
        logger.debug(f"No project config found in: {project_config_dir}")
        return None
    
    def _load_from_global_config(self, config_key: str = 'linter') -> Optional[Dict[str, Any]]:
        """Load configuration from global user config directory."""
        try:
            # Use os.path.expanduser to handle ~ on all platforms
            global_config_dir = Path(os.path.expanduser('~')) / '.auto-coder' / '.autocoderlinters'
            
            # Try different config file formats in order of preference
            config_files = [
                global_config_dir / 'config.json',
                global_config_dir / 'config.yaml',
                global_config_dir / 'config.yml',
                global_config_dir / 'linter.json',
                global_config_dir / 'linter.yaml',
                global_config_dir / 'linter.yml',
            ]
            
            for config_file in config_files:
                if config_file.exists():
                    config = self._load_from_file(str(config_file), config_key)
                    if config is not None:
                        logger.info(f"Loaded linter config from global user config: {config_file}")
                        return config
        
        except Exception as e:
            logger.debug(f"Error checking global user config: {e}")
        
        logger.debug("No global user config found")
        return None
    
    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize configuration.
        
        Args:
            config: Raw configuration dictionary
            
        Returns:
            Validated and normalized configuration
        """
        # Ensure all required keys exist with defaults
        validated = self.DEFAULT_CONFIG.copy()
        
        if isinstance(config, dict):
            # Update with provided config
            validated.update(config)
            
            # Validate specific fields
            if 'mode' in config and config['mode'] not in ['blocking', 'warning', 'silent']:
                logger.warning(f"Invalid linter mode '{config['mode']}', using 'warning'")
                validated['mode'] = 'warning'
            
            if 'report' in config and isinstance(config['report'], dict):
                report_config = validated['report']
                report_config.update(config['report'])
                
                if 'format' in config['report'] and config['report']['format'] not in ['simple', 'detailed', 'json']:
                    logger.warning(f"Invalid report format '{config['report']['format']}', using 'simple'")
                    report_config['format'] = 'simple'
        
        return validated
    
    @classmethod
    def load_manager_config(cls, config_path: Optional[str] = None, 
                           source_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Load configuration specifically for LinterManager.
        
        This is a convenience method that loads the full configuration
        (not just the linter section) for use by LinterManager.
        
        Args:
            config_path: Explicit path to configuration file
            source_dir: Base directory for relative path resolution
            
        Returns:
            Full configuration dictionary for LinterManager
        """
        loader = cls(source_dir)
        
        # Try to load full config (without extracting just 'linter' section)
        if config_path:
            config = loader._load_from_file(config_path, config_key=None)
            if config is not None:
                return config
        
        # Check environment variable for full config
        env_config = os.environ.get('AUTOCODER_LINTER_CONFIG')
        if env_config:
            try:
                return json.loads(env_config)
            except json.JSONDecodeError:
                pass
        
        # Check project and global config files
        for config_source in [loader._load_from_project_config, loader._load_from_global_config]:
            config = config_source(config_key=None)  # Load full config
            if config is not None:
                return config
        
        # Return empty config if nothing found
        return {}


def load_linter_config(config_path: Optional[str] = None,
                      source_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to load and validate linter configuration.
    
    Args:
        config_path: Explicit path to configuration file
        source_dir: Base directory for relative path resolution
        
    Returns:
        Validated linter configuration dictionary
    """
    loader = LinterConfigLoader(source_dir)
    raw_config = loader.load_config(config_path)
    return loader.validate_config(raw_config)
