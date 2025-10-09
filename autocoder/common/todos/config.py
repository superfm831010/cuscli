"""
Todo manager configuration class.
"""

import os
import json
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class TodoManagerConfig:
    """Configuration class for todo manager"""
    
    storage_path: str = "./.auto-coder/todos"
    max_cache_size: int = 50
    cache_ttl: float = 300.0
    enable_compression: bool = False
    log_level: str = "INFO"
    
    def __post_init__(self):
        """Validate configuration"""
        self._validate()
    
    def _validate(self):
        """Validate configuration data"""
        # Validate storage path
        if not self.storage_path or not isinstance(self.storage_path, str):
            raise ValueError("Storage path cannot be empty")
        
        # Validate cache size
        if not isinstance(self.max_cache_size, int) or self.max_cache_size <= 0:
            raise ValueError("Cache size must be a positive integer")
        
        # Validate cache TTL
        if not isinstance(self.cache_ttl, (int, float)) or self.cache_ttl <= 0:
            raise ValueError("Cache TTL must be a positive number")
        
        # Validate log level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_levels:
            raise ValueError(f"Invalid log level: {self.log_level}, valid levels: {valid_levels}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "storage_path": self.storage_path,
            "max_cache_size": self.max_cache_size,
            "cache_ttl": self.cache_ttl,
            "enable_compression": self.enable_compression,
            "log_level": self.log_level
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TodoManagerConfig":
        """Create config from dictionary"""
        config = cls()
        
        for key, value in data.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        config._validate()
        return config
    
    @classmethod
    def from_env(cls, prefix: str = "TODO_") -> "TodoManagerConfig":
        """Create config from environment variables"""
        config = cls()
        
        env_mapping = {
            f"{prefix}STORAGE_PATH": "storage_path",
            f"{prefix}MAX_CACHE_SIZE": "max_cache_size",
            f"{prefix}CACHE_TTL": "cache_ttl",
            f"{prefix}ENABLE_COMPRESSION": "enable_compression",
            f"{prefix}LOG_LEVEL": "log_level"
        }
        
        for env_key, attr_name in env_mapping.items():
            env_value = os.environ.get(env_key)
            if env_value is not None:
                try:
                    if attr_name in ["max_cache_size"]:
                        value = int(env_value)
                    elif attr_name in ["cache_ttl"]:
                        value = float(env_value)
                    elif attr_name in ["enable_compression"]:
                        value = env_value.lower() in ["true", "1", "yes", "on"]
                    else:
                        value = env_value
                    
                    setattr(config, attr_name, value)
                except (ValueError, TypeError) as e:
                    raise ValueError(f"Environment variable {env_key} has invalid value '{env_value}': {e}")
        
        config._validate()
        return config
    
    def save_to_file(self, file_path: str):
        """Save config to file"""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_from_file(cls, file_path: str) -> "TodoManagerConfig":
        """Load config from file"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Config file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Config file format error: {e}")
    
    def copy(self) -> "TodoManagerConfig":
        """Create a deep copy of the config"""
        return TodoManagerConfig.from_dict(self.to_dict())
    
    def update(self, **kwargs):
        """Update config fields"""
        backup_values = {}
        for key in kwargs.keys():
            if hasattr(self, key):
                backup_values[key] = getattr(self, key)
            else:
                raise AttributeError(f"Config has no attribute: {key}")
        
        try:
            for key, value in kwargs.items():
                setattr(self, key, value)
            self._validate()
        except Exception:
            for key, value in backup_values.items():
                setattr(self, key, value)
            raise
    
    def __repr__(self) -> str:
        """String representation"""
        return (f"TodoManagerConfig("
                f"storage_path='{self.storage_path}', "
                f"max_cache_size={self.max_cache_size}, "
                f"cache_ttl={self.cache_ttl}, "
                f"log_level='{self.log_level}')")
    
    def __eq__(self, other) -> bool:
        """Equality comparison"""
        if not isinstance(other, TodoManagerConfig):
            return False
        
        return self.to_dict() == other.to_dict() 