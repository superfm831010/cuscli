"""
Library management functionality.

This module provides methods for managing libraries and their configurations.
"""

from typing import Dict, Any, Optional
from .models import LibsDict


class LibManagerMixin:
    """Mixin class providing library management functionality."""
    
    def get_libs(self) -> LibsDict:
        """Get all libraries."""
        return self._memory.libs.copy()
    
    def add_lib(self, name: str, config: Optional[Dict[str, Any]] = None) -> bool:
        """Add a library."""
        if name not in self._memory.libs:
            self._memory.libs[name] = config or {}
            self.save_memory()
            return True
        return False
    
    def remove_lib(self, name: str) -> bool:
        """Remove a library."""
        if name in self._memory.libs:
            del self._memory.libs[name]
            self.save_memory()
            return True
        return False
    
    def has_lib(self, name: str) -> bool:
        """Check if library exists."""
        return name in self._memory.libs
    
    def set_lib_config(self, name: str, config: Dict[str, Any]):
        """Set configuration for a library."""
        if name in self._memory.libs:
            self._memory.libs[name] = config
            self.save_memory()
    
    def get_lib_config(self, name: str) -> Dict[str, Any]:
        """Get configuration for a library."""
        return self._memory.libs.get(name, {})
    
    def set_lib_proxy(self, proxy_url: str):
        """Set library proxy URL."""
        self.set_config("lib-proxy", proxy_url)
    
    def get_lib_proxy(self) -> str:
        """Get library proxy URL."""
        return self.get_config("lib-proxy", "https://github.com/allwefantasy/llm_friendly_packages")
